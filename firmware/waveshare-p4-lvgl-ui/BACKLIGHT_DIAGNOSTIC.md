# Temporary standalone backlight diagnostic

For ESP32-P4-WIFI6-DB with the 8.8-inch 480x1920 DSI panel in landscape.
The current hardware ACKs slider writes without visible dimming. This test
isolates brightness commands from touch interaction and LVGL slider events.
It does not establish that the controller protocol matches this panel revision.

## Enable and run

From `firmware/waveshare-p4-lvgl-ui`, activate ESP-IDF 6.1.x, then:

```sh
idf.py menuconfig
# Backlight diagnostic -> Enable temporary standalone backlight diagnostic
idf.py build
idf.py -p YOUR_PORT flash monitor
```

The switch is `CONFIG_BACKLIGHT_DIAGNOSTIC=y`, **off by default**. Do not change
DSI initialization or regenerate UI resources to enable this test. Preserve your
known-good firmware before flashing. No hardware was flashed during development.

After the existing backlight probe/registration and UI attachment, a FreeRTOS
task runs once per boot, independently of touch events and LVGL timers:

| Command | Payload at 7-bit address 0x45 | Hold |
| --- | --- | --- |
| 100% | `96 FF` | 3000 ms |
| 10% | `96 19` | 3000 ms |

That pair repeats **three times** (about 18 seconds plus transaction/scheduling
time), followed by one `96 BF` command to restore 75%. Holds start after each
successful synchronous write. The normal initial 75% command is skipped in this
mode. A failed cycle command aborts the remaining cycles and makes just one
75% recovery attempt. A failed probe/device registration or task allocation
starts no test. There are no automatic retries or off/zero commands.

The slider is disabled and its regular writer is compiled out for the entire
diagnostic boot, including after completion or failure. The card says
`Diagnostic` and `Backlight test | See serial log`; it does not claim to display
measured brightness. The task never accesses LVGL objects, so screen deletion
does not invalidate it and reattaching a screen cannot restart it.

DSI initialization, generated UI files, touch polling and coordinate mapping
are unchanged. The worker shares the existing I2C bus; the driver serializes
individual transactions. A backlight transaction can occur between GT9271
transactions but never addresses its registers. This is a temporary diagnostic,
not a new production touch scheduling policy.

## Interpret the serial log

Look for `DIAG begin`, six `DIAG cycle` entries, `DIAG restore`, and `DIAG end`.
Each write logs the requested percent, 7-bit address, register, payload byte,
and success/failure; failures include the ESP-IDF error name. Probe/registration
failure and task allocation failure are logged separately. Default INFO logging
shows these messages.

- Alternating optical brightness: the existing write protocol can affect this
  hardware independently of touch and slider handling.
- All writes OK but no visible alternation: ACK only proves transaction delivery.
  It does not prove the register controls this panel's backlight. Capture logs
  and the exact display/controller revision before further protocol changes.
- Any failed write: capture the error and whether the one restore attempt
  succeeded. `cycles=aborted` or failed restore is not a successful test.

Readback is deliberately **skipped**, with a log entry. The pinned vendor sources
in [BRIGHTNESS_TESTING.md](BRIGHTNESS_TESTING.md) establish the two-byte setter,
not a safe read protocol for register 0x96. No speculative register-pointer
write, receive, initialization replay, or undocumented write is performed.
A returned register value, even if safely supported later, would not measure
optical brightness.

## Disable

Uncheck the menuconfig option, save, rebuild and flash. The normal 75% startup
and slider writer return. Rebooting a diagnostic build runs the three cycles
again; it does not disable diagnostic mode. The switch is not saved as a
runtime brightness preference.

## Verification

The host suite compiles both modes against real LVGL and the existing generated
UI, with I2C and diagnostic task scheduling mocked. It checks exact payloads,
six 3000 ms delays, no writes from subject changes during holds or after the
test, single execution on reattachment, bounded write failure/recovery, probe
failure, and task allocation failure, plus the four normal-slider scenarios.
Run the commands in BRIGHTNESS_TESTING.md. These tests cannot verify optical
response, real task timing, DSI or electrical behavior; observe those on hardware.

Validation on 2026-11-05: ESP-IDF 6.1.0 / esp32p4 builds passed with the
switch disabled and enabled. All nine host scenarios, the UI synchronization
regression, and all 17 generated C/H byte comparisons passed in an isolated
copy without the local duplicate generated files. Existing generated-code
LVGL deprecation warnings remain. No firmware was flashed or optical response
verified.
