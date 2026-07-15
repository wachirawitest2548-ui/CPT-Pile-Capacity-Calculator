"""
Raw CPT/SCPT interpreter for PTTEP CPT Calculator.

Purpose
-------
Read Fugro GeoVisual / Wison .asc CPT files and generate:
1) raw CPT CSV: depth, qc, fs, u2
2) continuous raw profile plots like a CPT/GeoVisual viewer
3) WPA-01 Fugro-style calculator layers using fixed report/APICAP layer boundaries

Important
---------
This module does NOT infer final geotechnical design parameters from CPT alone.
For WPA-01 it uses the design layer boundaries and engineering parameters already
adopted in the project calculator/report, while using the raw ASC only as the
source profile for qc averaging/visualisation.
"""

from __future__ import annotations

import csv
import math
import os
import re
from pathlib import Path
from statistics import median
from typing import Dict, Iterable, List, Optional, Tuple

import matplotlib.pyplot as plt

Record = Dict[str, Optional[float]]
Layer = Dict[str, object]

# WPA-01 design model used in the verified calculator input.
# Format follows calculator CSV:
# from_depth,to_depth,soil_type,behavior,gamma_top,gamma_bot,cu_top,cu_bot,qc_f,qc_eb,delta_cv,k0,flim,qlim
WPA01_FUGRO_LAYERS: List[Layer] = [
    {"from_depth": 0.0, "to_depth": 3.0, "soil_type": "clay", "behavior": "cohesive", "gamma_top": 16.4, "gamma_bot": 16.4, "cu_top": 1.0, "cu_bot": 9.0},
    {"from_depth": 3.0, "to_depth": 7.9, "soil_type": "clay", "behavior": "cohesive", "gamma_top": 16.4, "gamma_bot": 16.4, "cu_top": 9.0, "cu_bot": 14.0},
    {"from_depth": 7.9, "to_depth": 10.8, "soil_type": "clay", "behavior": "cohesive", "gamma_top": 18.2, "gamma_bot": 18.2, "cu_top": 16.0, "cu_bot": 16.0},
    {"from_depth": 10.8, "to_depth": 14.0, "soil_type": "clay", "behavior": "cohesive", "gamma_top": 18.4, "gamma_bot": 18.4, "cu_top": 22.0, "cu_bot": 25.0},
    {"from_depth": 14.0, "to_depth": 20.9, "soil_type": "clay", "behavior": "cohesive", "gamma_top": 17.0, "gamma_bot": 17.0, "cu_top": 25.0, "cu_bot": 40.0},
    {"from_depth": 20.9, "to_depth": 27.4, "soil_type": "clay", "behavior": "cohesive", "gamma_top": 17.7, "gamma_bot": 17.7, "cu_top": 42.0, "cu_bot": 50.0},
    {"from_depth": 27.4, "to_depth": 32.5, "soil_type": "clay", "behavior": "cohesive", "gamma_top": 17.4, "gamma_bot": 17.4, "cu_top": 55.0, "cu_bot": 65.0},
    {"from_depth": 32.5, "to_depth": 36.8, "soil_type": "clay", "behavior": "cohesive", "gamma_top": 17.4, "gamma_bot": 17.4, "cu_top": 65.0, "cu_bot": 65.0},
    {"from_depth": 36.8, "to_depth": 47.0, "soil_type": "clay", "behavior": "cohesive", "gamma_top": 18.0, "gamma_bot": 18.0, "cu_top": 65.0, "cu_bot": 80.0},
    {"from_depth": 47.0, "to_depth": 50.0, "soil_type": "clay", "behavior": "cohesive", "gamma_top": 18.0, "gamma_bot": 18.0, "cu_top": 85.0, "cu_bot": 85.0},
    {"from_depth": 50.0, "to_depth": 51.6, "soil_type": "sand", "behavior": "frictional", "gamma_top": 18.3, "gamma_bot": 18.3, "qc_f_default": 8.0, "qc_eb_default": 9.0, "delta_cv": 28.8, "k0": 1.0},
    {"from_depth": 51.6, "to_depth": 57.7, "soil_type": "sand", "behavior": "frictional", "gamma_top": 19.2, "gamma_bot": 19.2, "qc_f_default": 27.0, "qc_eb_default": 18.0, "delta_cv": 26.1, "k0": 1.0},
    {"from_depth": 57.7, "to_depth": 61.0, "soil_type": "sand", "behavior": "frictional", "gamma_top": 19.2, "gamma_bot": 19.2, "qc_f_default": 26.0, "qc_eb_default": 26.0, "delta_cv": 26.1, "k0": 1.0},
    {"from_depth": 61.0, "to_depth": 64.0, "soil_type": "sand", "behavior": "frictional", "gamma_top": 18.7, "gamma_bot": 18.7, "qc_f_default": 10.5, "qc_eb_default": 10.5, "delta_cv": 28.8, "k0": 1.0},
    {"from_depth": 64.0, "to_depth": 66.7, "soil_type": "sand", "behavior": "frictional", "gamma_top": 18.7, "gamma_bot": 18.7, "qc_f_default": 17.0, "qc_eb_default": 17.0, "delta_cv": 28.8, "k0": 1.0},
    {"from_depth": 66.7, "to_depth": 68.5, "soil_type": "sand", "behavior": "frictional", "gamma_top": 20.0, "gamma_bot": 20.0, "qc_f_default": 26.0, "qc_eb_default": 40.0, "delta_cv": 26.1, "k0": 1.0},
    {"from_depth": 68.5, "to_depth": 71.0, "soil_type": "sand", "behavior": "frictional", "gamma_top": 20.0, "gamma_bot": 20.0, "qc_f_default": 40.0, "qc_eb_default": 33.0, "delta_cv": 26.1, "k0": 1.0},
    {"from_depth": 71.0, "to_depth": 74.0, "soil_type": "sand", "behavior": "frictional", "gamma_top": 20.0, "gamma_bot": 20.0, "qc_f_default": 24.0, "qc_eb_default": 24.0, "delta_cv": 26.1, "k0": 1.0},
    {"from_depth": 74.0, "to_depth": 77.3, "soil_type": "sand", "behavior": "frictional", "gamma_top": 20.0, "gamma_bot": 20.0, "qc_f_default": 31.5, "qc_eb_default": 31.5, "delta_cv": 26.1, "k0": 1.0},
    {"from_depth": 77.3, "to_depth": 83.0, "soil_type": "sand", "behavior": "frictional", "gamma_top": 19.2, "gamma_bot": 19.2, "qc_f_default": 23.0, "qc_eb_default": 25.0, "delta_cv": 26.1, "k0": 1.0},
    {"from_depth": 83.0, "to_depth": 95.2, "soil_type": "sand", "behavior": "frictional", "gamma_top": 20.1, "gamma_bot": 20.1, "qc_f_default": 30.0, "qc_eb_default": 30.0, "delta_cv": 26.1, "k0": 1.0},
    {"from_depth": 95.2, "to_depth": 102.6, "soil_type": "sand", "behavior": "frictional", "gamma_top": 18.7, "gamma_bot": 18.7, "qc_f_default": 16.0, "qc_eb_default": 16.0, "delta_cv": 28.8, "k0": 1.0},
    {"from_depth": 102.6, "to_depth": 106.8, "soil_type": "clay", "behavior": "cohesive", "gamma_top": 18.9, "gamma_bot": 18.9, "cu_top": 180.0, "cu_bot": 205.0},
    {"from_depth": 106.8, "to_depth": 108.8, "soil_type": "sand", "behavior": "frictional", "gamma_top": 20.0, "gamma_bot": 20.0, "qc_f_default": 20.0, "qc_eb_default": 20.0, "delta_cv": 28.8, "k0": 1.0},
    {"from_depth": 108.8, "to_depth": 110.8, "soil_type": "clay", "behavior": "cohesive", "gamma_top": 20.0, "gamma_bot": 20.0, "cu_top": 160.0, "cu_bot": 160.0},
    {"from_depth": 110.8, "to_depth": 112.0, "soil_type": "sand", "behavior": "frictional", "gamma_top": 18.1, "gamma_bot": 18.1, "qc_f_default": 18.0, "qc_eb_default": 18.0, "delta_cv": 28.8, "k0": 1.0},
    {"from_depth": 112.0, "to_depth": 113.7, "soil_type": "sand/clay", "behavior": "frictional", "gamma_top": 18.1, "gamma_bot": 18.1, "qc_f_default": 12.0, "qc_eb_default": 12.0, "delta_cv": 28.8, "k0": 1.0, "qlim": 2.2},
    {"from_depth": 113.7, "to_depth": 114.8, "soil_type": "clay", "behavior": "cohesive", "gamma_top": 19.1, "gamma_bot": 19.1, "cu_top": 230.0, "cu_bot": 230.0},
    {"from_depth": 114.8, "to_depth": 115.9, "soil_type": "sand", "behavior": "frictional", "gamma_top": 20.0, "gamma_bot": 20.0, "qc_f_default": 33.0, "qc_eb_default": 33.0, "delta_cv": 28.8, "k0": 1.0},
    {"from_depth": 115.9, "to_depth": 116.9, "soil_type": "sand/clay", "behavior": "frictional", "gamma_top": 19.3, "gamma_bot": 19.3, "qc_f_default": 8.0, "qc_eb_default": 8.0, "delta_cv": 28.8, "k0": 1.0, "qlim": 2.1},
    {"from_depth": 116.9, "to_depth": 118.8, "soil_type": "sand", "behavior": "frictional", "gamma_top": 19.1, "gamma_bot": 19.1, "qc_f_default": 17.0, "qc_eb_default": 17.0, "delta_cv": 28.8, "k0": 1.0},
    {"from_depth": 118.8, "to_depth": 123.5, "soil_type": "silt", "behavior": "frictional", "gamma_top": 19.1, "gamma_bot": 19.1, "qc_f_default": 11.0, "qc_eb_default": 11.0, "delta_cv": 28.8, "k0": 1.0},
    {"from_depth": 123.5, "to_depth": 125.5, "soil_type": "sand", "behavior": "frictional", "gamma_top": 19.1, "gamma_bot": 19.1, "qc_f_default": 14.5, "qc_eb_default": 14.5, "delta_cv": 28.8, "k0": 1.0},
    {"from_depth": 125.5, "to_depth": 129.6, "soil_type": "silt/clay", "behavior": "frictional", "gamma_top": 19.8, "gamma_bot": 19.8, "qc_f_default": 8.0, "qc_eb_default": 8.0, "delta_cv": 28.8, "k0": 1.0, "qlim": 2.0},
    {"from_depth": 129.6, "to_depth": 140.0, "soil_type": "clay", "behavior": "cohesive", "gamma_top": 19.5, "gamma_bot": 19.5, "cu_top": 250.0, "cu_bot": 250.0},
    {"from_depth": 140.0, "to_depth": 141.7, "soil_type": "sand", "behavior": "frictional", "gamma_top": 19.5, "gamma_bot": 19.5, "qc_f_default": 4.7, "qc_eb_default": 4.7, "delta_cv": 28.8, "k0": 1.0},
    {"from_depth": 141.7, "to_depth": 150.0, "soil_type": "clay", "behavior": "cohesive", "gamma_top": 18.5, "gamma_bot": 18.5, "cu_top": 275.0, "cu_bot": 350.0},
    {"from_depth": 150.0, "to_depth": 152.0, "soil_type": "silt", "behavior": "frictional", "gamma_top": 20.0, "gamma_bot": 20.0, "qc_f_default": 24.0, "qc_eb_default": 24.0, "delta_cv": 28.8, "k0": 1.0},
    {"from_depth": 152.0, "to_depth": 157.5, "soil_type": "clay", "behavior": "cohesive", "gamma_top": 18.5, "gamma_bot": 18.5, "cu_top": 350.0, "cu_bot": 350.0},
]


