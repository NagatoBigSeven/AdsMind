#!/usr/bin/env python3
"""Render the per-agent ablation dashboard (no_executor / no_validator).

Outputs (regenerated in-place):

- research/paper_plots/figure_per_agent_ablation/figure_A_6dft_cases.png
- research/paper_plots/figure_per_agent_ablation/figure_B_llm_vs_mace_scatter.png
- research/results/advanced_experiments/ablation_and_chemical_slip_diagnostics/
    per_agent_ablation/mae_by_variant.csv

Inputs come from research/results/basic_experiments/cmu20/adsmind/{backend}/
{no_executor,no_validator}/{case}/result.json and the paper-level summary
research/results/basic_experiments/summaries/cmu20_ablation_4backend.csv.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns


ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "research/results/basic_experiments/cmu20/adsmind"
FIG_DIR = ROOT / "research/paper_plots/figure_per_agent_ablation"
MAE_DIR = ROOT / "research/results/advanced_experiments/ablation_and_chemical_slip_diagnostics/per_agent_ablation"
FIG_DIR.mkdir(parents=True, exist_ok=True)
MAE_DIR.mkdir(parents=True, exist_ok=True)

BACKENDS = {
    "GPT-5.4":    "gpt54_mace_mp0_small",
    "Claude 4.6": "claude_sonnet46_mace_mp0_small",
    "Gemini 2.5": "gemini25pro_mace_mp0_small",
    "Grok-4.3":   "grok4_mace_mp0_small",
}

COLORS = {
    "GPT-5.4":    "#0173b2",
    "Claude 4.6": "#de8f05",
    "Gemini 2.5": "#029e73",
    "Grok-4.3":   "#cc78bc",
}

DFT = {
    "01": -1.122, "02": -3.066, "03": -0.319,
    "04": -0.996, "09": -2.594, "10": -2.511,
}
DFT_CASES = list(DFT.keys())
ALL_CASES = [f"{i:02d}" for i in range(1, 21)]

SYS_LABEL = {
    "01": "H\nMo$_3$Pd(111)",
    "02": "NNH\nMo$_3$Pd(111)",
    "03": "H\nCuPd$_3$(111)",
    "04": "NNH\nCuPd$_3$(111)",
    "09": "OH\nPt(111)",
    "10": "OH\nPt(100)",
}


def load_energy(backend_dir: str, variant: str, case_id: str) -> float | None:
    path = BASE / backend_dir / variant / case_id / "result.json"
    if not path.exists():
        return None
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("status") != "success":
        return None
    energy = payload.get("best_energy_eV")
    return float(energy) if isinstance(energy, (int, float)) else None


def collect() -> dict[str, dict[str, dict[str, float | None]]]:
    """Return data[variant][backend][case_id] = energy."""
    data: dict[str, dict[str, dict[str, float | None]]] = {
        "no_executor": {bk: {} for bk in BACKENDS},
        "no_validator": {bk: {} for bk in BACKENDS},
    }
    for bk, bk_dir in BACKENDS.items():
        for variant in data:
            for case in ALL_CASES:
                data[variant][bk][case] = load_energy(bk_dir, variant, case)
    return data


def figure_a(data) -> Path:
    """6-DFT-case grouped bars: DFT | MACE | each backend LLM-pred."""
    plt.style.use("default")
    sns.set_theme(style="ticks", context="paper", font_scale=1.1)
    plt.rcParams.update({
        "font.family": "Arial",
        "axes.labelsize": 14,
        "axes.titlesize": 14,
        "axes.spines.top": False,
        "axes.spines.right": False,
    })

    fig, ax = plt.subplots(figsize=(11, 5.0))
    x = np.arange(len(DFT_CASES))
    # bars: DFT + MACE (we use GPT-5.4 no_validator as the MACE Full reference)
    # + 4 LLM-pred (one per backend)
    bar_width = 0.12
    offsets = np.linspace(-3 * bar_width, 3 * bar_width, 6)

    def _clean(vals):
        return [v if isinstance(v, (int, float)) else np.nan for v in vals]

    dft_vals = _clean([DFT[c] for c in DFT_CASES])
    mace_vals = _clean([data["no_validator"]["GPT-5.4"].get(c) for c in DFT_CASES])
    ax.bar(x + offsets[0], dft_vals, bar_width, label="DFT (VASP/PBE)",
           color="#6C6C6C", hatch="//", edgecolor="white", linewidth=0.5)
    ax.bar(x + offsets[1], mace_vals, bar_width, label="MACE Full (GPT-5.4)",
           color="#999999", edgecolor="white", linewidth=0.5)
    for i, (bk, bk_dir) in enumerate(BACKENDS.items()):
        llm_vals = _clean([data["no_executor"][bk].get(c) for c in DFT_CASES])
        ax.bar(x + offsets[2 + i], llm_vals, bar_width,
               label=f"{bk} LLM-pred", color=COLORS[bk],
               edgecolor="white", linewidth=0.5)

    ax.axhline(0, color="black", linewidth=0.8)
    ax.set_xticks(x)
    ax.set_xticklabels([SYS_LABEL[c] for c in DFT_CASES], fontsize=10)
    ax.set_ylabel("Adsorption energy (eV)", fontweight="bold")
    ax.set_title("LLM-predicted (no_executor) vs MACE vs DFT — 6 reference cases", pad=10)
    ax.grid(axis="y", linestyle="--", alpha=0.3)
    ax.legend(frameon=False, loc="lower right", fontsize=9, ncol=2)

    # annotate MAE box
    mae_lines = ["MAE vs DFT (eV):"]
    for bk in BACKENDS:
        errs = [abs(data["no_executor"][bk][c] - DFT[c])
                for c in DFT_CASES if isinstance(data["no_executor"][bk][c], float)]
        if errs:
            mae_lines.append(f"  {bk}: {sum(errs)/len(errs):.3f}")
    # MACE MAE
    mace_errs = [abs(data["no_validator"]["GPT-5.4"][c] - DFT[c])
                 for c in DFT_CASES if isinstance(data["no_validator"]["GPT-5.4"][c], float)]
    if mace_errs:
        mae_lines.append(f"  MACE Full: {sum(mace_errs)/len(mace_errs):.3f}")
    ax.text(0.01, 0.98, "\n".join(mae_lines),
            transform=ax.transAxes, ha="left", va="top", fontsize=9,
            bbox=dict(boxstyle="round,pad=0.4", facecolor="white",
                      alpha=0.9, edgecolor="#cccccc"))
    plt.tight_layout()
    out = FIG_DIR / "figure_A_6dft_cases.png"
    fig.savefig(out, dpi=200, bbox_inches="tight")
    plt.close(fig)
    return out


def figure_b(data) -> Path:
    """LLM-pred vs MACE for all 20 CMU20 cases, per backend; DFT cases highlighted."""
    plt.style.use("default")
    sns.set_theme(style="ticks", context="paper", font_scale=1.0)
    plt.rcParams.update({
        "font.family": "Arial",
        "axes.spines.top": False,
        "axes.spines.right": False,
    })

    fig, axes = plt.subplots(2, 2, figsize=(10, 9), sharex=True, sharey=True)
    axes = axes.flatten()

    for ax, (bk, bk_dir) in zip(axes, BACKENDS.items()):
        xs, ys, is_dft = [], [], []
        for c in ALL_CASES:
            llm = data["no_executor"][bk].get(c)
            mace = data["no_validator"][bk].get(c)
            if isinstance(llm, float) and isinstance(mace, float):
                xs.append(mace)
                ys.append(llm)
                is_dft.append(c in DFT)

        xs_arr = np.array(xs)
        ys_arr = np.array(ys)
        is_dft_arr = np.array(is_dft)

        # diagonal
        all_vals = np.concatenate([xs_arr, ys_arr])
        lo, hi = float(all_vals.min()) - 0.5, float(all_vals.max()) + 0.5
        ax.plot([lo, hi], [lo, hi], color="#888", linestyle="--", linewidth=1, zorder=1)

        # non-DFT cases
        if (~is_dft_arr).any():
            ax.scatter(xs_arr[~is_dft_arr], ys_arr[~is_dft_arr],
                       s=55, color=COLORS[bk], alpha=0.5,
                       label="other CMU20 (n=14)", edgecolors="white", linewidth=0.6)
        # DFT-anchored cases
        if is_dft_arr.any():
            ax.scatter(xs_arr[is_dft_arr], ys_arr[is_dft_arr],
                       s=110, color=COLORS[bk], alpha=1.0,
                       label="DFT-anchored (n=6)", edgecolors="black", linewidth=1.2,
                       marker="D")

        # case labels on DFT points
        for c in DFT_CASES:
            llm = data["no_executor"][bk].get(c)
            mace = data["no_validator"][bk].get(c)
            if isinstance(llm, float) and isinstance(mace, float):
                ax.annotate(c, (mace, llm), fontsize=7, xytext=(4, 4),
                            textcoords="offset points")

        # Pearson-like spread metric
        if len(xs) > 1:
            r = float(np.corrcoef(xs_arr, ys_arr)[0, 1])
            mae_llm_mace = float(np.mean(np.abs(xs_arr - ys_arr)))
            ax.text(0.03, 0.97, f"{bk}\nn={len(xs)}/20\nMACE vs LLM:  R={r:.2f}, MAE={mae_llm_mace:.2f} eV",
                    transform=ax.transAxes, ha="left", va="top", fontsize=9,
                    bbox=dict(boxstyle="round,pad=0.35", facecolor="white",
                              alpha=0.9, edgecolor=COLORS[bk]))
        ax.set_xlim(lo, hi)
        ax.set_ylim(lo, hi)
        ax.grid(True, linestyle="--", alpha=0.25)
        ax.legend(frameon=False, loc="lower right", fontsize=8)

    for ax in axes[-2:]:
        ax.set_xlabel("MACE Full energy (eV) — no_validator variant", fontweight="bold")
    for ax in (axes[0], axes[2]):
        ax.set_ylabel("LLM-predicted energy (eV) — no_executor", fontweight="bold")
    fig.suptitle("LLM oracle vs MACE oracle — all 20 CMU20 cases, per backend",
                 fontsize=13, fontweight="bold", y=0.995)
    plt.tight_layout()
    out = FIG_DIR / "figure_B_llm_vs_mace_scatter.png"
    fig.savefig(out, dpi=200, bbox_inches="tight")
    plt.close(fig)
    return out


def _load_paper_variants() -> tuple[
    dict[str, dict[str, dict[str, float | None]]],
    dict[str, dict[str, str]],
]:
    """Read full/no_slip/no_forbid/no_termination/one_shot from the paper-level summary CSV.

    Returns (energies_by_variant_backend_case, llm_model_by_variant_backend).
    """
    path = ROOT / "research/results/basic_experiments/summaries/cmu20_ablation_4backend.csv"
    energies: dict[str, dict[str, dict[str, float | None]]] = {}
    models: dict[str, dict[str, str]] = {}
    if not path.exists():
        return energies, models
    key_to_name = {bk_dir: bk for bk, bk_dir in BACKENDS.items()}
    with path.open(encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            bk_name = key_to_name.get(row["backend"])
            if bk_name is None:
                continue
            variant = row["variant"]
            case = row["case_id"].zfill(2)
            try:
                e = float(row["best_energy_eV"])
            except (TypeError, ValueError):
                e = None
            success = (row.get("success") or "").strip().upper() == "TRUE"
            if not success:
                e = None
            energies.setdefault(variant, {}).setdefault(bk_name, {})[case] = e
            llm_model = (row.get("llm_model") or "").strip()
            if llm_model:
                models.setdefault(variant, {})[bk_name] = llm_model
    return energies, models


def _validator_rejection_count(backend_dir: str, variant: str) -> int:
    """Sum validation_attempt_records across all cases for one (backend, variant)."""
    total = 0
    for path in (BASE / backend_dir / variant).glob("*/result.json"):
        try:
            d = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        total += len(d.get("validation_attempt_records", []) or [])
    return total


def _llm_model_for_new_variant(backend_dir: str, variant: str) -> str:
    """Read the llm_model field from one run_config of a new variant on this backend."""
    pattern = BASE / backend_dir / variant
    for case_dir in sorted(pattern.glob("*")):
        config = case_dir / "run_config.public.json"
        if not config.exists():
            config = case_dir / "config.json"
        if config.exists():
            try:
                payload = json.loads(config.read_text(encoding="utf-8"))
                model = payload.get("frozen_config", {}).get("llm_model", "")
                if model:
                    return model
            except json.JSONDecodeError:
                continue
    return ""


def write_mae_summary(data) -> Path:
    """Write a wide per-(backend, variant) summary: n_success, mean_E, MAE vs DFT, MAE vs Full."""
    paper_variants, paper_models = _load_paper_variants()
    # Merge paper variants + new per-agent variants into one dict keyed by variant name.
    all_variants: dict[str, dict[str, dict[str, float | None]]] = dict(paper_variants)
    all_variants["no_executor"] = data["no_executor"]
    all_variants["no_validator"] = data["no_validator"]
    # Per-variant llm_model per backend (read once from a single run_config).
    new_models: dict[str, dict[str, str]] = {"no_executor": {}, "no_validator": {}}
    for variant in ("no_executor", "no_validator"):
        for bk, bk_dir in BACKENDS.items():
            new_models[variant][bk] = _llm_model_for_new_variant(bk_dir, variant)

    variant_order = [
        "full", "no_slip", "no_forbid", "no_termination", "one_shot",
        "no_executor", "no_validator",
    ]

    rows = []
    for bk in BACKENDS:
        full_per_case = (paper_variants.get("full") or {}).get(bk, {})
        for variant in variant_order:
            energies = (all_variants.get(variant) or {}).get(bk, {})
            successes = [(c, e) for c, e in energies.items() if isinstance(e, float)]
            n_success = len(successes)
            mean_e = (
                round(sum(e for _, e in successes) / n_success, 3)
                if n_success
                else None
            )

            dft_errs = [abs(energies[c] - DFT[c])
                        for c in DFT_CASES if isinstance(energies.get(c), float)]
            mae_dft = round(sum(dft_errs) / len(dft_errs), 3) if dft_errs else None

            full_errs = [
                abs(energies[c] - full_per_case[c])
                for c in ALL_CASES
                if isinstance(energies.get(c), float)
                and isinstance(full_per_case.get(c), float)
                and variant != "full"
            ]
            mae_full = round(sum(full_errs) / len(full_errs), 3) if full_errs else None

            if variant in ("no_executor", "no_validator"):
                llm_model = new_models[variant].get(bk, "")
            else:
                llm_model = (paper_models.get(variant) or {}).get(bk, "")
            validator_rejections = _validator_rejection_count(BACKENDS[bk], variant)
            rows.append({
                "backend": bk,
                "variant": variant,
                "llm_model": llm_model,
                "n_success": n_success,
                "mean_E_eV": mean_e if mean_e is not None else "",
                "validator_rejections": validator_rejections,
                "n_dft_overlap": len(dft_errs),
                "mae_vs_dft_eV": mae_dft if mae_dft is not None else "",
                "n_full_overlap": len(full_errs),
                "mae_vs_full_eV": mae_full if mae_full is not None else "",
            })

    out = MAE_DIR / "mae_by_variant.csv"
    with out.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    return out


def main() -> int:
    data = collect()
    fig_a = figure_a(data)
    fig_b = figure_b(data)
    mae_csv = write_mae_summary(data)
    print(fig_a)
    print(fig_b)
    print(mae_csv)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
