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

static void screen_main_rear_lights_overlay_hidden_binding_cb(lv_observer_t * observer, lv_subject_t * subject);
static void screen_main_wide_lights_overlay_hidden_binding_cb(lv_observer_t * observer, lv_subject_t * subject);
static void screen_main_amber_lights_overlay_hidden_binding_cb(lv_observer_t * observer, lv_subject_t * subject);

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

        lv_obj_t * screen_1_bg_widget = lv_image_create(lv_obj_0);
        lv_obj_set_name(screen_1_bg_widget, "screen_1_bg_widget");
        lv_image_set_src(screen_1_bg_widget, screen_1_bg);
        lv_obj_set_align(screen_1_bg_widget, LV_ALIGN_TOP_MID);
        lv_obj_set_x(screen_1_bg_widget, 0);
        lv_obj_set_y(screen_1_bg_widget, 0);
        lv_obj_set_clickable(screen_1_bg_widget, false);

        lv_obj_t * background_graphics = lv_obj_create(lv_obj_0);
        lv_obj_set_name(background_graphics, "background_graphics");
        lv_obj_set_width(background_graphics, lv_pct(100));
        lv_obj_set_height(background_graphics, lv_pct(100));
        lv_obj_set_style_bg_opa(background_graphics, (255 * 0 / 100), 0);
        lv_obj_set_style_border_width(background_graphics, 0, 0);
        lv_obj_set_style_pad_all(background_graphics, 0, 0);
        lv_obj_set_scrollable(background_graphics, false);
        lv_obj_set_clickable(background_graphics, false);
        lv_obj_t * dashboard_notch_overlay = lv_image_create(background_graphics);
        lv_obj_set_name(dashboard_notch_overlay, "dashboard_notch_overlay");
        lv_image_set_src(dashboard_notch_overlay, notch);
        lv_obj_set_align(dashboard_notch_overlay, LV_ALIGN_TOP_MID);

        lv_obj_t * dashboard_logo_overlay = lv_image_create(background_graphics);
        lv_obj_set_name(dashboard_logo_overlay, "dashboard_logo_overlay");
        lv_image_set_src(dashboard_logo_overlay, screen_1_logo);
        lv_obj_set_align(dashboard_logo_overlay, LV_ALIGN_CENTER);

        lv_obj_t * vehicle_graphics = lv_obj_create(lv_obj_0);
        lv_obj_set_name(vehicle_graphics, "vehicle_graphics");
        lv_obj_set_align(vehicle_graphics, LV_ALIGN_TOP_LEFT);
        lv_obj_set_x(vehicle_graphics, 0);
        lv_obj_set_y(vehicle_graphics, 0);
        lv_obj_set_height(vehicle_graphics, 480);
        lv_obj_set_width(vehicle_graphics, 500);
        lv_obj_set_scrollable(vehicle_graphics, false);
        lv_obj_set_clickable(vehicle_graphics, false);
        lv_obj_set_style_bg_opa(vehicle_graphics, 0, 0);
        lv_obj_set_style_border_width(vehicle_graphics, 0, 0);
        lv_obj_set_style_pad_all(vehicle_graphics, 0, 0);
        lv_obj_t * raptor_front_widget = lv_image_create(vehicle_graphics);
        lv_obj_set_name(raptor_front_widget, "raptor_front_widget");
        lv_image_set_src(raptor_front_widget, raptor_front);
        lv_obj_set_x(raptor_front_widget, 40);
        lv_obj_set_y(raptor_front_widget, 20);
        lv_obj_set_clickable(raptor_front_widget, false);

        lv_obj_t * raptor_rear_widget = lv_image_create(vehicle_graphics);
        lv_obj_set_name(raptor_rear_widget, "raptor_rear_widget");
        lv_image_set_src(raptor_rear_widget, raptor_rear);
        lv_obj_set_x(raptor_rear_widget, 40);
        lv_obj_set_y(raptor_rear_widget, 220);
        lv_obj_set_clickable(raptor_rear_widget, false);

        lv_obj_t * rear_lights_overlay = lv_image_create(vehicle_graphics);
        lv_obj_set_name(rear_lights_overlay, "rear_lights_overlay");
        lv_image_set_src(rear_lights_overlay, rear_lights);
        lv_obj_set_x(rear_lights_overlay, -40);
        lv_obj_set_y(rear_lights_overlay, 287);
        lv_obj_set_clickable(rear_lights_overlay, false);
        lv_subject_add_observer_obj(rear_lights_on, screen_main_rear_lights_overlay_hidden_binding_cb, rear_lights_overlay, NULL);

        lv_obj_t * wide_lights_overlay = lv_image_create(vehicle_graphics);
        lv_obj_set_name(wide_lights_overlay, "wide_lights_overlay");
        lv_image_set_src(wide_lights_overlay, wide_lights);
        lv_obj_set_x(wide_lights_overlay, 21);
        lv_obj_set_y(wide_lights_overlay, 124);
        lv_obj_set_clickable(wide_lights_overlay, false);
        lv_subject_add_observer_obj(wide_lights_on, screen_main_wide_lights_overlay_hidden_binding_cb, wide_lights_overlay, NULL);

        lv_obj_t * amber_lights_overlay = lv_image_create(vehicle_graphics);
        lv_obj_set_name(amber_lights_overlay, "amber_lights_overlay");
        lv_image_set_src(amber_lights_overlay, amber_lights);
        lv_obj_set_x(amber_lights_overlay, 38);
        lv_obj_set_y(amber_lights_overlay, 123);
        lv_obj_set_clickable(amber_lights_overlay, false);
        lv_subject_add_observer_obj(amber_lights_on, screen_main_amber_lights_overlay_hidden_binding_cb, amber_lights_overlay, NULL);

        lv_obj_t * svt_aux_switches = lv_obj_create(lv_obj_0);
        lv_obj_set_name(svt_aux_switches, "svt_aux_switches");
        lv_obj_set_align(svt_aux_switches, LV_ALIGN_BOTTOM_RIGHT);
        lv_obj_set_x(svt_aux_switches, -30);
        lv_obj_set_y(svt_aux_switches, -70);
        lv_obj_set_width(svt_aux_switches, 308);
        lv_obj_set_height(svt_aux_switches, 176);
        lv_obj_set_style_pad_all(svt_aux_switches, 0, 0);
        lv_obj_set_style_bg_opa(svt_aux_switches, (255 * 0 / 100), 0);
        lv_obj_set_style_border_width(svt_aux_switches, 0, 0);
        lv_obj_set_scrollable(svt_aux_switches, false);
        lv_obj_set_clickable(svt_aux_switches, false);
        lv_obj_t * svt_switch_base = lv_image_create(svt_aux_switches);
        lv_obj_set_name(svt_switch_base, "svt_switch_base");
        lv_image_set_src(svt_switch_base, svt_switches);
        lv_obj_set_x(svt_switch_base, 0);
        lv_obj_set_y(svt_switch_base, 0);
        lv_obj_set_width(svt_switch_base, 308);
        lv_obj_set_height(svt_switch_base, 176);
        lv_obj_set_scrollable(svt_switch_base, false);
        lv_obj_set_clickable(svt_switch_base, false);

        lv_obj_t * svt_switch_1 = lv_imagebutton_create(svt_aux_switches);
        lv_obj_set_name(svt_switch_1, "svt_switch_1");
        lv_obj_set_x(svt_switch_1, 29);
        lv_obj_set_y(svt_switch_1, 36);
        lv_obj_set_width(svt_switch_1, 64);
        lv_obj_set_height(svt_switch_1, 94);
        lv_obj_set_checkable(svt_switch_1, true);
        lv_obj_bind_checked(svt_switch_1, amber_lights_on);
        lv_obj_set_style_bg_opa(svt_switch_1, (255 * 0 / 100), 0);
        lv_obj_set_style_border_width(svt_switch_1, 0, 0);
        lv_obj_set_style_pad_all(svt_switch_1, 0, 0);
        lv_imagebutton_set_src_mid(svt_switch_1, LV_IMAGEBUTTON_STATE_RELEASED, svt_switch_1_off);
        lv_imagebutton_set_src_mid(svt_switch_1, LV_IMAGEBUTTON_STATE_PRESSED, svt_switch_1_off);
        lv_imagebutton_set_src_mid(svt_switch_1, LV_IMAGEBUTTON_STATE_CHECKED_RELEASED, svt_switch_1_on);
        lv_imagebutton_set_src_mid(svt_switch_1, LV_IMAGEBUTTON_STATE_CHECKED_PRESSED, svt_switch_1_on);

        lv_obj_t * svt_switch_2 = lv_imagebutton_create(svt_aux_switches);
        lv_obj_set_name(svt_switch_2, "svt_switch_2");
        lv_obj_set_x(svt_switch_2, 91);
        lv_obj_set_y(svt_switch_2, 36);
        lv_obj_set_width(svt_switch_2, 62);
        lv_obj_set_height(svt_switch_2, 94);
        lv_obj_set_checkable(svt_switch_2, true);
        lv_obj_bind_checked(svt_switch_2, wide_lights_on);
        lv_obj_set_style_bg_opa(svt_switch_2, (255 * 0 / 100), 0);
        lv_obj_set_style_border_width(svt_switch_2, 0, 0);
        lv_obj_set_style_pad_all(svt_switch_2, 0, 0);
        lv_imagebutton_set_src_mid(svt_switch_2, LV_IMAGEBUTTON_STATE_RELEASED, svt_switch_2_off);
        lv_imagebutton_set_src_mid(svt_switch_2, LV_IMAGEBUTTON_STATE_PRESSED, svt_switch_2_off);
        lv_imagebutton_set_src_mid(svt_switch_2, LV_IMAGEBUTTON_STATE_CHECKED_RELEASED, svt_switch_2_on);
        lv_imagebutton_set_src_mid(svt_switch_2, LV_IMAGEBUTTON_STATE_CHECKED_PRESSED, svt_switch_2_on);

        lv_obj_t * svt_switch_3 = lv_imagebutton_create(svt_aux_switches);
        lv_obj_set_name(svt_switch_3, "svt_switch_3");
        lv_obj_set_x(svt_switch_3, 154);
        lv_obj_set_y(svt_switch_3, 36);
        lv_obj_set_width(svt_switch_3, 62);
        lv_obj_set_height(svt_switch_3, 94);
        lv_obj_set_checkable(svt_switch_3, true);
        lv_obj_bind_checked(svt_switch_3, rear_lights_on);
        lv_obj_set_style_bg_opa(svt_switch_3, (255 * 0 / 100), 0);
        lv_obj_set_style_border_width(svt_switch_3, 0, 0);
        lv_obj_set_style_pad_all(svt_switch_3, 0, 0);
        lv_imagebutton_set_src_mid(svt_switch_3, LV_IMAGEBUTTON_STATE_RELEASED, svt_switch_3_off);
        lv_imagebutton_set_src_mid(svt_switch_3, LV_IMAGEBUTTON_STATE_PRESSED, svt_switch_3_off);
        lv_imagebutton_set_src_mid(svt_switch_3, LV_IMAGEBUTTON_STATE_CHECKED_RELEASED, svt_switch_3_on);
        lv_imagebutton_set_src_mid(svt_switch_3, LV_IMAGEBUTTON_STATE_CHECKED_PRESSED, svt_switch_3_on);

        lv_obj_t * svt_switch_4 = lv_imagebutton_create(svt_aux_switches);
        lv_obj_set_name(svt_switch_4, "svt_switch_4");
        lv_obj_set_x(svt_switch_4, 216);
        lv_obj_set_y(svt_switch_4, 36);
        lv_obj_set_width(svt_switch_4, 64);
        lv_obj_set_height(svt_switch_4, 94);
        lv_obj_set_checkable(svt_switch_4, true);
        lv_obj_bind_checked(svt_switch_4, seat_eject_true);
        lv_obj_set_style_bg_opa(svt_switch_4, (255 * 0 / 100), 0);
        lv_obj_set_style_border_width(svt_switch_4, 0, 0);
        lv_obj_set_style_pad_all(svt_switch_4, 0, 0);
        lv_imagebutton_set_src_mid(svt_switch_4, LV_IMAGEBUTTON_STATE_RELEASED, svt_switch_4_off);
        lv_imagebutton_set_src_mid(svt_switch_4, LV_IMAGEBUTTON_STATE_PRESSED, svt_switch_4_off);
        lv_imagebutton_set_src_mid(svt_switch_4, LV_IMAGEBUTTON_STATE_CHECKED_RELEASED, svt_switch_4_on);
        lv_imagebutton_set_src_mid(svt_switch_4, LV_IMAGEBUTTON_STATE_CHECKED_PRESSED, svt_switch_4_on);

        lv_obj_t * gauges = lv_obj_create(lv_obj_0);
        lv_obj_set_name(gauges, "gauges");
        lv_obj_set_height(gauges, lv_pct(100));
        lv_obj_set_style_bg_opa(gauges, (255 * 0 / 100), 0);
        lv_obj_set_style_border_width(gauges, 0, 0);
        lv_obj_set_style_pad_all(gauges, 0, 0);
        lv_obj_set_scrollable(gauges, false);
        lv_obj_set_clickable(gauges, false);
        lv_obj_set_x(gauges, 0);
        lv_obj_set_y(gauges, 2);
        lv_obj_set_width(gauges, 100);

        lv_obj_t * brightness_container = lv_obj_create(lv_obj_0);
        lv_obj_set_name(brightness_container, "brightness_container");
        lv_obj_set_width(brightness_container, 240);
        lv_obj_set_height(brightness_container, 30);
        lv_obj_set_align(brightness_container, LV_ALIGN_BOTTOM_RIGHT);
        lv_obj_set_x(brightness_container, -30);
        lv_obj_set_y(brightness_container, -20);
        lv_obj_set_scrollable(brightness_container, false);
        lv_obj_set_style_bg_opa(brightness_container, (255 * 0 / 100), 0);
        lv_obj_set_style_border_width(brightness_container, 0, 0);
        lv_obj_set_style_pad_all(brightness_container, 0, 0);
        lv_obj_t * brightness_slider = lv_slider_create(brightness_container);
        lv_obj_set_name(brightness_slider, "brightness_slider");
        lv_obj_set_width(brightness_slider, 240);
        lv_obj_set_height(brightness_slider, 24);
        lv_obj_set_align(brightness_slider, LV_ALIGN_CENTER);
        lv_slider_set_min_value(brightness_slider, 10);
        lv_slider_set_max_value(brightness_slider, 100);
        lv_slider_bind_value(brightness_slider, subject_brightness);

        lv_obj_t * brightness_percent = lv_label_create(brightness_container);
        lv_obj_set_name(brightness_percent, "brightness_percent");
        lv_label_bind_text(brightness_percent, subject_brightness, "%d%%");
        lv_obj_set_align(brightness_percent, LV_ALIGN_LEFT_MID);
        lv_obj_set_style_text_font(brightness_percent, font_bold_20, 0);
        lv_obj_set_style_text_color(brightness_percent, lv_color_hex(0x4c4c4c), 0);
        lv_obj_set_x(brightness_percent, 12);

        lv_obj_t * brightness_status = lv_label_create(brightness_container);
        lv_obj_set_name(brightness_status, "brightness_status");
        lv_label_set_text(brightness_status, "10-100% | Drag to adjust");
        lv_obj_set_hidden(brightness_status, true);

        the_root = lv_obj_0;
    }
    #endif

    LV_TRACE_OBJ_CREATE("finished");

    return the_root;
}

/**********************
 *   STATIC FUNCTIONS
 **********************/

static void screen_main_rear_lights_overlay_hidden_binding_cb(lv_observer_t * observer, lv_subject_t * subject)
{
    LV_UNUSED(subject);
    lv_obj_t * obj = lv_observer_get_target_obj(observer);
    lv_obj_set_hidden(obj, lv_subject_get_int(rear_lights_on) == 0);
}

static void screen_main_wide_lights_overlay_hidden_binding_cb(lv_observer_t * observer, lv_subject_t * subject)
{
    LV_UNUSED(subject);
    lv_obj_t * obj = lv_observer_get_target_obj(observer);
    lv_obj_set_hidden(obj, lv_subject_get_int(wide_lights_on) == 0);
}

static void screen_main_amber_lights_overlay_hidden_binding_cb(lv_observer_t * observer, lv_subject_t * subject)
{
    LV_UNUSED(subject);
    lv_obj_t * obj = lv_observer_get_target_obj(observer);
    lv_obj_set_hidden(obj, lv_subject_get_int(amber_lights_on) == 0);
}

