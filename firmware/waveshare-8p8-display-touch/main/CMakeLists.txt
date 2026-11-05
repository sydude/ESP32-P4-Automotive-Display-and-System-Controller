idf_component_register(SRCS "display_touch.c"
    PRIV_REQUIRES waveshare__esp_lcd_dsi esp_lcd esp_driver_gpio
                  esp_driver_i2c esp_driver_spi esp_hw_support esp_timer esp_mm lvgl__lvgl espressif__esp_lvgl_port)
