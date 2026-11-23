# Canonical KiCad project

This directory contains the canonical KiCad project for the ESP32-P4 Displayman Development Daughterboard. The existing project name is preserved.

## Design authority and phase boundary

The committed native three-sheet KiCad hierarchy is the authoritative editable design source. The earlier Python schematic generator is retained only as a blocked historical record: it exits before writing anything, so ordinary KiCad edits cannot diverge from or be overwritten by a second source of truth. The ten unreferenced legacy sheets are documented in `LEGACY_GENERATED_SHEETS.md` and are not part of the active project hierarchy.

The schematic is populated for independent Phase 2 electrical review. The PCB now contains the validated Nano/header datums, the 130 × 100 mm mechanical envelope, all BOM footprints and the pad/net-driven routing-ready component placement documented in `engineering-grade-component-placement.md`. It remains explicitly unrouted: no tracks, copper zones, stackup decision, differential tuning or thermal-via design has begun. The locked, edited/rescaled Waveshare drawing on `User.1` is still a visual working reference rather than production geometry; the validated P1/P2 `F.Fab` datums control the two socket placements.

## Schematic organization

| Page | Sheet | Contents |
|---:|---|---|
| 1 | Root | Three-sheet project hierarchy and review boundary |
| 2 | Power | Protected nominal-12 V input, LM7480-Q1, LM5176-Q1 to `SYS_24V`, LM76003 and TPS25947 Nano feed |
| 3 | Display Power & Backlight | Hold-up, power-fail/sequencing, 1.8/2.8/3.3 V rails, reset gating and TPS922053 backlight driver |
| 4 | Interfaces & Nano | Nano headers/DSI, MIPI ESD and panel connector, touch isolation/ESD and debug/service interfaces |

The post-audit sheets use ordinary-grid pin stubs and explicit net labels. This removes the former fragile near-coincident routes while retaining native editable KiCad symbols and the same hierarchy. The owner may perform a later aesthetic rearrangement, but every such change must preserve the netlist and pass ERC.

## Libraries and portability

- Supported editor/library generation: KiCad 10.
- `Phase2.kicad_sym` is the project-local symbol library.
- `Phase2.pretty` is the project-local footprint library.
- `Phase2.3dshapes` contains project-owned manufacturer or dimension-controlled STEP models.
- Project libraries use `${KIPRJMOD}` and standard KiCad libraries use `${KICAD10_FOOTPRINT_DIR}` / `${KICAD10_3DMODEL_DIR}`. No user-specific absolute path is required.

The project-local footprints and models are committed. A clean checkout with KiCad 10 and its standard footprint/3D packages should open without remapping libraries.

## Verification

The single-source electrical hierarchy was checked with KiCad 10.0.6:

```sh
kicad-cli sch export netlist -o /tmp/phase2.net "hardware/kicad/ESP32-P4 Display Development Daughterboard.kicad_sch"
kicad-cli sch export pdf -o /tmp/phase2.pdf "hardware/kicad/ESP32-P4 Display Development Daughterboard.kicad_sch"
kicad-cli sch erc --severity-all -o hardware/kicad/erc-report.txt "hardware/kicad/ESP32-P4 Display Development Daughterboard.kicad_sch"
```

The committed ERC report records the last native KiCad run before the Nano-header correction: zero messages, errors or warnings, with `endpoint_off_grid` enabled as an error. The subsequent chart-led P1/P2 correction and SSQ metadata change were checked structurally and by explicit connector-pin/net audits in an environment without `kicad-cli`; regenerate the native ERC report and PCB DRC in KiCad 10 before routing authorization. The historical comparison against `cfd665b0` found exactly 25 intentionally removed physical references and the documented rail renames to `SYS_24V`/`SYS24_PGOOD`; that hash is provenance, not the current design baseline.

See `docs/design-notes/maintainability-library-review.md` for the inventory and portability review, `docs/design-notes/project-local-footprint-verification.md` for the completed manufacturer land-pattern audit, `docs/design-notes/mechanical-interface-verification.md` for the original Nano geometry/source validation, `docs/design-notes/preliminary-placement-mechanical-baseline.md` for the SSQ stack/outline baseline, and `docs/design-notes/engineering-grade-component-placement.md` for the routing-ready electrical placement.

## Phase boundary

Engineering-grade placement is complete under owner authorization. Do not begin trace routing, pours, stackup freeze, differential tuning or thermal-via finalization without the next authorization. The sample checks in `preliminary-placement-mechanical-baseline.md` remain prerequisites to mechanical freeze, and the routing gates in `engineering-grade-component-placement.md` apply to the next pass.
