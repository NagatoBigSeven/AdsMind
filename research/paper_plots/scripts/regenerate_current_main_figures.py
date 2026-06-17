#!/usr/bin/env python3
"""Regenerate current manuscript Figure 2 and Figure 3 from paper-facing data."""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import matplotlib.transforms as mtransforms
import numpy as np
import pandas as pd
from matplotlib.lines import Line2D
from matplotlib.offsetbox import AnnotationBbox, OffsetImage
from matplotlib.patches import Patch, Polygon
from matplotlib.colors import to_rgba


ROOT = Path(__file__).resolve().parents[3]


def setup_style() -> None:
    plt.style.use("default")
    plt.rcParams.update(
        {
            "font.family": "Arial",
            "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans"],
            "axes.spines.top": False,
            "axes.spines.right": False,
            "axes.labelsize": 12,
            "axes.titlesize": 13,
            "xtick.labelsize": 10,
            "ytick.labelsize": 10,
            "figure.facecolor": "white",
            "axes.facecolor": "white",
        }
    )


def save_all(fig: plt.Figure, paths: list[Path]) -> None:
    for path in paths:
        path.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(path, dpi=300, bbox_inches="tight")
        print(f"saved {path.relative_to(ROOT)}")


def regenerate_dft_validation() -> None:
    systems = [
        "H\nMo$_3$Pd(111)",
        "NNH\nMo$_3$Pd(111)",
        "H\nCuPd$_3$(111)",
        "NNH\nCuPd$_3$(111)",
        "OH\nPt(111)",
        "OH\nPt(100)",
    ]
    adsorb_agent = np.array([-0.764, -1.265, -0.380, 0.745, 0.990, 0.991])
    vasp = np.array([-1.122, -3.066, -0.319, -0.996, -2.594, -2.511])
    adsmind = np.array(
        [
            -3.627323865890503,
            -4.769039154052734,
            -3.351963758468628,
            -2.2549095153808594,
            -1.9912567138671875,
            -2.7095260620117188,
        ]
    )
    mae_aa = np.mean(np.abs(adsorb_agent - vasp))
    mae_am = np.mean(np.abs(adsmind - vasp))

    x = np.arange(len(systems))
    width = 0.25
    fig, ax = plt.subplots(figsize=(8, 4.6))
    colors = {
        "aa": "#CA9161",
        "vasp": "#6C6C6C",
        "am": "#0173B2",
    }
    ax.bar(
        x - width,
        adsorb_agent,
        width,
        label="Adsorb-Agent (EquiformerV2)",
        color=colors["aa"],
        edgecolor="white",
        linewidth=0.5,
        zorder=3,
    )
    ax.bar(
        x,
        vasp,
        width,
        label="DFT/PBE (VASP)",
        color=colors["vasp"],
        edgecolor="white",
        linewidth=0.5,
        hatch="//",
        zorder=3,
    )
    ax.bar(
        x + width,
        adsmind,
        width,
        label="AdsMind (MACE-MP-0 small)",
        color=colors["am"],
        edgecolor="white",
        linewidth=0.5,
        zorder=3,
    )

    for idx in [3, 4, 5]:
        cx = x[idx] - width
        cy = max(0, adsorb_agent[idx]) + 0.45
        ax.scatter(
            cx,
            cy,
            marker="X",
            s=120,
            color="#CC3333",
            edgecolors="white",
            linewidths=0.6,
            zorder=10,
        )
        ax.annotate(
            "sign mismatch",
            (cx, max(0, adsorb_agent[idx]) + 0.9),
            ha="center",
            fontsize=7.5,
            color="#CC3333",
            fontweight="bold",
        )

    ax.axhline(0, color="black", linewidth=0.8, zorder=2)
    ax.set_ylabel("Adsorption Energy (eV)", fontweight="bold", fontsize=13)
    ax.set_xticks(x)
    ax.set_xticklabels(systems, fontsize=10.5)
    ax.set_ylim(-6.5, 2.5)
    ax.grid(True, axis="y", alpha=0.25, linestyle="--", linewidth=0.65)
    ax.grid(False, axis="x")
    ax.set_axisbelow(True)

    ref_dir = ROOT / "research/paper_plots/figure5/reference"
    ref_images = [
        "01_Mo3Pd_111_H_template_v6.png",
        "02_Mo3Pd_111_NNH.png",
        "03_Pd3Cu_111_H.png",
        "04_Pd3Cu_111_NNH.png",
        "09_Pt_111_OH.png",
        "10_Pt_100_OH.png",
    ]
    transform = mtransforms.blended_transform_factory(ax.transData, ax.transAxes)
    for i, xi in enumerate(x):
        img_path = ref_dir / ref_images[i]
        if img_path.exists():
            img = plt.imread(img_path)
            image = OffsetImage(img, zoom=0.08)
            ab = AnnotationBbox(
                image,
                (xi, -0.15),
                xycoords=transform,
                frameon=False,
                box_alignment=(0.5, 1.0),
            )
            ax.add_artist(ab)

    ax.legend(frameon=False, fontsize=8.5, loc="lower left")
    ax.text(
        0.02,
        0.95,
        f"MAE vs DFT/PBE:\nAdsorb-Agent: {mae_aa:.2f} eV\nAdsMind: {mae_am:.2f} eV",
        transform=ax.transAxes,
        ha="left",
        va="top",
        fontsize=9,
        bbox=dict(boxstyle="round,pad=0.35", facecolor="white", alpha=0.88, edgecolor="none"),
    )
    fig.subplots_adjust(bottom=0.24)
    save_all(
        fig,
        [
            ROOT / "research/paper_plots/figure5/figure5_vasp_validation.png",
            ROOT / "overleaf/images/figure2_vasp_validation.png",
        ],
    )
    plt.close(fig)


