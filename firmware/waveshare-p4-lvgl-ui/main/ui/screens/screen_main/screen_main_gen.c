/**
 * @file screen_main_gen.c
 * @brief Template source file for LVGL objects
 */

/*********************
 *      INCLUDES
 *********************/

#include "screen_main_gen.h"
#include "../../basicrace1920x480v1.h"

/*********************
 *      DEFINES
 *********************/

/**********************
 *      TYPEDEFS
 **********************/

/***********************
 *  STATIC VARIABLES
 **********************/

/***********************
 *  STATIC PROTOTYPES
 **********************/

/**********************
 *   GLOBAL FUNCTIONS
 **********************/

lv_obj_t * screen_main_create(void)
{
    LV_TRACE_OBJ_CREATE("begin");


    lv_obj_t * the_root = NULL;

    #if BASICRACE1920X480V1_CHECK_COMPILE_TARGET(BASICRACE1920X480V1_TARGET_ALL)
    if (basicrace1920x480v1_check_target(BASICRACE1920X480V1_TARGET_ALL)) {
        lv_obj_t * lv_obj_0 = lv_obj_create(NULL);
        lv_obj_set_name_static(lv_obj_0, "screen_main_#");
        lv_obj_set_scrollable(lv_obj_0, false);

        lv_obj_add_style(lv_obj_0, &style_background_1, 0);
        lv_obj_add_style(lv_obj_0, &style_text_default, 0);
        lv_obj_t * lv_obj_1 = lv_obj_create(lv_obj_0);
        lv_obj_set_width(lv_obj_1, 720);
        lv_obj_set_height(lv_obj_1, 300);
        lv_obj_set_align(lv_obj_1, LV_ALIGN_CENTER);
        lv_obj_set_scrollable(lv_obj_1, false);
        lv_obj_set_flex_flow(lv_obj_1, LV_FLEX_FLOW_COLUMN);
        lv_obj_set_style_flex_main_place(lv_obj_1, LV_FLEX_ALIGN_CENTER, 0);
        lv_obj_set_style_flex_cross_place(lv_obj_1, LV_FLEX_ALIGN_CENTER, 0);
        lv_obj_set_style_flex_track_place(lv_obj_1, LV_FLEX_ALIGN_CENTER, 0);
        lv_obj_set_style_pad_all(lv_obj_1, 32, 0);
        lv_obj_set_style_pad_row(lv_obj_1, 20, 0);
        lv_obj_set_style_radius(lv_obj_1, 20, 0);
        lv_obj_set_style_bg_color(lv_obj_1, lv_color_hex(0x101820), 0);
        lv_obj_set_style_bg_opa(lv_obj_1, (255 * 100 / 100), 0);
        lv_obj_set_style_border_width(lv_obj_1, 0, 0);
        lv_obj_t * lv_label_0 = lv_label_create(lv_obj_1);
        lv_label_set_text(lv_label_0, "Display brightness");
        lv_obj_set_style_text_font(lv_label_0, font_bold_36, 0);

        lv_obj_t * brightness_percent = lv_label_create(lv_obj_1);
        lv_obj_set_name(brightness_percent, "brightness_percent");
        lv_label_bind_text(brightness_percent, subject_brightness, "%d%%");
        lv_obj_set_style_text_font(brightness_percent, font_bold_36, 0);

        lv_obj_t * brightness_slider = lv_slider_create(lv_obj_1);
        lv_obj_set_name(brightness_slider, "brightness_slider");
        lv_obj_set_width(brightness_slider, 600);
        lv_obj_set_height(brightness_slider, 32);
        lv_slider_set_min_value(brightness_slider, 10);
        lv_slider_set_max_value(brightness_slider, 100);
        lv_obj_set_adv_hittest(brightness_slider, false);
        lv_slider_bind_value(brightness_slider, subject_brightness);

        lv_obj_t * brightness_status = lv_label_create(lv_obj_1);
        lv_obj_set_name(brightness_status, "brightness_status");
        lv_label_set_text(brightness_status, "10-100% | Drag to adjust");
        lv_obj_set_style_text_font(brightness_status, font_body, 0);

        the_root = lv_obj_0;
    }
    #endif

    LV_TRACE_OBJ_CREATE("finished");

    return the_root;
}

/**********************
 *   STATIC FUNCTIONS
 **********************/

