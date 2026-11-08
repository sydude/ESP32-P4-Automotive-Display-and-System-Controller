#include "ui/basicrace1920x480v1.h"
#include "brightness_control.h"
#include "soc/soc_caps.h"

#if SOC_MIPI_DSI_SUPPORTED

#include <inttypes.h>
#include <assert.h>
#include <string.h>
#include "esp_lvgl_port.h"
#include "esp_check.h"
#include "freertos/FreeRTOS.h"
#include "freertos/semphr.h"
#include "freertos/task.h"
#include "driver/spi_master.h"
#include "driver/gpio.h"
#include "esp_heap_caps.h"
#include "esp_log.h"
#include "esp_timer.h"
#include "esp_lcd_panel_ops.h"
#include "esp_lcd_panel_io.h"
#include "esp_ldo_regulator.h"
#include "esp_dma_utils.h"
#include "esp_lcd_mipi_dsi.h"
#include "esp_lcd_dsi.h"

#include "driver/i2c_master.h"

#define TEST_LCD_H_RES (480)
#define TEST_LCD_V_RES (1920)
#define TEST_LCD_BIT_PER_PIXEL (24)
#define TEST_PIN_NUM_LCD_RST (-1)
#define TEST_PIN_NUM_BK_LIGHT (-1) // set to -1 if not used
#define TEST_LCD_BK_LIGHT_ON_LEVEL (1)
#define TEST_LCD_BK_LIGHT_OFF_LEVEL !TEST_LCD_BK_LIGHT_ON_LEVEL

#if TEST_LCD_BIT_PER_PIXEL == 24
#define TEST_MIPI_DPI_PX_FORMAT (LCD_COLOR_PIXEL_FORMAT_RGB888)
#elif TEST_LCD_BIT_PER_PIXEL == 18
#define TEST_MIPI_DPI_PX_FORMAT (LCD_COLOR_PIXEL_FORMAT_RGB666)
#elif TEST_LCD_BIT_PER_PIXEL == 16
#define TEST_MIPI_DPI_PX_FORMAT (LCD_COLOR_PIXEL_FORMAT_RGB565)
#endif

#define TEST_DELAY_TIME_MS (3000)

#define TEST_MIPI_DSI_PHY_PWR_LDO_CHAN (3)
#define TEST_MIPI_DSI_PHY_PWR_LDO_VOLTAGE_MV (2500)

