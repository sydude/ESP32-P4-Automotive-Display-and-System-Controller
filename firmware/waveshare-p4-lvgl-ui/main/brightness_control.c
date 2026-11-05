#include "brightness_control.h"
#include "brightness_subject.h"
#include "esp_log.h"
#ifdef ESP_PLATFORM
#include "sdkconfig.h"
#endif
#ifdef CONFIG_BACKLIGHT_DIAGNOSTIC
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#endif

/* Verified against waveshare/esp_lcd_dsi 2.0.0 and the Waveshare WIFI6-DB BSP.
 * The DSI driver owns bus creation and the C0/C2/AC/AB/AA/AD init sequence.
 * Never replay that sequence here: it also affects the shared touch hardware.
 */
#define BACKLIGHT_ADDRESS 0x45
#define BACKLIGHT_REGISTER 0x96
#define BACKLIGHT_TIMEOUT_MS 20
#define BRIGHTNESS_UPDATE_MS 50
#define BRIGHTNESS_DEFAULT 75

static const char *TAG = "brightness";
static i2c_master_dev_handle_t backlight;
static esp_err_t backlight_error = ESP_ERR_INVALID_STATE;
static int applied_percent = -1; /* Last successful transmit, not readback. */
static lv_obj_t *slider;
static lv_obj_t *percent_label;
static lv_obj_t *status_label;
static lv_timer_t *update_timer;

static int clamp_percent(int value)
{
    return value < 10 ? 10 : value > 100 ? 100 : value;
}

static esp_err_t write_percent(int percent)
{
    percent = clamp_percent(percent);
    /* Match the vendor's integer scaling: 10->25, 75->191, 100->255. */
    const uint8_t command[] = {BACKLIGHT_REGISTER, (uint8_t)(255U * (unsigned)percent / 100U)};
    esp_err_t err = i2c_master_transmit(backlight, command, sizeof(command), BACKLIGHT_TIMEOUT_MS);
    if (err == ESP_OK) {
        applied_percent = percent;
        /* Temporary diagnostics: successful transmit, not brightness readback. */
        ESP_LOGI(TAG, "Backlight I2C write OK: requested=%d%%, 7-bit address=0x%02X, register=0x%02X, byte=0x%02X (%u)",
                 percent, BACKLIGHT_ADDRESS, BACKLIGHT_REGISTER, (unsigned)command[1], (unsigned)command[1]);
    } else {
        ESP_LOGE(TAG, "Backlight I2C write FAILED: requested=%d%%, 7-bit address=0x%02X, register=0x%02X, byte=0x%02X (%u): %s",
                 percent, BACKLIGHT_ADDRESS, BACKLIGHT_REGISTER, (unsigned)command[1], (unsigned)command[1], esp_err_to_name(err));
    }
    return err;
}

#ifdef CONFIG_BACKLIGHT_DIAGNOSTIC
/* No LVGL access in this worker. The diagnostic build never creates the
 * slider timer; the I2C master driver serializes transactions with touch.
 * A brightness transaction may occur between touch transactions, but never
 * writes any touch register or replays panel initialization.
 */
static bool diagnostic_started;
static void backlight_diagnostic(void *arg)
{
    (void)arg;
    ESP_LOGW(TAG, "DIAG begin: 3 cycles, 100%%/10%%, 3000 ms each; slider writes disabled");
    ESP_LOGW(TAG, "DIAG readback skipped: no documented safe 0x96 read protocol");
    bool failed = false;
    for (unsigned step = 0; step < 6; ++step) {
        const int percent = step % 2 == 0 ? 100 : 10;
        ESP_LOGI(TAG, "DIAG cycle %u/3: command %d%%, hold 3000 ms", step / 2 + 1, percent);
        if (write_percent(percent) != ESP_OK) {
            failed = true;
            ESP_LOGE(TAG, "DIAG aborted after write failure; no further cycle commands");
            break;
        }
        vTaskDelay(pdMS_TO_TICKS(3000));
    }
    /* One bounded recovery attempt even after failure, never a retry loop. */
    ESP_LOGI(TAG, "DIAG restore: command 75%%");
    esp_err_t restore = write_percent(BRIGHTNESS_DEFAULT);
    ESP_LOGW(TAG, "DIAG end: cycles=%s, restore=%s; slider stays disabled; ACK is not optical feedback",
             failed ? "aborted" : "complete", esp_err_to_name(restore));
    vTaskDelete(NULL);
}
#endif

