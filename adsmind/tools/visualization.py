"""Deterministic visualization helpers for AdsMind reports."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Iterable

import numpy as np


ELEMENT_COLORS = {
    "H": "#f7f7f7",
    "C": "#3b3b3b",
    "N": "#2f56d2",
    "O": "#e33d2e",
    "S": "#f2c744",
    "P": "#e36a1a",
    "Mo": "#6f8ca7",
    "Pd": "#c89133",
    "Pt": "#c2c8d2",
    "Cu": "#c8783e",
    "Ag": "#c9c9c9",
    "Au": "#d3a526",
    "Ru": "#6d7a8b",
    "Rh": "#7a89a6",
    "Co": "#5378b8",
    "Ni": "#5c9a73",
    "Fe": "#a56b4f",
    "Mn": "#9a78b5",
    "Cr": "#70876a",
    "V": "#80935c",
    "Ti": "#9aa0a6",
    "Zr": "#8ca7aa",
    "Hf": "#6e8f9b",
    "Ta": "#668099",
    "W": "#536a83",
    "Re": "#6a7890",
    "Al": "#b5bec8",
    "Ga": "#a7a0c0",
    "In": "#9aa9c9",
    "Tl": "#8d91a6",
    "Bi": "#9c88a8",
    "Pb": "#7c8297",
    "Sn": "#9ba3a7",
    "Sb": "#9c8794",
    "As": "#a37864",
    "Se": "#d4934b",
    "Te": "#b58a55",
    "Si": "#c3a36c",
    "Ge": "#a98869",
    "Ca": "#98ad64",
    "Sr": "#8eaa5a",
    "Y": "#78a79b",
    "Sc": "#8fa39a",
    "Na": "#7c99d6",
    "K": "#8e78c7",
    "Os": "#667b89",
}

FALLBACK_COLORS = [
    "#78909c",
    "#a1887f",
    "#90a4ae",
    "#8d6e63",
    "#7986cb",
    "#4db6ac",
    "#9575cd",
]

ELEMENT_RADII = {
    "H": 0.22,
    "C": 0.34,
    "N": 0.34,
    "O": 0.34,
    "S": 0.40,
    "P": 0.40,
}

DEFAULT_METAL_RADIUS = 0.46

BLENDER_RENDER_SCRIPT = r"""
import json
import sys
from pathlib import Path

import bpy
from mathutils import Vector


def load_payload() -> dict:
    try:
        marker = sys.argv.index("--")
    except ValueError:
        raise SystemExit("Missing -- payload argument for AdsMind Blender renderer")
    return json.loads(Path(sys.argv[marker + 1]).read_text(encoding="utf-8"))


def hex_to_rgba(value: str) -> tuple[float, float, float, float]:
    value = value.strip().lstrip("#")
    return (
        int(value[0:2], 16) / 255.0,
        int(value[2:4], 16) / 255.0,
        int(value[4:6], 16) / 255.0,
        1.0,
    )


def display_rgba(value: str) -> tuple[float, float, float, float]:
    r, g, b, a = hex_to_rgba(value)
    return (
        min(1.0, r * 1.28 + 0.06),
        min(1.0, g * 1.28 + 0.06),
        min(1.0, b * 1.28 + 0.06),
        a,
    )


payload = load_payload()
atoms = payload["atoms"]
output = payload["output"]

bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete()

scene = bpy.context.scene
scene.render.engine = "CYCLES"
scene.cycles.samples = 128
scene.cycles.use_denoising = True
scene.render.film_transparent = True
scene.render.resolution_x = int(payload.get("resolution", 1200))
scene.render.resolution_y = int(payload.get("resolution", 1200))
try:
    scene.view_settings.view_transform = "Standard"
    scene.view_settings.look = "None"
except TypeError:
    pass
scene.view_settings.exposure = 0.35
scene.view_settings.gamma = 1

