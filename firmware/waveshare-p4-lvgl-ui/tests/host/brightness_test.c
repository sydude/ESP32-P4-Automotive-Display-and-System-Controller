/* Real LVGL + compiled UI and firmware handler; only I2C is mocked. */
#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "brightness_control.h"
#include "brightness_subject.h"

static const char *mode;
static int attempts;
static uint8_t bytes[16];
static uint8_t last_byte;
static bool fail_writes;
_Alignas(64) static uint8_t framebuffer[1920 * 480 * 3];
static lv_point_t pointer;
static bool pointer_down;
static int flushes;

esp_err_t i2c_master_probe(i2c_master_bus_handle_t bus, uint16_t address, int timeout)
{
    assert(bus == (void *)1 && address == 0x45 && timeout == 20);
    return strcmp(mode, "probe_failure") == 0 ? ESP_FAIL : ESP_OK;
}
esp_err_t i2c_master_bus_add_device(i2c_master_bus_handle_t bus, const i2c_device_config_t *cfg, i2c_master_dev_handle_t *out)
{
    assert(bus == (void *)1 && cfg->device_address == 0x45 && cfg->scl_speed_hz == 100000);
    *out = (void *)2;
    return ESP_OK;
}
esp_err_t i2c_master_transmit(i2c_master_dev_handle_t dev, const uint8_t *data, size_t size, int timeout)
{
    assert(dev == (void *)2 && size == 2 && data[0] == 0x96 && timeout == 20);
    bytes[attempts] = data[1];
    ++attempts;
    last_byte = data[1];
    return fail_writes || (strcmp(mode, "diagnostic_mid_failure") == 0 && attempts == 4) ? ESP_FAIL : ESP_OK;
}
static void flush(lv_display_t *display, const lv_area_t *area, uint8_t *pixels)
{
    (void)area; (void)pixels;
    ++flushes;
    lv_display_flush_ready(display);
}
static void read_pointer(lv_indev_t *indev, lv_indev_data_t *data)
{
    (void)indev;
    data->point = pointer;
    data->state = pointer_down ? LV_INDEV_STATE_PRESSED : LV_INDEV_STATE_RELEASED;
}
static void run_ms(unsigned ms)
{
    for (unsigned i = 0; i < ms; i += 5) {
        lv_tick_inc(5);
        lv_timer_handler();
    }
}
#ifdef CONFIG_BACKLIGHT_DIAGNOSTIC
static void (*worker)(void *);
static int delays, deletes;
int xTaskCreate(void (*task)(void *), const char *name, unsigned stack, void *arg, unsigned priority, void *handle)
{
    (void)name; (void)stack; (void)arg; (void)priority; (void)handle;
    if (strcmp(mode, "task_failure") == 0) return 0;
    assert(!worker);
    worker = task;
    return 1;
}
void vTaskDelay(unsigned ms)
{
    assert(ms == 3000);
    ++delays;
    int before = attempts;
    lv_subject_set_int(brightness_subject(), 42);
    run_ms(ms);
    assert(attempts == before); /* Slider subject cannot introduce writes. */
}
void vTaskDelete(void *task) { assert(!task); ++deletes; }
#endif
int main(int argc, char **argv)
{
    assert(argc >= 2);
    mode = argv[1];
    fail_writes = strcmp(mode, "init_write_failure") == 0;
    brightness_control_init((void *)1);
    lv_init();
    lv_display_t *display = lv_display_create(1920, 480);
    lv_display_set_color_format(display, LV_COLOR_FORMAT_RGB888);
    lv_display_set_buffers(display, framebuffer, NULL, sizeof(framebuffer), LV_DISPLAY_RENDER_MODE_DIRECT);
    lv_display_set_flush_cb(display, flush);
    basicrace1920x480v1_init(NULL);
    lv_obj_t *screen = screen_main_create();
    brightness_control_attach(screen);
    lv_screen_load(screen);
    lv_indev_t *input = lv_indev_create();
    lv_indev_set_type(input, LV_INDEV_TYPE_POINTER);
    lv_indev_set_display(input, display);
    lv_indev_set_read_cb(input, read_pointer);
    lv_obj_update_layout(screen);
    lv_refr_now(display);
    run_ms(100);
    lv_obj_t *slider = lv_obj_find_by_name(screen, "brightness_slider");
    lv_obj_t *percent = lv_obj_find_by_name(screen, "brightness_percent");
    lv_obj_t *status = lv_obj_find_by_name(screen, "brightness_status");
    assert(slider && percent && status);
    assert(flushes > 0);
    assert(lv_obj_get_width(slider) == 600 && lv_obj_get_height(slider) == 32);
    assert(lv_slider_get_min_value(slider) == 10 && lv_slider_get_max_value(slider) == 100);
#ifdef CONFIG_BACKLIGHT_DIAGNOSTIC
    assert(lv_obj_has_state(slider, LV_STATE_DISABLED));
    assert(attempts == 0);
    if (strcmp(mode, "probe_failure") == 0 || strcmp(mode, "task_failure") == 0) {
        assert(!worker);
        return 0;
    }
    assert(worker);
    fail_writes = strcmp(mode, "diagnostic_failure") == 0;
    worker(NULL);
    assert(deletes == 1);
    if (fail_writes) {
        assert(attempts == 2 && delays == 0 && bytes[0] == 255 && bytes[1] == 191);
    } else if (strcmp(mode, "diagnostic_mid_failure") == 0) {
        const uint8_t expected[] = {255, 25, 255, 25, 191};
        assert(attempts == 5 && delays == 3);
        assert(memcmp(bytes, expected, sizeof(expected)) == 0);
    } else {
        const uint8_t expected[] = {255, 25, 255, 25, 255, 25, 191};
        assert(attempts == 7 && delays == 6);
        assert(memcmp(bytes, expected, sizeof(expected)) == 0);
    }
    int diagnostic_before = attempts;
    run_ms(10000);
    brightness_control_attach(screen);
    run_ms(10000);
    assert(attempts == diagnostic_before && deletes == 1);
    puts("Diagnostic payloads, holds, bounded failure, slider isolation and single run passed");
    return 0;
#endif
    if (strcmp(mode, "probe_failure") == 0 || fail_writes) {
        assert(lv_obj_has_state(slider, LV_STATE_DISABLED));
        assert(strcmp(lv_label_get_text(percent), "Unavailable") == 0);
        assert(attempts == (fail_writes ? 1 : 0));
        puts("Startup failure safely disables brightness UI");
        return 0;
    }
    assert(attempts == 1 && last_byte == 191);
    assert(strcmp(lv_label_get_text(percent), "75%") == 0);
    if (strcmp(mode, "update_failure") == 0) {
        fail_writes = true;
        lv_subject_set_int(brightness_subject(), 50);
        run_ms(100);
        assert(attempts == 2 && lv_obj_has_state(slider, LV_STATE_DISABLED));
        assert(lv_subject_get_int(brightness_subject()) == 75);
        assert(strstr(lv_label_get_text(status), "Write failed"));
        run_ms(500);
        assert(attempts == 2);
        puts("Failed update restores last sent value and stops retries");
        return 0;
    }
    /* A real LVGL pointer press and drag drives the compiled slider binding. */
    lv_area_t coords;
    lv_obj_get_coords(slider, &coords);
    pointer = (lv_point_t){coords.x1 + (coords.x2 - coords.x1) * 65 / 90, (coords.y1 + coords.y2) / 2};
    pointer_down = true;
    run_ms(100);
    pointer.x = coords.x1;
    run_ms(100);
    assert(lv_subject_get_int(brightness_subject()) == 10 && last_byte == 25);
    pointer.x = coords.x2;
    run_ms(100);
    pointer_down = false;
    run_ms(100);
    assert(lv_subject_get_int(brightness_subject()) == 100 && last_byte == 255);
    assert(strcmp(lv_label_get_text(percent), "100%") == 0);
    pointer.x = coords.x1 + (coords.x2 - coords.x1) * 40 / 90;
    pointer_down = true;
    run_ms(100);
    pointer_down = false;
    run_ms(100);
    assert(lv_subject_get_int(brightness_subject()) >= 49 && lv_subject_get_int(brightness_subject()) <= 51);
    int before = attempts;
    run_ms(250);
    assert(attempts == before); /* No redundant writes. */
    lv_subject_set_int(brightness_subject(), -100);
    run_ms(100);
    assert(lv_subject_get_int(brightness_subject()) == 10 && last_byte == 25);
    lv_subject_set_int(brightness_subject(), 1000);
    run_ms(100);
    assert(lv_subject_get_int(brightness_subject()) == 100 && last_byte == 255);
    /* Latest value wins within a timer period. */
    before = attempts;
    lv_subject_set_int(brightness_subject(), 20);
    lv_subject_set_int(brightness_subject(), 40);
    lv_subject_set_int(brightness_subject(), 75);
    run_ms(100);
    assert(attempts == before + 1 && last_byte == 191);
    if (argc > 2) {
        lv_obj_invalidate(screen);
        lv_refr_now(display);
        assert(flushes > 0);
        FILE *image = fopen(argv[2], "wb");
        assert(image);
        fprintf(image, "P6\n1920 480\n255\n");
        /* LVGL RGB888 stores B,G,R bytes; PPM expects R,G,B. */
        for (size_t i = 0; i < sizeof(framebuffer); i += 3) {
            fputc(framebuffer[i + 2], image);
            fputc(framebuffer[i + 1], image);
            fputc(framebuffer[i], image);
        }
        fclose(image);
    }
    lv_obj_t *empty = lv_obj_create(NULL);
    lv_screen_load(empty);
    lv_obj_delete(screen);
    before = attempts;
    lv_subject_set_int(brightness_subject(), 50);
    run_ms(100);
    assert(attempts == before); /* Timer is gone with its screen. */
    puts("Pointer drag, bounds, label binding, coalescing, and lifecycle passed");
    return 0;
}
