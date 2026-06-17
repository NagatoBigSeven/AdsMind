"""Join AdsMind summaries with paper-derived Adsorb-Agent results and run stats."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Dict, List, Optional

from scipy.stats import wilcoxon

from research.agent_eval.common import (
    benjamini_hochberg,
    compute_bootstrap_ci,
    exact_mcnemar,
    rank_biserial_from_differences,
)


def load_csv(path: Path | str) -> List[Dict[str, str]]:
    """Load a CSV file as a list of dicts."""
    with Path(path).open("r", encoding="utf-8", newline="") as handle:
        return [{key: value for key, value in row.items()} for row in csv.DictReader(handle)]


def parse_bool(value: str) -> bool:
    """Parse a common boolean-like string."""
    return str(value).strip().lower() in {"1", "true", "yes", "y", "success"}


def parse_optional_float(value: str) -> Optional[float]:
    """Parse a float-like string, returning None on blanks."""
    if value is None or value == "":
        return None
    return float(value)


def write_csv(path: Path | str, rows: List[Dict[str, object]], fieldnames: List[str]) -> None:
    """Write a CSV file with explicit column order."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def main(argv: Optional[list[str]] = None) -> int:
    """CLI entrypoint for AdsMind vs Adsorb-Agent comparison."""
    parser = argparse.ArgumentParser(description="Compare AdsMind results against Adsorb-Agent paper results.")
    parser.add_argument("--adsmind-summary", required=True, help="Path to AdsMind summary.csv")
    parser.add_argument("--adsorbagent-results", required=True, help="Path to adsorbagent_paper_results.csv")
    parser.add_argument("--output", required=True, help="Output directory for comparison artifacts")
    args = parser.parse_args(argv)

    adsmind_rows = {row["case_id"].zfill(2): row for row in load_csv(args.adsmind_summary)}
    competitor_rows = {row["case_id"].zfill(2): row for row in load_csv(args.adsorbagent_results)}
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    comparison_rows: List[Dict[str, object]] = []
    energy_differences: List[float] = []
    success_pairs = []

    for case_id in sorted(set(adsmind_rows) & set(competitor_rows)):
        ours = adsmind_rows[case_id]
        theirs = competitor_rows[case_id]
        ours_energy = parse_optional_float(ours.get("best_energy_eV", ""))
        theirs_energy = parse_optional_float(theirs.get("adsorbagent_best_energy", ""))
        ours_success = parse_bool(ours.get("status", ""))
        theirs_success = parse_bool(theirs.get("adsorbagent_success", ""))
        success_pairs.append((ours_success, theirs_success))

        energy_diff = None
        winner = "tie"
        if ours_energy is not None and theirs_energy is not None:
            energy_diff = ours_energy - theirs_energy
            energy_differences.append(energy_diff)
            if energy_diff < 0:
                winner = "adsmind"
            elif energy_diff > 0:
                winner = "adsorbagent"

        comparison_rows.append(
            {
                "case_id": case_id,
                "surface": Path(ours["slab_file"]).stem,
                "adsorbate": ours["adsorbate_name"],
                "adsmind_best_energy": ours_energy,
                "adsmind_iterations": int(ours.get("iteration_count") or 0),
                "adsmind_success": ours_success,
                "adsmind_slip_count": int(ours.get("chemical_slip_count") or 0),
                "adsmind_dissociation": int(ours.get("dissociation_count") or 0),
                "adsorbagent_best_energy": theirs_energy,
                "adsorbagent_success": theirs_success,
                "adsorbagent_configs_tested": parse_optional_float(
                    theirs.get("adsorbagent_configs_tested", "")
                )
                or 0.0,
                "energy_diff": energy_diff,
                "winner": winner,
                "notes": theirs.get("notes", ""),
            }
        )

    comparison_path = output_dir / "comparison.csv"
    write_csv(
        comparison_path,
        comparison_rows,
        [
            "case_id",
            "surface",
            "adsorbate",
            "adsmind_best_energy",
            "adsmind_iterations",
            "adsmind_success",
            "adsmind_slip_count",
            "adsmind_dissociation",
            "adsorbagent_best_energy",
            "adsorbagent_success",
            "adsorbagent_configs_tested",
            "energy_diff",
            "winner",
            "notes",
        ],
    )

    stats_payload: Dict[str, object] = {
        "num_cases": len(comparison_rows),
        "wilcoxon": None,
        "mcnemar": exact_mcnemar(success_pairs),
        "rank_biserial": rank_biserial_from_differences(energy_differences),
        "bootstrap_ci": compute_bootstrap_ci(energy_differences),
    }
    if len(energy_differences) >= 2:
        wilcoxon_result = wilcoxon(energy_differences, alternative="two-sided", zero_method="wilcox")
        stats_payload["wilcoxon"] = {
            "statistic": float(wilcoxon_result.statistic),
            "p_value": float(wilcoxon_result.pvalue),
        }

    raw_p_values = {
        "wilcoxon": stats_payload["wilcoxon"]["p_value"] if stats_payload["wilcoxon"] else None,
        "mcnemar": stats_payload["mcnemar"]["p_value"] if stats_payload["mcnemar"] else None,
    }
    stats_payload["benjamini_hochberg"] = benjamini_hochberg(raw_p_values)

    stats_path = output_dir / "comparison_stats.json"
    with stats_path.open("w", encoding="utf-8") as handle:
        json.dump(stats_payload, handle, indent=2, ensure_ascii=False)

    print(comparison_path)
    print(stats_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
