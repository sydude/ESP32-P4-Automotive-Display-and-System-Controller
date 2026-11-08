#pragma once
#include <stdint.h>
#include <stddef.h>
typedef int esp_err_t;
typedef void *i2c_master_bus_handle_t;
typedef void *i2c_master_dev_handle_t;
typedef struct { int dev_addr_length; unsigned device_address; unsigned scl_speed_hz; } i2c_device_config_t;
#define ESP_OK 0
#define ESP_ERR_INVALID_STATE -1
#define ESP_FAIL -2
#define I2C_ADDR_BIT_LEN_7 0
esp_err_t i2c_master_probe(i2c_master_bus_handle_t, uint16_t, int);
esp_err_t i2c_master_bus_add_device(i2c_master_bus_handle_t, const i2c_device_config_t *, i2c_master_dev_handle_t *);
esp_err_t i2c_master_transmit(i2c_master_dev_handle_t, const uint8_t *, size_t, int);