def load_cmu_ablation() -> pd.DataFrame:
    adsmind_dir = ROOT / "research/results/basic_experiments/cmu20/adsmind"
    backend_dirs = [
        "gpt54_mace_mp0_small",
        "grok4_mace_mp0_small",
        "gemini25pro_mace_mp0_small",
        "claude_sonnet46_mace_mp0_small",
    ]
    frames = [pd.read_csv(adsmind_dir / b / "all_variants_summary.csv") for b in backend_dirs]
    df = pd.concat(frames, ignore_index=True)
    df["case_id"] = df["case_id"].astype(str).str.strip().str.zfill(2)
    df["best_energy"] = pd.to_numeric(df["best_energy"], errors="coerce")
    df["success_bool"] = df["success"].astype(str).str.upper().eq("TRUE")
    df.loc[~df["success_bool"], "best_energy"] = np.nan
    return df


def trapezoid_panel(ax: plt.Axes, df: pd.DataFrame) -> None:
    full = df[df["variant"] == "full"][["backend_key", "case_id", "best_energy"]].rename(
        columns={"best_energy": "full_energy"}
    )
    merged = df.merge(full, on=["backend_key", "case_id"], how="left")
    merged["delta"] = merged["best_energy"] - merged["full_energy"]

    backend_order = ["gemini", "gpt", "claude", "grok"]
    backend_labels = {
        "gemini": "Gemini 2.5 Pro",
        "gpt": "GPT-5.4",
        "claude": "Claude Sonnet 4.6",
        "grok": "Grok-4",
    }
    backend_colors = {
        "gemini": "#7EA6E0",
        "gpt": "#F08A7B",
        "claude": "#FFCC00",
        "grok": "#43B988",
    }
    variant_order = [("one_shot", "1-Shot"), ("no_termination", "w/o Term")]
    x_base = np.arange(1, len(variant_order) + 1)
    offsets = np.linspace(-0.27, 0.27, len(backend_order))
    box_half_width = 0.065
    neck_half_width = 0.6 * box_half_width
    rng = np.random.default_rng(2026)

    max_val = -np.inf
    for offset, backend in zip(offsets, backend_order):
        color = backend_colors[backend]
        values_by_variant = []
        for variant, _ in variant_order:
            values = (
                merged[(merged["backend_key"] == backend) & (merged["variant"] == variant)]["delta"]
                .dropna()
                .to_numpy(float)
            )
            if len(values):
                max_val = max(max_val, float(np.nanmax(values)))
            values_by_variant.append(values)

        x_positions = x_base + offset
        ax.boxplot(
            values_by_variant,
            positions=x_positions,
            widths=2.0 * box_half_width,
            whis=(0, 100),
            patch_artist=True,
            showfliers=False,
            boxprops={"facecolor": "none", "edgecolor": "none", "linewidth": 0.0},
            whiskerprops={"color": color, "linewidth": 1.2},
            capprops={"color": color, "linewidth": 1.2},
            medianprops={"color": color, "linewidth": 0.0},
        )
        for pos, values in zip(x_positions, values_by_variant):
            if len(values) == 0:
                continue
            q1 = float(np.nanpercentile(values, 25))
            q3 = float(np.nanpercentile(values, 75))
            med = float(np.nanmedian(values))
            mean = float(np.nanmean(values))
            lower = Polygon(
                [
                    (pos - box_half_width, q1),
                    (pos + box_half_width, q1),
                    (pos + neck_half_width, med),
                    (pos - neck_half_width, med),
                ],
                closed=True,
                facecolor=to_rgba(color, 0.22),
                edgecolor=color,
                linewidth=1.4,
                zorder=3.1,
            )
            upper = Polygon(
                [
                    (pos - neck_half_width, med),
                    (pos + neck_half_width, med),
                    (pos + box_half_width, q3),
                    (pos - box_half_width, q3),
                ],
                closed=True,
                facecolor=to_rgba(color, 0.22),
                edgecolor=color,
                linewidth=1.4,
                zorder=3.1,
            )
            ax.add_patch(lower)
            ax.add_patch(upper)
            ax.hlines(med, pos - neck_half_width, pos + neck_half_width, color=color, linewidth=2, zorder=3.8)
            ax.scatter(pos, mean, marker="D", s=70, facecolor="white", edgecolor=color, linewidth=1.4, zorder=4)
            jitter = rng.uniform(-0.028, 0.028, size=len(values))
            ax.scatter(
                np.full_like(values, pos, dtype=float) + jitter,
                values,
                s=28,
                color=color,
                edgecolors="white",
                linewidths=0.45,
                alpha=0.6,
                zorder=5,
            )

    ax.axhline(0, color="black", linestyle="--", linewidth=1.1, alpha=0.9, zorder=2)
    ax.axhline(0.05, color="black", linestyle=":", linewidth=1.1, alpha=0.9, zorder=2)
    ax.axhline(-0.05, color="black", linestyle=":", linewidth=1.1, alpha=0.9, zorder=2)

    handles = [Patch(facecolor=backend_colors[b], edgecolor="none", label=backend_labels[b]) for b in backend_order]
    ax.legend(handles=handles, loc="upper center", bbox_to_anchor=(0.5, 1.15), ncol=4, frameon=False, fontsize=15)
    style_handles = [
        Patch(facecolor=to_rgba("#666666", 0.22), edgecolor="black", linewidth=1.4, label="IQR box"),
        Line2D([0], [0], color="black", linewidth=2.0, label="Median"),
        Line2D([0], [0], marker="D", linestyle="None", markersize=7, markerfacecolor="white", markeredgecolor="black", markeredgewidth=1.2, label="Mean"),
        Line2D([0], [0], marker="o", linestyle="None", markersize=6, markerfacecolor="#666666", markeredgecolor="white", markeredgewidth=0.7, alpha=0.6, label="Individual case"),
        Line2D([0], [0], color="black", linestyle="--", linewidth=1.1, label="Parity (dE = 0 eV)"),
        Line2D([0], [0], color="black", linestyle=":", linewidth=1.1, label="Tolerance band (+/-0.05 eV)"),
    ]
    ax.legend(handles=style_handles, bbox_to_anchor=(1.02, 1.05), loc="upper right", fontsize=11, frameon=False)
    ax.set_xlim(0.5, len(variant_order) + 0.5)
    ax.set_xticks(x_base)
    ax.set_xticklabels([label for _, label in variant_order], fontsize=20)
    for tick, color in zip(ax.get_xticklabels(), ["#CF2526", "#C298C6"]):
        tick.set_color(color)
    ax.set_ylim(-1, 1.2)
    ax.set_yticks(np.arange(-1, 1.21, 0.2))
    if np.isfinite(max_val) and max_val > 1.2:
        ax.text(0.2, 0.95, f"Up to {max_val:.2f} eV", transform=ax.transAxes, fontsize=14, color=backend_colors["grok"], va="top", ha="left")
    ax.set_xlabel("Ablation", fontsize=20, fontweight="bold")
    ax.set_ylabel(r"$\Delta E = E_{\mathrm{variant}} - E_{\mathrm{Full}}$ (eV)", fontsize=20, fontweight="bold")
    ax.grid(True, axis="y", linestyle="--", linewidth=0.65, alpha=0.55)
    ax.grid(False, axis="x")