def _to_float(text: str) -> Optional[float]:
    text = str(text).strip().replace(",", "")
    if text in {"", "-", "--", "NA", "N/A", "nan", "NaN"}:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def parse_geovisual_asc(file_path: str | os.PathLike[str]) -> List[Record]:
    """Parse Fugro GeoVisual/Wison ASC text and return records."""
    path = Path(file_path)
    text = path.read_text(errors="ignore")
    lines = text.splitlines()

    records: List[Record] = []
    data_started = False
    header_found = False

    for line in lines:
        raw = line.strip()
        if not raw:
            continue

        # Detect a header line containing Depth/Cone/Friction/Pore.
        low = raw.lower()
        if "depth" in low and ("cone" in low or "qc" in low):
            header_found = True
            data_started = True
            continue

        # Many GeoVisual tables have one or two unit lines after header. Skip non-numeric starts.
        parts = re.split(r"\s+|,|;|\t", raw)
        parts = [p for p in parts if p != ""]
        if len(parts) < 4:
            continue

        nums = [_to_float(p) for p in parts[:8]]
        numeric_count = sum(v is not None for v in nums)
        if numeric_count < 3:
            continue

        # Expected common format:
        # Rec Depth Time Cone Friction Pore2 ...
        # But sometimes no Rec column. Use heuristics.
        rec = nums[0]
        depth = nums[1] if len(nums) > 1 else None
        qc = nums[3] if len(nums) > 3 else None
        fs = nums[4] if len(nums) > 4 else None
        u2 = nums[5] if len(nums) > 5 else None

        if depth is None or depth < 0 or depth > 1000:
            # Try no-rec format: Depth Time Cone Friction Pore2
            depth = nums[0]
            qc = nums[2] if len(nums) > 2 else None
            fs = nums[3] if len(nums) > 3 else None
            u2 = nums[4] if len(nums) > 4 else None

        if depth is None or qc is None:
            continue
        if depth < 0 or depth > 1000:
            continue
        if qc < -10 or qc > 1000:
            continue

        records.append({"depth": depth, "qc": qc, "fs": fs, "u2": u2})

    # Remove duplicate depths while preserving order; sort for plotting.
    cleaned: Dict[float, Record] = {}
    for r in records:
        d = round(float(r["depth"]), 4)
        cleaned[d] = r
    out = list(cleaned.values())
    out.sort(key=lambda r: float(r["depth"]))

    if not out:
        raise ValueError("No CPT data rows found in ASC file. Expected columns like Depth, Cone, Friction and Pore 2.")
    return out


