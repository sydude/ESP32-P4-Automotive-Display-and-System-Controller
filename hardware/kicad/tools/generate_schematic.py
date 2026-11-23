#!/usr/bin/env python3
"""Retired Phase-2 generator retained only as a historical implementation record.

The committed native three-sheet KiCad hierarchy is authoritative. This legacy
script is deliberately blocked because running it would recreate the obsolete
ten-sheet, label-only hierarchy and overwrite human-maintained schematic work.
"""

from __future__ import annotations

raise SystemExit(
    "Retired generator: edit the committed native KiCad 10 schematic files. "
    "See hardware/kicad/README.md."
)

import csv
import math
import uuid
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
KICAD = ROOT / "hardware" / "kicad"
PROJECT = "ESP32-P4 Display Development Daughterboard"
ROOT_SCH = KICAD / f"{PROJECT}.kicad_sch"


def uid() -> str:
    return str(uuid.uuid4())


def q(value: str) -> str:
    return '"' + value.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n') + '"'


@dataclass
class Pin:
    number: str
    name: str
    etype: str
    net: str | None
    side: str = "L"


@dataclass
class Part:
    ref: str
    value: str
    footprint: str
    datasheet: str
    pins: list[Pin]
    x: float
    y: float
    mpn: str = ""
    manufacturer: str = ""
    description: str = ""
    dnp: bool = False
    virtual: bool = False
    fields: dict[str, str] = field(default_factory=dict)


@dataclass
class Sheet:
    filename: str
    title: str
    page: int
    parts: list[Part]
    notes: list[str]


def pin(number, name, etype, net, side="L"):
    return Pin(str(number), name, etype, net, side)


def passive(ref, value, footprint, a, b, x, y, *, mpn="", manufacturer="", description="", dnp=False):
    return Part(ref, value, footprint, "", [pin(1, "1", "passive", a), pin(2, "2", "passive", b, "R")], x, y,
                mpn, manufacturer, description, dnp)


def diode(ref, value, footprint, cathode, anode, x, y, *, mpn="", manufacturer="", description="", dnp=False):
    """Two-terminal diode using KiCad's pad convention: pin 1=K, pin 2=A."""
    return Part(ref, value, footprint, "", [pin(1, "K", "passive", cathode), pin(2, "A", "passive", anode, "R")], x, y,
                mpn, manufacturer, description, dnp)


def pwr_flag(ref, net, x, y):
    """ERC-only power source marker, excluded from the PCB and BOM."""
    return Part(ref, "PWR_FLAG", "", "", [pin(1, "PWR_FLAG", "power_out", net)], x, y,
                description="ERC power-source marker", virtual=True)


def tp(ref, net, x, y):
    return Part(ref, net, "TestPoint:TestPoint_THTPad_D1.0mm_Drill0.5mm", "",
                [pin(1, net, "passive", net)], x, y, description="Labeled test point")


def connector(ref, value, footprint, nets, x, y, *, mpn="", manufacturer="", names=None, description=""):
    names = names or [f"PIN_{i + 1}" for i in range(len(nets))]
    pins = [pin(i + 1, names[i], "passive", nets[i], "L" if i % 2 == 0 else "R") for i in range(len(nets))]
    return Part(ref, value, footprint, "", pins, x, y, mpn, manufacturer, description)


def ic(ref, value, footprint, datasheet, pins, x, y, *, mpn="", manufacturer="Texas Instruments", description=""):
    return Part(ref, value, footprint, datasheet, pins, x, y, mpn or value, manufacturer, description)


def mosfet(ref, net_s, net_g, net_d, x, y, *, value="CSD19531Q5A", footprint="Package_SON:Texas_DQK", description="100 V N-channel MOSFET"):
    return Part(ref, value, footprint, "https://www.ti.com/lit/ds/symlink/csd19531q5a.pdf",
                [pin(1, "S", "passive", net_s), pin(2, "S", "passive", net_s), pin(3, "S", "passive", net_s),
                 pin(4, "G", "input", net_g), pin(5, "D", "passive", net_d, "R"), pin(6, "D", "passive", net_d, "R"),
                 pin(7, "D", "passive", net_d, "R"), pin(8, "D", "passive", net_d, "R"), pin(9, "EP", "passive", net_d, "R")],
                x, y, value, "Texas Instruments", description)


def lm74700(ref, anode, cathode, prefix, x, y):
    return ic(ref, "LM74700QDBVRQ1", "Package_TO_SOT_SMD:SOT-23-6", "https://www.ti.com/lit/ds/symlink/lm74700-q1.pdf", [
        pin(1, "VCAP", "power_out", f"{prefix}_VCAP"), pin(2, "GND", "power_in", "GND"),
        pin(3, "EN", "input", anode), pin(4, "CATHODE", "input", cathode, "R"),
        pin(5, "GATE", "output", f"{prefix}_GATE", "R"), pin(6, "ANODE", "input", anode, "R")], x, y,
        description="Ideal-diode controller, reverse-current blocking")


def tlv755(ref, value, out, enable, x, y):
    return ic(ref, value, "Package_TO_SOT_SMD:SOT-23-5", "https://www.ti.com/lit/ds/symlink/tlv755p.pdf", [
        pin(1, "IN", "power_in", "DISP_HOLD_5V" if out.startswith("LCD_") else "SYS_5V_3A"),
        pin(2, "GND", "power_in", "GND"), pin(3, "EN", "input", enable),
        pin(4, "NC", "no_connect", None, "R"), pin(5, "OUT", "power_out", out, "R")], x, y,
        description=f"500 mA fixed LDO for {out}")


def lvc1g07(ref, inp, out, vcc, x, y):
    return ic(ref, "SN74LVC1G07DBVR", "Package_TO_SOT_SMD:SOT-23-5", "https://www.ti.com/lit/ds/symlink/sn74lvc1g07.pdf", [
        pin(1, "NC", "no_connect", None), pin(2, "A", "input", inp), pin(3, "GND", "power_in", "GND"),
        pin(4, "Y_OD", "open_collector", out, "R"), pin(5, "VCC", "power_in", vcc, "R")], x, y,
        description="Partial-power-down open-drain reset clamp")


