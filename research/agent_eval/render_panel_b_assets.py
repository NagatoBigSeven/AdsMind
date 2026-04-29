#!/usr/bin/env python3
"""Render transparent structure thumbnails for manuscript Panel B.

The asset pack is intentionally a visual handoff layer, not a scientific
post-processing step.  It uses relaxed AdsMind Full-run structures from a
single backend/checkpoint combination so the thumbnails are internally
consistent and easy to trace back to result files.
"""

from __future__ import annotations

import csv
import json
import math
import re
import shutil
import zipfile
from dataclasses import dataclass
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = ROOT / "research/results/analysis/panel_b_assets_20260429"

CMU_MANIFEST = ROOT / "research/agent_eval/manifests/cmu_manifest.csv"
OCD_REP50_MANIFEST = (
    ROOT / "research/agent_eval/manifests/ocd_gmae_rep50_manifest.csv"
)

CMU_MAIN_RESULT = ROOT / "research/results/openai_gpt54_ablation_v1/full"
CMU_EXTRA5_RESULT = (
    ROOT / "research/results/cmu_extra5_openai_gpt54_ablation_v1/full"
)
OCD_REP50_RESULT = ROOT / "research/results/ocd_gmae_rep50_openai_gpt54_full_v1/full"

CMU_EXTRA5 = {"03", "06", "07", "08", "11"}
BACKEND_LABEL = "GPT-5.4"
VARIANT_LABEL = "Full"
CHECKPOINT_LABEL = "MACE-MP-0 small"


ADSORBATE_ATOM_COUNTS = {
    "H": 1,
    "NNH": 3,
    "OH": 2,
    "CH2CH2OH": 8,
    "OCHCH3": 7,
    "ONN(CH3)2": 11,
    "[NH2]": 3,
    "[N]=N": 2,
    "[NH]": 2,
    "N": 1,
    "[N]=O": 2,
    "NO": 2,
    "O=N": 2,
    "[CH]=O": 3,
    "C(=O)C": 7,
    "CO": 2,
    "C(C)O": 8,
    "C[O]": 5,
    "[CH2][O]": 4,
    "C([CH2])O": 7,
    "[CH3]": 4,
    "[CH2]C": 6,
}

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


@dataclass
class AssetRow:
    dataset: str
    case_id: str
    surface: str
    adsorbate: str
    reaction_class: str
    selection_bucket: str
    result_dir: Path
    adsorbate_atoms: int
    selected_for_panel_b: bool = False


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="") as handle:
        return list(csv.DictReader(handle))


def formula_count(formula: str) -> int | None:
    if not formula:
        return None
    if formula in ADSORBATE_ATOM_COUNTS:
        return ADSORBATE_ATOM_COUNTS[formula]
    total = 0
    for element, count in re.findall(r"([A-Z][a-z]?)(\d*)", formula):
        total += int(count) if count else 1
    return total or None


def load_result(result_dir: Path) -> dict:
    path = result_dir / "result.json"
    if not path.exists():
        return {}
    with path.open() as handle:
        return json.load(handle)


def best_xyz(result_dir: Path) -> Path:
    artifacts = result_dir / "artifacts"
    result = load_result(result_dir)
    best_file = (
        result.get("best_result", {})
        .get("analysis_json", {})
        .get("best_structure_file", "")
    )
    if best_file:
        candidate = artifacts / Path(best_file).name
        if candidate.exists():
            return candidate

    best_energy = result.get("best_energy_eV")
    best_candidates = sorted(artifacts.glob("BEST_*.xyz"))
    if best_candidates and best_energy is not None:
        def distance_to_result(path: Path) -> float:
            match = re.search(r"_E(-?\d+(?:\.\d+)?)\.xyz$", path.name)
            if not match:
                return math.inf
            return abs(float(match.group(1)) - float(best_energy))

        return min(best_candidates, key=distance_to_result)

    if (artifacts / "final.xyz").exists():
        return artifacts / "final.xyz"
    if best_candidates:
        return best_candidates[0]
    raise FileNotFoundError(f"No XYZ artifact found in {artifacts}")


def parse_xyz(path: Path) -> tuple[list[str], np.ndarray, str]:
    with path.open() as handle:
        lines = handle.readlines()
    natoms = int(lines[0].strip())
    comment = lines[1].strip()
    symbols: list[str] = []
    coords: list[list[float]] = []
    for line in lines[2 : 2 + natoms]:
        parts = line.split()
        symbols.append(parts[0])
        coords.append([float(parts[1]), float(parts[2]), float(parts[3])])
    return symbols, np.asarray(coords, dtype=float), comment