def write_raw_csv(records: Iterable[Record], output_path: str | os.PathLike[str]) -> str:
    path = Path(output_path)
    with path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(["depth_m", "qc_mpa", "fs_mpa", "u2_mpa"])
        for r in records:
            writer.writerow([r.get("depth"), r.get("qc"), r.get("fs"), r.get("u2")])
    return str(path)


def _values_in_interval(records: List[Record], key: str, z1: float, z2: float, trim_margin: float = 0.05) -> List[float]:
    lo = z1 + trim_margin
    hi = z2 - trim_margin
    if hi <= lo:
        lo, hi = z1, z2
    vals = []
    for r in records:
        d = r.get("depth")
        v = r.get(key)
        if d is None or v is None:
            continue
        if lo <= float(d) <= hi and math.isfinite(float(v)):
            vals.append(float(v))
    return vals


def _robust_median(vals: List[float], fallback: Optional[float] = None) -> Optional[float]:
    if not vals:
        return fallback
    vals = sorted(vals)
    # Trim extreme 5% spikes if enough data are available.
    if len(vals) >= 40:
        n = len(vals)
        vals = vals[int(0.05 * n): int(0.95 * n)] or vals
    return float(median(vals))


def build_wpa01_fugro_layers_from_raw(records: List[Record], use_raw_qc: bool = True) -> List[Layer]:
    """Build calculator input layers using WPA-01 Fugro-style boundaries."""
    layers: List[Layer] = []
    for base in WPA01_FUGRO_LAYERS:
        layer = dict(base)
        if layer["behavior"] == "frictional":
            fallback_f = float(layer.get("qc_f_default", 0.0))
            fallback_eb = float(layer.get("qc_eb_default", fallback_f))
            if use_raw_qc:
                vals = _values_in_interval(records, "qc", float(layer["from_depth"]), float(layer["to_depth"]))
                q_med = _robust_median(vals, fallback=fallback_f)
                # Use raw median as qc_f and qc_eb only when ASC exists in interval.
                # Keep Fugro default fallback for layers below CPT final depth or bad data.
                layer["qc_f"] = round(float(q_med if q_med is not None else fallback_f), 2)
                layer["qc_eb"] = round(float(q_med if q_med is not None else fallback_eb), 2)
            else:
                layer["qc_f"] = fallback_f
                layer["qc_eb"] = fallback_eb
        layers.append(layer)
    return layers


