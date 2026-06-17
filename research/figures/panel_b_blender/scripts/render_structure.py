"""
Panel B Blender renderer — single-structure entry point.

Loads an extended-XYZ file, builds a CatDT-style scene, renders a transparent PNG.
Designed to be called from Blender (via BlenderMCP exec or `blender --background -P`).
Style spec: research/figures/panel_b_blender/STYLE_SPEC.md
"""

from __future__ import annotations

import json
import math
import os
from dataclasses import dataclass

import bpy
import mathutils

# Atomic numbers for elements appearing in our Panel B cases (drives Z-ordered
# metal assignment when applying a categorical palette from the lab compendium).
ATOMIC_NUMBER = {
    "H": 1, "C": 6, "N": 7, "O": 8,
    "Ti": 22, "Mn": 25, "Fe": 26, "Co": 27, "Ni": 28, "Cu": 29, "Zn": 30,
    "Ga": 31, "As": 33, "Zr": 40, "Mo": 42, "Rh": 45, "Pd": 46, "In": 49,
    "Sn": 50, "Hf": 72, "Pt": 78,
}
NONMETAL_CPK = {"O": "#E03030", "N": "#3868D8", "C": "#383838", "H": "#F0F0F0"}

# CatDT-style palette (sRGB hex). See STYLE_SPEC.md for source.
ELEMENT_COLOR = {
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
    "V":  "#B0B0B4",
    "Mo": "#5566AA",
    "Rh": "#4B5C7A",
    "As": "#B07FCC",
    "Hf": "#B0C8D0",
    "O":  "#E03030",
    "N":  "#3868D8",
    "C":  "#383838",
    "H":  "#FFFFFF",
}

# Covalent radii in Å (Cordero 2008, abridged).
COVALENT_RADIUS = {
    "H": 0.31, "C": 0.76, "N": 0.71, "O": 0.66,
    "Mo": 1.54, "Pd": 1.39, "Pt": 1.36, "Sn": 1.39, "Mn": 1.39,
    "Ni": 1.24, "Ga": 1.22, "In": 1.42, "Cu": 1.32, "Zr": 1.75,
    "Ti": 1.60, "Co": 1.26, "Fe": 1.32, "Zn": 1.22, "V": 1.53,
    "Rh": 1.42, "As": 1.19, "Hf": 1.75,
}

# Sphere radius = COVALENT_RADIUS * RADIUS_SCALE (CatDT look has chunky overlap at metal-metal contact).
RADIUS_SCALE = 0.85

# Hydrogen reads as invisible-white on a white BG; bright center + thick dark rim
# pops against any backdrop (white BG OR grey/dark metal neighbors).
# (Advisor 2026-04-29 PM: "可以让H原子的球的边框加重". v5 used mid-grey center which
# clashed with steel-grey Pd in Mo3Pd case; v6 bright center + stronger rim fixes this.)
H_DISPLAY_RADIUS = 0.55  # Å, larger than covalent so it reads in the figure
H_DISPLAY_COLOR = "#F0F0F0"  # near-white center — pops on any background
H_RIM_DARK = (0.0, 0.0, 0.0, 1.0)  # pure black rim
H_RIM_STRENGTH = 0.85  # 0.0 = no rim, 1.0 = full black silhouette
H_RIM_IOR = 1.6  # higher IOR = thicker rim


@dataclass
class Atom:
    element: str
    pos: mathutils.Vector


def hex_to_rgba(h: str) -> tuple[float, float, float, float]:
    h = h.lstrip("#")
    r, g, b = (int(h[i:i+2], 16) / 255.0 for i in (0, 2, 4))
    # Blender principled BSDF expects linear RGB; sRGB→linear via srgb_to_linear.
    def srgb_to_linear(c: float) -> float:
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
    return (srgb_to_linear(r), srgb_to_linear(g), srgb_to_linear(b), 1.0)


def parse_extxyz(path: str) -> list[Atom]:
    """Parse extended-XYZ; ignore lattice/extras, just return element + position."""
    with open(path) as f:
        n = int(f.readline().strip())
        f.readline()  # comment / Lattice line
        atoms: list[Atom] = []
        for _ in range(n):
            parts = f.readline().split()
            elem = parts[0]
            x, y, z = (float(parts[i]) for i in (1, 2, 3))
            atoms.append(Atom(elem, mathutils.Vector((x, y, z))))
    return atoms


def wipe_scene() -> None:
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    for block in (bpy.data.meshes, bpy.data.materials, bpy.data.lights, bpy.data.cameras):
        for item in list(block):
            block.remove(item)


def _principled_bsdf(mat: bpy.types.Material):
    """Find the Principled BSDF node by type — locale-agnostic
    (Blender's GUI may localize node names, e.g. 'Principled BSDF' → '原理化 BSDF')."""
    return next(n for n in mat.node_tree.nodes if n.type == "BSDF_PRINCIPLED")