def build_sheets() -> list[Sheet]:
    s: list[Sheet] = []

    # 01 - regulated 24 V bench input. Reverse blocking is on the ORing sheet.
    p = [
        connector("J101", "RAPC722X 24V BENCH", "Phase2:Switchcraft_RAPC722X_RightAngle", ["BENCH_24V_RAW", "GND", None], 35, 55,
                  mpn="RAPC722X", manufacturer="Switchcraft", names=["CENTER_+24V", "SLEEVE_GND", "SWITCH_NC"], description="5.5 mm OD bench barrel jack; footprint verify before PCB freeze"),
        passive("F101", "2A FAST", "Fuse:Fuse_1206_3216Metric", "BENCH_24V_RAW", "BENCH_FUSED_24V", 80, 45,
                mpn="0451002.MRL", manufacturer="Littelfuse", description="125 V fast acting input fuse"),
        diode("D101", "SMBJ30A", "Diode_SMD:D_SMB", "BENCH_FUSED_24V", "GND", 80, 65,
                mpn="SMBJ30A", manufacturer="Littelfuse", description="600 W unidirectional TVS"),
        passive("C101", "100nF 100V X7R", "Capacitor_SMD:C_0603_1608Metric", "BENCH_FUSED_24V", "GND", 125, 45),
        passive("C102", "10uF 50V", "Capacitor_SMD:C_1210_3225Metric", "BENCH_FUSED_24V", "GND", 125, 65),
        passive("C103", "47uF 50V", "Capacitor_SMD:CP_Elec_8x10", "BENCH_FUSED_24V", "GND", 170, 45),
        tp("TP101", "BENCH_24V_RAW", 170, 65), tp("TP102", "BENCH_FUSED_24V", 215, 45), tp("TP103", "GND", 215, 65),
        pwr_flag("PWR101", "GND", 255, 45),
    ]
    s.append(Sheet("01_bench_input.kicad_sch", "Bench 24 V Input", 2, p, [
        "Regulated 24 V bench input: 21.6–26.4 V. Center positive.",
        "F101/TVS coordination and adapter inrush are prototype verification items; no automotive qualification claim.",
        "The independent ideal-diode stage is shown on Source ORing (sheet 04).",
    ]))

    # 02 - vehicle protection.
    p = [
        connector("J201", "VEHICLE 12V", "Connector_Molex:Molex_Micro-Fit_3.0_43045-0218_2x01-1MP_P3.00mm_Vertical", ["VEH_12V_RAW", "GND"], 30, 55,
                  mpn="43045-0218", manufacturer="Molex", names=["BATT+", "BATT-"], description="2-circuit vertical Micro-Fit 3.0 SMT header; sealing not claimed"),
        passive("F201", "5A TIME DELAY", "Fuse:Fuseholder_Blade_Mini_Keystone_3568", "VEH_12V_RAW", "VEH_FUSED", 70, 35,
                mpn="0297005.WXNV / 3568", manufacturer="Littelfuse / Keystone", description="5 A MINI blade fuse in Keystone 3568 holder"),
        passive("L201", "2.2uH 8A", "Inductor_SMD:L_Bourns_SRP1038C_10.0x10.0mm", "VEH_FUSED", "VEH_FILTER", 70, 55,
                mpn="SRP1038A-2R2M", manufacturer="Bourns", description="Shielded AEC-Q200 input filter inductor"),
        passive("C201", "100nF 100V", "Capacitor_SMD:C_0603_1608Metric", "VEH_FILTER", "GND", 70, 75),
        passive("C202", "22uF 50V X7R", "Capacitor_SMD:C_1210_3225Metric", "VEH_FILTER", "GND", 110, 35),
        passive("C203", "100uF 50V", "Capacitor_SMD:CP_Elec_10x10", "VEH_FILTER", "GND", 110, 55),
        passive("R201", "1.0R 2W", "Resistor_SMD:R_2512_6332Metric", "VEH_FILTER", "VEH_DAMP", 110, 75, description="Series damping leg"),
        passive("C204", "10uF 50V", "Capacitor_SMD:C_1210_3225Metric", "VEH_DAMP", "GND", 150, 35),
        diode("D201", "SM8S24CA-Q", "Phase2:Bourns_DO-218AB", "VEH_FILTER", "GND", 150, 55, mpn="SM8S24CA-Q", manufacturer="Bourns", description="6.6 kW bidirectional vehicle TVS"),
        ic("U201", "LM74800QDRRRQ1", "Phase2:Texas_DRR0012A_WSON-12_3x3mm_P0.5mm_EP1.2x2.5mm", "https://www.ti.com/lit/ds/symlink/lm7480-q1.pdf", [
            pin(1, "DGATE", "output", "VEH_DGATE"), pin(2, "A", "input", "VEH_FILTER"), pin(3, "VSNS", "input", "VEH_FILTER"),
            pin(4, "SW", "input", "VEH_OV_TOP"), pin(5, "OV", "input", "VEH_OV"), pin(6, "EN/UVLO", "input", "VEH_UVLO"),
            pin(7, "GND", "power_in", "GND", "R"), pin(8, "HGATE", "output", "VEH_HGATE", "R"),
            pin(9, "OUT", "input", "VEH_PROT", "R"), pin(10, "VS", "power_in", "VEH_FET_MID", "R"),
            pin(11, "CAP", "power_out", "VEH_CAP", "R"), pin(12, "C", "input", "VEH_FET_MID", "R"),
            pin(13, "RTN_EP", "no_connect", None, "R")], 205, 55,
            description="Reverse-battery, ideal-diode, OV and back-to-back disconnect controller"),
        mosfet("Q201", "VEH_FILTER", "VEH_DGATE", "VEH_FET_MID", 255, 35),
        mosfet("Q202", "VEH_PROT", "VEH_HGATE", "VEH_FET_MID", 255, 65),
        passive("C205", "100nF 100V", "Capacitor_SMD:C_0603_1608Metric", "VEH_CAP", "VEH_FET_MID", 310, 35),
        passive("C206", "100nF 100V", "Capacitor_SMD:C_0603_1608Metric", "VEH_FET_MID", "GND", 310, 55),
        passive("R202", "56.2k 1%", "Resistor_SMD:R_0603_1608Metric", "VEH_FILTER", "VEH_UVLO", 310, 75),
        passive("R203", "10.0k 1%", "Resistor_SMD:R_0603_1608Metric", "VEH_UVLO", "GND", 310, 95),
        passive("R204", "100k 1%", "Resistor_SMD:R_0603_1608Metric", "VEH_OV_TOP", "VEH_OV", 355, 35),
        passive("R205", "6.49k 1%", "Resistor_SMD:R_0603_1608Metric", "VEH_OV", "GND", 355, 55),
        tp("TP201", "VEH_12V_RAW", 400, 55), tp("TP202", "VEH_PROT", 400, 75),
        pwr_flag("PWR201", "VEH_FET_MID", 400, 95), pwr_flag("PWR202", "VEH_PROT", 445, 35),
    ]
    s.append(Sheet("02_vehicle_protection.kicad_sch", "Vehicle Input Protection", 3, p, [
        "UVLO divider 56.2k/10.0k: 8.15 V rising, about 7.49 V falling using LM7480 thresholds.",
        "OV divider 100k/6.49k: 20.18 V nominal cutoff; rejects accidental 24 V vehicle-port connection.",
        "Q201/Q202 are common-drain 100 V FETs: ideal-diode plus independent high-side disconnect/reverse blocking.",
        "LM7480 RTN exposed pad is intentionally floating per TI; do not connect it to PCB copper.",
        "SM8S24CA-Q protects the evaluation input; compliance with ISO 7637/16750 is not claimed.",
    ]))

    # 03 - 30 W LM5176 buck-boost.
    lm5176_pins = [
        pin(1, "EN/UVLO", "input", "VEH_PROT"), pin(2, "VIN", "power_in", "VEH_PROT"), pin(3, "VISNS", "input", "VEH_PROT"),
        pin(4, "MODE", "input", "LM5176_MODE"), pin(5, "DITH", "input", "GND"), pin(6, "RT/SYNC", "input", "LM5176_RT"),
        pin(7, "SLOPE", "input", "LM5176_SLOPE"), pin(8, "SS", "input", "LM5176_SS"), pin(9, "COMP", "output", "LM5176_COMP"),
        pin(10, "AGND", "power_in", "GND"), pin(11, "FB", "input", "VEH_FB"), pin(12, "VOSNS", "input", "VEH_24V"),
        pin(13, "ISNS-", "input", "VEH_24V", "R"), pin(14, "ISNS+", "input", "VEH_24V", "R"),
        pin(15, "CSG", "input", "LM5176_CSG", "R"), pin(16, "CS", "input", "LM5176_CS", "R"),
        pin(17, "PGOOD", "open_collector", "VEH_PGOOD", "R"), pin(18, "SW2", "passive", "SW2", "R"),
        pin(19, "HDRV2", "output", "HDRV2", "R"), pin(20, "BOOT2", "passive", "BOOT2", "R"),
        pin(21, "LDRV2", "output", "LDRV2", "R"), pin(22, "PGND", "power_in", "GND", "R"),
        pin(23, "VCC", "power_out", "LM5176_VCC", "R"), pin(24, "BIAS", "power_in", "VEH_24V", "R"),
        pin(25, "LDRV1", "output", "LDRV1", "R"), pin(26, "BOOT1", "passive", "BOOT1", "R"),
        pin(27, "HDRV1", "output", "HDRV1", "R"), pin(28, "SW1", "passive", "SW1", "R"),
        pin(29, "EP", "power_in", "GND", "R"),
    ]
    p = [ic("U301", "LM5176QPWPRQ1", "Phase2:Texas_PWP0029_HTSSOP-28-EP", "https://www.ti.com/lit/ds/symlink/lm5176-q1.pdf", lm5176_pins, 90, 85,
            description="300 kHz four-switch buck-boost controller, 24 V/30 W"),
         mosfet("Q301", "SW1", "HDRV1", "VEH_PROT", 155, 35), mosfet("Q302", "BUCK_SHUNT_HI", "LDRV1", "SW1", 155, 60),
         mosfet("Q303", "SW2", "HDRV2", "VEH_24V", 155, 85), mosfet("Q304", "GND", "LDRV2", "SW2", 155, 110),
         passive("L301", "15uH", "Inductor_SMD:L_Coilcraft_XAL7070-XXX", "SW1", "SW2", 215, 35, mpn="XAL7070-153MEC", manufacturer="Coilcraft", description="Shielded AEC-Q200 buck-boost inductor; 10.1 A saturation rating"),
         passive("R301", "20mR 1% 2W", "Resistor_SMD:R_2512_6332Metric", "BUCK_SHUNT_HI", "GND", 215, 60, description="Current-limit shunt, 6 A nominal boost peak limit"),
         passive("R302", "100R", "Resistor_SMD:R_0402_1005Metric", "BUCK_SHUNT_HI", "LM5176_CS", 215, 85),
         passive("R309", "100R", "Resistor_SMD:R_0402_1005Metric", "GND", "LM5176_CSG", 215, 110),
         passive("C301", "47pF C0G", "Capacitor_SMD:C_0402_1005Metric", "LM5176_CS", "LM5176_CSG", 490, 55),
         passive("R303", "27.4k 1%", "Resistor_SMD:R_0603_1608Metric", "LM5176_RT", "GND", 270, 35),
         passive("R304", "93.1k 1%", "Resistor_SMD:R_0603_1608Metric", "LM5176_MODE", "GND", 270, 55),
         passive("C302", "270pF C0G", "Capacitor_SMD:C_0603_1608Metric", "LM5176_SLOPE", "GND", 270, 75),
         passive("C303", "100nF", "Capacitor_SMD:C_0603_1608Metric", "LM5176_SS", "GND", 270, 95),
         passive("R305", "15.0k 1%", "Resistor_SMD:R_0603_1608Metric", "LM5176_COMP", "COMP_RC", 270, 115),
         passive("C304", "82nF X7R", "Capacitor_SMD:C_0603_1608Metric", "COMP_RC", "GND", 325, 35),
         passive("C305", "270pF C0G", "Capacitor_SMD:C_0603_1608Metric", "LM5176_COMP", "GND", 325, 55),
         passive("R306", "580k 1%", "Resistor_SMD:R_0603_1608Metric", "VEH_24V", "VEH_FB", 325, 75),
         passive("R307", "20.0k 1%", "Resistor_SMD:R_0603_1608Metric", "VEH_FB", "GND", 325, 95),
         passive("C306", "1uF 16V", "Capacitor_SMD:C_0603_1608Metric", "LM5176_VCC", "GND", 325, 115),
         passive("C307", "100nF", "Capacitor_SMD:C_0603_1608Metric", "BOOT1", "SW1", 380, 35),
         passive("C308", "100nF", "Capacitor_SMD:C_0603_1608Metric", "BOOT2", "SW2", 380, 55),
         diode("D301", "BAT46W-E3-08", "Diode_SMD:D_SOD-123", "BOOT1", "LM5176_VCC", 490, 75,
               mpn="BAT46W-E3-08", manufacturer="Vishay", description="100 V Schottky bootstrap diode for buck-side high gate"),
         diode("D302", "BAT46W-E3-08", "Diode_SMD:D_SOD-123", "BOOT2", "LM5176_VCC", 490, 95,
               mpn="BAT46W-E3-08", manufacturer="Vishay", description="100 V Schottky bootstrap diode for boost-side high gate"),
         passive("C309", "220uF 35V", "Capacitor_SMD:CP_Elec_10x12.5", "VEH_PROT", "GND", 380, 75),
         passive("C310", "22uF 50V", "Capacitor_SMD:C_1210_3225Metric", "VEH_PROT", "GND", 380, 95),
         passive("C311", "220uF 35V", "Capacitor_SMD:CP_Elec_10x12.5", "VEH_24V", "GND", 380, 115),
         passive("C312", "22uF 50V", "Capacitor_SMD:C_1210_3225Metric", "VEH_24V", "GND", 435, 35),
         passive("C313", "22uF 50V", "Capacitor_SMD:C_1210_3225Metric", "VEH_24V", "GND", 435, 55),
         passive("R308", "47k", "Resistor_SMD:R_0603_1608Metric", "VEH_PGOOD", "SYS_5V_3A", 435, 75),
         tp("TP301", "VEH_24V", 435, 95), tp("TP302", "VEH_PGOOD", 435, 115),
         pwr_flag("PWR301", "VEH_24V", 490, 35)]
    s.append(Sheet("03_vehicle_buckboost.kicad_sch", "LM5176 Vehicle Buck-Boost", 4, p, [
        "Target: 24.0 V, 30 W continuous, 300 kHz. RFB 580k/20k gives 24.0 V nominal.",
        "At 8 V/30 W/85%, Iavg=4.41 A. With 15 uH, ripple is about 1.19 App and peak about 5.00 A.",
        "20 mΩ shunt gives about 6 A boost peak limit. 15 uH replaces the provisional 6.8 uH PRD anchor.",
        "D301/D302 are the external Schottky charge paths required from VCC to the BOOT1/BOOT2 capacitors.",
        "Compensation start point: 15k/82nF (129 Hz zero) with 270pF HF pole; verify Bode/transient margin on prototype.",
    ]))

    # 04 - independent source ideal diodes.
    p = [lm74700("U401", "BENCH_FUSED_24V", "BENCH_OR_24V", "BENCH_ID", 65, 45),
         mosfet("Q401", "BENCH_FUSED_24V", "BENCH_ID_GATE", "BENCH_OR_24V", 120, 45),
         passive("C401", "100nF 25V", "Capacitor_SMD:C_0603_1608Metric", "BENCH_ID_VCAP", "BENCH_FUSED_24V", 175, 45),
         passive("C405", "22nF 100V", "Capacitor_SMD:C_0603_1608Metric", "BENCH_FUSED_24V", "GND", 175, 65),
         passive("C407", "100nF 50V", "Capacitor_SMD:C_0603_1608Metric", "BENCH_OR_24V", "GND", 175, 25),
         lm74700("U402", "VEH_24V", "VEH_OR_24V", "VEH_ID", 65, 85),
         mosfet("Q402", "VEH_24V", "VEH_ID_GATE", "VEH_OR_24V", 120, 85),
         passive("C402", "100nF 25V", "Capacitor_SMD:C_0603_1608Metric", "VEH_ID_VCAP", "VEH_24V", 175, 85),
         passive("C406", "22nF 100V", "Capacitor_SMD:C_0603_1608Metric", "VEH_24V", "GND", 175, 105),
         passive("C408", "100nF 50V", "Capacitor_SMD:C_0603_1608Metric", "VEH_OR_24V", "GND", 175, 125),
         passive("R401", "0R", "Resistor_SMD:R_2512_6332Metric", "BENCH_OR_24V", "VIN_PROT_24V", 230, 45, description="Branch current-measure link"),
         passive("R402", "0R", "Resistor_SMD:R_2512_6332Metric", "VEH_OR_24V", "VIN_PROT_24V", 230, 85, description="Branch current-measure link"),
         passive("C403", "220uF 50V", "Capacitor_SMD:CP_Elec_10x12.5", "VIN_PROT_24V", "GND", 285, 45),
         passive("C404", "10uF 50V", "Capacitor_SMD:C_1210_3225Metric", "VIN_PROT_24V", "GND", 285, 85),
         tp("TP401", "VIN_PROT_24V", 340, 45), tp("TP402", "BENCH_OR_24V", 340, 65), tp("TP403", "VEH_OR_24V", 340, 85),
         pwr_flag("PWR401", "VIN_PROT_24V", 390, 45)]
    s.append(Sheet("04_source_oring.kicad_sch", "Source ORing", 5, p, [
        "Each branch has independent LM74700 reverse-current blocking; simultaneous sources are legal.",
        "No active current sharing is claimed. The source with the higher delivered voltage supplies the common bus.",
    ]))

    # 05 - LM76003 and TPS25947 Nano feed.
    p = [ic("U501", "LM76003RNPR", "Package_DFN_QFN:Texas_RNP0030B_WQFN-30-1EP_4x6mm_P0.5mm_EP1.8x4.5mm_ThermalVias", "https://www.ti.com/lit/ds/symlink/lm76003.pdf", [
            pin(1, "SW", "power_out", "LM760_SW"), pin(2, "SW", "passive", "LM760_SW"), pin(3, "SW", "passive", "LM760_SW"),
            pin(4, "SW", "passive", "LM760_SW"), pin(5, "SW", "passive", "LM760_SW"), pin(6, "BOOT", "passive", "LM760_BOOT"),
            pin(7, "NC_GND", "passive", "GND"), pin(8, "VCC", "power_out", "LM760_VCC"),
            pin(9, "BIAS", "power_in", "SYS_5V_3A"), pin(10, "RT", "input", None), pin(11, "SS/TRK", "input", "LM760_SS"),
            pin(12, "FB", "input", "LM760_FB"), pin(13, "AGND", "power_in", "GND"), pin(14, "AGND", "passive", "GND"),
            pin(15, "AGND", "passive", "GND"), pin(16, "PGOOD", "open_collector", "SYS5_PGOOD", "R"),
            pin(17, "SYNC/MODE", "input", "GND", "R"), pin(18, "EN", "input", "LM760_EN", "R"), pin(19, "NC_GND", "passive", "GND", "R"),
            pin(20, "PVIN", "power_in", "VIN_PROT_24V", "R"), pin(21, "PVIN", "passive", "VIN_PROT_24V", "R"),
            pin(22, "PVIN", "passive", "VIN_PROT_24V", "R"), pin(23, "NC_GND", "passive", "GND", "R"),
            pin(24, "PGND", "power_in", "GND", "R"), pin(25, "PGND", "passive", "GND", "R"), pin(26, "PGND", "passive", "GND", "R"),
            pin(27, "NC_GND", "passive", "GND", "R"), pin(28, "NC_GND", "passive", "GND", "R"),
            pin(29, "NC_GND", "passive", "GND", "R"), pin(30, "NC_GND", "passive", "GND", "R"), pin(31, "EP", "power_in", "GND", "R")], 75, 70,
            description="500 kHz 5 V/3 A synchronous buck"),
         passive("L501", "10uH", "Inductor_SMD:L_Coilcraft_XAL7070-XXX", "LM760_SW", "SYS_5V_3A", 140, 35, mpn="XAL7070-103MEC", manufacturer="Coilcraft", description="Isat >=5.5 A shielded inductor"),
         passive("C501", "470nF", "Capacitor_SMD:C_0603_1608Metric", "LM760_BOOT", "LM760_SW", 140, 55),
         passive("C502", "2.2uF 10V", "Capacitor_SMD:C_0603_1608Metric", "LM760_VCC", "GND", 140, 75),
         passive("C503", "1uF 10V", "Capacitor_SMD:C_0603_1608Metric", "SYS_5V_3A", "GND", 140, 95),
         passive("C504", "22nF", "Capacitor_SMD:C_0603_1608Metric", "LM760_SS", "GND", 195, 35),
         passive("R501", "100k 0.1%", "Resistor_SMD:R_0603_1608Metric", "SYS_5V_3A", "LM760_FB", 195, 55),
         passive("R502", "24.9k 0.1%", "Resistor_SMD:R_0603_1608Metric", "LM760_FB", "GND", 195, 75),
         passive("R503", "1.00M 1%", "Resistor_SMD:R_0603_1608Metric", "VIN_PROT_24V", "LM760_EN", 195, 95),
         passive("R504", "68.1k 1%", "Resistor_SMD:R_0603_1608Metric", "LM760_EN", "GND", 250, 35),
         passive("C505", "4.7uF 100V", "Capacitor_SMD:C_1210_3225Metric", "VIN_PROT_24V", "GND", 250, 55),
         passive("C506", "4.7uF 100V", "Capacitor_SMD:C_1210_3225Metric", "VIN_PROT_24V", "GND", 250, 75),
         passive("C507", "47nF 100V", "Capacitor_SMD:C_0603_1608Metric", "VIN_PROT_24V", "GND", 250, 95),
         passive("C508", "22uF 10V", "Capacitor_SMD:C_1210_3225Metric", "SYS_5V_3A", "GND", 305, 35),
         passive("C509", "22uF 10V", "Capacitor_SMD:C_1210_3225Metric", "SYS_5V_3A", "GND", 305, 55),
         passive("C510", "22uF 10V", "Capacitor_SMD:C_1210_3225Metric", "SYS_5V_3A", "GND", 305, 75),
         passive("C511", "22uF 10V", "Capacitor_SMD:C_1210_3225Metric", "SYS_5V_3A", "GND", 305, 95),
         ic("U502", "TPS259470ARPWR", "Phase2:Texas_RPW0010A_HotRod_QFN-10_2x2mm_P0.45mm", "https://www.ti.com/lit/ds/symlink/tps25947.pdf", [
             pin(1, "EN/UVLO", "input", "EFUSE_EN"), pin(2, "OVLO", "input", "EFUSE_OV"), pin(3, "AUXOFF", "no_connect", None),
             pin(4, "FLT", "open_collector", "NANO_EFUSE_FLT"), pin(5, "IN", "power_in", "SYS_5V_3A"),
             pin(6, "OUT", "power_out", "NANO_5V_EFUSED", "R"), pin(7, "DVDT", "output", "EFUSE_DVDT", "R"),
             pin(8, "GND", "power_in", "GND", "R"), pin(9, "ILM", "output", "EFUSE_ILM", "R"), pin(10, "ITIMER", "no_connect", None, "R")], 365, 70,
             description="True reverse-current blocking Nano feed eFuse"),
         passive("R505", "549R 1%", "Resistor_SMD:R_0603_1608Metric", "EFUSE_ILM", "GND", 430, 35, description="DNP 6.07 A laboratory option only", dnp=True),
         passive("R506", "1.05k 1%", "Resistor_SMD:R_0603_1608Metric", "EFUSE_ILM", "GND", 430, 55, description="Populated current limit resistor: about 3.18 A"),
         passive("C512", "10nF", "Capacitor_SMD:C_0603_1608Metric", "EFUSE_DVDT", "GND", 430, 75, description="About 5 ms 5 V output rise"),
         passive("C513", "1uF 10V", "Capacitor_SMD:C_0603_1608Metric", "SYS_5V_3A", "GND", 430, 115, description="Local TPS25947 input bypass"),
         passive("C514", "1uF 10V", "Capacitor_SMD:C_0603_1608Metric", "NANO_5V_EFUSED", "GND", 485, 135, description="Local TPS25947 controlled output capacitance"),
         passive("R507", "100k", "Resistor_SMD:R_0603_1608Metric", "SYS_5V_3A", "EFUSE_OV", 430, 95),
         passive("R508", "26.7k", "Resistor_SMD:R_0603_1608Metric", "EFUSE_OV", "GND", 485, 35),
         passive("J501", "SERVICE LINK 5V", "Jumper:SolderJumper-2_P1.3mm_Bridged_RoundedPad1.0x1.5mm", "NANO_5V_EFUSED", "NANO_5V", 485, 55, description="Normally closed service/current-measure disconnect"),
         passive("R509", "47k", "Resistor_SMD:R_0603_1608Metric", "NANO_EFUSE_FLT", "SYS_5V_3A", 485, 75),
         passive("R510", "47k", "Resistor_SMD:R_0603_1608Metric", "SYS5_PGOOD", "SYS_5V_3A", 485, 95),
         passive("R511", "100k", "Resistor_SMD:R_0603_1608Metric", "SYS_5V_3A", "EFUSE_EN", 540, 35),
         passive("R512", "100k", "Resistor_SMD:R_0603_1608Metric", "EFUSE_EN", "GND", 540, 55),
         tp("TP501", "SYS_5V_3A", 570, 75), tp("TP502", "NANO_5V", 570, 95), tp("TP503", "SYS5_PGOOD", 570, 115),
         tp("TP504", "NANO_EFUSE_FLT", 520, 115), pwr_flag("PWR501", "SYS_5V_3A", 520, 135)]
    s.append(Sheet("05_system_5v.kicad_sch", "System 5 V and Nano Feed", 6, p, [
        "LM76003: 500 kHz, 10 uH; ripple about 0.81 App at 26.4 V/3 A. 4x22 uF output bank.",
        "100k/24.9k feedback gives 5.016 V nominal. 22 nF SS gives approximately 11 ms ramp.",
        "Populate R506 (1.05k) and DNP R505 to set ~3.18 A. R505 is retained only as a documented 6 A lab option.",
        "R511/R512 hold EN near 2.5 V, inside the recommended pin range; OVLO 100k/26.7k trips near 5.69 V.",
        "TPS259470A blocks Nano/USB-derived 5 V from SYS_5V_3A. Opposite-direction Nano USB path still requires prototype test.",
    ]))

    # 06 - hold-up, rails, sequencer and reset wired-AND.
    p = [diode("D601", "SS34-E3/57T", "Diode_SMD:D_SMA", "HOLD_CHARGE", "SYS_5V_3A", 45, 35,
               mpn="SS34-E3/57T", manufacturer="Vishay", description="Hold-up reverse isolation"),
         passive("R601", "3.3R 2W PULSE", "Resistor_SMD:R_2512_6332Metric", "HOLD_CHARGE", "DISP_HOLD_5V", 45, 55, description="Hold-up capacitor inrush limiter, about 1.4 A initial"),
         passive("C601", "6800uF 10V", "Phase2:CP_Elec_6800uF_10V", "DISP_HOLD_5V", "GND", 45, 75, description="Display-only hard-unplug hold-up; body size frozen before PCB placement"),
         ic("U601", "TPS3808G01DBVR", "Package_TO_SOT_SMD:SOT-23-6", "https://www.ti.com/lit/ds/symlink/tps3808.pdf", [
             pin(1, "RESET_N", "open_collector", "VIN_GOOD"), pin(2, "GND", "power_in", "GND"), pin(3, "MR_N", "input", "DISP_HOLD_5V"),
             pin(4, "CT", "input", "TPS3808_CT", "R"), pin(5, "SENSE", "input", "BUS_SENSE", "R"), pin(6, "VDD", "power_in", "DISP_HOLD_5V", "R")], 100, 55,
             description="Early common-bus failure supervisor"),
         passive("R602", "1.00M 1%", "Resistor_SMD:R_0603_1608Metric", "VIN_PROT_24V", "BUS_SENSE", 155, 35),
         passive("R603", "21.5k 1%", "Resistor_SMD:R_0603_1608Metric", "BUS_SENSE", "GND", 155, 55),
         passive("C602", "100pF C0G", "Capacitor_SMD:C_0603_1608Metric", "TPS3808_CT", "GND", 155, 75),
         passive("R604", "47k", "Resistor_SMD:R_0603_1608Metric", "VIN_GOOD", "DISP_HOLD_5V", 155, 95),
         ic("U602", "LM3880MF-1AA/NOPB", "Package_TO_SOT_SMD:SOT-23-6", "https://www.ti.com/lit/ds/symlink/lm3880.pdf", [
             pin(1, "VCC", "power_in", "DISP_HOLD_5V"), pin(2, "GND", "power_in", "GND"), pin(3, "EN", "input", "SEQ_ENABLE"),
             pin(4, "FLAG3", "open_collector", "SEQ_FLAG3", "R"), pin(5, "FLAG2", "open_collector", "SEQ_FLAG2", "R"), pin(6, "FLAG1", "open_collector", "SEQ_FLAG1", "R")], 215, 55,
             description="10 ms 1-2-3 / 3-2-1 rail sequencer"),
         passive("R605", "10k", "Resistor_SMD:R_0603_1608Metric", "LCD_PWR_EN", "SEQ_ENABLE", 270, 35),
         passive("R606", "47k", "Resistor_SMD:R_0603_1608Metric", "SEQ_ENABLE", "GND", 270, 55),
         diode("D602", "1N4148W", "Diode_SMD:D_SOD-123", "VIN_GOOD", "SEQ_ENABLE", 270, 75, description="VIN_GOOD clamps sequencer enable low on bus failure"),
         passive("R607", "47k", "Resistor_SMD:R_0603_1608Metric", "SEQ_FLAG1", "DISP_HOLD_5V", 270, 95),
         passive("R608", "47k", "Resistor_SMD:R_0603_1608Metric", "SEQ_FLAG2", "DISP_HOLD_5V", 325, 35),
         passive("R609", "47k", "Resistor_SMD:R_0603_1608Metric", "SEQ_FLAG3", "DISP_HOLD_5V", 325, 55),
         tlv755("U603", "TLV75518PDBVR", "LCD_IOVCC", "SEQ_FLAG1", 325, 80),
         tlv755("U604", "TLV75528PDBVR", "LCD_VCI_RAW", "SEQ_FLAG1", 385, 40),
         ic("U605", "TPS22919DCKR", "Package_TO_SOT_SMD:SOT-363_SC-70-6", "https://www.ti.com/lit/ds/symlink/tps22919.pdf", [
             pin(1, "VIN", "power_in", "LCD_VCI_RAW"), pin(2, "GND", "power_in", "GND"), pin(3, "ON", "input", "SEQ_FLAG2"),
             pin(4, "NC", "no_connect", None, "R"), pin(5, "QOD", "passive", "LCD_VCI", "R"),
             pin(6, "VOUT", "power_out", "LCD_VCI", "R")], 385, 80,
             description="VCI sequenced load switch with quick output discharge"),
         passive("C603", "1uF 10V", "Capacitor_SMD:C_0603_1608Metric", "DISP_HOLD_5V", "GND", 445, 35),
         passive("C604", "2.2uF 6.3V", "Capacitor_SMD:C_0603_1608Metric", "LCD_IOVCC", "GND", 445, 55),
         passive("C605", "2.2uF 6.3V", "Capacitor_SMD:C_0603_1608Metric", "LCD_VCI_RAW", "GND", 445, 75),
         passive("C606", "4.7uF 6.3V", "Capacitor_SMD:C_0603_1608Metric", "LCD_VCI", "GND", 445, 95),
         lvc1g07("U606", "LCD_RESET_CMD_N", "LCD_RESET_N", "LCD_IOVCC", 505, 35),
         lvc1g07("U607", "SEQ_FLAG3", "LCD_RESET_N", "LCD_IOVCC", 505, 65),
         lvc1g07("U608", "VIN_GOOD", "LCD_RESET_N", "LCD_IOVCC", 505, 95),
         passive("R610", "10k", "Resistor_SMD:R_0603_1608Metric", "LCD_IOVCC", "LCD_RESET_N", 565, 35),
         passive("R611", "100k", "Resistor_SMD:R_0603_1608Metric", "LCD_RESET_N", "GND", 565, 55),
         tp("TP601", "VIN_GOOD", 500, 120), tp("TP602", "SEQ_FLAG1", 535, 120), tp("TP603", "SEQ_FLAG2", 570, 120),
         tp("TP604", "SEQ_FLAG3", 500, 145), tp("TP605", "LCD_IOVCC", 535, 145), tp("TP606", "LCD_VCI", 570, 145),
         tp("TP607", "LCD_RESET_N", 500, 170), pwr_flag("PWR601", "DISP_HOLD_5V", 570, 170)]
    s.append(Sheet("06_display_power_sequence.kicad_sch", "Display Rails and Sequencing", 7, p, [
        "6800 uF is isolated from Nano/backlight. At 0.20 A for 30 ms, droop is 0.88 V; sequencing remains above LDO dropout.",
        "TPS3808 threshold: 0.405*(1M+21.5k)/21.5k = 19.23 V nominal. Its reset directly clamps sequence/reset/backlight validity.",
        "LM3880-1AA gives 10 ms between IOVCC, VCI, READY and reverse 10 ms shutdown intervals.",
        "Three open-drain buffers form a wired-AND reset: firmware command, FLAG3 readiness, and VIN_GOOD must all be high.",
    ]))

    # 07 - MIPI and panel connector.
    nano_nets = ["DSI_D1_N_SRC", "DSI_D1_P_SRC", "GND", "DSI_CLK_N_SRC", "DSI_CLK_P_SRC", "GND", "DSI_D0_N_SRC", "DSI_D0_P_SRC", "GND", None,
                 "NANO_I2C_SCL", "NANO_I2C_SDA", "GND", "NANO_3V3_REF", "NANO_3V3_REF"]
    nano_names = ["DSI_D1_N", "DSI_D1_P", "GND", "DSI_CLK_N", "DSI_CLK_P", "GND", "DSI_D0_N", "DSI_D0_P", "GND", "NC_VERIFY",
                  "GPIO8_I2C_SCL", "GPIO7_I2C_SDA", "GND", "ESP_3V3_REF", "ESP_3V3_REF"]
    panel_nets = [None, "LCD_VCI", "LCD_IOVCC", "GND", "LCD_RESET_N", None, "GND", "MIPI_0N", "MIPI_0P", "GND", "MIPI_1N", "MIPI_1P", "GND", "MIPI_CLKN", "MIPI_CLKP"]
    panel_nets += ["GND"] * 7 + [None, None, "GND"] + [None] * 4 + ["GND", "LED_K", "LED_K"] + [None] * 6 + ["LED_A", "LED_A"]
    panel_names = ["NC", "VCI_2V8", "IOVCC_1V8", "GND", "RESET_N", "NC", "GND", "MIPI_0N", "MIPI_0P", "GND", "MIPI_1N", "MIPI_1P", "GND", "MIPI_CLKN", "MIPI_CLKP"]
    panel_names += ["GND"] * 7 + ["NC", "NC", "GND"] + ["NC"] * 4 + ["GND", "LED-", "LED-"] + ["NC"] * 6 + ["LED+", "LED+"]
    p = [connector("J701", "NANO DSI 15P", "Phase2:Amphenol_SFW15R-2STE1LF", nano_nets, 50, 75,
                  mpn="SFW15R-2STE1LF", manufacturer="Amphenol ICC", names=nano_names, description="Nano-facing top-contact provisional connector"),
         connector("J702", "DISPLAYMAN LCD 40P", "Phase2:Molex_505110-4096", panel_nets, 310, 80,
                  mpn="505110-4096", manufacturer="Molex", names=panel_names, description="Exact Displayman-specified bottom-contact panel connector"),
         passive("R701", "0R 0201", "Resistor_SMD:R_0201_0603Metric", "DSI_D0_N_SRC", "MIPI_0N", 125, 30),
         passive("R702", "0R 0201", "Resistor_SMD:R_0201_0603Metric", "DSI_D0_P_SRC", "MIPI_0P", 125, 50),
         passive("R703", "0R 0201", "Resistor_SMD:R_0201_0603Metric", "DSI_D1_N_SRC", "MIPI_1N", 125, 70),
         passive("R704", "0R 0201", "Resistor_SMD:R_0201_0603Metric", "DSI_D1_P_SRC", "MIPI_1P", 125, 90),
         passive("R705", "0R 0201", "Resistor_SMD:R_0201_0603Metric", "DSI_CLK_N_SRC", "MIPI_CLKN", 125, 110),
         passive("R706", "0R 0201", "Resistor_SMD:R_0201_0603Metric", "DSI_CLK_P_SRC", "MIPI_CLKP", 125, 130),
         ic("U701", "TPD6E05U06RVZR", "Phase2:Texas_RVZ0014A_USON-14", "https://www.ti.com/lit/ds/symlink/tpd6e05u06.pdf", [
             pin(1, "NC", "no_connect", None), pin(2, "NC", "no_connect", None), pin(3, "NC", "no_connect", None), pin(4, "NC", "no_connect", None),
             pin(5, "GND", "power_in", "GND"), pin(6, "NC", "no_connect", None), pin(7, "NC", "no_connect", None),
             pin(8, "D3-", "bidirectional", "MIPI_CLKP", "R"), pin(9, "D3+", "bidirectional", "MIPI_CLKN", "R"), pin(10, "GND", "power_in", "GND", "R"),
             pin(11, "D2-", "bidirectional", "MIPI_1P", "R"), pin(12, "D2+", "bidirectional", "MIPI_1N", "R"),
             pin(13, "D1-", "bidirectional", "MIPI_0P", "R"), pin(14, "D1+", "bidirectional", "MIPI_0N", "R")], 210, 80,
             description="0.5 pF six-channel panel-side MIPI ESD clamp")]
    s.append(Sheet("07_mipi_panel.kicad_sch", "MIPI DSI and LCD Connector", 8, p, [
        "Straight-through lane identity and polarity. No AC coupling, common-mode choke, probe pad, or branch.",
        "R701–R706 are inline zero-ohm 0201 tuning locations; layout them as minimal-discontinuity pass-through pads.",
        "Route all three pairs at 100 ohm differential, 50 ohm single-ended, continuous reference, <=0.15 mm intra-pair skew.",
        "No schematic parameter depends on the final D-PHY HS rate; the passive channel target remains >=1.5 Gb/s/lane.",
    ]))

    # 08 - touch rail and powered-off isolation.
    p = [tlv755("U801", "TLV75533PDBVR", "TOUCH_3V3", "VIN_GOOD", 50, 55),
         passive("C801", "1uF 10V", "Capacitor_SMD:C_0603_1608Metric", "SYS_5V_3A", "GND", 100, 35),
         passive("C802", "4.7uF 6.3V", "Capacitor_SMD:C_0603_1608Metric", "TOUCH_3V3", "GND", 100, 55),
         Part("Q801", "MMBT3904", "Package_TO_SOT_SMD:SOT-23", "", [pin(1, "B", "input", "NANO_3V3_DETECT"), pin(2, "E", "passive", "GND"), pin(3, "C", "open_collector", "TMUX_EN_N", "R")], 100, 80,
              "MMBT3904LT1G", "onsemi", "Nano-powered detector: isolation enabled only when Nano 3.3 V exists"),
         passive("R801", "100k", "Resistor_SMD:R_0603_1608Metric", "NANO_3V3_REF", "NANO_3V3_DETECT", 155, 35),
         passive("R802", "100k", "Resistor_SMD:R_0603_1608Metric", "TMUX_EN_N", "TOUCH_3V3", 155, 55),
         ic("U802", "TMUX1574PWR", "Package_SO:TSSOP-16_4.4x5mm_P0.65mm", "https://www.ti.com/lit/ds/symlink/tmux1574.pdf", [
             pin(1, "SEL", "input", "GND"), pin(2, "S1A", "bidirectional", "CTP_SCL"),
             pin(3, "S1B", "passive", "GND"), pin(4, "D1", "bidirectional", "NANO_I2C_SCL"),
             pin(5, "S2A", "bidirectional", "CTP_SDA"), pin(6, "S2B", "passive", "GND"),
             pin(7, "D2", "bidirectional", "NANO_I2C_SDA"), pin(8, "GND", "power_in", "GND"),
             pin(9, "D3", "bidirectional", "CTP_INT_NANO", "R"), pin(10, "S3B", "passive", "GND", "R"),
             pin(11, "S3A", "bidirectional", "CTP_INT", "R"), pin(12, "D4", "bidirectional", "CTP_RESET_N_NANO", "R"),
             pin(13, "S4B", "passive", "GND", "R"), pin(14, "S4A", "bidirectional", "CTP_RESET_N", "R"),
             pin(15, "EN_N", "input", "TMUX_EN_N", "R"), pin(16, "VDD", "power_in", "TOUCH_3V3", "R")], 215, 70,
             description="Four-channel powered-off-protected touch-domain isolation switch"),
         passive("C803", "100nF", "Capacitor_SMD:C_0603_1608Metric", "TOUCH_3V3", "GND", 275, 35),
         passive("R803", "4.7k", "Resistor_SMD:R_0603_1608Metric", "CTP_INT", "TOUCH_3V3", 275, 55),
         passive("R804", "100k", "Resistor_SMD:R_0603_1608Metric", "CTP_RESET_N", "GND", 275, 75),
         ic("U803", "TPD4E05U06DQAR", "Package_SON:USON-10_2.5x1.0mm_P0.5mm", "https://www.ti.com/lit/ds/symlink/tpd6e05u06.pdf", [
             pin(1, "D1+", "bidirectional", "CTP_SCL"), pin(2, "D1-", "bidirectional", "CTP_SDA"), pin(3, "GND", "power_in", "GND"),
             pin(4, "D2+", "bidirectional", "CTP_INT"), pin(5, "D2-", "bidirectional", "CTP_RESET_N"),
             pin(6, "NC", "no_connect", None, "R"), pin(7, "NC", "no_connect", None, "R"), pin(8, "GND", "power_in", "GND", "R"),
             pin(9, "NC", "no_connect", None, "R"), pin(10, "NC", "no_connect", None, "R")], 335, 70,
             description="Four-channel touch connector ESD clamp"),
         connector("J801", "GT9271 TOUCH 8P", "Connector_FFC-FPC:Hirose_FH12-8S-0.5SH_1x08-1MP_P0.50mm_Horizontal",
                   ["GND", None, "TOUCH_3V3", "CTP_SCL", "CTP_SDA", "CTP_INT", "CTP_RESET_N", "GND"], 405, 70,
                   mpn="FH12-8S-0.5SH(55)", manufacturer="Hirose", names=["GND", "NC", "VDD_3V3", "SCL", "SDA", "INT", "RST_N", "GND"], description="Bottom-contact touch FPC connector"),
         tp("TP801", "TOUCH_3V3", 465, 35), tp("TP802", "CTP_SCL", 465, 55), tp("TP803", "CTP_SDA", 465, 75),
         tp("TP804", "CTP_INT", 465, 95), tp("TP805", "CTP_RESET_N", 520, 35)]
    s.append(Sheet("08_touch.kicad_sch", "GT9271 Touch Interface", 9, p, [
        "TMUX1574 SEL=0 uses the A paths; all B paths are grounded per datasheet. EN_N is pulled high when Nano 3.3 V is absent.",
        "Nano I2C already has 2.2k pull-ups; no additional Nano-side pull-ups. Touch INT has the vendor-required 4.7k pull-up.",
        "Panel reset has a 100k pull-down, so an unpowered/isolated Nano cannot release the GT9271 from reset.",
    ]))

    # 09 - TPS922053 backlight.
    p = [ic("U901", "TPS922053DYYR", "Phase2:Texas_DYY0014A_TSOT-23-14", "https://www.ti.com/lit/ds/symlink/tps922053.pdf", [
            pin(1, "PGND", "power_in", "GND"), pin(2, "AGND", "power_in", "GND"), pin(3, "VIN", "power_in", "VIN_PROT_24V"),
            pin(4, "VCC", "power_out", "TPS922_VCC"), pin(5, "ADIM/HD", "input", "TPS922_VCC"), pin(6, "EN/PWM", "input", "BL_DIM"),
            pin(7, "FAULT_N", "open_collector", "BL_FAULT_N"), pin(8, "TEMP", "input", "GND", "R"), pin(9, "FSET", "input", "TPS922_FSET", "R"),
            pin(10, "COMP", "output", "TPS922_COMP", "R"), pin(11, "UVP", "input", "TPS922_UVP", "R"), pin(12, "CSP", "input", "TPS922_CSP", "R"),
            pin(13, "CSN", "input", "LED_SENSE_N", "R"), pin(14, "SW", "power_out", "BL_SW", "R")], 75, 70,
            description="300 kHz 240 mA buck LED driver"),
         passive("C901", "10uF 50V", "Capacitor_SMD:C_1210_3225Metric", "VIN_PROT_24V", "GND", 140, 30),
         passive("C902", "100nF 100V", "Capacitor_SMD:C_0603_1608Metric", "VIN_PROT_24V", "GND", 140, 50),
         passive("C903", "1uF 10V", "Capacitor_SMD:C_0603_1608Metric", "TPS922_VCC", "GND", 140, 70),
         diode("D901", "SS2H10-E3/52T", "Diode_SMD:D_SMA", "VIN_PROT_24V", "BL_SW", 140, 90, mpn="SS2H10-E3/52T", manufacturer="Vishay", description="100 V 2 A Schottky catch diode"),
         passive("L901", "68uH", "Inductor_SMD:L_Vishay_IHLP-6767", "BL_SW", "LED_SENSE_N", 140, 110,
                 mpn="IHLP6767GZER680M11", manufacturer="Vishay", description="Shielded 68 uH LED buck inductor; 6.1 A heat-rated / 4.5 A saturation typical"),
         passive("R901", "1.65R 0.1%", "Resistor_SMD:R_1206_3216Metric", "LED_K_RAW", "LED_SENSE_N", 200, 30, description="Half of 0.825 ohm LED sense network"),
         passive("R902", "1.65R 0.1%", "Resistor_SMD:R_1206_3216Metric", "LED_K_RAW", "LED_SENSE_N", 200, 50, description="Half of 0.825 ohm LED sense network"),
         passive("R903", "100R", "Resistor_SMD:R_0603_1608Metric", "LED_K_RAW", "TPS922_CSP", 200, 70, description="CSP Kelvin/noise filter resistor"),
         passive("C904", "1nF 50V", "Capacitor_SMD:C_0603_1608Metric", "TPS922_CSP", "LED_SENSE_N", 200, 90),
         passive("C905", "2.2uF 50V", "Capacitor_SMD:C_1210_3225Metric", "LED_A", "LED_K", 200, 110, description="LED ripple capacitor across the module string"),
         passive("R904", "83k 1%", "Resistor_SMD:R_0603_1608Metric", "TPS922_FSET", "GND", 260, 30),
         passive("C906", "1nF", "Capacitor_SMD:C_0603_1608Metric", "TPS922_COMP", "GND", 260, 50),
         passive("R905", "100R", "Resistor_SMD:R_0603_1608Metric", "TPS922_COMP", "TPS922_COMP_C", 260, 70),
         passive("C907", "1nF", "Capacitor_SMD:C_0603_1608Metric", "TPS922_COMP_C", "GND", 260, 90, dnp=True, description="DNP alternate series compensation branch"),
         passive("R906", "0R", "Resistor_SMD:R_0603_1608Metric", "LED_K", "TPS922_UVP", 260, 110, description="Direct LED-cathode undervoltage/open-load sense"),
         passive("R907", "1.00M", "Resistor_SMD:R_0603_1608Metric", "TPS922_UVP", "GND", 320, 30, dnp=True, description="DNP UVP loading/tuning option"),
         passive("R908", "47k", "Resistor_SMD:R_0603_1608Metric", "BL_FAULT_N", "TPS922_VCC", 320, 50,
                 description="FAULT pull-up local to LED-driver VCC; no touch-rail phantom-power path"),
         passive("R909", "100k", "Resistor_SMD:R_0603_1608Metric", "BL_DIM", "GND", 320, 70),
         ic("U902", "SN74LVC1G11DCKR", "Package_TO_SOT_SMD:SOT-363_SC-70-6", "https://www.ti.com/lit/ds/symlink/sn74lvc1g11.pdf", [
             pin(1, "A", "input", "BL_PWM"), pin(2, "B", "input", "SEQ_FLAG3"), pin(3, "GND", "power_in", "GND"),
             pin(4, "Y", "output", "BL_GATE_OK", "R"), pin(5, "C", "input", "VIN_GOOD", "R"), pin(6, "VCC", "power_in", "TOUCH_3V3", "R")], 380, 50,
             description="Three-condition hardware backlight enable gate"),
         passive("J901", "BL HARD DISABLE", "Connector_PinHeader_2.54mm:PinHeader_1x02_P2.54mm_Vertical", "BL_GATE_OK", "BL_DIM", 380, 85, description="Normally fitted hardware backlight disable shunt"),
         passive("R910", "0R LED CURRENT LINK", "Resistor_SMD:R_2512_6332Metric", "LED_K", "LED_K_RAW", 380, 110, description="Populated removable link for controlled current measurement"),
         tp("TP901", "BL_PWM", 440, 30), tp("TP902", "BL_DIM", 440, 50), tp("TP903", "LED_A", 440, 70), tp("TP904", "LED_K", 440, 90), tp("TP905", "BL_FAULT_N", 440, 110),
         passive("FB901", "600R@100MHz 1A", "Inductor_SMD:L_0603_1608Metric", "VIN_PROT_24V", "LED_A", 500, 50,
                 mpn="BLM18KG601SN1D", manufacturer="Murata", description="Panel LED anode EMI bead; verify DC loss/headroom"),
         passive("C908", "10uF 50V", "Capacitor_SMD:C_1210_3225Metric", "LED_A", "GND", 500, 80)]
    s.append(Sheet("09_backlight.kicad_sch", "240 mA Backlight", 10, p, [
        "83k FSET selects 300 kHz. 68 uH gives about 243 mApp ripple at 26.4 V; worst-normal peak about 371 mA.",
        "Two 1.65 ohm/0.1% resistors in parallel give 0.825 ohm: 242.4 mA nominal; +3% threshold gives 249.9 mA.",
        "At 21.6 V, 97% duty limit leaves about 20.95 V before diode/switch loss versus 19.8 V LED + 0.20 V sense.",
        "U902 requires BL_PWM, sequencer READY, and VIN_GOOD. J901 removal forces BL_DIM low through R909.",
    ]))

    # 10 - Nano headers, GPIO assignments, indicators and test access.
    p1_nets = [None, "NANO_5V", None, "NANO_5V", None, "GND", "BL_PWM", None, "GND", None, None, None, "LCD_PWR_EN", "GND", "LCD_RESET_CMD_N", "CTP_RESET_N_NANO", None, None, None, "GND", None, None, "CTP_INT_NANO", None, "GND", None]
    p1_names = ["3V3", "5V", "GPIO7_I2C_SDA", "5V", "GPIO8_I2C_SCL", "GND", "GPIO23_BL_PWM", "GPIO37_UART0_TX_STRAP", "GND", "GPIO38_UART0_RX_STRAP", "GPIO5_JTAG", "GPIO4_JTAG", "GPIO20_LCD_PWR_EN", "GND", "GPIO21_LCD_RESET", "GPIO22_CTP_RESET", "3V3", "GPIO24_USB1P1_N0", "GPIO25_USB1P1_P0", "GND", "GPIO26_USB1P1_N1", "GPIO27_USB1P1_P1", "GPIO32_CTP_INT", "GPIO33", "GND", "GPIO36_STRAP"]
    p2_names = ["5V", "ESP_LDO_VO4", "GND", "GND", "3V3", "GPIO0_XTAL32K_N", "GND", "GPIO1_XTAL32K_P", "GPIO3_JTAG_TOUCH1", "GND", "GPIO2_JTAG_TOUCH0", "GPIO6_TOUCH4", "GPIO54_ADC2_CH7", "GPIO53_ADC2_CH6", "GPIO47", "GPIO48", "GPIO46", "GND", "GPIO45", "C6_U0RXD", "C6_IO12", "C6_U0TXD", "C6_IO13", "C6_IO9", "GND", "GND"]
    p = [connector("J1001", "NANO P1 2x13", "Connector_PinSocket_2.54mm:PinSocket_2x13_P2.54mm_Vertical", p1_nets, 65, 80,
                   mpn="SSW-113-02-G-D", manufacturer="Samtec", names=p1_names, description="Waveshare Nano P1 header; complete host pin functions shown"),
         connector("J1002", "NANO P2 2x13", "Connector_PinSocket_2.54mm:PinSocket_2x13_P2.54mm_Vertical", [None]*26, 190, 80,
                   mpn="SSW-113-02-G-D", manufacturer="Samtec", names=p2_names, description="Waveshare Nano P2 header; electrically unused by daughterboard"),
         passive("R1001", "100k", "Resistor_SMD:R_0603_1608Metric", "LCD_PWR_EN", "GND", 300, 35),
         passive("R1002", "100k", "Resistor_SMD:R_0603_1608Metric", "LCD_RESET_CMD_N", "GND", 300, 55),
         passive("R1003", "100k", "Resistor_SMD:R_0603_1608Metric", "BL_PWM", "GND", 300, 75),
         passive("R1004", "100k", "Resistor_SMD:R_0603_1608Metric", "CTP_RESET_N_NANO", "GND", 300, 95),
         passive("R1005", "47k", "Resistor_SMD:R_0603_1608Metric", "CTP_INT_NANO", "GND", 300, 115, dnp=True, description="DNP weak default; firmware drives address strap"),
         diode("D1001", "GREEN", "LED_SMD:LED_0603_1608Metric", "LED24_R", "VIN_PROT_24V", 365, 35,
               mpn="LTST-C191KGKT", manufacturer="Lite-On"),
         passive("R1006", "10k", "Resistor_SMD:R_0603_1608Metric", "LED24_R", "GND", 365, 55),
         diode("D1002", "GREEN", "LED_SMD:LED_0603_1608Metric", "LED5_R", "SYS_5V_3A", 365, 75,
               mpn="LTST-C191KGKT", manufacturer="Lite-On"),
         passive("R1007", "2.2k", "Resistor_SMD:R_0603_1608Metric", "LED5_R", "GND", 365, 95),
         connector("J1003", "DEBUG HEADER", "Connector_PinHeader_2.54mm:PinHeader_2x05_P2.54mm_Vertical", ["GND", "SYS_5V_3A", "VIN_GOOD", "SEQ_FLAG1", "SEQ_FLAG2", "SEQ_FLAG3", "LCD_RESET_N", "BL_FAULT_N", "NANO_EFUSE_FLT", "VEH_PGOOD"], 435, 75,
                   mpn="TSW-105-07-G-D", manufacturer="Samtec", names=["GND", "5V", "VIN_GOOD", "SEQ1", "SEQ2", "SEQ3", "LCD_RST", "BL_FAULT", "5V_FAULT", "VEH_PGOOD"], description="Low-speed development/debug access"),
         tp("TP1001", "LCD_PWR_EN", 505, 35), tp("TP1002", "LCD_RESET_CMD_N", 505, 55), tp("TP1003", "BL_PWM", 505, 75),
         tp("TP1004", "CTP_RESET_N_NANO", 505, 95), tp("TP1005", "CTP_INT_NANO", 505, 115), tp("TP1006", "GND", 560, 35)]
    s.append(Sheet("10_headers_debug.kicad_sch", "Nano Headers and Debug", 11, p, [
        "Corrected P1 controls: pin 7 GPIO23 BL PWM; 13 GPIO20 LCD power; 15 GPIO21 LCD reset; 16 GPIO22 touch reset; 23 GPIO32 touch INT.",
        "P1 pins 2/4 are Nano 5 V; all five controls are non-strapping P1 GPIOs. P2 is electrically unused.",
        "Unconnected Nano pins retain their actual host function names. Confirm physical header orientation before PCB placement freeze.",
    ]))
    return s