materials = {}
coords = [Vector(atom["coord"]) for atom in atoms]
center = sum(coords, Vector((0, 0, 0))) / max(len(coords), 1)
for atom in atoms:
    coord = Vector(atom["coord"]) - center
    symbol = atom["symbol"]
    if symbol not in materials:
        mat = bpy.data.materials.new(f"mat_{symbol}")
        mat.use_nodes = True
        bsdf = mat.node_tree.nodes.get("Principled BSDF")
        color = display_rgba(atom["color"])
        bsdf.inputs["Base Color"].default_value = color
        bsdf.inputs["Roughness"].default_value = 0.42
        bsdf.inputs["Metallic"].default_value = 0.0
        bsdf.inputs["Emission Color"].default_value = color
        bsdf.inputs["Emission Strength"].default_value = 0.18
        materials[symbol] = mat
    bpy.ops.mesh.primitive_uv_sphere_add(
        segments=48,
        ring_count=24,
        radius=float(atom["radius"]),
        location=coord,
    )
    obj = bpy.context.object
    obj.name = f"{symbol}_{atom['index']}"
    obj.data.materials.append(materials[symbol])
    bpy.ops.object.shade_smooth()

xs = [float(v.x - center.x) for v in coords]
ys = [float(v.y - center.y) for v in coords]
zs = [float(v.z - center.z) for v in coords]
span = max(max(xs) - min(xs), max(ys) - min(ys), max(zs) - min(zs), 1.0)

bpy.ops.object.light_add(type="AREA", location=(0.2 * span, -0.9 * span, 2.25 * span))
key = bpy.context.object
key.name = "Key_Area_Light"
key.data.energy = 700
key.data.size = 5.0

bpy.ops.object.light_add(type="AREA", location=(-1.4 * span, 1.1 * span, 1.15 * span))
fill = bpy.context.object
fill.name = "Fill_Area_Light"
fill.data.energy = 180
fill.data.size = 7.0

bpy.ops.object.light_add(type="AREA", location=(1.1 * span, 1.0 * span, 1.6 * span))
rim = bpy.context.object
rim.name = "Rim_Area_Light"
rim.data.energy = 120
rim.data.size = 5.5

bpy.ops.object.camera_add(location=(1.10 * span, -1.45 * span, 0.92 * span), rotation=(0, 0, 0))
camera = bpy.context.object
direction = Vector((0, 0, 0)) - camera.location
camera.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()
camera.data.type = "ORTHO"
camera.data.ortho_scale = span * 1.75
scene.camera = camera

world = scene.world or bpy.data.worlds.new("World")
scene.world = world
world.color = (1.0, 1.0, 1.0)

