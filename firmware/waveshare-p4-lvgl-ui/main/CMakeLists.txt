file(GLOB_RECURSE UI_SOURCES
    "ui/*.c"
)

idf_component_register(
    SRCS "display_touch.c" "brightness_control.c" ${UI_SOURCES}
    INCLUDE_DIRS "." "ui"
    PRIV_REQUIRES
        waveshare__esp_lcd_dsi
        esp_lcd
        esp_driver_gpio
        esp_driver_i2c
        esp_driver_spi
        esp_hw_support
        esp_timer
        esp_mm
        lvgl__lvgl
        espressif__esp_lvgl_port
)
# LVGL Pro generated headers support a simple LVGL include when this is defined.
target_compile_definitions(${COMPONENT_LIB} PRIVATE LV_LVGL_H_INCLUDE_SIMPLE=1)