def layer_to_calculator_line(layer: Layer) -> str:
    def fmt(v: object, nd: int = 3) -> str:
        if v is None:
            return ""
        if isinstance(v, str):
            return v
        try:
            val = float(v)
        except Exception:
            return ""
        if abs(val - round(val)) < 1e-9:
            return str(int(round(val)))
        return f"{val:.{nd}f}".rstrip("0").rstrip(".")

    if layer["behavior"] == "cohesive":
        fields = [
            fmt(layer.get("from_depth")), fmt(layer.get("to_depth")), layer.get("soil_type", ""), "cohesive",
            fmt(layer.get("gamma_top")), fmt(layer.get("gamma_bot")),
            fmt(layer.get("cu_top")), fmt(layer.get("cu_bot")),
            "", "", "", "", "", "",
        ]
    else:
        fields = [
            fmt(layer.get("from_depth")), fmt(layer.get("to_depth")), layer.get("soil_type", ""), "frictional",
            fmt(layer.get("gamma_top")), fmt(layer.get("gamma_bot")),
            "", "",
            fmt(layer.get("qc_f"), 2), fmt(layer.get("qc_eb"), 2),
            fmt(layer.get("delta_cv"), 1), fmt(layer.get("k0"), 2),
            fmt(layer.get("flim")), fmt(layer.get("qlim"), 2),
        ]
    return ",".join(str(x) for x in fields)


