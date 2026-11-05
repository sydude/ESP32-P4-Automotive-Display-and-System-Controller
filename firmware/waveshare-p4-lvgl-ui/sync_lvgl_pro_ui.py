#!/usr/bin/env python3
"""Copy generated C/H files from an LVGL Pro XML project into this ESP-IDF app.

Usage: python3 sync_lvgl_pro_ui.py [optional/path/to/basicrace1920x480v1]
The source project must already have run LVGL Pro's Generate command.
"""
from pathlib import Path
import argparse
import re
import shutil
import sys

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", nargs="?", type=Path, default=Path(__file__).resolve().parent / "lvgl-project" / "basicrace1920x480v1", help="LVGL Pro project containing generated C/H files (defaults to the adjacent tracked project)")
    parser.add_argument("--check", action="store_true", help="Check that the firmware copy matches the exported C/H files without writing")
    args = parser.parse_args()
    source = args.source.expanduser().resolve()
    dest = Path(__file__).resolve().parent / "main" / "ui"
    required = ("basicrace1920x480v1.h", "basicrace1920x480v1_gen.h", "basicrace1920x480v1_gen.c",
                "basicrace1920x480v1.c", "screens/screen_main/screen_main_gen.c",
                "images/race_background_1_data.c")
    missing = [name for name in required if not (source / name).is_file()]
    if missing:
        parser.error("Generate the LVGL Pro project first. Missing: " + ", ".join(missing))
    files = [f for f in source.rglob("*") if f.is_file() and f.suffix in (".c", ".h")
             and not any(part in ("preview-build", "preview-bin", "sim", ".git", "__MACOSX") for part in f.relative_to(source).parts)]
    if not files:
        parser.error("No generated C/H files found")
    # The firmware attaches by these stable XML names and exported subject.
    # Reject an old export before deleting any working firmware resources.
    contracts = {
        "basicrace1920x480v1_gen.h": ("subject_brightness",),
        "basicrace1920x480v1_gen.c": ("subject_brightness",),
        "screens/screen_main/screen_main_gen.c": (
            '"brightness_slider"', '"brightness_percent"', '"brightness_status"',
            "lv_slider_bind_value", "subject_brightness"),
    }
    for name, tokens in contracts.items():
        text = (source / name).read_text()
        if any(token not in text for token in tokens):
            parser.error("Stale brightness export: regenerate the updated XML project first: " + name)
    # Accept complete, internally consistent exports from either generator API.
    header = (source / "basicrace1920x480v1_gen.h").read_text()
    generated = (source / "basicrace1920x480v1_gen.c").read_text()
    screen = (source / "screens/screen_main/screen_main_gen.c").read_text()
    def matches(pattern, text):
        return re.search(pattern, text) is not None

    pointer = matches(r"extern\s+lv_subject_t\s*\*\s*subject_brightness\s*;", header)
    ref = r"subject_brightness" if pointer else r"&\s*subject_brightness"
    declaration = r"lv_subject_t\s*" + (r"\*\s*" if pointer else r"\s+") + r"subject_brightness\s*;"
    initialization = (
        matches(r"subject_brightness\s*=\s*lv_subject_create\s*\(\s*LV_SUBJECT_TYPE_INT\s*\)\s*;", generated)
        and matches(r"lv_subject_set_int\s*\(\s*subject_brightness\s*,\s*75\s*\)", generated)
        if pointer else matches(r"lv_subject_init_int\s*\(\s*&\s*subject_brightness\s*,\s*75\s*\)", generated)
    )
    if not (matches(r"extern\s+" + declaration, header)
            and matches(declaration, generated) and initialization
            and matches(r'lv_xml_register_subject\s*\(\s*NULL\s*,\s*"subject_brightness"\s*,\s*' + ref + r"\s*\)", generated)
            and matches(r"lv_slider_bind_value\s*\([^,]+,\s*" + ref + r"\s*\)", screen)
            and matches(r'lv_label_bind_text\s*\([^,]+,\s*' + ref + r'\s*,\s*"%d%%"\s*\)', screen)):
        parser.error("Stale or inconsistent brightness subject API: regenerate the complete XML project (default 75 and slider/percent bindings required)")
    if args.check:
        expected = {f.relative_to(source) for f in files}
        actual = {f.relative_to(dest) for f in dest.rglob("*") if f.is_file() and f.suffix in (".c", ".h")}
        different = [str(p) for p in sorted(expected | actual)
                     if p not in expected or p not in actual or (source / p).read_bytes() != (dest / p).read_bytes()]
        if different:
            parser.error("Firmware UI is out of sync: " + ", ".join(different))
        print(f"All {len(files)} exported C/H files match main/ui")
        return
    dest.mkdir(parents=True, exist_ok=True)
    for old in dest.rglob("*"):
        if old.is_file() and old.suffix in (".c", ".h"):
            old.unlink()
    for file in files:
        target = dest / file.relative_to(source)
        target.parent.mkdir(parents=True, exist_ok=True)
        # Use fresh timestamps so an older export still triggers recompilation.
        shutil.copyfile(file, target)
    print(f"Copied {len(files)} generated C/H files to {dest}")
    print("Now run: idf.py build")

if __name__ == "__main__":
    main()