def element_color(symbol: str) -> str:
    if symbol in ELEMENT_COLORS:
        return ELEMENT_COLORS[symbol]
    idx = sum(ord(ch) for ch in symbol) % len(FALLBACK_COLORS)
    return FALLBACK_COLORS[idx]


def render_structure(
    xyz_path: Path,
    out_path: Path,
    adsorbate_atoms: int,
    elev: float = 24.0,
    azim: float = -54.0,
) -> None:
    symbols, coords, _ = parse_xyz(xyz_path)
    if adsorbate_atoms <= 0 or adsorbate_atoms > len(symbols):
        adsorbate_atoms = 0
    ads_idx = set(range(len(symbols) - adsorbate_atoms, len(symbols)))
    slab_idx = [idx for idx in range(len(symbols)) if idx not in ads_idx]

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

    for indices, is_adsorbate in ((slab_idx, False), (sorted(ads_idx), True)):
        if not indices:
            continue
        xs = centered[indices, 0]
        ys = centered[indices, 1]
        zs = centered[indices, 2]
        colors = [element_color(symbols[idx]) for idx in indices]
        if is_adsorbate:
            sizes = [160 if symbols[idx] != "H" else 72 for idx in indices]
            alpha = 1.0
            edge = "#1f2933"
            linewidth = 0.55
        else:
            sizes = [82 + 34 * z_norm[idx] for idx in indices]
            alpha = 0.92
            edge = "#263238"
            linewidth = 0.22
        ax.scatter(
            xs,
            ys,
            zs,
            s=sizes,
            c=colors,
            edgecolors=edge,
            linewidths=linewidth,
            alpha=alpha,
            depthshade=True,
        )

    ranges = centered.max(axis=0) - centered.min(axis=0)
    max_range = max(float(ranges.max()), 1.0)
    mid = (centered.max(axis=0) + centered.min(axis=0)) / 2.0
    pad = max_range * 0.08
    ax.set_xlim(mid[0] - max_range / 2 - pad, mid[0] + max_range / 2 + pad)
    ax.set_ylim(mid[1] - max_range / 2 - pad, mid[1] + max_range / 2 + pad)
    ax.set_zlim(centered[:, 2].min() - pad, centered[:, 2].max() + pad)
    ax.set_box_aspect((1, 1, 0.78))
    ax.set_axis_off()
    plt.subplots_adjust(left=0, right=1, bottom=0, top=1)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, transparent=True, bbox_inches="tight", pad_inches=0.02)
    plt.close(fig)


def contact_sheet(
    rows: list[dict[str, str]],
    out_path: Path,
    title: str,
    columns: int = 5,
    thumb_size: tuple[int, int] = (300, 230),
) -> None:
    font = ImageFont.load_default()
    label_h = 42
    title_h = 46
    rows_n = math.ceil(len(rows) / columns)
    width = columns * thumb_size[0]
    height = title_h + rows_n * (thumb_size[1] + label_h)
    canvas = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(canvas)
    draw.text((16, 14), title, fill="#111111", font=font)
    for i, row in enumerate(rows):
        col = i % columns
        r = i // columns
        x = col * thumb_size[0]
        y = title_h + r * (thumb_size[1] + label_h)
        with Image.open(row["png_path"]).convert("RGBA") as image:
            image.thumbnail((thumb_size[0] - 24, thumb_size[1] - 18))
            px = x + (thumb_size[0] - image.width) // 2
            py = y + (thumb_size[1] - image.height) // 2
            canvas.paste(image, (px, py), image)
        label = f"{row['case_id']} {row['surface']} / {row['adsorbate']}"
        draw.text((x + 10, y + thumb_size[1] + 4), label[:42], fill="#222222", font=font)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(out_path)


def cmu_rows() -> list[AssetRow]:
    rows = []
    for row in read_csv(CMU_MANIFEST):
        case_id = row["case_id"]
        result_root = CMU_EXTRA5_RESULT if case_id in CMU_EXTRA5 else CMU_MAIN_RESULT
        result_dir = result_root / case_id
        surface = Path(row["slab_file"]).stem.removeprefix(f"{case_id}_")
        adsorbate = row["adsorbate_name"]
        count = formula_count(adsorbate)
        if count is None:
            raise ValueError(f"Unknown CMU adsorbate atom count for {adsorbate}")
        rows.append(
            AssetRow(
                dataset="CMU20",
                case_id=case_id,
                surface=surface,
                adsorbate=adsorbate,
                reaction_class=row["reaction_class"],
                selection_bucket="cmu20",
                result_dir=result_dir,
                adsorbate_atoms=count,
                selected_for_panel_b=True,
            )
        )
    return rows