def write_layers_csv(layers: Iterable[Layer], output_path: str | os.PathLike[str]) -> str:
    path = Path(output_path)
    header = ["from_depth", "to_depth", "soil_type", "behavior", "gamma_top", "gamma_bot", "cu_top", "cu_bot", "qc_f", "qc_eb", "delta_cv", "k0", "flim", "qlim"]
    with path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(header)
        for layer in layers:
            writer.writerow(layer_to_calculator_line(layer).split(","))
    return str(path)


def calculator_text_from_layers(layers: Iterable[Layer]) -> str:
    return "\n".join(layer_to_calculator_line(layer) for layer in layers)


def _draw_ground_column(ax, layers: List[Layer], max_depth: float) -> None:
    ax.set_xlim(0, 1)
    ax.set_ylim(max_depth, 0)
    ax.set_xticks([])
    ax.tick_params(left=False, labelleft=False)
    ax.grid(True, axis="y", color="black", linewidth=0.35, alpha=0.45)

    for layer in layers:
        z1 = float(layer["from_depth"])
        z2 = float(layer["to_depth"])
        if z2 <= z1:
            continue
        behavior = str(layer["behavior"])
        soil = str(layer["soil_type"]).title()
        hatch = "///" if behavior == "frictional" else ""
        code = "F" if behavior == "frictional" else "C"
        ax.fill_betweenx([z1, z2], 0.02, 0.42, facecolor="white", edgecolor="black", hatch=hatch, linewidth=0.55)
        mid = 0.5 * (z1 + z2)
        thick = z2 - z1
        ax.text(0.22, mid, code, ha="center", va="center", fontsize=5.5, fontweight="bold")
        if thick > 1.4:
            ax.text(0.72, mid, soil, ha="center", va="center", fontsize=4.8 if len(soil) < 10 else 4.2)
    ax.set_title("Ground\nBehaviour", fontsize=7)