def make_material(name: str, hex_color: str, roughness: float = 0.25) -> bpy.types.Material:
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    bsdf = _principled_bsdf(mat)
    bsdf.inputs["Base Color"].default_value = hex_to_rgba(hex_color)
    bsdf.inputs["Roughness"].default_value = roughness
    if "Metallic" in bsdf.inputs:
        bsdf.inputs["Metallic"].default_value = 0.0
    return mat


def make_material_with_rim(name: str, hex_color: str, rim_rgba, rim_strength: float,
                           rim_ior: float, roughness: float = 0.25) -> bpy.types.Material:
    """PBR material with Fresnel-driven dark rim (visible silhouette outline).
    Used for H atoms so they read against a white background."""
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    bsdf = _principled_bsdf(mat)
    bsdf.inputs["Roughness"].default_value = roughness
    if "Metallic" in bsdf.inputs:
        bsdf.inputs["Metallic"].default_value = 0.0

    # Fresnel weights how much the rim color shows at grazing angles.
    fresnel = nodes.new("ShaderNodeFresnel")
    fresnel.inputs["IOR"].default_value = rim_ior
    # Map fresnel (0..1) to (0..rim_strength) so rim isn't 100% black.
    multiply = nodes.new("ShaderNodeMath")
    multiply.operation = "MULTIPLY"
    multiply.inputs[1].default_value = rim_strength
    links.new(fresnel.outputs["Fac"], multiply.inputs[0])
    # Mix base color toward rim color using the scaled fresnel.
    mix = nodes.new("ShaderNodeMixRGB")
    mix.blend_type = "MIX"
    mix.inputs["Color1"].default_value = hex_to_rgba(hex_color)
    mix.inputs["Color2"].default_value = rim_rgba
    links.new(multiply.outputs["Value"], mix.inputs["Fac"])
    links.new(mix.outputs["Color"], bsdf.inputs["Base Color"])
    return mat


def build_palette_from_scheme(scheme_colors: list[str], elements: set[str]) -> dict[str, str]:
    """Apply a categorical scheme: cycle through scheme_colors for metals
    (Z-ordered for stability across runs), keep CPK for nonmetals."""
    palette = dict(NONMETAL_CPK)
    metals = sorted([e for e in elements if e not in NONMETAL_CPK],
                    key=lambda e: ATOMIC_NUMBER.get(e, 999))
    for i, m in enumerate(metals):
        palette[m] = scheme_colors[i % len(scheme_colors)]
    return palette


def build_atom_meshes(atoms: list[Atom]) -> tuple[mathutils.Vector, mathutils.Vector]:
    """Create one UV sphere per atom; return (centroid, bbox_size) for camera framing."""
    # Resolve palette: PANEL_B_SCHEME_JSON env var (path to a scheme JSON) overrides
    # the hardcoded CatDT-extracted ELEMENT_COLOR; nonmetals always use CPK.
    elements = {a.element for a in atoms}
    scheme_path = os.environ.get("PANEL_B_SCHEME_JSON", "").strip()
    if scheme_path:
        with open(scheme_path) as f:
            scheme = json.load(f)
        palette = build_palette_from_scheme(scheme["colors"], elements)
        print(f"[panel_b] palette from scheme: {scheme.get('id', scheme_path)}")
    else:
        palette = {e: ELEMENT_COLOR.get(e, "#888888") for e in elements}
        palette["H"] = H_DISPLAY_COLOR  # ensure H uses rim-friendly color
        print("[panel_b] palette: CatDT-extracted (default)")

    elems_seen: dict[str, bpy.types.Material] = {}
    for elem in elements:
        if elem == "H":
            elems_seen[elem] = make_material_with_rim(
                "mat_H", palette["H"], H_RIM_DARK, H_RIM_STRENGTH, H_RIM_IOR
            )
        else:
            elems_seen[elem] = make_material(f"mat_{elem}", palette[elem])

    coords = [a.pos for a in atoms]
    centroid = sum(coords, mathutils.Vector((0, 0, 0))) / len(coords)
    mins = mathutils.Vector(tuple(min(p[i] for p in coords) for i in range(3)))
    maxs = mathutils.Vector(tuple(max(p[i] for p in coords) for i in range(3)))
    size = maxs - mins

    for atom in atoms:
        if atom.element == "H":
            radius = H_DISPLAY_RADIUS
        else:
            radius = COVALENT_RADIUS.get(atom.element, 1.4) * RADIUS_SCALE
        bpy.ops.mesh.primitive_uv_sphere_add(
            radius=radius,
            segments=48, ring_count=24,
            location=(atom.pos - centroid),
        )
        sphere = bpy.context.active_object
        sphere.name = f"{atom.element}_{len(bpy.data.objects)}"
        bpy.ops.object.shade_smooth()
        sphere.data.materials.append(elems_seen[atom.element])

    return mathutils.Vector((0, 0, 0)), size  # centroid is now origin


def setup_world_transparent_white() -> None:
    world = bpy.data.worlds.get("World") or bpy.data.worlds.new("World")
    bpy.context.scene.world = world
    world.use_nodes = True
    bg = world.node_tree.nodes.get("Background")
    if bg:
        bg.inputs["Color"].default_value = (1, 1, 1, 1)
        bg.inputs["Strength"].default_value = 1.0
    bpy.context.scene.render.film_transparent = True  # alpha PNG


