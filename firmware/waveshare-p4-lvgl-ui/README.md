# Waveshare ESP32-P4 8.8-inch LVGL Pro UI integration

ESP-IDF **6.1.x** application for the Waveshare **ESP32-P4-WIFI6-DB** and **480 × 1920** DSI LCD, presented in **1920 × 480 landscape**. This project is derived from the verified `../waveshare-8p8-display-touch/` hardware baseline. That baseline is preserved separately.

## Project layout

- `main/display_touch.c`: verified DSI RGB888 initialization, landscape partial flush, GT9271 touch, and LVGL Pro UI startup.
- `lvgl-project/basicrace1920x480v1/`: editable LVGL Pro XML source project and generated C/H resources.
- `main/ui/`: generated C/H source files copied from LVGL Pro; ESP-IDF compiles these, not the XML files.
- `sync_lvgl_pro_ui.py`: synchronizes the generated C/H resources into `main/ui/`.
- `partitions.csv`: 8 MiB factory application partition for embedded graphics and fonts.
- `reference/`: archived Waveshare source, not part of the active build.

## Build

Activate ESP-IDF 6.1.x (the local Mac installation previously used `source "$HOME/.espressif/tools/activate_idf_v6.1.sh"`). From this directory:

```sh
python3 sync_lvgl_pro_ui.py
idf.py build
```

The script requires that the LVGL Pro project has already been **generated** in the editor. It copies generated `.c` and `.h` files, not preview-build artifacts, and removes stale C/H files from `main/ui/` before copying.

The ESP-IDF project is named `waveshare_p4_lvgl_ui`, targets `esp32p4`, and retains the working hardware configuration and managed-component lockfile. The LVGL Pro generated code targets LVGL 9.6.0. This integration uses the compiled C screen (`screen_main_create()`), not XML loaded at runtime.

## Current UI and hardware

The initial screen displays the embedded `race_background_1` image and the centered `Hello P4!` label. It retains the native DSI panel configuration, RGB888 rendering, custom 90-degree partial flush, GT9271 I2C polling, and landscape touch coordinate mapping from the baseline. The LVGL port manages task, tick, and locking.

The two allocated 46,080-byte PSRAM buffers are a draw buffer and a rotation buffer, not double buffering. The Waveshare driver owns its native display framebuffer. No hardware rendering behavior has been changed for this integration.

## Validation status

**Not yet built or flashed with the generated UI.** Run the synchronization script and build first. Inspect any compilation errors before flashing. Do not merge the draft integration pull request until a successful build is confirmed. Flashing to hardware is a separate explicit step.

## Notes

`sdkconfig` and `sdkconfig.defaults` preserve ESP-IDF 6.1 and board settings. Translation support is enabled because LVGL Pro generates translation registration calls. The 8 MiB app partition is intended to provide space for the embedded full-screen background and fonts; it does not change the board's 32 MB physical flash size.