def plot_raw_cpt_profile(records: List[Record], output_path: Optional[str | os.PathLike[str]] = None, show_layers: bool = True) -> plt.Figure:
    """Plot continuous raw qc/fs/u2 profile, not layer-average bars."""
    depths = [float(r["depth"]) for r in records if r.get("depth") is not None]
    max_depth = max(depths) if depths else 0.0
    max_depth = max(20, int(math.ceil(max_depth / 20.0) * 20))

    qc = [r.get("qc") for r in records]
    fs = [r.get("fs") for r in records]
    u2 = [r.get("u2") for r in records]
    d = [r.get("depth") for r in records]

    fig = plt.figure(figsize=(11.69, 8.27), dpi=150, facecolor="white")
    ax_qc = fig.add_axes([0.08, 0.17, 0.25, 0.68])
    ax_fs = fig.add_axes([0.37, 0.17, 0.20, 0.68], sharey=ax_qc)
    ax_u2 = fig.add_axes([0.61, 0.17, 0.18, 0.68], sharey=ax_qc)
    ax_soil = fig.add_axes([0.83, 0.17, 0.10, 0.68], sharey=ax_qc)

    ax_qc.plot(qc, d, linewidth=0.75)
    ax_fs.plot(fs, d, linewidth=0.75)
    ax_u2.plot(u2, d, linewidth=0.75)

    for ax in [ax_qc, ax_fs, ax_u2]:
        ax.set_ylim(max_depth, 0)
        ax.set_yticks(range(0, int(max_depth) + 1, 20))
        ax.grid(True, which="major", color="black", linewidth=0.35, alpha=0.45)
        ax.xaxis.tick_top()
        ax.xaxis.set_label_position("top")
        ax.tick_params(labelsize=7)

    ax_qc.set_xlabel("Cone Resistance, qc [MPa]", fontsize=7)
    ax_fs.set_xlabel("Sleeve Friction, fs [MPa]", fontsize=7)
    ax_u2.set_xlabel("Pore Pressure, u2 [MPa]", fontsize=7)
    ax_qc.set_ylabel("Depth Below Seafloor [m]", fontsize=8)
    plt.setp(ax_fs.get_yticklabels(), visible=False)
    plt.setp(ax_u2.get_yticklabels(), visible=False)

    _draw_ground_column(ax_soil, WPA01_FUGRO_LAYERS, max_depth)

    fig.text(0.50, 0.925, "RAW CPT / SCPT PROFILE FROM GEOVISUAL ASC", ha="center", fontsize=11, fontweight="bold")
    fig.text(0.50, 0.900, "Continuous raw qc, fs and u2 profiles with WPA-01 design layer column", ha="center", fontsize=7)
    fig.text(0.50, 0.080, "Raw measurements are plotted continuously. WPA-01 design layers are used only as a reference column.", ha="center", fontsize=6.5)

    if output_path:
        fig.savefig(output_path)
    return fig


