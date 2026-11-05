file(GLOB_RECURSE UI_SOURCES CONFIGURE_DEPENDS
    "ui/*.c"
)

idf_component_register(
    SRCS "display_touch.c" ${UI_SOURCES}
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