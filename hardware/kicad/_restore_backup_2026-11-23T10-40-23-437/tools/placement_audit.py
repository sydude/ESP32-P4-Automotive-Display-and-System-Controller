#!/usr/bin/env python3
"""Audit and render the un-routed KiCad placement.

The script deliberately operates on footprint positions and courtyard geometry only.
It does not create tracks, vias, zones, or copper.  `--apply` performs a narrowly
scoped textual rewrite of each footprint's top-level `(at ...)` record so KiCad's
formatting, UUIDs, and embedded library geometry remain unchanged.
"""

from __future__ import annotations

import argparse
import json
import math
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from sexpdata import loads


def head(item: object) -> str:
    return str(item[0]) if isinstance(item, list) and item else ""


def child(item: list, name: str) -> list | None:
    return next((part for part in item if head(part) == name), None)


def children(item: list, name: str) -> Iterable[list]:
    return (part for part in item if head(part) == name)


def property_value(item: list, name: str) -> str | None:
    for part in children(item, "property"):
        if len(part) >= 3 and part[1] == name:
            return str(part[2])
    return None


def number(value: object) -> float:
    return float(value)


def point(form: list | None) -> tuple[float, float] | None:
    if form is None or len(form) < 3:
        return None
    return number(form[1]), number(form[2])


def rotate_translate(
    xy: tuple[float, float], at: tuple[float, float, float]
) -> tuple[float, float]:
    theta = math.radians(at[2])
    x, y = xy
    return (
        at[0] + x * math.cos(theta) - y * math.sin(theta),
        at[1] + x * math.sin(theta) + y * math.cos(theta),
    )


@dataclass
class Footprint:
    reference: str
    name: str
    layer: str
    at: tuple[float, float, float]
    courtyard_points: list[tuple[float, float]]
    pads: list[tuple[str, str, tuple[float, float]]]

    @property
    def courtyard_bbox(self) -> tuple[float, float, float, float]:
        points = [rotate_translate(p, self.at) for p in self.courtyard_points]
        if not points:
            points = [(self.at[0], self.at[1])]
        xs = [p[0] for p in points]
        ys = [p[1] for p in points]
        return min(xs), min(ys), max(xs), max(ys)


def footprint_from_form(form: list) -> Footprint:
    reference = property_value(form, "Reference") or "?"
    at_form = child(form, "at")
    if at_form is None:
        at = (0.0, 0.0, 0.0)
    else:
        at = (
            number(at_form[1]),
            number(at_form[2]),
            number(at_form[3]) if len(at_form) > 3 else 0.0,
        )
    layer_form = child(form, "layer")
    layer = str(layer_form[1]) if layer_form else "?"

    courtyard_points: list[tuple[float, float]] = []
    for graphic in form:
        if head(graphic) not in {"fp_line", "fp_rect", "fp_arc", "fp_circle", "fp_poly"}:
            continue
        graphic_layer = child(graphic, "layer")
        if graphic_layer is None or "CrtYd" not in str(graphic_layer[1]):
            continue
        graphic_head = head(graphic)
        local_points: list[tuple[float, float]] = []
        for key in ("start", "end", "mid", "center"):
            xy = point(child(graphic, key))
            if xy is not None:
                local_points.append(xy)
        if graphic_head == "fp_circle":
            center_xy = point(child(graphic, "center"))
            end_xy = point(child(graphic, "end"))
            if center_xy is not None and end_xy is not None:
                radius = math.dist(center_xy, end_xy)
                local_points.extend(
                    [
                        (center_xy[0] - radius, center_xy[1]),
                        (center_xy[0] + radius, center_xy[1]),
                        (center_xy[0], center_xy[1] - radius),
                        (center_xy[0], center_xy[1] + radius),
                    ]
                )
        courtyard_points.extend(local_points)
        pts = child(graphic, "pts")
        if pts:
            for xy_form in children(pts, "xy"):
                xy = point(xy_form)
                if xy is not None:
                    courtyard_points.append(xy)

    pads: list[tuple[str, str, tuple[float, float]]] = []
    for pad in children(form, "pad"):
        pad_at = child(pad, "at")
        local = point(pad_at) or (0.0, 0.0)
        net = child(pad, "net")
        net_name = str(net[1]) if net and len(net) > 1 else ""
        pads.append((str(pad[1]), net_name, rotate_translate(local, at)))

    return Footprint(
        reference=reference,
        name=str(form[1]),
        layer=layer,
        at=at,
        courtyard_points=courtyard_points,
        pads=pads,
    )


def load_footprints(path: Path) -> list[Footprint]:
    root = loads(path.read_text())
    return [footprint_from_form(item) for item in root if head(item) == "footprint"]


def footprint_text_blocks(text: str) -> list[tuple[int, int, str]]:
    blocks: list[tuple[int, int, str]] = []
    token = "(footprint "
    cursor = 0
    while True:
        start = text.find(token, cursor)
        if start < 0:
            break
        depth = 0
        in_string = False
        escaped = False
        end = start
        for end in range(start, len(text)):
            char = text[end]
            if in_string:
                if escaped:
                    escaped = False
                elif char == "\\":
                    escaped = True
                elif char == '"':
                    in_string = False
                continue
            if char == '"':
                in_string = True
            elif char == "(":
                depth += 1
            elif char == ")":
                depth -= 1
                if depth == 0:
                    end += 1
                    break
        block = text[start:end]
        match = re.search(r'\(property\s+"Reference"\s+"([^"]+)"', block)
        if match:
            blocks.append((start, end, match.group(1)))
        cursor = end
    return blocks


