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
        lv_obj_t * lv_label_0 = lv_label_create(lv_obj_0);
        lv_label_set_text(lv_label_0, "Hello P4!");
        lv_obj_set_align(lv_label_0, LV_ALIGN_CENTER);
        lv_obj_set_style_text_font(lv_label_0, font_bold_36, 0);

        the_root = lv_obj_0;
    }
    #endif

    LV_TRACE_OBJ_CREATE("finished");

    return the_root;
}

/**********************
 *   STATIC FUNCTIONS
 **********************/

