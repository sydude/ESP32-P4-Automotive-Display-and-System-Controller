#pragma once
#include "ui/basicrace1920x480v1.h"

/* LVGL Pro exports a pointer; retain compatibility with the earlier draft
 * value export without modifying generated files. Always return a pointer. */
static inline lv_subject_t *brightness_subject(void)
{
    return _Generic(&subject_brightness,
                    lv_subject_t **: subject_brightness,
                    lv_subject_t *: &subject_brightness);
}
