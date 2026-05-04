"""Render quick PNG snapshots from DFT-alignment XYZ structures.

These renders are intentionally lightweight handoff artifacts for discussion
with figure authors. They are not a replacement for publication-quality
visualization in VESTA/ASE/PPT/Blender.
"""

from __future__ import annotations

import argparse
import math
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

import matplotlib
import numpy as np
from PIL import Image, ImageDraw

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from mpl_toolkits.mplot3d import Axes3D  # noqa: F401,E402


COLORS: Dict[str, str] = {
    "Mo": "#4C78A8",
    "Pd": "#D18F2F",
    "H": "#E45756",
}

SIZES: Dict[str, int] = {
    "Mo": 60,
    "Pd": 70,
    "H": 150,
}


def read_xyz(path: Path) -> List[Tuple[str, float, float, float]]:
    lines = path.read_text(encoding="utf-8").splitlines()
    atoms: List[Tuple[str, float, float, float]] = []
    for line in lines[2:]:
        parts = line.split()
        if len(parts) < 4:
            continue
        try:
            atoms.append((parts[0], float(parts[1]), float(parts[2]), float(parts[3])))
        except ValueError:
            continue
    return atoms


def render_xyz(path: Path, output: Path) -> bool:
    atoms = read_xyz(path)
    if not atoms:
        return False

    arr = np.array([[x, y, z] for _, x, y, z in atoms])
    center = arr.mean(axis=0)
    fig = plt.figure(figsize=(4.2, 3.2), dpi=180)
    fig.patch.set_alpha(0)
    ax = fig.add_subplot(111, projection="3d")
    ax.set_facecolor((1, 1, 1, 0))

    elements = sorted({symbol for symbol, *_ in atoms if symbol not in COLORS})
    for element in ["Mo", "Pd", *elements, "H"]:
        pts = np.array([[x, y, z] for symbol, x, y, z in atoms if symbol == element])
        if len(pts) == 0:
            continue
        alpha = 0.78 if element != "H" else 1.0
        edge = "#333333" if element == "H" else "#666666"
        ax.scatter(
            pts[:, 0],
            pts[:, 1],
            pts[:, 2],
            s=SIZES.get(element, 45),
            c=COLORS.get(element, "#999999"),
            edgecolors=edge,
            linewidths=0.35,
            alpha=alpha,
            depthshade=True,
        )

    max_range = (arr.max(axis=0) - arr.min(axis=0)).max() * 0.55
    ax.set_xlim(center[0] - max_range, center[0] + max_range)
    ax.set_ylim(center[1] - max_range, center[1] + max_range)
    ax.set_zlim(arr[:, 2].min() - 0.5, arr[:, 2].max() + 1.8)
    ax.view_init(elev=22, azim=-58)
    ax.set_axis_off()
    ax.set_box_aspect((1, 1, 0.8))
    plt.tight_layout(pad=0)
    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output, transparent=True, bbox_inches="tight", pad_inches=0.02)
    plt.close(fig)
    return True


def make_contact_sheet(items: Iterable[Tuple[str, str, Path]], output: Path) -> None:
    thumbs: List[Image.Image] = []
    for backend, stem, path in items:
        image = Image.open(path).convert("RGBA")
        image.thumbnail((280, 220))
        canvas = Image.new("RGBA", (300, 270), (255, 255, 255, 0))
        canvas.alpha_composite(image, ((300 - image.width) // 2, 5))
        draw = ImageDraw.Draw(canvas)
        label = f"{backend}\n{stem.replace('_', ' ')}"
        draw.multiline_text((10, 220), label[:88], fill=(20, 20, 20, 255), spacing=2)
        thumbs.append(canvas)

    if not thumbs:
        return

    cols = 4
    rows = math.ceil(len(thumbs) / cols)
    sheet = Image.new("RGBA", (cols * 300, rows * 270), (255, 255, 255, 0))
    for index, thumb in enumerate(thumbs):
        sheet.alpha_composite(thumb, ((index % cols) * 300, (index // cols) * 270))
    output.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(output)


def render_alignment_package(case_dir: Path) -> int:
    structures_dir = case_dir / "structures"
    snapshots_dir = case_dir / "snapshots"
    created: List[Tuple[str, str, Path]] = []

    for backend_dir in sorted(structures_dir.glob("*")):
        if not backend_dir.is_dir():
            continue
        backend = backend_dir.name
        for xyz_path in sorted(backend_dir.glob("*.xyz")):
            output = snapshots_dir / backend / f"{xyz_path.stem}.png"
            if render_xyz(xyz_path, output):
                created.append((backend, xyz_path.stem, output))

    make_contact_sheet(created, case_dir / "snapshot_contact_sheet.png")
    return len(created)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--case-dir",
        default="research/results/advanced_experiments/case_studies/dft_iteration_alignment/cmu20/case01",
        help="DFT alignment case directory containing structures/.",
    )
    args = parser.parse_args()
    count = render_alignment_package(Path(args.case_dir))
    print(f"created {count} snapshots")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