void brightness_control_init(i2c_master_bus_handle_t bus)
{
    /* Reuse the vendor's existing bus; GT9271 is a separate 0x14 device. */
    backlight_error = i2c_master_probe(bus, BACKLIGHT_ADDRESS, BACKLIGHT_TIMEOUT_MS);
    if (backlight_error == ESP_OK) {
        const i2c_device_config_t config = {
            .dev_addr_length = I2C_ADDR_BIT_LEN_7,
            .device_address = BACKLIGHT_ADDRESS,
            .scl_speed_hz = 100000,
        };
        backlight_error = i2c_master_bus_add_device(bus, &config, &backlight);
    }
#ifndef CONFIG_BACKLIGHT_DIAGNOSTIC
    if (backlight_error == ESP_OK) {
        /* No off/zero step: keep the screen visible throughout startup. */
        backlight_error = write_percent(BRIGHTNESS_DEFAULT);
    }
#endif
    if (backlight_error != ESP_OK) {
        ESP_LOGW(TAG, "Backlight unavailable: %s; display and touch continue", esp_err_to_name(backlight_error));
    } else {
#ifdef CONFIG_BACKLIGHT_DIAGNOSTIC
        ESP_LOGW(TAG, "DIAG ready: backlight registered; test starts when UI attaches");
#else
        ESP_LOGI(TAG, "Backlight 0x45 register 0x96: %d%%", applied_percent);
#endif
    }
}

static void show_failure(void)
{
    lv_obj_add_state(slider, LV_STATE_DISABLED);
    if (applied_percent >= 10) {
        lv_subject_set_int(brightness_subject(), applied_percent);
        lv_label_set_text(status_label, "Write failed | Last sent value shown | Reboot to retry");
    } else {
        lv_label_set_text(percent_label, "Unavailable");
        lv_label_set_text(status_label, "Backlight unavailable | Display and touch still active");
    }
}

#ifndef CONFIG_BACKLIGHT_DIAGNOSTIC
static void update_brightness(lv_timer_t *timer)
{
    (void)timer;
    /* This timer and read_touch run in the same LVGL task. No competing worker
     * can interrupt GT9271's status/point/clear transaction sequence.
     * The synchronous I2C master API also serializes bus transactions.
     */
    int requested = clamp_percent(lv_subject_get_int(brightness_subject()));
    if (requested != lv_subject_get_int(brightness_subject())) {
        lv_subject_set_int(brightness_subject(), requested);
    }
    if (requested == applied_percent) {
        return;
    }
    backlight_error = write_percent(requested);
    if (backlight_error != ESP_OK) {
        show_failure();
        lv_timer_pause(update_timer); /* No retry storm on a shared bus. */
    }
}

#endif

static void screen_deleted(lv_event_t *event)
{
    (void)event;
    if (update_timer) {
        lv_timer_delete(update_timer);
        update_timer = NULL;
    }
    slider = percent_label = status_label = NULL;
}

void brightness_control_attach(lv_obj_t *screen)
{
    slider = lv_obj_find_by_name(screen, "brightness_slider");
    percent_label = lv_obj_find_by_name(screen, "brightness_percent");
    status_label = lv_obj_find_by_name(screen, "brightness_status");
    if (!slider || !percent_label || !status_label) {
        /* A stale export must never result in writes from an invisible control. */
        ESP_LOGE(TAG, "Missing brightness widgets; regenerate and sync the LVGL Pro project");
        return;
    }
    lv_obj_add_event_cb(screen, screen_deleted, LV_EVENT_DELETE, NULL);
    if (backlight_error != ESP_OK) {
        show_failure();
        return;
    }
#ifdef CONFIG_BACKLIGHT_DIAGNOSTIC
    lv_obj_add_state(slider, LV_STATE_DISABLED);
    lv_label_set_text(percent_label, "Diagnostic");
    lv_label_set_text(status_label, "Backlight test | See serial log");
    if (!diagnostic_started) {
        diagnostic_started = true; /* Run once per boot, even if screen is recreated. */
        if (xTaskCreate(backlight_diagnostic, "backlight_diag", 4096, NULL, 2, NULL) != pdPASS) {
            lv_label_set_text(status_label, "Backlight test could not start");
            ESP_LOGE(TAG, "DIAG task creation failed; no brightness commands sent");
        }
    }
#else
    lv_subject_set_int(brightness_subject(), applied_percent);
    update_timer = lv_timer_create(update_brightness, BRIGHTNESS_UPDATE_MS, NULL);
    if (!update_timer) {
        lv_obj_add_state(slider, LV_STATE_DISABLED);
        lv_label_set_text(status_label, "Brightness updates unavailable | Reboot to retry");
        ESP_LOGE(TAG, "Could not allocate brightness timer");
    }
#endif
}
