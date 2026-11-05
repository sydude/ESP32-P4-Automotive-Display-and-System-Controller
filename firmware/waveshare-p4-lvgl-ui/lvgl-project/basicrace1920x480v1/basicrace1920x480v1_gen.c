/**
 * @file basicrace1920x480v1_gen.c
 */

/*********************
 *      INCLUDES
 *********************/

#include "basicrace1920x480v1.h"

#if defined(LV_USE_XML) && LV_USE_XML
#endif /* LV_USE_XML */

/*********************
 *      DEFINES
 *********************/

/**********************
 *      TYPEDEFS
 **********************/

/**********************
 *  STATIC PROTOTYPES
 **********************/

static void check_font(lv_font_t ** font, const char * name);

/**********************
 *  STATIC VARIABLES
 **********************/

static uint32_t basicrace1920x480v1_target = BASICRACE1920X480V1_COMPILE_TARGET;

/*----------------
 * Translations
 *----------------*/

#ifndef LV_EDITOR_PREVIEW
    static const char * translation_languages[] = {"en", "de", NULL};
    static const char * translation_tags[] = {"dog", "cat", "house", NULL};
    static const char * translation_texts[] = {
        "This is a dog", "Das ist ein Hund", /* dog */
        "A curious little cat", "Eine neugierige kleine Katze", /* cat */
        "The house is cozy and warm", "Das Haus ist gemütlich und warm", /* house */
    };
#endif

/**********************
 *  GLOBAL VARIABLES
 **********************/

/*--------------------
 *  Permanent screens
 *-------------------*/

/*----------------
 * Fonts
 *----------------*/

lv_font_t * font_default;
extern lv_font_t font_default_data;
lv_font_t * font_bold_20;
extern lv_font_t font_bold_20_data;
lv_font_t * font_bold_36;
extern lv_font_t font_bold_36_data;
lv_font_t * font_body_symbols;
extern lv_font_t font_body_symbols_data;
lv_font_t * font_body;
extern lv_font_t font_body_data;

/*----------------
 * Images
 *----------------*/

/* Targets: any */
const void * race_background_1 = NULL;
extern const void * race_background_1_data;

/*----------------
 * Global styles
 *----------------*/

lv_style_t style_background_1;
lv_style_t style_text_default;

/*----------------
 * Subjects
 *----------------*/

lv_subject_t subject_brightness;

/**********************
 *      MACROS
 **********************/

/**********************
 *   GLOBAL FUNCTIONS
 **********************/