static char *TAG = "waveshare_display_touch";
static esp_ldo_channel_handle_t ldo_mipi_phy = NULL;
static esp_lcd_panel_handle_t panel_handle = NULL;
static esp_lcd_dsi_bus_handle_t mipi_dsi_bus = NULL;
static esp_lcd_panel_io_handle_t mipi_dbi_io = NULL;
static void test_init_lcd(void)
{
#if TEST_PIN_NUM_BK_LIGHT >= 0
    ESP_LOGI(TAG, "Turn on LCD backlight");
    gpio_config_t bk_gpio_config = {
        .mode = GPIO_MODE_OUTPUT,
        .pin_bit_mask = 1ULL << TEST_PIN_NUM_BK_LIGHT};
    ESP_ERROR_CHECK(gpio_config(&bk_gpio_config));
    ESP_ERROR_CHECK(gpio_set_level(TEST_PIN_NUM_BK_LIGHT, TEST_LCD_BK_LIGHT_ON_LEVEL));
#endif

    // Turn on the power for MIPI DSI PHY, so it can go from "No Power" state to "Shutdown" state
#ifdef TEST_MIPI_DSI_PHY_PWR_LDO_CHAN
    ESP_LOGI(TAG, "MIPI DSI PHY Powered on");
    esp_ldo_channel_config_t ldo_mipi_phy_config = {
        .chan_id = TEST_MIPI_DSI_PHY_PWR_LDO_CHAN,
        .voltage_mv = TEST_MIPI_DSI_PHY_PWR_LDO_VOLTAGE_MV,
    };
    ESP_ERROR_CHECK(esp_ldo_acquire_channel(&ldo_mipi_phy_config, &ldo_mipi_phy));
#endif

    ESP_LOGI(TAG, "Initialize MIPI DSI bus");
    esp_lcd_dsi_bus_config_t bus_config = DSI_PANEL_BUS_DSI_2CH_CONFIG();
    ESP_ERROR_CHECK(esp_lcd_new_dsi_bus(&bus_config, &mipi_dsi_bus));

    ESP_LOGI(TAG, "Install panel IO");
    esp_lcd_dbi_io_config_t dbi_config = DSI_PANEL_IO_DBI_CONFIG();
    ESP_ERROR_CHECK(esp_lcd_new_panel_io_dbi(mipi_dsi_bus, &dbi_config, &mipi_dbi_io));

    ESP_LOGI(TAG, "Install LCD driver of dsi");
    esp_lcd_dpi_panel_config_t dpi_config = DSI_PANEL_DPI_8_8_INCH_CONFIG(TEST_MIPI_DPI_PX_FORMAT);
    dsi_vendor_config_t vendor_config = {
        .mipi_config = {
            .dsi_bus = mipi_dsi_bus,
            .dpi_config = &dpi_config,
        },
    };
    const esp_lcd_panel_dev_config_t panel_config = {
        .reset_gpio_num = TEST_PIN_NUM_LCD_RST,
        .rgb_ele_order = LCD_RGB_ELEMENT_ORDER_RGB,
        .bits_per_pixel = TEST_LCD_BIT_PER_PIXEL,
        .vendor_config = &vendor_config,
    };
    ESP_ERROR_CHECK(esp_lcd_new_panel_dsi(mipi_dbi_io, &panel_config, &panel_handle));
    ESP_ERROR_CHECK(esp_lcd_panel_init(panel_handle));

    // The Waveshare IDF 6 driver enables async DMA2D. Small CPU copies make
    // draw_bitmap synchronous, including framebuffer cache writeback.
    ESP_ERROR_CHECK(esp_lcd_dpi_panel_disable_dma2d(panel_handle));
}

#define GUI_WIDTH 1920
#define GUI_HEIGHT 480
#define DRAW_PIXELS (GUI_WIDTH * 8)
#define DRAW_BYTES (DRAW_PIXELS * 3)

static i2c_master_dev_handle_t gt;
static uint8_t *rotated_pixels;

static void flush_landscape(lv_display_t *display, const lv_area_t *area, uint8_t *pixels)
{
    const int width = lv_area_get_width(area);
    const int height = lv_area_get_height(area);
    const uint32_t stride = lv_draw_buf_width_to_stride(width, LV_COLOR_FORMAT_RGB888);
    assert((size_t)width * height <= DRAW_PIXELS);
    // Inverse of touch mapping: native_x = 479 - gui_y, native_y = gui_x.
    // Pack a native rectangle of width=height and height=width, no row padding.
    for (int y = 0; y < height; ++y) {
        for (int x = 0; x < width; ++x) {
            memcpy(rotated_pixels + ((size_t)x * height + height - 1 - y) * 3,
                   pixels + (size_t)y * stride + x * 3, 3);
        }
    }
    ESP_ERROR_CHECK(esp_lcd_panel_draw_bitmap(panel_handle,
        GUI_HEIGHT - 1 - area->y2, area->x1,
        GUI_HEIGHT - area->y1, area->x2 + 1, rotated_pixels));
    // No asynchronous hook or ISR callback: the CPU copy is complete on return.
    lv_display_flush_ready(display);
}

// Temporary release diagnostics: no extra I2C traffic or input filtering.
// Buffer fresh pressed reports; print only around release, at most 120 lines/boot.
#define TOUCH_DIAG_HISTORY 4
#define TOUCH_DIAG_LINES 120
#define TOUCH_DIAG_REPRESS_US 250000