Path(output).parent.mkdir(parents=True, exist_ok=True)
scene.render.filepath = output
bpy.ops.render.render(write_still=True)
"""


def parse_xyz(path: Path | str) -> tuple[list[str], np.ndarray, str]:
    """Parse an XYZ file into symbols, coordinates, and comment text."""
    xyz_path = Path(path)
    with xyz_path.open(encoding="utf-8") as handle:
        lines = handle.readlines()
    if len(lines) < 2:
        raise ValueError(f"Invalid XYZ file with fewer than two lines: {xyz_path}")
    natoms = int(lines[0].strip())
    if len(lines) < natoms + 2:
        raise ValueError(f"XYZ file is truncated: {xyz_path}")

    symbols: list[str] = []
    coords: list[list[float]] = []
    for line in lines[2 : 2 + natoms]:
        parts = line.split()
        if len(parts) < 4:
            raise ValueError(f"Invalid XYZ coordinate row in {xyz_path}: {line!r}")
        symbols.append(parts[0])
        coords.append([float(parts[1]), float(parts[2]), float(parts[3])])
    return symbols, np.asarray(coords, dtype=float), lines[1].strip()


def element_color(symbol: str) -> str:
    """Return a stable display color for an element symbol."""
    if symbol in ELEMENT_COLORS:
        return ELEMENT_COLORS[symbol]
    idx = sum(ord(ch) for ch in symbol) % len(FALLBACK_COLORS)
    return FALLBACK_COLORS[idx]


def _as_float_sequence(values: Iterable[object]) -> list[float]:
    floats: list[float] = []
    for value in values:
        if value is None:
            continue
        try:
            floats.append(float(value))
        except (TypeError, ValueError):
            continue
    return floats


def render_best_structure_png(
    xyz_path: Path | str,
    out_path: Path | str,
    *,
    elev: float = 24.0,
    azim: float = -54.0,
) -> Path:
    """Render a transparent PNG snapshot of a relaxed adsorption structure.

    Blender is preferred for publication-facing reports. The matplotlib path is
    retained as a dependency-light fallback for headless benchmark machines.
    """
    try:
        return render_best_structure_blender(xyz_path, out_path)
    except Exception:
        return render_best_structure_matplotlib(xyz_path, out_path, elev=elev, azim=azim)


def render_best_structure_matplotlib(
    xyz_path: Path | str,
    out_path: Path | str,
    *,
    elev: float = 24.0,
    azim: float = -54.0,
) -> Path:
    """Render a lightweight matplotlib fallback snapshot."""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    symbols, coords, _ = parse_xyz(xyz_path)
    if len(symbols) == 0:
        raise ValueError(f"Cannot render empty XYZ file: {xyz_path}")

    centered = coords.copy()
    centered[:, 0] -= centered[:, 0].mean()
    centered[:, 1] -= centered[:, 1].mean()

    fig = plt.figure(figsize=(4.0, 3.2), dpi=240)
    fig.patch.set_alpha(0.0)
    ax = fig.add_subplot(111, projection="3d")
    ax.set_facecolor((1, 1, 1, 0))
    ax.view_init(elev=elev, azim=azim)
    try:
        ax.set_proj_type("ortho")
    except Exception:
        pass

    z = centered[:, 2]
    z_span = max(float(z.max() - z.min()), 1e-6)
    z_norm = (z - z.min()) / z_span

    indices = sorted(range(len(symbols)), key=lambda idx: centered[idx, 2])
    for idx in indices:
        symbol = symbols[idx]
        size = 124 if symbol != "H" else 54
        if symbol in {"C", "N", "O", "H", "S", "P"}:
            size *= 1.18
            edge_color = "#1f2a33"
            alpha = 0.98
        else:
            edge_color = "#6b5a32"
            alpha = 0.70 + 0.24 * float(z_norm[idx])
        ax.scatter(
            centered[idx, 0],
            centered[idx, 1],
            centered[idx, 2],
            s=size,
            c=element_color(symbol),
            edgecolors=edge_color,
            linewidths=0.35,
            alpha=alpha,
            depthshade=True,
        )

    max_range = max(
        float(np.ptp(centered[:, 0])),
        float(np.ptp(centered[:, 1])),
        float(np.ptp(centered[:, 2])),
        1.0,
    )
    mid = centered.mean(axis=0)
    pad = max_range * 0.58
    ax.set_xlim(mid[0] - pad, mid[0] + pad)
    ax.set_ylim(mid[1] - pad, mid[1] + pad)
    ax.set_zlim(mid[2] - pad, mid[2] + pad)
    ax.set_axis_off()
    fig.tight_layout(pad=0)

    output = Path(out_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output, transparent=True, bbox_inches="tight", pad_inches=0)
    plt.close(fig)
    return output


def find_blender_executable(explicit_path: str | None = None) -> str | None:
    """Locate Blender without making it a hard runtime dependency."""
    if explicit_path:
        return explicit_path
    candidates = [
        os.environ.get("ADSMIND_BLENDER_EXECUTABLE"),
        shutil.which("blender"),
        "/opt/homebrew/bin/blender",
        "/usr/local/bin/blender",
        "/Applications/Blender.app/Contents/MacOS/Blender",
    ]
    for candidate in candidates:
        if not candidate:
            continue
        path = Path(candidate)
        if ("/" in candidate or "\\" in candidate) and not path.exists():
            continue
        return candidate
    return None


def render_best_structure_blender(
    xyz_path: Path | str,
    out_path: Path | str,
    *,
    blender_executable: str | None = None,
    timeout: int = 90,
) -> Path:
    """Render a publication-style atomistic snapshot with headless Blender."""
    blender = find_blender_executable(blender_executable)
    if not blender:
        raise RuntimeError("Blender executable not found")
    if not Path(blender).exists() and ("/" in blender or "\\" in blender):
        raise RuntimeError(f"Blender executable not found: {blender}")

    symbols, coords, _ = parse_xyz(xyz_path)
    if len(symbols) == 0:
        raise ValueError(f"Cannot render empty XYZ file: {xyz_path}")

    atoms = []
    for index, (symbol, coord) in enumerate(zip(symbols, coords)):
        atoms.append(
            {
                "index": index,
                "symbol": symbol,
                "coord": [float(coord[0]), float(coord[1]), float(coord[2])],
                "color": element_color(symbol),
                "radius": ELEMENT_RADII.get(symbol, DEFAULT_METAL_RADIUS),
            }
        )

    output = Path(out_path)
    with tempfile.TemporaryDirectory(prefix="adsmind_blender_") as tmpdir:
        tmp = Path(tmpdir)
        script_path = tmp / "render_adsmind_structure.py"
        payload_path = tmp / "payload.json"
        script_path.write_text(BLENDER_RENDER_SCRIPT, encoding="utf-8")
        payload_path.write_text(
            json.dumps({"atoms": atoms, "output": str(output), "resolution": 1200}),
            encoding="utf-8",
        )
        output.parent.mkdir(parents=True, exist_ok=True)
        completed = subprocess.run(
            [
                blender,
                "--background",
                "--factory-startup",
                "--python",
                str(script_path),
                "--",
                str(payload_path),
            ],
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            timeout=timeout,
        )
        if completed.returncode != 0:
            raise RuntimeError(
                "Blender render failed with exit code "
                f"{completed.returncode}: {completed.stdout[-2000:]}"
            )
    if not output.exists() or output.stat().st_size == 0:
        raise RuntimeError(f"Blender did not create a nonempty PNG: {output}")
    return output


def render_iteration_energy_curve(
    attempt_records: Iterable[dict],
    out_path: Path | str,
) -> Path:
    """Render a transparent energy trajectory plot from attempt records."""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    records = list(attempt_records)
    energies = _as_float_sequence(record.get("most_stable_energy_eV") for record in records)
    if not energies:
        raise ValueError("No valid attempt energies available for trajectory rendering.")

    attempts: list[int] = []
    plotted_energies: list[float] = []
    for idx, record in enumerate(records, start=1):
        value = record.get("most_stable_energy_eV")
        try:
            plotted_energies.append(float(value))
            attempts.append(idx)
        except (TypeError, ValueError):
            continue

    running_best: list[float] = []
    best = float("inf")
    for energy in plotted_energies:
        best = min(best, energy)
        running_best.append(best)

    fig, ax = plt.subplots(figsize=(4.0, 2.4), dpi=220)
    fig.patch.set_alpha(0.0)
    ax.set_facecolor((1, 1, 1, 0))
    ax.plot(attempts, plotted_energies, marker="o", color="#607d8b", label="Attempt")
    ax.plot(attempts, running_best, marker="s", color="#2e7d32", label="Running best")
    ax.set_xlim(0.5, max(attempts) + 0.5)
    ax.set_xticks(attempts)
    ax.set_xlabel("Iteration")
    ax.set_ylabel("Adsorption energy (eV)")
    ax.grid(True, alpha=0.25)
    ax.legend(frameon=False, fontsize=8)
    fig.tight_layout()

    output = Path(out_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output, transparent=True, bbox_inches="tight", pad_inches=0.04)
    plt.close(fig)
    return output