def ocd_rows() -> list[AssetRow]:
    rows = []
    for row in read_csv(OCD_REP50_MANIFEST):
        case_id = row["case_id"]
        rows.append(
            AssetRow(
                dataset="OCD-GMAE rep50",
                case_id=case_id,
                surface=row["surface_formula"],
                adsorbate=row["adsorbate_name"],
                reaction_class=row["reaction_class"],
                selection_bucket=row["selection_bucket"],
                result_dir=OCD_REP50_RESULT / case_id,
                adsorbate_atoms=int(row["adsorbate_atoms"]),
                selected_for_panel_b=False,
            )
        )
    return rows


def select_ocd_examples(rows: list[AssetRow]) -> set[str]:
    selected: list[str] = []
    by_bucket = {"small_n_species": [], "small_organic": []}
    for row in rows:
        if row.selection_bucket in by_bucket:
            by_bucket[row.selection_bucket].append(row)
    # Ten examples from each non-CMU bucket gives a compact, visually diverse
    # coverage panel without treating the 6 CMU-like rep50 rows as new chemistry.
    for bucket in ("small_n_species", "small_organic"):
        seen_adsorbates: set[str] = set()
        for row in by_bucket[bucket]:
            if row.adsorbate in seen_adsorbates and len(seen_adsorbates) < 8:
                continue
            selected.append(row.case_id)
            seen_adsorbates.add(row.adsorbate)
            if len([case for case in selected if case in {r.case_id for r in by_bucket[bucket]}]) >= 10:
                break
        for row in by_bucket[bucket]:
            if row.case_id not in selected:
                selected.append(row.case_id)
            if len([case for case in selected if case in {r.case_id for r in by_bucket[bucket]}]) >= 10:
                break
    return set(selected[:20])


def write_readme(manifest_rows: list[dict[str, str]], selected_count: int) -> None:
    readme = OUT_DIR / "README.md"
    readme.write_text(
        "\n".join(
            [
                "# Panel B Structure Assets 2026-04-29",
                "",
                "Purpose: visual素材包 for the dataset/coverage panel.",
                "",
                "Source convention:",
                "",
                f"- CMU20 thumbnails use {BACKEND_LABEL} {VARIANT_LABEL} relaxed structures from `openai_gpt54_ablation_v1/full` plus `cmu_extra5_openai_gpt54_ablation_v1/full`.",
                f"- OCD-GMAE thumbnails use {BACKEND_LABEL} {VARIANT_LABEL} relaxed structures from `ocd_gmae_rep50_openai_gpt54_full_v1/full`.",
                f"- Force field/checkpoint label for these rendered structures: {CHECKPOINT_LABEL}.",
                "- Individual PNGs use transparent backgrounds.",
                "- Contact sheets are white-background previews for quick review; use individual PNGs for figure assembly.",
                "",
                "Contents:",
                "",
                "- `cmu20/`: 20 CMU benchmark thumbnails.",
                "- `ocd_rep50_all/`: all 50 OCD-GMAE rep50 thumbnails.",
                f"- `ocd_rep50_selected/`: {selected_count} non-CMU-selected OCD-GMAE thumbnails for Panel B coverage.",
                "- `contact_sheets/`: preview sheets.",
                "- `manifest.csv`: source/result path and metadata for every rendered asset.",
                "- `panel_b_assets_20260429.zip`: zip archive for WeChat/group handoff.",
                "",
                "Caveat:",
                "",
                "These are visualization assets from AdsMind relaxed structures, not DFT validation snapshots. Use Bowen's VASP snapshots separately when discussing DFT/PBE validation.",
                "",
            ]
        ),
        encoding="utf-8",
    )


def write_handoff_message() -> None:
    handoff = OUT_DIR / "wechat_handoff_message.md"
    handoff.write_text(
        "\n".join(
            [
                "# WeChat Handoff Message",
                "",
                "老师、师兄，我这边先把 Panel B 可能用到的结构素材整理出来了，包括 CMU20 全部 20 个体系，以及 OCD-GMAE rep50 中 20 个和 CMU 不同的代表体系；另外也保留了 OCD-GMAE rep50 全 50 个体系的单图，方便后面挑选。",
                "",
                "素材包路径：",
                "",
                "`research/results/analysis/panel_b_assets_20260429/panel_b_assets_20260429.zip`",
                "",
                "里面有：",
                "",
                "- `cmu20/`：CMU20 全部 20 个 relaxed adsorption structure，透明背景 PNG。",
                "- `ocd_rep50_selected/`：20 个非 CMU-like 的 OCD-GMAE 代表体系，透明背景 PNG。",
                "- `ocd_rep50_all/`：OCD-GMAE rep50 全 50 个体系，透明背景 PNG。",
                "- `contact_sheets/`：两张预览图，方便快速看整体效果。",
                "- `manifest.csv`：每张图对应的 case、surface、adsorbate、source result path 和 best energy。",
                "",
                f"这里的截图来源统一用 {BACKEND_LABEL} {VARIANT_LABEL} run 的 relaxed structures，力场是 {CHECKPOINT_LABEL}；这些是给 dataset/coverage panel 用的可视化素材，不是博文那边的 DFT validation snapshot。DFT 对齐那部分我等博文 source files 齐了以后再单独整理。",
                "",
            ]
        ),
        encoding="utf-8",
    )