def lib_symbol(part: Part) -> tuple[str, dict[str, tuple[float, float, str]], str]:
    lib = f"Phase2:{part.ref}_{part.value}".replace(" ", "_").replace("/", "_")
    left = [p for p in part.pins if p.side == "L"]
    right = [p for p in part.pins if p.side == "R"]
    rows = max(len(left), len(right), 2)
    half_h = max(5.08, (rows + 1) * 1.27)
    half_w = 10.16
    pos: dict[str, tuple[float, float, str]] = {}
    subbase = lib.split(":", 1)[1]
    in_bom = "no" if part.virtual else "yes"
    on_board = "no" if part.virtual else "yes"
    out = [f"    (symbol {q(lib)} (pin_names (offset 0.8)) (in_bom {in_bom}) (on_board {on_board})",
           f"      (property \"Reference\" {q(part.ref.rstrip('0123456789') or part.ref)} (at 0 {half_h + 2.0:.2f} 0) (effects (font (size 1.27 1.27))))",
           f"      (property \"Value\" {q(part.value)} (at 0 {-half_h - 2.0:.2f} 0) (effects (font (size 1.0 1.0))))",
           f"      (property \"Footprint\" {q(part.footprint)} (at 0 0 0) (effects (font (size 1.0 1.0)) hide))",
           f"      (property \"Datasheet\" {q(part.datasheet)} (at 0 0 0) (effects (font (size 1.0 1.0)) hide))",
           f"      (property \"Description\" {q(part.description)} (at 0 0 0) (effects (font (size 1.0 1.0)) hide))",
           f"      (symbol {q(subbase + '_0_1')} (rectangle (start {-half_w} {half_h}) (end {half_w} {-half_h}) (stroke (width 0.25) (type default)) (fill (type background))))",
           f"      (symbol {q(subbase + '_1_1')}" ]
    for side, pins in (("L", left), ("R", right)):
        for i, p in enumerate(pins):
            yy = (len(pins) - 1) * 1.27 - i * 2.54
            xx = -12.70 if side == "L" else 12.70
            ang = 0 if side == "L" else 180
            pos[p.number] = (xx, yy, side)
            out.append(f"        (pin {p.etype} line (at {xx:.2f} {yy:.2f} {ang}) (length 2.54) (name {q(p.name)} (effects (font (size 0.8 0.8)))) (number {q(p.number)} (effects (font (size 0.8 0.8)))))")
    out += ["      )", "    )"]
    return lib, pos, "\n".join(out)


