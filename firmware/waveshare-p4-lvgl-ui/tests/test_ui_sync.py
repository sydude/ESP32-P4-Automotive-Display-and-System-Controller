"""Regression checks for the destructive-copy guard and incremental build fix."""
from pathlib import Path
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest

APP = Path(__file__).resolve().parents[1]


class UISyncTests(unittest.TestCase):
    def test_sync_check_stale_guard_and_fresh_timestamps(self):
        with tempfile.TemporaryDirectory() as directory:
            app = Path(directory)
            script = app / "sync_lvgl_pro_ui.py"
            shutil.copyfile(APP / script.name, script)
            source = app / "lvgl-project" / "basicrace1920x480v1"
            real_source = APP / "lvgl-project" / "basicrace1920x480v1"
            for name in ("basicrace1920x480v1.c", "basicrace1920x480v1.h",
                         "basicrace1920x480v1_gen.c", "basicrace1920x480v1_gen.h",
                         "screens/screen_main/screen_main_gen.c", "images/race_background_1_data.c"):
                target = source / name
                target.parent.mkdir(parents=True, exist_ok=True)
                # The asset bytes aren't relevant to the synchronization contract.
                target.write_bytes(b"/* asset */" if name.startswith("images/") else (real_source / name).read_bytes())
                os.utime(target, (1000, 1000))

            def run(*args):
                return subprocess.run([sys.executable, str(script), *args], capture_output=True, text=True)

            self.assertEqual(run().returncode, 0)
            self.assertEqual(run("--check").returncode, 0)
            dest = app / "main" / "ui"
            self.assertGreater((dest / "basicrace1920x480v1.c").stat().st_mtime, 1000)
            copied = dest / "basicrace1920x480v1.c"
            copied.write_text("out of sync")
            self.assertNotEqual(run("--check").returncode, 0)
            self.assertEqual(copied.read_text(), "out of sync")
            self.assertEqual(run().returncode, 0)
            # The tracked export uses a pointer subject. Also exercise the
            # older value API with a fixture derived from the same screen.
            gen = source / "basicrace1920x480v1_gen.c"
            header = source / "basicrace1920x480v1_gen.h"
            screen = source / "screens/screen_main/screen_main_gen.c"
            pointer_export = {file: file.read_text() for file in (gen, header, screen)}
            declaration = r"lv_subject_t\s*\*\s*subject_brightness"
            header.write_text(re.sub(declaration, "lv_subject_t subject_brightness", pointer_export[header]))
            value_gen = re.sub(declaration, "lv_subject_t subject_brightness", pointer_export[gen])
            value_gen = re.sub(
                r"subject_brightness\s*=\s*lv_subject_create\(LV_SUBJECT_TYPE_INT\);"
                r"\s*lv_subject_set_int\(subject_brightness, 75\);",
                "lv_subject_init_int(&subject_brightness, 75);",
                value_gen,
            )
            gen.write_text(value_gen.replace('"subject_brightness", subject_brightness',
                                             '"subject_brightness", &subject_brightness'))
            slider_binding = r"(lv_slider_bind_value\s*\([^,]+,\s*)subject_brightness\b"
            percent_binding = r"(lv_label_bind_text\s*\([^,]+,\s*)subject_brightness\b"
            value_screen = re.sub(slider_binding, r"\1&subject_brightness", pointer_export[screen])
            screen.write_text(re.sub(percent_binding, r"\1&subject_brightness", value_screen))
            self.assertEqual(run().returncode, 0)
            self.assertEqual(run("--check").returncode, 0)

            for file, original in pointer_export.items():
                file.write_text(original)
            self.assertEqual(run().returncode, 0)
            self.assertEqual(run("--check").returncode, 0)
            snapshot = {p.relative_to(dest): p.read_bytes() for p in dest.rglob("*") if p.is_file()}
            for file, pattern, replacement in (
                (gen, "LV_SUBJECT_TYPE_INT", "LV_SUBJECT_TYPE_STRING"),
                (gen, "subject_brightness, 75", "subject_brightness, 0"),
                (header, declaration, "lv_subject_t subject_brightness"),
                (screen, slider_binding, r"\1&subject_brightness"),
                (screen, percent_binding, r"\1&subject_brightness"),
            ):
                with self.subTest(mismatch=pattern):
                    original = file.read_text()
                    invalid, substitutions = re.subn(pattern, replacement, original)
                    self.assertEqual(substitutions, 1)
                    file.write_text(invalid)
                    result = run()
                    self.assertNotEqual(result.returncode, 0)
                    self.assertIn("Stale or inconsistent brightness subject API", result.stderr)
                    self.assertEqual(snapshot, {p.relative_to(dest): p.read_bytes() for p in dest.rglob("*") if p.is_file()})
                    file.write_text(original)
            before = {p.relative_to(dest): p.read_bytes() for p in dest.rglob("*") if p.is_file()}
            (source / "screens/screen_main/screen_main_gen.c").write_text("stale export")
            result = run()
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("Stale brightness export", result.stderr)
            after = {p.relative_to(dest): p.read_bytes() for p in dest.rglob("*") if p.is_file()}
            self.assertEqual(before, after)


if __name__ == "__main__":
    unittest.main()
