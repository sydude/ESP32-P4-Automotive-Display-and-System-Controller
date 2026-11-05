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

        lv_obj_add_style(lv_obj_0, &style_background_1, 0);
        lv_obj_add_style(lv_obj_0, &style_text_default, 0);
        lv_obj_remove_flag(lv_obj_0, LV_OBJ_FLAG_SCROLLABLE);
        lv_obj_t * card = lv_obj_create(lv_obj_0);
        lv_obj_set_size(card, 720, 300);
        lv_obj_set_align(card, LV_ALIGN_CENTER);
        lv_obj_remove_flag(card, LV_OBJ_FLAG_SCROLLABLE);
        lv_obj_set_flex_flow(card, LV_FLEX_FLOW_COLUMN);
        lv_obj_set_flex_align(card, LV_FLEX_ALIGN_CENTER, LV_FLEX_ALIGN_CENTER, LV_FLEX_ALIGN_CENTER);
        lv_obj_set_style_pad_all(card, 32, 0);
        lv_obj_set_style_pad_row(card, 20, 0);
        lv_obj_set_style_radius(card, 20, 0);
        lv_obj_set_style_bg_color(card, lv_color_hex(0x101820), 0);
        lv_obj_set_style_bg_opa(card, LV_OPA_COVER, 0);
        lv_obj_set_style_border_width(card, 0, 0);

        lv_obj_t * title = lv_label_create(card);
        lv_label_set_text(title, "Display brightness");
        lv_obj_set_style_text_font(title, font_bold_36, 0);
        lv_obj_t * percent = lv_label_create(card);
        lv_obj_set_name_static(percent, "brightness_percent");
        lv_label_bind_text(percent, &subject_brightness, "%d%%");
        lv_obj_set_style_text_font(percent, font_bold_36, 0);
        lv_obj_t * slider = lv_slider_create(card);
        lv_obj_set_name_static(slider, "brightness_slider");
        lv_obj_set_size(slider, 600, 32);
        lv_slider_set_range(slider, 10, 100);
        lv_obj_remove_flag(slider, LV_OBJ_FLAG_ADV_HITTEST);
        lv_slider_bind_value(slider, &subject_brightness);
        lv_obj_t * status = lv_label_create(card);
        lv_obj_set_name_static(status, "brightness_status");
        lv_label_set_text(status, "10-100% | Drag to adjust");
        lv_obj_set_style_text_font(status, font_body, 0);

        the_root = lv_obj_0;
    }
    #endif

    LV_TRACE_OBJ_CREATE("finished");

    return the_root;
}

/**********************
 *   STATIC FUNCTIONS
 **********************/

