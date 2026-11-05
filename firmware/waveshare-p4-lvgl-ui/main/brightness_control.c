#include "brightness_control.h"
#include "brightness_subject.h"
#include "esp_log.h"

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
    }
    return err;
}

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
    if (backlight_error == ESP_OK) {
        /* No off/zero step: keep the screen visible throughout startup. */
        backlight_error = write_percent(BRIGHTNESS_DEFAULT);
    }
    if (backlight_error != ESP_OK) {
        ESP_LOGW(TAG, "Backlight unavailable: %s; display and touch continue", esp_err_to_name(backlight_error));
    } else {
        ESP_LOGI(TAG, "Backlight 0x45 register 0x96: %d%%", applied_percent);
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
        ESP_LOGW(TAG, "Brightness write failed: %s", esp_err_to_name(backlight_error));
        show_failure();
        lv_timer_pause(update_timer); /* No retry storm on a shared bus. */
    }
}

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
    lv_subject_set_int(brightness_subject(), applied_percent);
    update_timer = lv_timer_create(update_brightness, BRIGHTNESS_UPDATE_MS, NULL);
    if (!update_timer) {
        lv_obj_add_state(slider, LV_STATE_DISABLED);
        lv_label_set_text(status_label, "Brightness updates unavailable | Reboot to retry");
        ESP_LOGE(TAG, "Could not allocate brightness timer");
    }
}