def main() -> None:
    if OUT_DIR.exists():
        shutil.rmtree(OUT_DIR)
    OUT_DIR.mkdir(parents=True)

    cmu = cmu_rows()
    ocd = ocd_rows()
    selected_ocd = select_ocd_examples(ocd)

    manifest_rows: list[dict[str, str]] = []
    contact_cmu: list[dict[str, str]] = []
    contact_ocd_selected: list[dict[str, str]] = []

    for row in cmu + ocd:
        selected = row.dataset == "CMU20" or row.case_id in selected_ocd
        section = "cmu20" if row.dataset == "CMU20" else "ocd_rep50_all"
        xyz_path = best_xyz(row.result_dir)
        result = load_result(row.result_dir)
        png_name = f"{row.case_id}_{row.surface}_{row.adsorbate}".replace("/", "-")
        png_name = re.sub(r"[^A-Za-z0-9_.=-]+", "_", png_name) + ".png"
        png_path = OUT_DIR / section / png_name
        render_structure(xyz_path, png_path, row.adsorbate_atoms)

        record = {
            "dataset": row.dataset,
            "case_id": row.case_id,
            "surface": row.surface,
            "adsorbate": row.adsorbate,
            "reaction_class": row.reaction_class,
            "selection_bucket": row.selection_bucket,
            "selected_for_panel_b": str(selected),
            "backend": BACKEND_LABEL,
            "variant": VARIANT_LABEL,
            "checkpoint": CHECKPOINT_LABEL,
            "best_energy_eV": str(result.get("best_energy_eV", "")),
            "source_result_dir": str(row.result_dir.relative_to(ROOT)),
            "source_xyz": str(xyz_path.relative_to(ROOT)),
            "png_path": str(png_path.relative_to(ROOT)),
        }
        manifest_rows.append(record)

        contact_record = {**record, "png_path": str(png_path)}
        if row.dataset == "CMU20":
            contact_cmu.append(contact_record)
        elif selected:
            selected_dir = OUT_DIR / "ocd_rep50_selected"
            selected_dir.mkdir(exist_ok=True)
            selected_path = selected_dir / png_path.name
            shutil.copy2(png_path, selected_path)
            selected_record = {
                **record,
                "png_path": str(selected_path.relative_to(ROOT)),
            }
            manifest_rows.append({**selected_record, "dataset": "OCD-GMAE selected"})
            contact_ocd_selected.append({**selected_record, "png_path": str(selected_path)})

    manifest_path = OUT_DIR / "manifest.csv"
    with manifest_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(manifest_rows[0].keys()))
        writer.writeheader()
        writer.writerows(manifest_rows)

    contact_sheet(
        contact_cmu,
        OUT_DIR / "contact_sheets/cmu20_contact_sheet.png",
        "CMU20 relaxed adsorption structures",
        columns=5,
    )
    contact_sheet(
        contact_ocd_selected,
        OUT_DIR / "contact_sheets/ocd_rep50_selected_contact_sheet.png",
        "OCD-GMAE rep50 selected non-CMU coverage",
        columns=5,
    )
    write_readme(manifest_rows, len(contact_ocd_selected))
    write_handoff_message()

    zip_path = OUT_DIR / "panel_b_assets_20260429.zip"
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in OUT_DIR.rglob("*"):
            if path == zip_path or path.is_dir():
                continue
            archive.write(path, path.relative_to(OUT_DIR.parent))

    print(f"Wrote {OUT_DIR}")
    print(f"CMU20 images: {len(contact_cmu)}")
    print(f"OCD-GMAE all images: {len(ocd)}")
    print(f"OCD-GMAE selected images: {len(contact_ocd_selected)}")
    print(f"Manifest rows: {len(manifest_rows)}")
    print(f"Zip: {zip_path}")


if __name__ == "__main__":
    main()