def setup_lights(bbox_size: mathutils.Vector) -> None:
    extent = max(bbox_size) or 5.0
    # Key — large area light, upper-front-left.
    bpy.ops.object.light_add(type="AREA", location=(-extent, -extent * 1.2, extent * 1.5))
    key = bpy.context.active_object
    key.data.energy = 2000
    key.data.size = extent * 3
    key.rotation_euler = (math.radians(45), math.radians(-15), math.radians(-30))
    # Fill — top-down, dimmer.
    bpy.ops.object.light_add(type="AREA", location=(0, 0, extent * 2.5))
    fill = bpy.context.active_object
    fill.data.energy = 600
    fill.data.size = extent * 4


def setup_camera(atoms: list[Atom], centroid: mathutils.Vector, bbox_size: mathutils.Vector,
                 padding: float = 0.12) -> None:
    """Orthographic camera looking down-and-forward at the structure, so the surface
    (where adsorbates live) reads clearly. CatDT reference is near-orthographic.
    ortho_scale is computed by projecting all atom centers (+ radii) into camera
    image space, so framing is tight regardless of cell aspect ratio."""
    extent = max(bbox_size)
    distance = extent * 3.0
    # Upper-front, ~50° down elevation, slight rotation around vertical axis.
    cam_loc = mathutils.Vector((distance * 0.55, -distance * 0.75, distance * 1.05))
    bpy.ops.object.camera_add(location=cam_loc)
    cam = bpy.context.active_object
    direction = mathutils.Vector((0, 0, 0)) - cam_loc
    cam.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()
    cam.data.type = "ORTHO"
    bpy.context.view_layer.update()  # critical: matrix_world is stale until depsgraph refreshes

    # Project all atom centers into camera image space, find half-extent + worst-case radius.
    cam_matrix_inv = cam.matrix_world.inverted()
    max_x = max_y = 0.0
    max_radius = 0.0
    for atom in atoms:
        local = cam_matrix_inv @ (atom.pos - centroid)
        max_x = max(max_x, abs(local.x))
        max_y = max(max_y, abs(local.y))
        if atom.element == "H":
            r = H_DISPLAY_RADIUS
        else:
            r = COVALENT_RADIUS.get(atom.element, 1.4) * RADIUS_SCALE
        max_radius = max(max_radius, r)
    half_extent = max(max_x, max_y) + max_radius
    cam.data.ortho_scale = 2.0 * half_extent * (1.0 + padding)
    bpy.context.scene.camera = cam


def setup_render(out_png: str, resolution: int = 1024, samples: int = 256) -> None:
    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    scene.cycles.samples = samples
    scene.cycles.use_denoising = True
    scene.cycles.denoiser = "OPENIMAGEDENOISE"
    scene.render.resolution_x = resolution
    scene.render.resolution_y = resolution
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGBA"
    scene.render.image_settings.color_depth = "8"
    scene.view_settings.view_transform = "Standard"  # not Filmic
    scene.render.filepath = out_png
    # GPU if available.
    try:
        prefs = bpy.context.preferences.addons["cycles"].preferences
        prefs.compute_device_type = "METAL"
        for d in prefs.devices:
            d.use = True
        scene.cycles.device = "GPU"
    except Exception:
        scene.cycles.device = "CPU"


def render_xyz(xyz_path: str, out_png: str, resolution: int = 1024, samples: int = 256) -> None:
    print(f"[panel_b] rendering {xyz_path} -> {out_png}")
    atoms = parse_extxyz(xyz_path)
    print(f"[panel_b] parsed {len(atoms)} atoms; elements: {sorted({a.element for a in atoms})}")
    wipe_scene()
    setup_world_transparent_white()
    centroid_world = sum((a.pos for a in atoms), mathutils.Vector((0, 0, 0))) / len(atoms)
    centered = [Atom(a.element, a.pos - centroid_world) for a in atoms]
    _, bbox = build_atom_meshes(atoms)  # build_atom_meshes still re-centers internally
    setup_lights(bbox)
    setup_camera(centered, mathutils.Vector((0, 0, 0)), bbox)
    setup_render(out_png, resolution=resolution, samples=samples)
    bpy.ops.render.render(write_still=True)
    print(f"[panel_b] wrote {out_png}")


if __name__ == "__main__":
    # Globals can be overridden by the caller via env vars (BlenderMCP-friendly).
    xyz_path = os.environ.get("PANEL_B_XYZ", "").strip()
    out_path = os.environ.get("PANEL_B_OUT", "").strip()
    if not xyz_path or not out_path:
        raise SystemExit("Set PANEL_B_XYZ and PANEL_B_OUT before running this renderer.")
    res = int(os.environ.get("PANEL_B_RES", "1024"))
    samples = int(os.environ.get("PANEL_B_SAMPLES", "256"))
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    render_xyz(xyz_path, out_path, resolution=res, samples=samples)
