#!/usr/bin/env python3
"""Render reproducible draft ablation panels for Figure 2.

The final paper figure can be redesigned in Illustrator/PowerPoint, but this
script keeps the data transformations, axis convention, and failure counts
auditable from committed CSV files.
"""

from __future__ import annotations

import csv
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
OUT = ROOT / "output"

BACKEND_ORDER = [
    "openrouter_gemini25pro_mace_mp0_small",
    "openai_gpt54_mace_mp0_small",
    "anthropic_claude_sonnet46_mace_mp0_small",
    "openrouter_grok4_mace_mp0_small",
]
BACKEND_LABEL = {
    "openrouter_gemini25pro_mace_mp0_small": "Gemini 2.5 Pro",
    "openai_gpt54_mace_mp0_small": "GPT-5.4",
    "anthropic_claude_sonnet46_mace_mp0_small": "Claude Sonnet 4.6",
    "openrouter_grok4_mace_mp0_small": "Grok-4",
}
BACKEND_COLOR = {
    "openrouter_gemini25pro_mace_mp0_small": "#7EA6E0",
    "openai_gpt54_mace_mp0_small": "#F28B82",
    "anthropic_claude_sonnet46_mace_mp0_small": "#F9C80E",
    "openrouter_grok4_mace_mp0_small": "#45B97C",
}
VARIANT_ORDER = ["single_shot", "no_slip", "no_forbid", "no_termination"]
VARIANT_LABEL = {
    "single_shot": "1-Shot",
    "no_slip": "w/o Slip",
    "no_forbid": "w/o Forbid",
    "no_termination": "w/o Term",
}


def canonical_dataset_name(name: str) -> str:
    return name


def load_failure_counts() -> dict[tuple[str, str], int]:
    path = DATA / "failure_audit.csv"
    counts: dict[tuple[str, str], int] = {}
    if not path.exists():
        return counts
    with path.open(newline="") as fh:
        for row in csv.DictReader(fh):
            if row.get("natural_failure") != "True":
                continue
            key = (canonical_dataset_name(row["dataset"]), row["variant"])
            counts[key] = counts.get(key, 0) + 1
    return counts


def plot_dataset(ax: plt.Axes, df: pd.DataFrame, dataset: str, failures: dict[tuple[str, str], int]) -> None:
    value_col = "delta_E_variant_minus_full_eV"

    variants = [variant for variant in VARIANT_ORDER if variant in set(df["variant"])]
    x_positions = range(len(variants))
    offsets = [-0.24, -0.08, 0.08, 0.24]

    ymax = max(0.12, df[value_col].astype(float).max())
    ymin = min(-0.12, df[value_col].astype(float).min())
    pad = max(0.10, 0.08 * (ymax - ymin))
    ax.set_ylim(ymin - pad, ymax + pad)

    for xi, variant in zip(x_positions, variants):
        for offset, backend in zip(offsets, BACKEND_ORDER):
            subset = df[(df["variant"] == variant) & (df["backend"] == backend)]
            if subset.empty:
                continue
            x = xi + offset
            vals = subset[value_col].astype(float).to_numpy()
            ax.scatter(
                [x] * len(vals),
                vals,
                s=20,
                color=BACKEND_COLOR[backend],
                alpha=0.45,
                edgecolors="none",
            )
            ax.boxplot(
                vals,
                positions=[x],
                widths=0.13,
                showfliers=False,
                patch_artist=True,
                boxprops={"facecolor": BACKEND_COLOR[backend], "alpha": 0.18, "edgecolor": BACKEND_COLOR[backend]},
                medianprops={"color": "black", "linewidth": 1.2},
                whiskerprops={"color": BACKEND_COLOR[backend]},
                capprops={"color": BACKEND_COLOR[backend]},
            )

    ax.axhline(0.0, color="black", linewidth=1.0, linestyle="--")
    ax.axhline(0.05, color="#555555", linewidth=0.8, linestyle=":")
    ax.axhline(-0.05, color="#555555", linewidth=0.8, linestyle=":")
    ax.set_xticks(list(x_positions))
    ax.set_xticklabels([VARIANT_LABEL[v] for v in variants])
    ax.set_ylabel("Energy error (eV)")
    ax.set_title(dataset)
    ax.grid(axis="y", alpha=0.25)
    ax.set_xlim(-0.5, max(len(variants) - 0.5, 0.5))
    ax.tick_params(axis="x", rotation=0)

    dataset_key = canonical_dataset_name(df["dataset"].iloc[0])
    for xi, variant in zip(x_positions, variants):
        count = failures.get((dataset_key, variant), 0)
        if count:
            ax.text(xi, ymax + 0.35 * pad, f"{count} fail", ha="center", va="bottom", color="#B00020", fontsize=8)
    full_failures = failures.get((dataset_key, "full"), 0)
    if full_failures:
        ax.text(
            0.99,
            0.98,
            f"{full_failures} Full ref fail",
            ha="right",
            va="top",
            transform=ax.transAxes,
            color="#B00020",
            fontsize=8,
        )


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    failures = load_failure_counts()

    plt.rcParams.update(
        {
            "font.size": 9,
            "axes.titlesize": 11,
            "axes.labelsize": 9,
            "xtick.labelsize": 9,
            "ytick.labelsize": 9,
            "legend.fontsize": 9,
        }
    )

    panels = [
        ("CMU20", DATA / "plot_cmu20_delta_points.csv"),
        ("OCD62", DATA / "plot_ocd62_delta_points.csv"),
    ]

    fig, axes = plt.subplots(1, 2, figsize=(10.0, 4.2), sharey=False)
    for ax, (title, path) in zip(axes, panels):
        df = pd.read_csv(path)
        plot_dataset(ax, df, title, failures)

    handles = [
        plt.Line2D([0], [0], marker="o", linestyle="", color=BACKEND_COLOR[b], label=BACKEND_LABEL[b], markersize=7)
        for b in BACKEND_ORDER
    ]
    fig.legend(handles=handles, loc="upper center", bbox_to_anchor=(0.5, 1.02), ncol=4, frameon=False)
    fig.suptitle("Ablation Energy Error by LLM Backend", y=0.94, fontsize=13)
    fig.tight_layout(rect=(0, 0, 1, 0.88))
    fig.savefig(OUT / "figure2_ablation_draft.png", dpi=300, bbox_inches="tight")
    fig.savefig(OUT / "figure2_ablation_draft.pdf", bbox_inches="tight")


if __name__ == "__main__":
    main()