typedef struct {
    int64_t time_us;
    uint8_t status;
    esp_err_t status_err, point_err, clear_err;
    bool raw_valid, pressed;
    unsigned raw_x, raw_y;
    lv_point_t output;
} touch_diag_report_t;

static void touch_diag_log(const char *event, const touch_diag_report_t *r)
{
    static unsigned lines;
    if (lines >= TOUCH_DIAG_LINES) {
        return;
    }
    ESP_LOGI(TAG, "GT9271 %s t=%" PRId64 "us status=0x%02x count=%u "
             "err(status/point/clear)=%d/%d/%d raw_valid=%u raw=(%u,%u) "
             "mapped=(%d,%d) out=(%d,%d) state=%s",
             event, r->time_us, (unsigned)r->status, (unsigned)(r->status & 0x0f),
             (int)r->status_err, (int)r->point_err, (int)r->clear_err,
             (unsigned)r->raw_valid, r->raw_x, r->raw_y,
             r->raw_valid ? (int)r->raw_y : -1,
             r->raw_valid ? GUI_HEIGHT - 1 - (int)r->raw_x : -1,
             (int)r->output.x, (int)r->output.y, r->pressed ? "PRESSED" : "RELEASED");
    if (++lines == TOUCH_DIAG_LINES) {
        ESP_LOGI(TAG, "GT9271 diagnostic limit reached; reboot to capture more");
    }
}

static void touch_diag_record(const touch_diag_report_t *r, bool was_pressed)
{
    static touch_diag_report_t history[TOUCH_DIAG_HISTORY];
    static unsigned next, used;
    static int64_t release_us;
    static bool had_release;
    if (was_pressed && !r->pressed) {
        for (unsigned i = 0; i < used; ++i) {
            touch_diag_log("last-pressed", &history[(next + TOUCH_DIAG_HISTORY - used + i) % TOUCH_DIAG_HISTORY]);
        }
        touch_diag_log("release", r);
        next = used = 0;
        release_us = r->time_us;
        had_release = true;
    } else if (!was_pressed && r->pressed) {
        if (had_release && r->time_us - release_us <= TOUCH_DIAG_REPRESS_US) {
            touch_diag_log("immediate-repress", r);
        }
        had_release = false;
    }
    if (r->pressed && r->status_err == ESP_OK && (r->status & 0x80)) {
        history[next] = *r;
        next = (next + 1) % TOUCH_DIAG_HISTORY;
        if (used < TOUCH_DIAG_HISTORY) {
            ++used;
        }
    }
}

static void read_touch(lv_indev_t *indev, lv_indev_data_t *data)
{
    static lv_point_t last_point;
    static bool pressed;
    const bool was_pressed = pressed;
    touch_diag_report_t diag = {
        .time_us = esp_timer_get_time(),
        // NOT_FINISHED means this transaction was not attempted.
        .point_err = ESP_ERR_NOT_FINISHED,
        .clear_err = ESP_ERR_NOT_FINISHED,
    };
    const uint8_t status_reg[] = {0x81, 0x4e};
    uint8_t status = 0;
    esp_err_t err = i2c_master_transmit_receive(gt, status_reg, 2, &status, 1, 100);
    diag.status = status;
    diag.status_err = err;
    if (err != ESP_OK) {
        pressed = false;
    } else if (status & 0x80) {
        const unsigned count = status & 0x0f;
        pressed = false;
        if (count > 0 && count <= 5) {
            const uint8_t point_reg[] = {0x81, 0x4f};
            uint8_t point[8];
            err = i2c_master_transmit_receive(gt, point_reg, 2, point, sizeof(point), 100);
            diag.point_err = err;
            if (err == ESP_OK) {
                unsigned raw_x = point[1] | (point[2] << 8);
                unsigned raw_y = point[3] | (point[4] << 8);
                diag.raw_valid = true;
                diag.raw_x = raw_x;
                diag.raw_y = raw_y;
                if (raw_x < GUI_HEIGHT && raw_y < GUI_WIDTH) {
                    last_point.x = raw_y;
                    last_point.y = GUI_HEIGHT - 1 - raw_x;
                    pressed = true;
                }
            }
        }
        const uint8_t clear[] = {0x81, 0x4e, 0};
        diag.clear_err = i2c_master_transmit(gt, clear, sizeof(clear), 100);
        if (diag.clear_err != ESP_OK) {
            pressed = false;
        }
    }
    // A not-ready status is not a release; retain state until a fresh report.
    data->point = last_point;
    data->state = pressed ? LV_INDEV_STATE_PRESSED : LV_INDEV_STATE_RELEASED;
    diag.output = last_point;
    diag.pressed = pressed;
    touch_diag_record(&diag, was_pressed);
}