def radar_panel(ax: plt.Axes, df: pd.DataFrame) -> None:
    full = df[df["variant"] == "full"][["backend_key", "case_id", "best_energy"]].rename(
        columns={"best_energy": "full_energy"}
    )
    merged = df.merge(full, on=["backend_key", "case_id"], how="left")
    merged["delta"] = merged["best_energy"] - merged["full_energy"]

    variants = [("one_shot", "1-Shot", "#CF2526"), ("no_termination", "w/o Term", "#C298C6"), ("full", "Full", "#8D948C")]
    rows = []
    for variant, label, color in variants:
        sub = merged[merged["variant"] == variant].copy()
        mean_delta = 0.0 if variant == "full" else float(sub["delta"].mean())
        success = float(sub["success_bool"].mean())
        pivot = sub.pivot(index="case_id", columns="backend_key", values="best_energy")
        ranges = pivot.max(axis=1, skipna=True) - pivot.min(axis=1, skipna=True)
        ranges = ranges[pivot.count(axis=1) >= 2]
        mean_range = float(ranges.mean())
        agreement = float((ranges <= 0.05).mean())
        rows.append(
            {
                "label": label,
                "color": color,
                "Energy Accuracy": max(0.0, min(1.0, 1 - abs(mean_delta) / 0.25)),
                "Success\nRate": success,
                "Backend Robustness": max(0.0, min(1.0, 1 - mean_range / 0.5)),
                "Cross-LLM\nAgreement": agreement,
            }
        )

    categories = ["Energy Accuracy", "Success\nRate", "Backend Robustness", "Cross-LLM\nAgreement"]
    angles = [n / float(len(categories)) * 2 * np.pi for n in range(len(categories))]
    angles += angles[:1]

    ax.set_theta_offset(np.pi / 2)
    ax.set_theta_direction(-1)
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels([])
    label_rs = [1.28, 1.38, 1.30, 1.18]
    for i, (angle, label) in enumerate(zip(angles[:-1], categories)):
        ha = "center"
        va = "center"
        if i == 0:
            va = "bottom"
        elif i == 2:
            va = "top"
        elif i == 3:
            ha = "center"
        ax.text(angle, label_rs[i], label, fontsize=14, fontweight="bold", ha=ha, va=va)
    ax.set_yticks([0.25, 0.5, 0.75, 1.0])
    ax.set_yticklabels(["0.25", "0.5", "0.75", "1.0"], color="grey", size=8)
    ax.set_ylim(0, 1.15)
    ax.spines["polar"].set_edgecolor("grey")

    label_offsets = {
        "1-Shot": [0.08, 0.08, 0.08, 0.09],
        "w/o Term": [0.08, 0.08, 0.08, 0.08],
        "Full": [0.08, 0.08, 0.08, 0.08],
    }
    angle_offsets = {"1-Shot": -0.04, "w/o Term": 0.05, "Full": 0.0}
    for row in rows:
        values = [row[c] for c in categories]
        values_closed = values + values[:1]
        ax.plot(angles, values_closed, "o-", linewidth=2, label=row["label"], color=row["color"])
        ax.fill(angles, values_closed, alpha=0.10, color=row["color"])
        for j, (angle, val) in enumerate(zip(angles[:-1], values)):
            ax.text(
                angle + angle_offsets[row["label"]],
                val + label_offsets[row["label"]][j],
                f"{val:.2f}",
                ha="center",
                va="center",
                fontsize=9,
                color=row["color"],
                fontweight="bold",
                bbox=dict(boxstyle="round,pad=0.28", facecolor="white", alpha=0.45, edgecolor="none"),
            )
    ax.legend(loc="upper right", bbox_to_anchor=(1.25, 1.05), fontsize=13, frameon=False)