def render_sheet(sheet: Sheet, root_uuid: str, sheet_uuid: str) -> str:
    sch_uuid = uid()
    libdefs = []
    libids = {}
    pinposes = {}
    for part in sheet.parts:
        lib, pos, txt = lib_symbol(part)
        libids[part.ref] = lib
        pinposes[part.ref] = pos
        libdefs.append(txt)

    blocks = [f"(kicad_sch (version 20230121) (generator eeschema)", f"  (uuid {sch_uuid})", '  (paper "A2")',
              f"  (title_block (title {q(sheet.title)}) (date \"2026-09-16\") (rev \"Phase 2 / v0.1\") (company \"ESP32-P4 Displayman Development Daughterboard\"))",
              "  (lib_symbols", *libdefs, "  )"]

    for i, note in enumerate(sheet.notes):
        blocks.append(f"  (text {q(note)} (at 20 {15 + i*5} 0) (effects (font (size 1.27 1.27)) (justify left bottom)) (uuid {uid()}))")

    for part in sheet.parts:
        px = round(part.x / 1.27) * 1.27
        py = round(part.y / 1.27) * 1.27
        puid = uid()
        blocks += [f"  (symbol (lib_id {q(libids[part.ref])}) (at {px:.2f} {py:.2f} 0) (unit 1) (in_bom {'no' if part.virtual else 'yes'}) (on_board {'no' if part.virtual else 'yes'}) (dnp {'yes' if part.dnp else 'no'})",
                   f"    (uuid {puid})",
                   f"    (property \"Reference\" {q(part.ref)} (at {px:.2f} {py-14:.2f} 0) (effects (font (size 1.27 1.27))))",
                   f"    (property \"Value\" {q(part.value)} (at {px:.2f} {py+14:.2f} 0) (effects (font (size 1.0 1.0))))",
                   f"    (property \"Footprint\" {q(part.footprint)} (at {px:.2f} {py:.2f} 0) (effects (font (size 1.0 1.0)) hide))",
                   f"    (property \"Datasheet\" {q(part.datasheet)} (at {px:.2f} {py:.2f} 0) (effects (font (size 1.0 1.0)) hide))",
                   f"    (property \"Description\" {q(part.description)} (at {px:.2f} {py:.2f} 0) (effects (font (size 1.0 1.0)) hide))",
                   f"    (property \"Manufacturer\" {q(part.manufacturer)} (at {px:.2f} {py:.2f} 0) (effects (font (size 1.0 1.0)) hide))",
                   f"    (property \"MPN\" {q(part.mpn)} (at {px:.2f} {py:.2f} 0) (effects (font (size 1.0 1.0)) hide))"]
        for pn in pinposes[part.ref]:
            blocks.append(f"    (pin {q(pn)} (uuid {uid()}))")
        blocks += ["    (instances", f"      (project {q(PROJECT)}", f"        (path \"/{root_uuid}/{sheet_uuid}\" (reference {q(part.ref)}) (unit 1))", "      )", "    )", "  )"]

        for pp in part.pins:
            dx, dy, side = pinposes[part.ref][pp.number]
            ax, ay = px + dx, py - dy
            if pp.net is None and pp.etype != "no_connect":
                blocks.append(f"  (no_connect (at {ax:.2f} {ay:.2f}) (uuid {uid()}))")
            elif pp.net is not None:
                angle = 180 if side == "L" else 0
                justify = "right" if side == "L" else "left"
                blocks.append(f"  (global_label {q(pp.net)} (shape bidirectional) (at {ax:.2f} {ay:.2f} {angle}) (effects (font (size 0.8 0.8)) (justify {justify})) (uuid {uid()}) (property \"Intersheetrefs\" \"${{INTERSHEET_REFS}}\" (at 0 0 0) (effects (font (size 1.0 1.0)) hide)))")

    blocks += ["  (sheet_instances (path \"/\" (page \"1\")))", ")", ""]
    return "\n".join(blocks)