static void start_gui(void)
{
    lvgl_port_cfg_t port_cfg = ESP_LVGL_PORT_INIT_CONFIG();
    port_cfg.task_max_sleep_ms = 20;
    ESP_ERROR_CHECK(lvgl_port_init(&port_cfg));
    assert(lvgl_port_lock(0));
    // Use the port for task/tick/mutex only. Its display helper uses PPA for
    // rotation on P4; this explicit partial flush avoids those constraints.
    uint8_t *draw_pixels = heap_caps_aligned_alloc(CONFIG_LV_DRAW_BUF_ALIGN,
        DRAW_BYTES, MALLOC_CAP_SPIRAM | MALLOC_CAP_8BIT);
    rotated_pixels = heap_caps_malloc(DRAW_BYTES, MALLOC_CAP_SPIRAM | MALLOC_CAP_8BIT);
    assert(draw_pixels && rotated_pixels);
    lv_display_t *display = lv_display_create(GUI_WIDTH, GUI_HEIGHT);
    assert(display);
    lv_display_set_color_format(display, LV_COLOR_FORMAT_RGB888);
    lv_display_set_buffers(display, draw_pixels, NULL, DRAW_BYTES, LV_DISPLAY_RENDER_MODE_PARTIAL);
    lv_display_set_flush_cb(display, flush_landscape);
    // The generated UI owns the screen and its graphics resources.
    // The display driver, rotation, and touch handling remain unchanged.
    lv_display_set_default(display);
    basicrace1920x480v1_init(NULL);
    lv_obj_t *screen = screen_main_create();
    assert(screen);
    brightness_control_attach(screen);
    lv_screen_load(screen);
    lv_indev_t *input = lv_indev_create();
    assert(input);
    lv_indev_set_type(input, LV_INDEV_TYPE_POINTER);
    lv_indev_set_display(input, display);
    lv_indev_set_read_cb(input, read_touch);
    lvgl_port_unlock();
    ESP_LOGI(TAG, "LVGL Pro screen loaded: landscape 1920x480; 46080-byte draw and rotation buffers");
}

void app_main(void)
{
    test_init_lcd();
    i2c_master_bus_handle_t gt_bus;
    ESP_ERROR_CHECK(i2c_master_get_bus_handle(I2C_NUM_1, &gt_bus));
    const i2c_device_config_t gt_cfg = {
        .dev_addr_length = I2C_ADDR_BIT_LEN_7,
        .device_address = 0x14,
        .scl_speed_hz = 100000,
    };
    ESP_ERROR_CHECK(i2c_master_bus_add_device(gt_bus, &gt_cfg, &gt));
    const uint8_t id_reg[] = {0x81, 0x40};
    char product_id[5] = {0};
    ESP_ERROR_CHECK(i2c_master_transmit_receive(gt, id_reg, 2, (uint8_t *)product_id, 4, 100));
    ESP_LOGI(TAG, "Touch controller product ID: %s", product_id);
    brightness_control_init(gt_bus);
    start_gui();
}
#endif