def regenerate_aa20_ablation() -> None:
    df_ablation = load_cmu_ablation()

    fig = plt.figure(figsize=(20, 12), dpi=180)
    gs = fig.add_gridspec(2, 2, height_ratios=[1.0, 1.1], width_ratios=[1.75, 1.05], hspace=0.35, wspace=0.18)
    ax_a = fig.add_subplot(gs[0, :])
    ax_b = fig.add_subplot(gs[1, 0])
    ax_c = fig.add_subplot(gs[1, 1], projection="polar")

    cases = np.arange(1, 21)
    adsmind = pd.read_csv(ROOT / "research/results/processed/si_figures/basic_experiments/cmu20/gpt/full/summary.csv").set_index("case_id")["best_energy"]
    heuristic = pd.read_csv(ROOT / "research/results/processed/si_figures/basic_experiments/cmu20/baselines/heuristic/summary.csv").set_index("case_id")["best_energy"]
    adsorb_agent = pd.read_csv(ROOT / "research/paper_plots/scripts/CMU20_results_in_paper.csv").set_index("case_id")["energy"]
    methods = [
        ("Heuristic", heuristic, "#5DA0CB"),
        ("AdsMind (MACE-MP-0)", adsmind, "#141F48"),
        ("Adsorb-Agent (EquiformerV2)", adsorb_agent, "#FDECAF"),
    ]
    bar_w = 0.18
    for i, (label, series, color) in enumerate(methods):
        values = [float(series.loc[c]) for c in cases]
        x = cases + i * bar_w - len(methods) * bar_w / 2 + bar_w / 2
        ax_a.bar(x, values, width=bar_w, label=label, color=color, alpha=0.88, edgecolor="black", linewidth=0.7)
    ax_a.set_xlabel("Case ID", fontsize=16, fontweight="bold")
    ax_a.set_ylabel("Best Energy (eV)", fontsize=16, fontweight="bold")
    ax_a.set_xticks(cases)
    ax_a.set_xticklabels([f"{i:02d}" for i in cases], fontsize=14)
    ax_a.tick_params(axis="y", labelsize=14)
    ax_a.legend(fontsize=15, loc="lower left", frameon=False)
    ax_a.grid(True, alpha=0.25, linestyle="--", axis="y")
    ax_a.text(-0.05, 1.02, "a", transform=ax_a.transAxes, fontsize=24, fontweight="bold", va="top", ha="left")

    trapezoid_panel(ax_b, df_ablation)
    ax_b.text(-0.09, 1.1, "b", transform=ax_b.transAxes, fontsize=24, fontweight="bold", va="top", ha="left")

    radar_panel(ax_c, df_ablation)
    ax_c.text(-0.2, 1.1, "c", transform=ax_c.transAxes, fontsize=24, fontweight="bold", va="top", ha="left")

    save_all(
        fig,
        [
            ROOT / "research/paper_plots/figure2/figure2_combined_panelabc.png",
            ROOT / "overleaf/images/figure3_combined_panelabc.png",
        ],
    )
    plt.close(fig)


def main() -> None:
    setup_style()
    regenerate_dft_validation()
    regenerate_aa20_ablation()


if __name__ == "__main__":
    main()
