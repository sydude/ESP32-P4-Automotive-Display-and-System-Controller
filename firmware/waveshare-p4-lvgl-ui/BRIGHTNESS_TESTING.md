# Brightness control: evidence, regeneration, and hardware test

## Preserved baseline

This change is based on `47da933dba6ad962d5faaca70f6c99157a005618` on
`integration/lvgl-pro-1920x480`. That commit records the user's successful
landscape display test. The separate `../archive/waveshare-8p8-display-touch/` baseline,
DSI initialization, partial RGB888 rotation, framebuffer sizes, and GT9271
status/point/clear polling and coordinate mapping are unchanged.
The feature remains in draft PR #2. Hardware acceptance was confirmed on
November 8, 2026, as recorded below.

## Backlight protocol for the 8.8inch DSI LCD

The actual dependency downloaded from the project's lockfile is
`waveshare/esp_lcd_dsi` **2.0.0**, component hash
`004e3455a2e331eadef75da0df28eb090d03681e0300d75abccb1722fbca66c4`.
Its package manifest identifies vendor commit
[`9daffb7168b3c093a330da700988a22092294eef`](https://github.com/waveshareteam/Waveshare-ESP32-components/blob/9daffb7168b3c093a330da700988a22092294eef/display/lcd/esp_lcd_dsi/esp_lcd_dsi.c).
The installed `managed_components/waveshare__esp_lcd_dsi/esp_lcd_dsi.c`
was inspected directly:

- `esp_lcd_new_panel_dsi()` creates **I2C_NUM_1**, SDA **7**, SCL **8**, **100 kHz**.
- It creates the **7-bit 0x45** controller device and writes this ordered sequence:
  `C0=01`, `C2=01`, `AC=01`, `AB=00`, `AA=01`, `AD=01`.
- It removes its temporary device, keeps the bus alive, and waits **1000 ms**.
- The existing app subsequently gets this bus and adds GT9271 at **0x14**.

The [8.8inch DSI LCD instructions](https://www.waveshare.com/wiki/8.8inch_DSI_LCD#Adjust_Backlight_Brightness)
use the Raspberry Pi's `8_8_inch` overlay. The [panel driver](https://github.com/raspberrypi/linux/blob/rpi-6.12.y/drivers/gpu/drm/panel/panel-waveshare-dsi.c#L391-L397)
writes the inverted brightness to `0xAB`, then applies it with a separate
`AA 01` write. Both use the same 7-bit device address `0x45`.

| Requested | Level write | Apply write |
| --- | --- | --- |
| 10% | `AB E6` | `AA 01` |
| 50% | `AB 80` | `AA 01` |
| 75% | `AB 40` | `AA 01` |
| 100% | `AB 00` | `AA 01` |

The [8.8-DSI-TOUCH-A](https://www.waveshare.com/wiki/8.8-DSI-TOUCH-A#Backlight_Control)
uses `0x96` instead. The LCD acknowledged that command without visible dimming.
On November 8, 2026, a temporary standalone test confirmed visible dimming on the
LCD using `0xAB` followed by `0xAA`.

The app reuses the existing 100 kHz bus after panel and touch initialization.
It probes `0x45`, registers the device, and requests 75% on startup. It skips the
apply write if the level write fails and records the new percentage only when
both writes succeed.

## Runtime behavior

XML owns the card, 10–100 slider, percent binding, stable widget names, and
`subject_brightness` (default 75). Firmware code in `main/brightness_control.c`
attaches after `screen_main_create()` under the LVGL lock. No hardware callbacks
live in generated code, so future generation preserves the integration.
The Raptor layout keeps display and sound controls on the right. Firmware
positions the brightness card entirely in that half at startup.

A 50 ms LVGL timer coalesces rapid slider changes, skips repeated values, clamps
again in firmware, and performs two synchronous writes with a 20 ms timeout per write.
The timer and touch polling run in the same LVGL task, so brightness cannot
interrupt a touch status/point/clear sequence. The I2C master driver also
serializes individual bus transactions. There is no worker or interrupt writer.
A slow brightness update can delay one LVGL iteration by up to two write timeouts.

The percent label shows the requested value while dragging. A successful write
means the controller acknowledged the transaction; it is not optical feedback
or register readback. On update failure, the slider is disabled, the last
successfully sent percent is restored, an error appears, and retries stop.
If initialization fails, the label says `Unavailable`; display/touch continue.
Reboot retries initialization. Values are not saved to flash.

## Regeneration contract

The user confirmed LVGL Pro Build/Preview works and the slider updates.
The fresh editor export declares `lv_subject_t * subject_brightness`, creates
it with `lv_subject_create(LV_SUBJECT_TYPE_INT)`, and initializes it with
`lv_subject_set_int(subject_brightness, 75)`. Keep that generated API intact.
`brightness_subject.h` returns the pointer for firmware and host tests, while
also supporting the older value-based export. The tracked generated files use
the pointer-based API.

1. Open the tracked `lvgl-project/basicrace1920x480v1/project.xml` in LVGL Pro.
2. Validate and preview `screen_main`, then Generate C (Ctrl+E in the editor).
3. Keep the global integer `subject_brightness`, its default **75**, and names
   `brightness_slider`, `brightness_percent`, `brightness_status`.
4. From this firmware directory run:

   ```sh
   python3 sync_lvgl_pro_ui.py
   python3 sync_lvgl_pro_ui.py --check
   idf.py build
   ```

The sync script rejects stale exports missing the brightness contract before
removing firmware resources. It checks matching C/H subject types, default 75,
XML registration, and slider/percent bindings for both generator APIs. `--check` compares all exported C/H bytes with
`main/ui/` without writing. Copies receive fresh timestamps so even an older
export recompiles. Never edit only `main/ui/`; synchronization replaces it.
Review the generated diff and repeat tests before merging.

## Repeatable desktop tests

After `idf.py build` has populated the locked managed components, with CMake,
Ninja and a host C/C++ compiler available:

```sh
cmake -S tests/host -B build-host -G Ninja
cmake --build build-host -j 8
ctest --test-dir build-host --output-on-failure
python3 tests/test_ui_sync.py
```

These compile the actual firmware handler, copied C UI, fonts, and LVGL 9.6
sources. Only the I2C functions and logging are replaced by host stubs. Scenarios
cover pointer dragging, bounds, percent binding, exact payloads, duplicate-write
suppression, coalescing, startup probe/write failures, failed updates without a
retry storm, and timer cleanup on screen deletion. They do not exercise DSI,
GT9271, electrical bus behavior, or the physical backlight.

Optional compiled-screen image:

```sh
build-host/brightness_test success /tmp/brightness-preview.ppm
```

## Validation performed on 2026-11-05

- ESP-IDF **6.1.0**, target **esp32p4**: firmware build passed.
- Four host test scenarios passed; a real LVGL pointer drag and track tap updated
  the subject, label, and mocked I2C payloads.
- Synchronization regression test and all 17 C/H byte comparisons passed.
- XML parsed successfully as XML; this is not LVGL Pro schema validation.
- The compiled screen was rendered at **1920 × 480** and visually inspected:
  background, card, percent, slider, and status fit without clipping.
- Generated-style C produces LVGL deprecation warnings; the build succeeds.
- No firmware was flashed. Electrical behavior, visible dimming, GT9271
  interaction remain pending. Editor Build/Preview and slider updates were
  subsequently confirmed by the user; fresh C export sync/build is still required.

## Subject API follow-up validation

- Sync regression passed for both value and pointer exports, including rejection
  without destination changes for mixed C/H types, wrong subject type/default,
  mismatched bindings, and missing brightness widgets.
- All four real-LVGL host scenarios passed with the tracked value export and
  again with a temporary fixture matching the reported pointer export.
- Tracked generated C/H files were not modified. These fixture checks do not
  replace syncing and building the user's actual freshly generated files.

## Hardware acceptance confirmed on 2026-11-08

- The normal right-side slider was built with ESP-IDF 6.1 and flashed successfully.
- All nine host scenarios, the UI sync regression, and 17 generated file comparisons passed.
- The user confirmed reliable touch and visible dimming on the 8.8inch DSI LCD.
- Serial capture recorded 159 acknowledged updates across 10–100% with no write errors.
- After a power cycle, the slider returned to 75% and the display visibly brightened.
- The right-side layout is the intended Raptor layout. Full dim and volume remain future work.

The November 5 notes above describe earlier validation, not outstanding hardware
acceptance. Repeat the following checks after future firmware or UI changes.

## Repeatable local hardware acceptance

Save your current known-good binary/build or keep a separate baseline checkout
before flashing. Activate the same ESP-IDF 6.1 installation used for the baseline.
Build this feature branch, then flash only when ready:

```sh
idf.py -p YOUR_PORT flash monitor
```

1. Confirm the existing landscape background and orientation remain correct.
   The brightness card on the right should show **75%**. Confirm the GT9271 ID
   log and `Backlight I2C OK: 75%, 0x45: AB 40 then AA 01`.
2. Drag slowly to **10%**, **50%**, **75%**, and **100%**. Check visible dimming,
   label tracking, correct finger direction, and reaching both endpoints.
3. Drag rapidly back and forth for 30 seconds, release at each end, and verify
   the final brightness settles correctly, touch stays responsive, and no I2C
   errors, freezes, flicker, or resets occur. Tap several track positions too.
4. Power-cycle: it should return to **75%**. Settings intentionally do not persist.
5. If brightness is unavailable or a write fails, capture the log and confirm
   the UI remains alive. Do not unplug or alter the powered display to force a
   failure; desktop tests cover those paths without risking the hardware.

If display or touch regresses, stop testing and reflash your saved baseline,
or build the baseline commit in a separate checkout. Do not reset or overwrite
local changes. Report the build/flash result, observed dimming at 10/50/100%,
touch behavior, and any serial errors when validating future changes.
