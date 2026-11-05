/**
 * @file basicrace1920x480v1.h
 */

#ifndef LVGL_PRO_BASICRACE1920X480V1_H
#define LVGL_PRO_BASICRACE1920X480V1_H

#ifdef __cplusplus
extern "C" {
#endif

/*********************
 *      DEFINES
 *********************/

/* Target(s) select at startup: one or more BASICRACE1920X480V1_TARGET_* values OR-ed together. */
#ifndef BASICRACE1920X480V1_COMPILE_TARGET
#define BASICRACE1920X480V1_COMPILE_TARGET BASICRACE1920X480V1_TARGET_ALL
#endif

/*********************
 *      INCLUDES
 *********************/

#include "basicrace1920x480v1_gen.h"

/**********************
 *      TYPEDEFS
 **********************/

/**********************
 * GLOBAL VARIABLES
 **********************/

/**********************
 * GLOBAL PROTOTYPES
 **********************/

/**
 * Initialize the component library
 */
void basicrace1920x480v1_init(const char * asset_path);

/**********************
 *      MACROS
 **********************/

#ifdef __cplusplus
} /*extern "C"*/
#endif

#endif /*LVGL_PRO_BASICRACE1920X480V1_H*/