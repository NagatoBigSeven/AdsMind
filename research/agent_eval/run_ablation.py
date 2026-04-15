"""Execute the locked ablation matrix for selected AdsMind cases."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Dict, List, Optional

from scipy.stats import friedmanchisquare, wilcoxon

from research.agent_eval.common import (
    ABLATED_VARIANTS,
    benjamini_hochberg,
    compute_bootstrap_ci,
    load_frozen_config,
    load_manifest_map,
    normalise_case_ids,
    resolve_repo_path,
)
from research.agent_eval.run_case import execute_case


def write_csv(path: Path, rows: List[Dict[str, object]], fieldnames: List[str]) -> None:
    """Write a CSV file with explicit field order."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def main(argv: Optional[list[str]] = None) -> int:
    """CLI entrypoint for ablation execution."""
    parser = argparse.ArgumentParser(description="Run AdsMind ablation variants.")
    parser.add_argument("--manifest", required=True, help="Path to cmu_manifest.csv")
    parser.add_argument("--config", required=True, help="Path to frozen_config.json")
    parser.add_argument("--output", required=True, help="Output directory for ablation runs")
    parser.add_argument("--cases", default="01,02,09,14,19", help="Comma-separated case ids")
    parser.add_argument(
        "--variants",
        default="full,no_slip,no_forbid,no_termination,single_shot",
        help="Comma-separated ablation variants",
    )
    parser.add_argument("--api-key", default=None, help="Optional explicit API key override")
    parser.add_argument("--dry-run", action="store_true", help="Use deterministic fake executor")
    args = parser.parse_args(argv)

    manifest = load_manifest_map(args.manifest)
    frozen_config = load_frozen_config(args.config)
    repo_root = Path(__file__).resolve().parents[2]
    output_root = resolve_repo_path(args.output, repo_root=repo_root)
    output_root.mkdir(parents=True, exist_ok=True)

    case_ids = normalise_case_ids(args.cases)
    variants = [item.strip() for item in args.variants.split(",") if item.strip()]

    summary_rows: List[Dict[str, object]] = []
    full_energy_by_case: Dict[str, float] = {}
    variant_energies: Dict[str, List[float]] = {variant: [] for variant in variants}

    for variant in variants:
        if variant not in ABLATED_VARIANTS:
            raise ValueError(f"Unknown ablation variant: {variant}")
        variant_dir = output_root / variant
        for case_id in case_ids:
            case_row = manifest[case_id]
            run = execute_case(
                case_row=case_row,
                frozen_config=frozen_config,
                output_root=variant_dir,
                runtime_overrides=ABLATED_VARIANTS[variant],
                explicit_api_key=args.api_key,
                dry_run=args.dry_run,
                repo_root=repo_root,
            )
            best_energy = run.result.get("best_energy_eV")
            if variant == "full" and isinstance(best_energy, (int, float)):
                full_energy_by_case[case_id] = float(best_energy)
            delta = None
            if case_id in full_energy_by_case and isinstance(best_energy, (int, float)):
                delta = float(best_energy) - full_energy_by_case[case_id]
            summary_rows.append(
                {
                    "case_id": case_id,
                    "variant": variant,
                    "best_energy": best_energy,
                    "delta_vs_full": delta,
                    "iterations": run.result.get("iteration_count", 0),
                    "wasted_iterations": run.result.get("calc_failure_count", 0),
                    "waste_ratio": (
                        (run.result.get("calc_failure_count", 0) / run.result.get("iteration_count", 1))
                        if run.result.get("iteration_count", 0)
                        else 0
                    ),
                    "success": run.result.get("status") == "success",
                    "slip_count": run.result.get("chemical_slip_count", 0),
                    "dissociation_count": run.result.get("dissociation_count", 0),
                    "tokens_used": run.result.get("total_input_tokens", 0) + run.result.get("total_output_tokens", 0),
                }
            )
            if isinstance(best_energy, (int, float)):
                variant_energies[variant].append(float(best_energy))

    summary_path = output_root / "ablation_summary.csv"
    write_csv(
        summary_path,
        summary_rows,
        [
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
        ],
    )

    stats_payload: Dict[str, object] = {"friedman": None, "pairwise": {}, "bh_fdr": {}}
    matrix = [variant_energies[variant] for variant in variants if len(variant_energies[variant]) == len(case_ids)]
    if len(matrix) >= 3 and len({tuple(scores) for scores in matrix}) > 1:
        friedman = friedmanchisquare(*matrix)
        stats_payload["friedman"] = {
            "statistic": float(friedman.statistic),
            "p_value": float(friedman.pvalue),
        }

    raw_p_values: Dict[str, Optional[float]] = {}
    full_scores = variant_energies.get("full", [])
    for variant in variants:
        if variant == "full":
            continue
        other_scores = variant_energies.get(variant, [])
        if len(full_scores) == len(case_ids) and len(other_scores) == len(case_ids):
            deltas = [other - full for full, other in zip(full_scores, other_scores)]
            if any(delta != 0 for delta in deltas):
                test = wilcoxon(deltas, alternative="two-sided", zero_method="wilcox")
                stats_payload["pairwise"][variant] = {
                    "statistic": float(test.statistic),
                    "p_value": float(test.pvalue),
                    "bootstrap_ci": compute_bootstrap_ci(deltas),
                }
                raw_p_values[variant] = float(test.pvalue)
            else:
                stats_payload["pairwise"][variant] = {
                    "statistic": 0.0,
                    "p_value": 1.0,
                    "bootstrap_ci": compute_bootstrap_ci(deltas),
                }
                raw_p_values[variant] = 1.0
        else:
            stats_payload["pairwise"][variant] = None
            raw_p_values[variant] = None
    stats_payload["bh_fdr"] = benjamini_hochberg(raw_p_values)

    stats_path = output_root / "ablation_stats.json"
    with stats_path.open("w", encoding="utf-8") as handle:
        json.dump(stats_payload, handle, indent=2, ensure_ascii=False)

    print(summary_path)
    print(stats_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
