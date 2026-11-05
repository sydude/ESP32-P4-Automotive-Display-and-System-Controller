"""Regression checks for the destructive-copy guard and incremental build fix."""
from pathlib import Path
import os
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
            before = {p.relative_to(dest): p.read_bytes() for p in dest.rglob("*") if p.is_file()}
            (source / "screens/screen_main/screen_main_gen.c").write_text("stale export")
            result = run()
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("Stale brightness export", result.stderr)
            after = {p.relative_to(dest): p.read_bytes() for p in dest.rglob("*") if p.is_file()}
            self.assertEqual(before, after)


if __name__ == "__main__":
    unittest.main()
