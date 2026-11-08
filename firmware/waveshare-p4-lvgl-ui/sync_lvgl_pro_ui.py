#!/usr/bin/env python3
"""Copy generated C/H files from an LVGL Pro XML project into this ESP-IDF app.

Usage: python3 sync_lvgl_pro_ui.py [optional/path/to/basicrace1920x480v1]
The source project must already have run LVGL Pro's Generate command.
"""
from pathlib import Path
import argparse
import shutil
import sys

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", nargs="?", type=Path, default=Path(__file__).resolve().parent / "lvgl-project" / "basicrace1920x480v1", help="LVGL Pro project containing generated C/H files (defaults to the adjacent tracked project)")
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
    dest.mkdir(parents=True, exist_ok=True)
    for old in dest.rglob("*"):
        if old.is_file() and old.suffix in (".c", ".h"):
            old.unlink()
    for file in files:
        target = dest / file.relative_to(source)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(file, target)
    print(f"Copied {len(files)} generated C/H files to {dest}")
    print("Now run: idf.py build")

if __name__ == "__main__":
    main()
