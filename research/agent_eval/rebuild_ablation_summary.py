"""Rebuild ablation summary from existing result.json files on disk.

Unlike run_ablation.py (which generates summaries only from the current
execution run), this script scans the ablation output directory and
rebuilds summary CSV + stats JSON from all persisted result.json files.
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from scipy.stats import friedmanchisquare, wilcoxon

from research.agent_eval.common import (
    benjamini_hochberg,
    compute_bootstrap_ci,
    rank_biserial_from_differences,
)

SUMMARY_FIELDS = [
    "case_id",
    "variant",
    "best_energy",
    "delta_vs_full",
    "iterations",
    "wasted_iterations",
    "waste_ratio",
    "success",
    "slip_count",
    "dissociation_count",
    "tokens_used",
]


def load_result(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def rebuild(
    ablation_dir: Path,
    variants: List[str],
    case_ids: List[str],
    one_shot_dir: Optional[Path] = None,
) -> tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """Scan ablation_dir/{variant}/{case_id}/result.json and rebuild summaries."""

    full_energy: Dict[str, float] = {}
    variant_energies: Dict[str, List[float]] = {v: [] for v in variants}
    rows: List[Dict[str, Any]] = []

    # First pass: collect full energies
    for cid in case_ids:
        rpath = ablation_dir / "full" / cid / "result.json"
        if rpath.exists():
            r = load_result(rpath)
            e = r.get("best_energy_eV")
            if isinstance(e, (int, float)):
                full_energy[cid] = float(e)

    # If one_shot/single_shot is not in ablation dir, try one_shot_dir.
    one_shot_energy: Dict[str, float] = {}
    if one_shot_dir:
        for cid in case_ids:
            rpath = one_shot_dir / cid / "result.json"
            if rpath.exists():
                r = load_result(rpath)
                e = r.get("best_energy_eV")
                if isinstance(e, (int, float)):
                    one_shot_energy[cid] = float(e)

    for variant in variants:
        for cid in case_ids:
            if variant in {"one_shot", "single_shot"}:
                rpath = ablation_dir / variant / cid / "result.json"
                if not rpath.exists():
                    alternate = "single_shot" if variant == "one_shot" else "one_shot"
                    rpath = ablation_dir / alternate / cid / "result.json"
                if not rpath.exists() and one_shot_dir:
                    rpath = one_shot_dir / cid / "result.json"
            else:
                rpath = ablation_dir / variant / cid / "result.json"

            if not rpath.exists():
                rows.append({
                    "case_id": cid,
                    "variant": variant,
                    "best_energy": None,
                    "delta_vs_full": None,
                    "iterations": 0,
                    "wasted_iterations": 0,
                    "waste_ratio": 0,
                    "success": False,
                    "slip_count": 0,
                    "dissociation_count": 0,
                    "tokens_used": 0,
                })
                continue

            r = load_result(rpath)
            e = r.get("best_energy_eV")
            iters = r.get("iteration_count", 0)
            calc_fail = r.get("calc_failure_count", 0)

            delta = None
            if cid in full_energy and isinstance(e, (int, float)):
                delta = float(e) - full_energy[cid]

            rows.append({
                "case_id": cid,
                "variant": variant,
                "best_energy": e,
                "delta_vs_full": delta,
                "iterations": iters,
                "wasted_iterations": calc_fail,
                "waste_ratio": (calc_fail / iters) if iters else 0,
                "success": r.get("status") == "success",
                "slip_count": r.get("chemical_slip_count", 0),
                "dissociation_count": r.get("dissociation_count", 0),
                "tokens_used": r.get("total_input_tokens", 0) + r.get("total_output_tokens", 0),
            })
            if isinstance(e, (int, float)):
                variant_energies[variant].append(float(e))

    # Stats
    stats: Dict[str, Any] = {"friedman": None, "pairwise": {}, "bh_fdr": {}}
    n = len(case_ids)
    matrix = [variant_energies[v] for v in variants if len(variant_energies[v]) == n]
    if len(matrix) >= 3 and len({tuple(s) for s in matrix}) > 1:
        fr = friedmanchisquare(*matrix)
        stats["friedman"] = {"statistic": float(fr.statistic), "p_value": float(fr.pvalue)}

    raw_p: Dict[str, Optional[float]] = {}
    full_scores = variant_energies.get("full", [])
    for variant in variants:
        if variant == "full":
            continue
        other = variant_energies.get(variant, [])
        if len(full_scores) == n and len(other) == n:
            deltas = [o - f for f, o in zip(full_scores, other)]
            if any(d != 0 for d in deltas):
                test = wilcoxon(deltas, alternative="two-sided", zero_method="wilcox")
                stats["pairwise"][variant] = {
                    "statistic": float(test.statistic),
                    "p_value": float(test.pvalue),
                    "rank_biserial": rank_biserial_from_differences(deltas),
                    "bootstrap_ci": compute_bootstrap_ci(deltas),
                }
                raw_p[variant] = float(test.pvalue)
            else:
                stats["pairwise"][variant] = {
                    "statistic": 0.0,
                    "p_value": 1.0,
                    "rank_biserial": 0.0,
                    "bootstrap_ci": compute_bootstrap_ci(deltas),
                }
                raw_p[variant] = 1.0
        else:
            stats["pairwise"][variant] = None
            raw_p[variant] = None
    stats["bh_fdr"] = benjamini_hochberg(raw_p)

    return rows, stats


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Rebuild ablation summary from result.json files.")
    parser.add_argument("--ablation-dir", required=True, help="Ablation output directory")
    parser.add_argument("--one-shot-dir", default=None, help="One-shot results directory fallback")
    parser.add_argument("--cases", default="01,02,09,14,19")
    parser.add_argument("--variants", default="full,no_slip,no_forbid,no_termination,one_shot")
    args = parser.parse_args(argv)

    ablation_dir = Path(args.ablation_dir)
    one_shot_dir = Path(args.one_shot_dir) if args.one_shot_dir else None
    case_ids = [c.strip().zfill(2) for c in args.cases.split(",")]
    variants = [v.strip() for v in args.variants.split(",")]

    rows, stats = rebuild(ablation_dir, variants, case_ids, one_shot_dir)

    summary_path = ablation_dir / "ablation_summary.csv"
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    with summary_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=SUMMARY_FIELDS)
        writer.writeheader()
        writer.writerows(rows)

    stats_path = ablation_dir / "ablation_stats.json"
    with stats_path.open("w", encoding="utf-8") as f:
        json.dump(stats, f, indent=2, ensure_ascii=False)

    print(f"Summary: {summary_path}")
    print(f"Stats:   {stats_path}")

    # Print human-readable table
    print(f"\n{'case':>6s}", end="")
    for v in variants:
        print(f"  {v:>16s}", end="")
    print()
    for cid in case_ids:
        print(f"{cid:>6s}", end="")
        for v in variants:
            match = [r for r in rows if r["case_id"] == cid and r["variant"] == v]
            if match and match[0]["best_energy"] is not None:
                print(f"  {match[0]['best_energy']:>16.4f}", end="")
            else:
                print(f"  {'FAIL':>16s}", end="")
        print()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