def plot_wpa01_design_interpretation(records: List[Record], layers: List[Layer], output_path: Optional[str | os.PathLike[str]] = None) -> plt.Figure:
    """Plot continuous raw qc profile plus Fugro-style design layers and averaged qc step profile."""
    depths = [float(r["depth"]) for r in records if r.get("depth") is not None]
    max_depth = max(max(depths) if depths else 0.0, max(float(l["to_depth"]) for l in layers))
    max_depth = max(20, int(math.ceil(max_depth / 20.0) * 20))

    d = [r.get("depth") for r in records]
    qc = [r.get("qc") for r in records]

    fig = plt.figure(figsize=(8.27, 11.69), dpi=150, facecolor="white")
    ax_raw = fig.add_axes([0.12, 0.19, 0.36, 0.66])
    ax_step = fig.add_axes([0.51, 0.19, 0.18, 0.66], sharey=ax_raw)
    ax_soil = fig.add_axes([0.74, 0.19, 0.14, 0.66], sharey=ax_raw)

    ax_raw.plot(qc, d, color="black", linewidth=0.65)

    # Step profile from layer qc values only in frictional layers.
    sx: List[Optional[float]] = []
    sy: List[Optional[float]] = []
    for layer in layers:
        z1 = float(layer["from_depth"])
        z2 = float(layer["to_depth"])
        if layer["behavior"] != "frictional":
            sx.extend([None])
            sy.extend([None])
            continue
        q = float(layer.get("qc_f", layer.get("qc_f_default", 0.0)))
        sx.extend([q, q, None])
        sy.extend([z1, z2, None])
    ax_step.plot(sx, sy, color="black", linewidth=1.2)

    for ax in [ax_raw, ax_step]:
        ax.set_ylim(max_depth, 0)
        ax.set_yticks(range(0, int(max_depth) + 1, 20))
        ax.grid(True, which="major", color="black", linewidth=0.40, alpha=0.50)
        ax.xaxis.tick_top()
        ax.xaxis.set_label_position("top")
        ax.tick_params(labelsize=7)
        ax.set_xlim(0, max(40, int(math.ceil(max([v for v in qc if v is not None] + [40]) / 10.0) * 10)))

    ax_raw.set_xlabel("Raw qc [MPa]", fontsize=7)
    ax_step.set_xlabel("Layer qc for Calculator [MPa]", fontsize=7)
    ax_raw.set_ylabel("Depth Below Seafloor [m]", fontsize=8)
    plt.setp(ax_step.get_yticklabels(), visible=False)

    _draw_ground_column(ax_soil, layers, max_depth)

    fig.text(0.50, 0.925, "WPA-01 FUGRO-STYLE CPT INTERPRETATION", ha="center", fontsize=11, fontweight="bold")
    fig.text(0.50, 0.902, "Raw qc is shown continuously; design layers follow WPA-01 Fugro/APICAP boundaries", ha="center", fontsize=7)
    fig.text(0.50, 0.080, "Calculator CSV uses WPA-01 design layer boundaries/parameters. Raw ASC qc is used for interval median qc where available.", ha="center", fontsize=6.5)

    if output_path:
        fig.savefig(output_path)
    return fig


def convert_asc_to_raw_outputs(file_path: str | os.PathLike[str], output_dir: Optional[str | os.PathLike[str]] = None) -> Tuple[List[Record], str, str]:
    input_path = Path(file_path)
    output_dir_path = Path(output_dir) if output_dir else input_path.parent
    output_dir_path.mkdir(parents=True, exist_ok=True)
    records = parse_geovisual_asc(input_path)
    stem = input_path.stem.replace(" ", "_")
    raw_csv = output_dir_path / f"{stem}_raw.csv"
    raw_png = output_dir_path / f"{stem}_raw_profile_continuous.png"
    write_raw_csv(records, raw_csv)
    fig = plot_raw_cpt_profile(records, raw_png)
    plt.close(fig)
    return records, str(raw_csv), str(raw_png)


def interpret_asc_to_wpa01_outputs(file_path: str | os.PathLike[str], output_dir: Optional[str | os.PathLike[str]] = None) -> Tuple[List[Record], List[Layer], str, str, str]:
    input_path = Path(file_path)
    output_dir_path = Path(output_dir) if output_dir else input_path.parent
    output_dir_path.mkdir(parents=True, exist_ok=True)
    records = parse_geovisual_asc(input_path)
    layers = build_wpa01_fugro_layers_from_raw(records, use_raw_qc=True)
    stem = input_path.stem.replace(" ", "_")
    out_csv = output_dir_path / f"{stem}_wpa01_fugro_design_layers.csv"
    out_png = output_dir_path / f"{stem}_wpa01_fugro_interpretation.png"
    write_layers_csv(layers, out_csv)
    fig = plot_wpa01_design_interpretation(records, layers, out_png)
    plt.close(fig)
    return records, layers, str(out_csv), str(out_png), calculator_text_from_layers(layers)
