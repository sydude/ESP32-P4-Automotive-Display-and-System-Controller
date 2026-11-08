#pragma once

#include "driver/i2c_master.h"
#include "lvgl.h"

/* Call after the Waveshare DSI driver has initialized I2C_NUM_1 and the panel. */
void brightness_control_init(i2c_master_bus_handle_t bus);
/* Call once with the compiled LVGL Pro screen, while holding the LVGL lock. */
void brightness_control_attach(lv_obj_t *screen);
