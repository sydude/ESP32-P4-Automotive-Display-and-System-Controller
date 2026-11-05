/**
 * @file basicrace1920x480v1_gen.h
 */

#ifndef LVGL_PRO_BASICRACE1920X480V1_GEN_H
#define LVGL_PRO_BASICRACE1920X480V1_GEN_H

#ifndef UI_SUBJECT_STRING_LENGTH
#define UI_SUBJECT_STRING_LENGTH 256
#endif

#ifdef __cplusplus
extern "C" {
#endif

/*********************
 *      INCLUDES
 *********************/

#ifdef LV_LVGL_H_INCLUDE_SIMPLE
    #include "lvgl.h"
#else
    #include "lvgl/lvgl.h"
#endif

#if defined(LV_USE_XML) && LV_USE_XML
    #include "lv_xml/lv_xml.h"
#endif



/* Prototypes for target functions, needed by responsive const definitions */

void basicrace1920x480v1_set_target(uint32_t target);
uint32_t basicrace1920x480v1_get_target(void);
bool basicrace1920x480v1_check_target(uint32_t target);

/*********************
 *      DEFINES
 *********************/

#define BASICRACE1920X480V1_TARGET_UNDEFINED  (0 << 1)
#define BASICRACE1920X480V1_TARGET_TARGET1    (1 << 1)
#define BASICRACE1920X480V1_TARGET_ALL        0x0FFFFFFF

/* By default compile for all targets, allowing to switch to any targets at runtime */
#ifndef BASICRACE1920X480V1_COMPILE_TARGET
#define BASICRACE1920X480V1_COMPILE_TARGET BASICRACE1920X480V1_TARGET_ALL
#endif

#define BASICRACE1920X480V1_CHECK_COMPILE_TARGET(target) (BASICRACE1920X480V1_COMPILE_TARGET & (target) ? 1 : 0)

#ifndef LV_XML_EVAL_STRING_BUF_SIZE
    #define LV_XML_EVAL_STRING_BUF_SIZE 256
#endif

/**
 * Animation path of a style transition with a `bezier(…)` easing. The control
 * points come from the transition descriptor's `user_data`, as a transition
 * descriptor cannot store animation parameters itself.
 */
static inline int32_t basicrace1920x480v1_style_transition_bezier_path_helper(const lv_anim_t * a)
{
    const lv_anim_bezier3_para_t * para = (const lv_anim_bezier3_para_t *)lv_anim_get_user_data(a);
    if(para == NULL) return lv_anim_path_linear(a);

    lv_anim_t a_tmp = *a;
    lv_anim_set_bezier3_param(&a_tmp, para->x1, para->y1, para->x2, para->y2);
    return lv_anim_path_custom_bezier3(&a_tmp);
}

/**********************
 *      TYPEDEFS
 **********************/

/**********************
 * GLOBAL VARIABLES
 **********************/

/*-------------------
 * Permanent screens
 *------------------*/

/*----------------
 * Global styles
 *----------------*/

extern lv_style_t style_background_1;
extern lv_style_t style_text_default;

/*----------------
 * Fonts
 *----------------*/

/* Targets: any */
extern lv_font_t * font_default;
extern lv_font_t * font_bold_20;
extern lv_font_t * font_bold_36;
extern lv_font_t * font_body_symbols;
extern lv_font_t * font_body;


/*----------------
 * Images
 *----------------*/

/* Targets: any */
extern const void * race_background_1;

/*----------------
 * Subjects
 *----------------*/

extern lv_subject_t subject_brightness;

/**********************
 * GLOBAL PROTOTYPES
 **********************/

/*----------------
 * Event Callbacks
 *----------------*/

/*----------------
 * Easing Callbacks
 *----------------*/

/**
 * Initialize the component library
 */

void basicrace1920x480v1_init_gen(const char * asset_path);

/**********************
 *      MACROS
 **********************/

/**********************
 *   POST INCLUDES
 **********************/

/*Include all the widgets, components and screens of this library*/
#include "screens/screen_main/screen_main_gen.h"

#ifdef __cplusplus
} /*extern "C"*/
#endif

#endif /*LVGL_PRO_BASICRACE1920X480V1_GEN_H*/