def apply_moves(path: Path, move_path: Path) -> None:
    moves = json.loads(move_path.read_text())
    text = path.read_text()
    blocks = footprint_text_blocks(text)
    seen: set[str] = set()
    for start, end, reference in reversed(blocks):
        if reference not in moves:
            continue
        x, y, angle = moves[reference]
        block = text[start:end]
        replacement = f"(at {x:.3f} {y:.3f} {angle:g})"
        block, count = re.subn(r"\(at\s+[-+0-9.eE]+\s+[-+0-9.eE]+(?:\s+[-+0-9.eE]+)?\)", replacement, block, count=1)
        if count != 1:
            raise RuntimeError(f"could not update top-level position for {reference}")
        text = text[:start] + block + text[end:]
        seen.add(reference)
    missing = sorted(set(moves) - seen)
    if missing:
        raise RuntimeError(f"references not found: {', '.join(missing)}")
    path.write_text(text)


def bbox_overlap(
    a: tuple[float, float, float, float], b: tuple[float, float, float, float]
) -> tuple[float, float] | None:
    dx = min(a[2], b[2]) - max(a[0], b[0])
    dy = min(a[3], b[3]) - max(a[1], b[1])
    return (dx, dy) if dx > 1e-6 and dy > 1e-6 else None


def report(path: Path, refs: set[str]) -> None:
    text = path.read_text()
    footprints = load_footprints(path)
    selected = [f for f in footprints if not refs or f.reference in refs]
    for fp in sorted(selected, key=lambda item: item.reference):
        x0, y0, x1, y1 = fp.courtyard_bbox
        print(
            f"{fp.reference:6} {fp.layer:5} at=({fp.at[0]:8.3f},{fp.at[1]:8.3f},{fp.at[2]:6.1f}) "
            f"ctyd=({x0:8.3f},{y0:8.3f})-({x1:8.3f},{y1:8.3f}) {fp.name}"
        )
    print(f"footprints={len(footprints)} top={sum(f.layer == 'F.Cu' for f in footprints)} bottom={sum(f.layer == 'B.Cu' for f in footprints)}")
    print(
        "tracks={} vias={} zones={}".format(
            len(re.findall(r"\n\s*\(segment\s", text)),
            len(re.findall(r"\n\s*\(via\s", text)),
            len(re.findall(r"\n\s*\(zone\s", text)),
        )
    )
    top = [f for f in footprints if f.layer == "F.Cu" and not f.reference.startswith("H")]
    overlaps = []
    for index, first in enumerate(top):
        for second in top[index + 1 :]:
            overlap = bbox_overlap(first.courtyard_bbox, second.courtyard_bbox)
            if overlap:
                overlaps.append((first.reference, second.reference, *overlap))
    print(f"top-courtyard-bbox-overlaps={len(overlaps)}")
    for item in sorted(overlaps, key=lambda value: value[2] * value[3], reverse=True)[:80]:
        print(f"  {item[0]} {item[1]} dx={item[2]:.3f} dy={item[3]:.3f}")


def render(path: Path, output: Path) -> None:
    import matplotlib.pyplot as plt
    from matplotlib.patches import Rectangle

    footprints = load_footprints(path)
    fig, axis = plt.subplots(figsize=(15, 12), dpi=160)
    axis.set_aspect("equal")
    axis.set_xlim(40, 175)
    axis.set_ylim(126, 22)
    axis.set_facecolor("#101820")
    colors = {
        "F.Cu": (0.2, 0.75, 0.95, 0.22),
        "B.Cu": (0.85, 0.3, 0.95, 0.16),
    }
    for fp in footprints:
        x0, y0, x1, y1 = fp.courtyard_bbox
        axis.add_patch(
            Rectangle(
                (x0, y0),
                x1 - x0,
                y1 - y0,
                facecolor=colors.get(fp.layer, (0.7, 0.7, 0.7, 0.15)),
                edgecolor=colors.get(fp.layer, (0.7, 0.7, 0.7, 0.5))[:3],
                linewidth=0.55,
            )
        )
        if not fp.reference.startswith("H"):
            axis.text(
                fp.at[0],
                fp.at[1],
                fp.reference,
                color="white",
                fontsize=4.2,
                ha="center",
                va="center",
            )
    axis.grid(color="white", alpha=0.10, linewidth=0.35)
    axis.set_xlabel("PCB X (mm)")
    axis.set_ylabel("PCB Y (mm)")
    fig.tight_layout()
    fig.savefig(output)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("board", type=Path)
    parser.add_argument("--apply", type=Path)
    parser.add_argument("--render", type=Path)
    parser.add_argument("--refs", default="")
    args = parser.parse_args()
    if args.apply:
        apply_moves(args.board, args.apply)
    if args.render:
        render(args.board, args.render)
    refs = {ref for ref in args.refs.split(",") if ref}
    report(args.board, refs)


if __name__ == "__main__":
    main()
