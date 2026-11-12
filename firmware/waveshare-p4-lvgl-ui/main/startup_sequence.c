#include "startup_sequence.h"
#include "lvgl.h"
#include "basicrace1920x480v1.h"
#include <assert.h>
#include "brightness_control.h"

static void set_logo_opacity(void *obj, int32_t value)
{
    lv_obj_set_style_opa((lv_obj_t *)obj, value, 0);
}

static void start_logo_animation(lv_obj_t *logo)
{
    lv_anim_t anim;
    lv_anim_init(&anim);

    lv_anim_set_var(&anim, logo);
    lv_anim_set_exec_cb(&anim, set_logo_opacity);

    lv_anim_set_values(&anim, LV_OPA_TRANSP, LV_OPA_COVER);
    lv_anim_set_duration(&anim, 3000);
    lv_anim_set_playback_duration(&anim, 3000);
    lv_anim_set_playback_delay(&anim, 3000);
    lv_anim_set_delay(&anim, 3000);

    lv_anim_start(&anim);
}

static void startup_finished(lv_timer_t *timer)
{
    lv_timer_delete(timer);

    lv_obj_t *main_screen = screen_main_create();
    assert(main_screen);

    brightness_control_attach(main_screen);
    lv_screen_load_anim(main_screen, LV_SCR_LOAD_ANIM_NONE, 0, 0, true);
}

void begin_startup_sequence(lv_obj_t *startup_screen)
{
    lv_obj_t *logo = lv_obj_find_by_name(
        startup_screen, "startup_svt_logo_widget"
    );

    if (logo) {
        start_logo_animation(logo);
    }

    lv_timer_t *timer = lv_timer_create(
        startup_finished, 12000, NULL
    );
    lv_timer_set_repeat_count(timer, 1);
}

