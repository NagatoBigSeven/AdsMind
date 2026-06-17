# Panel B Render Style Spec

Extracted from the CatDT paper Panel B reference. This is the target look for
the AdsMind Panel B structure renders.

## Layout (figure-level — handled in Illustrator/InDesign, not Blender)

- 6 columns × 3 rows = 18 cells per panel.
- Column header chip + colored frame per category. Frame colors:
  - Precious intermetallics → purple `#5E3F88`
  - Non-precious IMC & SAA → teal `#287A6E`
  - Metal@oxide SMSI → coral `#D5645A`
  - Single / dual atom on support → olive `#8E8B3C`
  - Zeolite-confined → near-black `#1F1F1F`
  - Bulk oxide (MvK) → mustard `#B89A2E`
- Cell label sits top-left in a small white chip, formula uses LaTeX subscripts (e.g. Pt₁Sn₁, Ni₃Ga, Ni@TiOₓ).
- Cell background pure white (`#FFFFFF`); no axis, no scale bar, no frame inside.

## Per-cell render (this is what Blender produces)

### Camera
- Slight perspective (35–50mm equiv. focal length), not orthographic.
- Camera elevation ~15–25° above horizon — atoms read as 3D, not flat.
- Slight rotation around vertical axis so motifs are recognizable (e.g. (111) terraces show the triangular pattern).
- Frame the structure with ~10% padding on all sides; no cropped atoms.

### Lighting
- Key: large area light from upper-front-left, soft (low intensity, big size).
- Fill: dim ambient via HDRI or a second area light, top-down, to lift shadows.
- Soft contact shadow underneath each atom (ambient occlusion, ~0.5–1.0 strength).
- No hard cast shadows — the look is studio-soft, not stage-spotlight.

### Background
- Pure white. Either world background = white emissive, OR transparent PNG (preferred — composited later).

### Atom rendering
- Spheres: smooth (subdivision 3+), no facets visible.
- Material: PBR principled BSDF.
  - Base color from palette below.
  - Roughness ≈ 0.35 (matte but with a soft highlight).
  - Specular default (~0.5).
  - No metallic (even for metal atoms — paper convention is non-metallic shading).
  - No transmission.
- Atom radii: covalent radii × ~0.6 (so they touch but don't fully overlap). H is small but visible.
- No bonds drawn between atoms — just spheres.

### Color palette (CatDT-style, NOT default Jmol/CPK)

| Element | Hex       | Notes                                    |
|---------|-----------|------------------------------------------|
| Pt      | `#EFE4C4` | Cream / pale tan (lighter than Jmol)     |
| Sn      | `#506C7C` | Dark slate teal                          |
| Mn      | `#EBE0C0` | Cream, similar to Pt                     |
| Ni      | `#3FBF44` | Saturated vivid green                    |
| Ga      | `#3FBF44` | Same green as Ni                         |
| In      | `#B57878` | Dusty rose / pink                        |
| Pd      | `#7E7E8A` | Steel grey-blue                          |
| Cu      | `#3FBF44` | Same vivid green (per ref)               |
| Zr      | `#3FBF44` | Same vivid green (per ref)               |
| Ti      | `#C8C8CC` | Light grey                               |
| Co      | `#E89AAB` | Pink / salmon                            |
| Fe      | `#9F4F4F` | Maroon                                   |
| Zn      | `#7868A8` | Muted purple                             |
| V       | `#B0B0B4` | Mid grey                                 |
| Mo      | `#5566AA` | Slate blue                               |
| O       | `#E03030` | Saturated red, small radius              |
| N       | `#3868D8` | Saturated blue                           |
| C       | `#383838` | Charcoal                                 |
| H       | `#FFFFFF` | White, very small                        |

Notes:
- The reference uses the same vivid green for Ni, Ga, Cu, Zr — i.e. the "active metal in this cell" gets green, regardless of element. A per-cell override (so the highlighted species reads green and the support reads its true color) is left as an optional refinement.
- Mo3Pd, Pd3Cu (CMU20 cases 01–04) are not in the reference panel; pick palette by analogy (Mo slate blue, Pd steel grey, Cu green per ref).

### Render settings
- Engine: Cycles (not Eevee — we want true GI for the soft look).
- Samples: 256+ (final), 64 (preview).
- Denoiser: ON (OpenImageDenoise).
- Resolution: 1024×1024 per cell (we crop+downscale in figure assembly).
- Output: PNG with alpha (transparent background).
- Color space: sRGB / Filmic OFF (Standard view transform — papers want literal colors, not cinematic).

## Render Input Manifest

Generate the current Panel B manifest with:

```bash
.venv/bin/python research/agent_eval/render_panel_b_assets.py
```

The generated `manifest.csv` records each selected structure, its source
`result_dir`, and the rendered PNG path. It is written under
`research/figures/panel_b_structure_assets/panel_b_assets_20260429/` when the
asset script is run locally.
