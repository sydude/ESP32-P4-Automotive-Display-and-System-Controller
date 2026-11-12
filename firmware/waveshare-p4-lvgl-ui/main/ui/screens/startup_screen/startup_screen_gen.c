/**
 * @file startup_screen_gen.c
 * @brief Template source file for LVGL objects
 */

/*********************
 *      INCLUDES
 *********************/

#include "startup_screen_gen.h"
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

lv_obj_t * startup_screen_create(void)
{
    LV_TRACE_OBJ_CREATE("begin");


    lv_obj_t * the_root = NULL;

    #if BASICRACE1920X480V1_CHECK_COMPILE_TARGET(BASICRACE1920X480V1_TARGET_ALL)
    if (basicrace1920x480v1_check_target(BASICRACE1920X480V1_TARGET_ALL)) {
        lv_obj_t * lv_image_0 = lv_image_create(NULL);
        lv_obj_set_name_static(lv_image_0, "startup_screen_#");
        lv_obj_set_scrollable(lv_image_0, false);

        lv_obj_add_style(lv_image_0, &style_startup_bg, 0);
        lv_obj_t * startup_svt_logo_widget = lv_image_create(lv_image_0);
        lv_obj_set_name(startup_svt_logo_widget, "startup_svt_logo_widget");
        lv_obj_set_align(startup_svt_logo_widget, LV_ALIGN_CENTER);
        lv_image_set_src(startup_svt_logo_widget, startup_svt_logo);
        lv_obj_set_style_opa(startup_svt_logo_widget, (255 * 0 / 100), 0);

        the_root = lv_image_0;
    }
    #endif

    LV_TRACE_OBJ_CREATE("finished");

    return the_root;
}

/**********************
 *   STATIC FUNCTIONS
 **********************/

