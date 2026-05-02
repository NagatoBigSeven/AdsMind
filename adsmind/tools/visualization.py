"""Deterministic visualization helpers for AdsMind reports."""

from __future__ import annotations

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
    """Render a transparent PNG snapshot of a relaxed adsorption structure."""
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
