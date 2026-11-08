# Waveshare ESP32-P4 8.8-inch display and touch baseline

Standalone ESP-IDF **6.1.0** project for the Waveshare **ESP32-P4-WIFI6-DB**, 8.8-inch **480 × 1920** DSI LCD and **GT9271** touch controller. This project lives in the ESP32-P4 Automotive Display and System Controller repository; it has no dependency on a sibling source checkout.

## Build

With ESP-IDF 6.1.0 installed and activated:

```sh
cd "firmware/waveshare-8p8-display-touch"
idf.py build
```

On the current Mac, activate the existing ESP-IDF Installation Manager environment first:

```sh
source "$HOME/.espressif/tools/activate_idf_v6.1.sh"
```

The CMake project defaults to `esp32p4`. The tracked `sdkconfig` preserves the full working configuration, including **32 MB flash**, PSRAM, and chip revision constraints. `sdkconfig.defaults` contains the same full baseline so regeneration retains board settings. The existing single-app partition layout is unchanged; 32 MB flash does not imply a 32 MB app partition. Keep `dependencies.lock` tracked. The first build downloads managed components.

No flashing is performed by a build. Flashing requires the user's explicit approval and a selected serial port. Monitor baud is 115200.

## Current behavior

A minimal LVGL smoke test shows a title, a large central **Tap me** button with a tap counter, and a live touch/release coordinate label. The GUI is **1920 × 480 landscape**. The original two-lane DSI preset, LDO channel 3 at 2500 mV, native **480 × 1920 RGB888** framebuffer, I2C bus 1 and GT9271 address `0x14` are retained. The driver creates the shared I2C bus; the application reads the product ID and polls the first touch point through the verified register protocol. Fresh reports are acknowledged, including release reports; a not-ready status retains the previous touch state.

Touch mapping is `gui_x = raw_y`, `gui_y = 479 - raw_x`. The drawing flush uses the inverse mapping, `native_x = 479 - gui_y`, `native_y = gui_x`. Out-of-range touch points are rejected. No panel axis swapping or LVGL display rotation is requested.

The ESP LVGL port supplies the task, tick and mutex. The app creates a custom LVGL RGB888 partial display and pointer input under that mutex; input and UI callbacks run in the port task. Two **46,080-byte PSRAM buffers** (draw and rotated transfer, 92,160 bytes total) supplement the driver's existing single 2,764,800-byte native framebuffer. The draw buffer holds eight full landscape rows; the flush respects LVGL source row stride and packs the rotated destination tightly.

The Waveshare IDF 6 driver enables asynchronous DMA2D by default. This test explicitly disables that copy hook using the installed IDF API. `esp_lcd_panel_draw_bitmap()` then copies synchronously by CPU and writes back framebuffer cache before returning; only then does the app signal `lv_display_flush_ready()`. No transfer ISR/semaphore is needed. This avoids PPA rotation restrictions and extra full-screen buffers. The single framebuffer can show tearing during updates; this is a functional smoke test, not a tear-free animation demo.

## Test on the device

After explicitly choosing to flash, activate the ESP-IDF environment, change into this project, then run:

```sh
idf.py -p /dev/tty.usbmodem5C931261821 flash monitor
```

Use your current serial port if it differs. This command writes firmware; `idf.py build` alone does not. Exit monitor with Ctrl+].

Check that the title is upright in landscape, then tap and release the central button repeatedly: its count should increase once per click. Touch near each corner: top-left should approach `(0, 0)`, top-right `(1919, 0)`, bottom-left `(0, 479)` and bottom-right `(1919, 479)`. Moving right should increase x; moving down should increase y. Releasing should show **Released**. Serial output should identify the GT9271 and report LVGL ready. Hardware behavior needs verification after flashing.

## Dependencies and provenance

- `waveshare/esp_lcd_dsi`: **2.0.0**, registry package, replacing the local relative dependency.
- `espressif/i2c_bus`: **1.5.2**, preserved.
- `espressif/cmake_utilities`: **0.5.3**, preserved.
- ESP-IDF: **6.1.0**, preserved and pinned in the manifest.
- `lvgl/lvgl`: **^9.6.0**, installed **9.6.0~1**.
- `espressif/esp_lvgl_port`: **^2.9.0**, installed **2.9.0**.

Source: `~/Documents/GitHub/Libraries/Waveshare-ESP32-components/display/lcd/esp_lcd_dsi/test_apps`, branch `esp32p4-display-touch-baseline`, commit `7011ae908c04bedb7e3d035b537c6f894c4b8957`.

`reference/` preserves the original source, CMake files, manifest, dependency lock, and configuration byte-for-byte. These files are archival and do not participate in this project's build. `reference/SHA256SUMS` records their checksums. The upstream Waveshare MIT license is retained in `LICENSE.waveshare.txt`.

The downloaded registry driver's `esp_lcd_dsi.c` and entire `include/` directory match the local baseline byte-for-byte. Build compatibility is checked using the installed ESP-IDF 6.1.0 toolchain; hardware behavior still needs confirmation after an approved flash.

## Validation

The original extraction build was verified on 2026-10-21. The LVGL smoke test build produced a 665,360-byte (`0xa2710`) application, with 37% of the existing 1 MiB app partition free. It was built with ESP-IDF 6.1.0 for `esp32p4`; generated flash arguments retain DIO, 80 MHz and **32 MB** flash. Existing dependency, editor and sdkconfig changes from the user's successful LVGL installation are retained. No board was flashed, and nothing was committed or pushed.