void basicrace1920x480v1_init_gen(const char * asset_path)
{
    /* When running from the editor the theme set from the XML should overwrite this */
#if !defined(LV_EDITOR_PREVIEW)
#if LV_USE_THEME_SIMPLE
    lv_display_t * disp = lv_display_get_default();
    lv_theme_t * th = lv_theme_simple_init(disp);
    lv_display_set_theme(disp, th);
#else
    LV_LOG_WARN("Simple theme is selected in project.xml but LV_USE_THEME_SIMPLE is disabled");
#endif
#endif /*LV_EDITOR_PREVIEW*/


    /*----------------
     * Fonts
     *----------------*/

    /* Targets: any */

    #if BASICRACE1920X480V1_CHECK_COMPILE_TARGET(BASICRACE1920X480V1_TARGET_ALL)
    if (basicrace1920x480v1_check_target(BASICRACE1920X480V1_TARGET_ALL)) {
        if (!font_default) {
            /* font_default */
            /* get font 'font_default' from a C array */
            font_default = &font_default_data;

        }
        if (!font_bold_20) {
            /* font_bold_20 */
            /* get font 'font_bold_20' from a C array */
            font_bold_20 = &font_bold_20_data;

        }
        if (!font_bold_36) {
            /* font_bold_36 */
            /* get font 'font_bold_36' from a C array */
            font_bold_36 = &font_bold_36_data;

        }
        if (!font_body_symbols) {
            /* font_body_symbols */
            /* get font 'font_body_symbols' from a C array */
            font_body_symbols = &font_body_symbols_data;

        }
        if (!font_body) {
            /* font_body */
            /* get font 'font_body' from a C array */
            font_body = &font_body_data;

        }
    }
    #endif

    /*----------------
     * Images
     *----------------*/

    /* Targets: any */
    #if BASICRACE1920X480V1_CHECK_COMPILE_TARGET(BASICRACE1920X480V1_TARGET_ALL)
    if (basicrace1920x480v1_check_target(BASICRACE1920X480V1_TARGET_ALL)) {
        /* race_background_1 */
        if (!race_background_1) {
            race_background_1 = &race_background_1_data;
        }
    }
    #endif

    /*----------------
     * Global styles
     *----------------*/

    static bool style_inited = false;

    if (!style_inited) {
        /*Init all styles*/
        lv_style_init(&style_background_1);
        lv_style_init(&style_text_default);

        lv_style_set_bg_image_src(&style_background_1, race_background_1);
        lv_style_set_text_color(&style_text_default, lv_color_hex(0xFFFFFF));
        lv_style_set_text_font(&style_text_default, font_default);
        lv_style_set_text_letter_space(&style_text_default, 0);
        lv_style_set_text_line_space(&style_text_default, 2);

        style_inited = true;
    }

    /*----------------
     * Subjects
     *----------------*/
    lv_subject_init_int(&subject_brightness, 75);
    /*----------------
     * Translations
     *----------------*/

    #ifndef LV_EDITOR_PREVIEW
        lv_translation_add_static(translation_languages, translation_tags, translation_texts);
        lv_translation_set_language(translation_languages[0]);
    #endif

#if defined(LV_USE_XML) && LV_USE_XML
    /* Register widgets */

    /* Check all fonts / default if needed. This prevents fonts that are used in one target but
       defined in another from causing assertion failures during rendering of the Preview. */
    check_font(&font_default, "font_default");
    check_font(&font_bold_20, "font_bold_20");
    check_font(&font_bold_36, "font_bold_36");
    check_font(&font_body_symbols, "font_body_symbols");
    check_font(&font_body, "font_body");

    /* Register fonts */
    lv_xml_register_font(NULL, "font_default", font_default);
    lv_xml_register_font(NULL, "font_bold_20", font_bold_20);
    lv_xml_register_font(NULL, "font_bold_36", font_bold_36);
    lv_xml_register_font(NULL, "font_body_symbols", font_body_symbols);
    lv_xml_register_font(NULL, "font_body", font_body);

    /* Register subjects */
    lv_xml_register_subject(NULL, "subject_brightness", &subject_brightness);

    /* Register callbacks */

    /* Register easing callbacks */
#endif

    /* Register all the global assets so that they won't be created again when globals.xml is parsed.
     * While running in the editor skip this step to update the preview when the XML changes */
#if defined(LV_USE_XML) && LV_USE_XML && !defined(LV_EDITOR_PREVIEW)
    /* Register images */
    lv_xml_register_image(NULL, "race_background_1", race_background_1);
#endif

#if !defined(LV_USE_XML) || LV_USE_XML == 0
    /*--------------------
     *  Permanent screens
     *-------------------*/
    /* If XML is enabled it's assumed that the permanent screens are created
     * manually from XML using lv_xml_create() */
#endif
}

void basicrace1920x480v1_set_target(uint32_t target)
{
    basicrace1920x480v1_target = target;
}

uint32_t basicrace1920x480v1_get_target(void)
{
    return basicrace1920x480v1_target;
}

bool basicrace1920x480v1_check_target(uint32_t target)
{
    return (basicrace1920x480v1_target & target) ? true : false;
}

/* Callbacks */

/**********************
 *   STATIC FUNCTIONS
 **********************/

static void check_font(lv_font_t ** font, const char * name)
{
    if (!(*font)) {
        *font = (lv_font_t *)LV_FONT_DEFAULT;
        LV_LOG_WARN("font `%s` was not set. Using `LV_FONT_DEFAULT` instead", name);
    }
}