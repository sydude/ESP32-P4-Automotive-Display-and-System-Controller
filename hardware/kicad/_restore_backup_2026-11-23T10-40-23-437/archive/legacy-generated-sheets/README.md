These sheets are historical artifacts from the original Phase 2 generated schematic architecture.
They are not part of the active KiCad hierarchy and must not be used as design authority.
They were superseded by the consolidated native KiCad sheets beginning with commit c3b3abaa2eb4a29d8d367f2da87068be705e9ada.
The active schematic consists of 01_power, 02_display_power_backlight, and 03_interfaces_nano.


-------------------------------------------------------

PRIOR 'LEGACY-GENERATED-SCHEMATIC-SHEETS.md' file contents:

    # Unreferenced legacy generated sheets

    The ten numbered schematic files named from `01_bench_input.kicad_sch` through `10_headers_debug.kicad_sch` are retained as historical snapshots to avoid destructively removing prior project artifacts. They are **not** referenced by the canonical root sheet and are **not** part of the active schematic hierarchy.

    The active, authoritative native KiCad 10 hierarchy is:

    - `ESP32-P4 Display Development Daughterboard.kicad_sch`
    - `01_power.kicad_sch`
    - `02_display_power_backlight.kicad_sch`
    - `03_interfaces_nano.kicad_sch`

    `tools/generate_schematic.py` is likewise retained only as a historical implementation record and exits without writing files. Do not use the legacy sheets or generator as a design source.