def write_root(sheets: list[Sheet]):
    root_uuid = uid()
    sheet_ids = {sh.filename: uid() for sh in sheets}
    out = ["(kicad_sch (version 20230121) (generator eeschema)", f"  (uuid {root_uuid})", '  (paper "A3")',
           '  (title_block (title "ESP32-P4 Displayman Development Daughterboard") (date "2026-09-16") (rev "Phase 2 / v0.1") (company "sydude/ESP32-P4-Display-Development-Daughterboard"))',
           "  (lib_symbols)",
           f"  (text \"PHASE 2 SCHEMATIC — PCB layout not started. Read docs/design-notes/schematic-calculations.md and schematic-review.md before review.\" (at 20 20 0) (effects (font (size 1.8 1.8)) (justify left bottom)) (uuid {uid()}))"]
    for idx, sh in enumerate(sheets):
        col, row = idx % 3, idx // 3
        x, y = 25 + col * 125, 35 + row * 55
        sid = sheet_ids[sh.filename]
        out += [f"  (sheet (at {x} {y}) (size 105 40) (stroke (width 0) (type solid)) (fill (color 0 0 0 0.0000)) (uuid {sid})",
                f"    (property \"Sheetname\" {q(sh.title)} (at {x} {y-0.8} 0) (effects (font (size 1.27 1.27)) (justify left bottom)))",
                f"    (property \"Sheetfile\" {q(sh.filename)} (at {x} {y+40.8} 0) (effects (font (size 1.0 1.0)) (justify left top)))",
                f"    (instances (project {q(PROJECT)} (path \"/{root_uuid}\" (page {q(str(sh.page))}))))", "  )"]
        (KICAD / sh.filename).write_text(render_sheet(sh, root_uuid, sid), encoding="utf-8")
    out += ["  (sheet_instances (path \"/\" (page \"1\")))", ")", ""]
    ROOT_SCH.write_text("\n".join(out), encoding="utf-8")


