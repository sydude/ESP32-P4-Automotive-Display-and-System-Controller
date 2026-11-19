#include "display_touch.h"

void app_main(void)
{
    /*
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
    */    
   display_touch_init();
}