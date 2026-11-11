# Waveshare ESP32-P4 LVGL display firmware

ESP-IDF **6.1.x** firmware for the Waveshare **ESP32-P4-WIFI6-DB** and 8.8-inch DSI LCD. The app renders in **1920 × 480 landscape** and polls the GT9271 touch controller.

- [main/](main/) contains the firmware and the compiled LVGL export in `main/ui/`.
- [lvgl-project/](lvgl-project/) contains the editable LVGL Pro project and its generated C/H files.
- [tests/](tests/) covers the normal brightness slider, the standalone backlight diagnostic, and export synchronization.
- The [archived hardware baseline](../archive/waveshare-8p8-display-touch/) retains the original [vendor snapshot and checksums](../archive/waveshare-8p8-display-touch/reference/).

## Build and update the UI

Activate ESP-IDF 6.1.x and run from this directory:

```sh
python3 sync_lvgl_pro_ui.py --check
idf.py build
```

For UI changes, open [project.xml](lvgl-project/basicrace1920x480v1/project.xml) in LVGL Pro, preview the screen, and Generate C. Run `python3 sync_lvgl_pro_ui.py` before repeating the check and build. Sync replaces C/H files in `main/ui/`. The export targets LVGL 9.6.0.

## Test

After the firmware build populates the managed components, run:

```sh
cmake -S tests/host -B build-host -G Ninja
cmake --build build-host
ctest --test-dir build-host --output-on-failure
python3 tests/test_ui_sync.py
```

The [brightness testing guide](docs/brightness-testing.md) covers the panel-specific I2C protocol, export requirements, and hardware acceptance. The [standalone backlight diagnostic](docs/backlight-diagnostic.md) exercises dimming independently of slider input and is off by default.

Software brightness control was verified on hardware on November 8, 2026. The user confirmed that the earlier right-side slider visibly dimmed the display and returned to 75% after a power cycle. The current generated screen centers the brightness card. The cracked display was diagnosed as the cause of the intermittent phantom touches.