def write_bom(sheets: list[Sheet]):
    bom = ROOT / "hardware" / "BOM.csv"
    bom.parent.mkdir(parents=True, exist_ok=True)
    rows = []
    for sh in sheets:
        for p in sh.parts:
            if p.virtual:
                continue
            rows.append({"Reference": p.ref, "Value": p.value, "Manufacturer": p.manufacturer, "MPN": p.mpn,
                         "Footprint": p.footprint, "DNP": "DNP" if p.dnp else "POP", "Sheet": sh.title,
                         "Description": p.description})
    with bom.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader(); w.writerows(rows)


def write_symbol_library(sheets: list[Sheet]):
    symbols = []
    for sh in sheets:
        for part in sh.parts:
            lib, _, txt = lib_symbol(part)
            local_name = lib.split(":", 1)[1]
            symbols.append(txt.replace(f"(symbol {q(lib)}", f"(symbol {q(local_name)}", 1).replace("    ", "  ", 1))
    content = ["(kicad_symbol_lib (version 20220914) (generator kicad_symbol_editor)", *symbols, ")", ""]
    (KICAD / "Phase2.kicad_sym").write_text("\n".join(content), encoding="utf-8")
    (KICAD / "sym-lib-table").write_text('(sym_lib_table\n  (lib (name "Phase2")(type "KiCad")(uri "${KIPRJMOD}/Phase2.kicad_sym")(options "")(descr "Generated Phase 2 schematic symbols"))\n)\n', encoding="utf-8")
    footprint_libraries = sorted({p.footprint.split(":", 1)[0] for sh in sheets for p in sh.parts if ":" in p.footprint})
    fp_rows = ["(fp_lib_table"]
    for library in footprint_libraries:
        uri = "${KIPRJMOD}/Phase2.pretty" if library == "Phase2" else f"${{KICAD9_FOOTPRINT_DIR}}/{library}.pretty"
        fp_rows.append(f'  (lib (name {q(library)})(type "KiCad")(uri {q(uri)})(options "")(descr ""))')
    fp_rows.extend([")", ""])
    (KICAD / "fp-lib-table").write_text("\n".join(fp_rows), encoding="utf-8")


