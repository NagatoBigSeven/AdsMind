"""Deterministic visualization helpers for AdsMind reports."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Iterable

import numpy as np


ELEMENT_COLORS = {
    # CatDT / research/figures Panel-B palette. Keep these values stable so
    # summarizer reports and manuscript figures do not drift in style.
    "Pt": "#EFE4C4",
    "Sn": "#506C7C",
    "Mn": "#EBE0C0",
    "Ni": "#3FBF44",
    "Ga": "#3FBF44",
    "In": "#B57878",
    "Pd": "#7E7E8A",
    "Cu": "#3FBF44",
    "Zr": "#3FBF44",
    "Ti": "#C8C8CC",
    "Co": "#E89AAB",
    "Fe": "#9F4F4F",
    "Zn": "#7868A8",
    "V": "#B0B0B4",
    "Mo": "#5566AA",
    "Rh": "#4B5C7A",
    "As": "#B07FCC",
    "Hf": "#B0C8D0",
    "O": "#E03030",
    "N": "#3868D8",
    "C": "#383838",
    "H": "#F0F0F0",
    # Extra elements observed in OCD-GMAE/CMU runs. These are subdued fallbacks
    # rather than a separate manuscript palette.
    "S": "#F2C744",
    "P": "#E36A1A",
    "Ag": "#c9c9c9",
    "Au": "#d3a526",
    "Ru": "#6d7a8b",
    "Cr": "#70876a",
    "Ta": "#668099",
    "W": "#536a83",
    "Re": "#6a7890",
    "Al": "#b5bec8",
    "Tl": "#8d91a6",
    "Bi": "#9c88a8",
    "Pb": "#7c8297",
    "Sb": "#9c8794",
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

COVALENT_RADII = {
    "H": 0.31,
    "C": 0.76,
    "N": 0.71,
    "O": 0.66,
    "S": 1.05,
    "P": 1.07,
    "Mo": 1.54,
    "Pd": 1.39,
    "Pt": 1.36,
    "Cu": 1.32,
    "Ag": 1.45,
    "Au": 1.36,
    "Ru": 1.46,
    "Rh": 1.42,
    "Co": 1.26,
    "Ni": 1.24,
    "Fe": 1.32,
    "Mn": 1.39,
    "Cr": 1.39,
    "V": 1.53,
    "Ti": 1.60,
    "Zr": 1.75,
    "Hf": 1.75,
    "Ta": 1.70,
    "W": 1.62,
    "Re": 1.51,
    "Al": 1.21,
    "Ga": 1.22,
    "In": 1.42,
    "Tl": 1.45,
    "Bi": 1.48,
    "Pb": 1.46,
    "Sn": 1.39,
    "Sb": 1.39,
    "As": 1.19,
    "Se": 1.20,
    "Te": 1.38,
    "Si": 1.11,
    "Ge": 1.20,
    "Ca": 1.76,
    "Sr": 1.95,
    "Y": 1.90,
    "Sc": 1.70,
    "Na": 1.66,
    "K": 2.03,
    "Os": 1.44,
}

DEFAULT_COVALENT_RADIUS = 1.35
PANELB_RADIUS_SCALE = 0.85
H_DISPLAY_RADIUS = 0.55
VALID_RENDER_STYLES = {"panelb", "ovito", "ballstick", "spacefill"}

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
    r, g, b = (int(value[i:i+2], 16) / 255.0 for i in (0, 2, 4))

    def srgb_to_linear(channel: float) -> float:
        if channel <= 0.04045:
            return channel / 12.92
        return ((channel + 0.055) / 1.055) ** 2.4

    return (
        srgb_to_linear(r),
        srgb_to_linear(g),
        srgb_to_linear(b),
        1.0,
    )


def _principled_bsdf(mat):
    return next(node for node in mat.node_tree.nodes if node.type == "BSDF_PRINCIPLED")


def make_material(symbol: str, color_hex: str):
    mat = bpy.data.materials.new(f"mat_{symbol}")
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    bsdf = _principled_bsdf(mat)
    bsdf.inputs["Roughness"].default_value = 0.25
    if "Metallic" in bsdf.inputs:
        bsdf.inputs["Metallic"].default_value = 0.0

    if symbol == "H":
        fresnel = nodes.new("ShaderNodeFresnel")
        fresnel.inputs["IOR"].default_value = 1.6
        multiply = nodes.new("ShaderNodeMath")
        multiply.operation = "MULTIPLY"
        multiply.inputs[1].default_value = 0.85
        mix = nodes.new("ShaderNodeMixRGB")
        mix.blend_type = "MIX"
        mix.inputs["Color1"].default_value = hex_to_rgba(color_hex)
        mix.inputs["Color2"].default_value = (0.0, 0.0, 0.0, 1.0)
        links.new(fresnel.outputs["Fac"], multiply.inputs[0])
        links.new(multiply.outputs["Value"], mix.inputs["Fac"])
        links.new(mix.outputs["Color"], bsdf.inputs["Base Color"])
    else:
        bsdf.inputs["Base Color"].default_value = hex_to_rgba(color_hex)
    return mat


payload = load_payload()
atoms = payload["atoms"]
bonds = payload.get("bonds", [])
output = payload["output"]
style = payload.get("style", "panelb")
draw_bonds = bool(payload.get("draw_bonds", True))
bond_radius = float(payload.get("bond_radius", 0.038))

bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete()

scene = bpy.context.scene
scene.render.engine = "CYCLES"
scene.cycles.samples = int(payload.get("samples", 256))
scene.cycles.use_denoising = True
try:
    scene.cycles.denoiser = "OPENIMAGEDENOISE"
except Exception:
    pass
scene.render.film_transparent = True
scene.render.resolution_x = int(payload.get("resolution", 1024))
scene.render.resolution_y = int(payload.get("resolution", 1024))
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
scene.render.image_settings.color_mode = "RGBA"
scene.render.image_settings.color_depth = "8"
try:
    scene.view_settings.view_transform = "Standard"
    scene.view_settings.look = "None"
except TypeError:
    pass
scene.view_settings.exposure = 0.0
scene.view_settings.gamma = 1

materials = {}
coords = [Vector(atom["coord"]) for atom in atoms]
center = sum(coords, Vector((0, 0, 0))) / max(len(coords), 1)
for atom in atoms:
    coord = Vector(atom["coord"]) - center
    symbol = atom["symbol"]
    if symbol not in materials:
        materials[symbol] = make_material(symbol, atom["color"])
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

if draw_bonds and bonds:
    bond_mat = bpy.data.materials.new("mat_bond")
    bond_mat.use_nodes = True
    bond_bsdf = bond_mat.node_tree.nodes.get("Principled BSDF")
    bond_bsdf.inputs["Base Color"].default_value = (0.50, 0.54, 0.56, 1.0)
    bond_bsdf.inputs["Roughness"].default_value = 0.48
    bond_bsdf.inputs["Metallic"].default_value = 0.0
    bond_bsdf.inputs["Emission Color"].default_value = (0.50, 0.54, 0.56, 1.0)
    bond_bsdf.inputs["Emission Strength"].default_value = 0.07
    for bond in bonds:
        start = Vector(bond["start"]) - center
        end = Vector(bond["end"]) - center
        mid = (start + end) / 2.0
        direction = end - start
        length = direction.length
        if length <= 1e-6:
            continue
        bpy.ops.mesh.primitive_cylinder_add(
            vertices=24,
            radius=bond_radius,
            depth=length,
            location=mid,
        )
        cyl = bpy.context.object
        cyl.name = f"bond_{bond['i']}_{bond['j']}"
        cyl.rotation_euler = direction.to_track_quat("Z", "Y").to_euler()
        cyl.data.materials.append(bond_mat)
        bpy.ops.object.shade_smooth()

xs = [float(v.x - center.x) for v in coords]
ys = [float(v.y - center.y) for v in coords]
zs = [float(v.z - center.z) for v in coords]
span = max(max(xs) - min(xs), max(ys) - min(ys), max(zs) - min(zs), 5.0)

bpy.ops.object.light_add(type="AREA", location=(-span, -span * 1.2, span * 1.5))
key = bpy.context.object
key.name = "Key_Area_Light"
key.data.energy = 2000
key.data.size = span * 3.0

bpy.ops.object.light_add(type="AREA", location=(0, 0, span * 2.5))
fill = bpy.context.object
fill.name = "Fill_Area_Light"
fill.data.energy = 600
fill.data.size = span * 4.0

distance = span * 3.0
cam_loc = Vector((distance * 0.55, -distance * 0.75, distance * 1.05))
bpy.ops.object.camera_add(location=cam_loc, rotation=(0, 0, 0))
camera = bpy.context.object
direction = Vector((0, 0, 0)) - camera.location
camera.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()
camera.data.type = "ORTHO"
scene.camera = camera
bpy.context.view_layer.update()

cam_matrix_inv = camera.matrix_world.inverted()
max_x = max_y = 0.0
max_radius = 0.0
for atom in atoms:
    local = cam_matrix_inv @ (Vector(atom["coord"]) - center)
    max_x = max(max_x, abs(local.x))
    max_y = max(max_y, abs(local.y))
    max_radius = max(max_radius, float(atom["radius"]))
half_extent = max(max_x, max_y) + max_radius
camera.data.ortho_scale = 2.0 * half_extent * 1.12

world = scene.world or bpy.data.worlds.new("World")
scene.world = world
world.use_nodes = True
bg = world.node_tree.nodes.get("Background")
if bg:
    bg.inputs["Color"].default_value = (1.0, 1.0, 1.0, 1.0)
    bg.inputs["Strength"].default_value = 1.0
else:
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


def normalize_render_style(style: str | None = None) -> str:
    """Resolve the structure-rendering style requested by env or caller."""
    requested = (style or os.environ.get("ADSMIND_VIS_RENDER_STYLE") or "panelb").strip().lower()
    aliases = {
        "default": "panelb",
        "blender": "panelb",
        "catdt": "panelb",
        "catdt-panel-b": "panelb",
        "catdt_panel_b": "panelb",
        "panel-b": "panelb",
        "panel_b": "panelb",
        "ovito-like": "ballstick",
        "ovito_like": "ballstick",
        "ball-stick": "ballstick",
        "ball_and_stick": "ballstick",
        "ball-and-stick": "ballstick",
        "space-fill": "spacefill",
        "space_fill": "spacefill",
        "space-filling": "spacefill",
    }
    resolved = aliases.get(requested, requested)
    return resolved if resolved in VALID_RENDER_STYLES else "panelb"


def covalent_radius(symbol: str) -> float:
    """Return a stable covalent radius estimate for bond inference."""
    return COVALENT_RADII.get(symbol, DEFAULT_COVALENT_RADIUS)


def infer_bonds(symbols: list[str], coords: np.ndarray, *, style: str) -> list[dict[str, object]]:
    """Infer near-neighbour bonds for OVITO-like ball-stick snapshots."""
    if style != "ballstick":
        return []
    scale = 1.12
    max_distance = 3.05
    bonds: list[dict[str, object]] = []
    for i, symbol_i in enumerate(symbols):
        for j in range(i + 1, len(symbols)):
            symbol_j = symbols[j]
            distance = float(np.linalg.norm(coords[i] - coords[j]))
            if distance < 0.35 or distance > max_distance:
                continue
            threshold = min(
                covalent_radius(symbol_i) + covalent_radius(symbol_j),
                max_distance / scale,
            )
            if distance <= threshold * scale:
                bonds.append(
                    {
                        "i": i,
                        "j": j,
                        "start": [float(v) for v in coords[i]],
                        "end": [float(v) for v in coords[j]],
                    }
                )
    return bonds


def display_radius(symbol: str, *, style: str) -> float:
    """Return a style-specific atomic display radius."""
    if symbol == "H" and style in {"panelb", "spacefill"}:
        return H_DISPLAY_RADIUS
    covalent = covalent_radius(symbol)
    if style == "spacefill":
        return covalent * 0.95
    if style == "ballstick":
        return max(ELEMENT_RADII.get(symbol, DEFAULT_METAL_RADIUS) * 0.68, 0.16)
    return covalent * PANELB_RADIUS_SCALE


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
    render_style = normalize_render_style()
    if render_style == "ovito":
        try:
            return render_best_structure_ovito(xyz_path, out_path)
        except Exception:
            # OVITO is optional and can be brittle on headless machines; fall
            # back to the deterministic Panel-B Blender style before matplotlib.
            pass
    try:
        return render_best_structure_blender(xyz_path, out_path, style=render_style)
    except Exception:
        return render_best_structure_matplotlib(xyz_path, out_path, elev=elev, azim=azim)


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def find_ovito_python(explicit_path: str | None = None) -> str | None:
    """Locate a Python runtime capable of importing OVITO."""
    if explicit_path:
        if ("/" in explicit_path or "\\" in explicit_path) and not Path(explicit_path).exists():
            return None
        return explicit_path
    candidates = [
        os.environ.get("ADSMIND_OVITO_PYTHON"),
        str(_repo_root() / ".venv-ovito" / "bin" / "python"),
        shutil.which("ovitos"),
        sys.executable,
    ]
    for candidate in candidates:
        if not candidate:
            continue
        path = Path(candidate)
        if ("/" in candidate or "\\" in candidate) and not path.exists():
            continue
        return candidate
    return None


def render_best_structure_ovito(
    xyz_path: Path | str,
    out_path: Path | str,
    *,
    ovito_python: str | None = None,
    timeout: int | None = None,
) -> Path:
    """Render using the OVITO/CatDT helper under research/figures when available."""
    script = _repo_root() / "research" / "figures" / "panel_b_ovito" / "scripts" / (
        "catalyst_surface_visualizer.py"
    )
    if not script.exists():
        raise RuntimeError(f"OVITO visualizer script not found: {script}")

    python_exec = find_ovito_python(ovito_python)
    if not python_exec:
        raise RuntimeError("OVITO Python runtime not found")

    output = Path(out_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    command = [
        python_exec,
        str(script),
        str(xyz_path),
        "-o",
        str(output),
        "--renderer",
        os.environ.get("ADSMIND_OVITO_RENDERER", "tachyon"),
        "--quality",
        os.environ.get("ADSMIND_OVITO_QUALITY", "high"),
        "--elevation",
        os.environ.get("ADSMIND_OVITO_ELEVATION", "30"),
        "--azimuth",
        os.environ.get("ADSMIND_OVITO_AZIMUTH", "45"),
        "--scale",
        os.environ.get("ADSMIND_OVITO_SCALE", "1.0"),
        "--background",
        os.environ.get("ADSMIND_OVITO_BACKGROUND", "white"),
        "--color-scheme",
        os.environ.get("ADSMIND_OVITO_COLOR_SCHEME", "jmol"),
        "--no-expand",
    ]
    completed = subprocess.run(
        command,
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        timeout=timeout or int(os.environ.get("ADSMIND_OVITO_TIMEOUT_SEC", "240")),
    )
    if completed.returncode != 0:
        raise RuntimeError(
            "OVITO render failed with exit code "
            f"{completed.returncode}: {completed.stdout[-2000:]}"
        )
    if not output.exists() or output.stat().st_size == 0:
        raise RuntimeError(f"OVITO did not create a nonempty PNG: {output}")
    return output


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
    style: str | None = None,
    timeout: int | None = None,
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

    render_style = normalize_render_style(style)
    atoms = []
    for index, (symbol, coord) in enumerate(zip(symbols, coords)):
        atoms.append(
            {
                "index": index,
                "symbol": symbol,
                "coord": [float(coord[0]), float(coord[1]), float(coord[2])],
                "color": element_color(symbol),
                "radius": display_radius(symbol, style=render_style),
            }
        )
    bonds = infer_bonds(symbols, coords, style=render_style)
    draw_bonds = render_style == "ballstick"

    output = Path(out_path)
    with tempfile.TemporaryDirectory(prefix="adsmind_blender_") as tmpdir:
        tmp = Path(tmpdir)
        script_path = tmp / "render_adsmind_structure.py"
        payload_path = tmp / "payload.json"
        script_path.write_text(BLENDER_RENDER_SCRIPT, encoding="utf-8")
        payload_path.write_text(
            json.dumps(
                {
                    "atoms": atoms,
                    "bonds": bonds,
                    "draw_bonds": draw_bonds,
                    "bond_radius": 0.032,
                    "output": str(output),
                    "resolution": int(os.environ.get("ADSMIND_VIS_RESOLUTION", "1024")),
                    "samples": int(os.environ.get("ADSMIND_VIS_SAMPLES", "256")),
                    "style": render_style,
                }
            ),
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
            timeout=timeout or int(os.environ.get("ADSMIND_BLENDER_TIMEOUT_SEC", "180")),
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