def validate_design_model(sheets: list[Sheet]):
    refs: set[str] = set()
    parts = {p.ref: p for sh in sheets for p in sh.parts}
    for part in parts.values():
        if part.ref in refs:
            raise ValueError(f"Duplicate reference: {part.ref}")
        refs.add(part.ref)
        numbers = [p.number for p in part.pins]
        if len(numbers) != len(set(numbers)):
            raise ValueError(f"Duplicate pin number on {part.ref}: {numbers}")
        if any("," in number or "-" in number for number in numbers):
            raise ValueError(f"Grouped physical pad on {part.ref}: {numbers}")
        if not part.virtual and not part.footprint:
            raise ValueError(f"Missing footprint on {part.ref}")
    required_maps = {
        "U201": range(1, 14), "U301": range(1, 30), "U501": range(1, 32), "U502": range(1, 11),
        "U605": range(1, 7), "U701": range(1, 15), "U802": range(1, 17), "U901": range(1, 15),
        "J701": range(1, 16), "J702": range(1, 41), "J801": range(1, 9),
        "J1001": range(1, 27), "J1002": range(1, 27),
    }
    for ref, expected in required_maps.items():
        actual = {int(p.number) for p in parts[ref].pins}
        if actual != set(expected):
            raise ValueError(f"Physical pin map mismatch on {ref}: {sorted(actual)}")
    expected_external_nets = {
        "J101": ["BENCH_24V_RAW", "GND", None],
        "J201": ["VEH_12V_RAW", "GND"],
        "J701": ["DSI_D1_N_SRC", "DSI_D1_P_SRC", "GND", "DSI_CLK_N_SRC", "DSI_CLK_P_SRC", "GND",
                 "DSI_D0_N_SRC", "DSI_D0_P_SRC", "GND", None, "NANO_I2C_SCL", "NANO_I2C_SDA", "GND",
                 "NANO_3V3_REF", "NANO_3V3_REF"],
        "J801": ["GND", None, "TOUCH_3V3", "CTP_SCL", "CTP_SDA", "CTP_INT", "CTP_RESET_N", "GND"],
        "J1001": [None, "NANO_5V", None, "NANO_5V", "BL_PWM", None, None, None, "CTP_RESET_N_NANO",
                  "LCD_RESET_CMD_N", "LCD_PWR_EN", None, None, "CTP_INT_NANO", None, None, None, None,
                  None, None, None, None, None, None, "GND", "GND"],
        "J1002": [None] * 24 + ["GND", "GND"],
        "J1003": ["GND", "SYS_5V_3A", "VIN_GOOD", "SEQ_FLAG1", "SEQ_FLAG2", "SEQ_FLAG3",
                  "LCD_RESET_N", "BL_FAULT_N", "NANO_EFUSE_FLT", "VEH_PGOOD"],
    }
    expected_external_nets["J702"] = [None, "LCD_VCI", "LCD_IOVCC", "GND", "LCD_RESET_N", None, "GND",
                                       "MIPI_0N", "MIPI_0P", "GND", "MIPI_1N", "MIPI_1P", "GND", "MIPI_CLKN",
                                       "MIPI_CLKP"] + ["GND"] * 7 + [None, None, "GND"] + [None] * 4 + ["GND",
                                       "LED_K", "LED_K"] + [None] * 6 + ["LED_A", "LED_A"]
    for ref, expected_nets in expected_external_nets.items():
        actual_nets = [p.net for p in sorted(parts[ref].pins, key=lambda item: int(item.number))]
        if actual_nets != expected_nets:
            raise ValueError(f"External connector net-map mismatch on {ref}")
    expected_ic_pins = {
        "U201": {1: ("DGATE", "VEH_DGATE"), 2: ("A", "VEH_FILTER"), 9: ("OUT", "VEH_PROT"),
                 10: ("VS", "VEH_FET_MID"), 12: ("C", "VEH_FET_MID"), 13: ("RTN_EP", None)},
        "U502": {1: ("EN/UVLO", "EFUSE_EN"), 5: ("IN", "SYS_5V_3A"), 6: ("OUT", "NANO_5V_EFUSED"),
                 10: ("ITIMER", None)},
        "U605": {1: ("VIN", "LCD_VCI_RAW"), 4: ("NC", None), 5: ("QOD", "LCD_VCI"),
                 6: ("VOUT", "LCD_VCI")},
        "U802": {1: ("SEL", "GND"), 2: ("S1A", "CTP_SCL"), 4: ("D1", "NANO_I2C_SCL"),
                 8: ("GND", "GND"), 12: ("D4", "CTP_RESET_N_NANO"), 14: ("S4A", "CTP_RESET_N"),
                 15: ("EN_N", "TMUX_EN_N"), 16: ("VDD", "TOUCH_3V3")},
        "U901": {1: ("PGND", "GND"), 3: ("VIN", "VIN_PROT_24V"), 6: ("EN/PWM", "BL_DIM"),
                 11: ("UVP", "TPS922_UVP"), 12: ("CSP", "TPS922_CSP"), 13: ("CSN", "LED_SENSE_N"),
                 14: ("SW", "BL_SW")},
    }
    for ref, expected in expected_ic_pins.items():
        actual = {int(p.number): (p.name, p.net) for p in parts[ref].pins}
        for number, name_net in expected.items():
            if actual[number] != name_net:
                raise ValueError(f"Critical pin mismatch on {ref}.{number}: {actual[number]} != {name_net}")


def main():
    sheets = build_sheets()
    validate_design_model(sheets)
    write_root(sheets)
    write_symbol_library(sheets)
    write_bom(sheets)
    print(f"Generated {len(sheets)} sheets, {sum(len(s.parts) for s in sheets)} symbols, and hardware/BOM.csv")


if __name__ == "__main__":
    main()
