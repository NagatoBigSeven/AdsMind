"""Rebuild baseline summary files from per-case result.json payloads."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np

from research.agent_eval.common import resolve_repo_path


COMMON_FIELDS = [
    "case_id",
    "status",
    "successful",
    "failed",
    "best_energy",
    "mean_energy",
    "std_energy",
    "best_structure_file",
    "wall_clock_sec",
]


def write_csv(path: Path, rows: List[Dict[str, Any]], fieldnames: List[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def valid_energy(value: Any, min_energy: float) -> bool:
    try:
        energy = float(value)
    except (TypeError, ValueError):
        return False
    return bool(np.isfinite(energy) and energy >= min_energy)


def sanitize_result(result: Dict[str, Any], min_energy: float) -> Dict[str, Any]:
    """Drop non-physical successful records and recompute scalar summary fields."""
    records = result.get("records", [])
    for record in records:
        if record.get("status") == "success" and not valid_energy(
            record.get("adsorption_energy_eV"), min_energy
        ):
            record["status"] = "error"
            record["error"] = "abnormal adsorption energy filtered during summary rebuild"

    successes = [
        record
        for record in records
        if record.get("status") == "success"
        and valid_energy(record.get("adsorption_energy_eV"), min_energy)
    ]
    successes.sort(key=lambda item: float(item["adsorption_energy_eV"]))
    energies = [float(record["adsorption_energy_eV"]) for record in successes]

    top_structures = [
        item
        for item in result.get("top_structures", [])
        if valid_energy(item.get("adsorption_energy_eV"), min_energy)
    ]
    top_structures.sort(key=lambda item: float(item["adsorption_energy_eV"]))

    result["status"] = "success" if successes else "failed"
    result["successful"] = len(successes)
    result["failed"] = len(records) - len(successes)
    result["best_energy_eV"] = min(energies) if energies else None
    result["mean_energy_eV"] = float(np.mean(energies)) if energies else None
    result["std_energy_eV"] = float(np.std(energies, ddof=0)) if energies else None
    result["best_structure_file"] = top_structures[0]["structure_file"] if top_structures else ""
    result["top_structures"] = top_structures
    return result


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline-dir", required=True)
    parser.add_argument("--kind", choices=["random", "heuristic"], required=True)
    parser.add_argument("--min-energy", type=float, default=-2000.0)
    args = parser.parse_args(argv)

    baseline_dir = resolve_repo_path(args.baseline_dir)
    case_results = sorted(baseline_dir.glob("*/result.json"))
    rows: List[Dict[str, Any]] = []
    cases: List[Dict[str, Any]] = []
    for result_path in case_results:
        with result_path.open("r", encoding="utf-8") as handle:
            result = json.load(handle)
        result = sanitize_result(result, args.min_energy)
        with result_path.open("w", encoding="utf-8") as handle:
            json.dump(result, handle, indent=2, ensure_ascii=False)
        case_id = result.get("case_id", result_path.parent.name.zfill(2))
        row = {
            "case_id": case_id,
            "status": result.get("status"),
            "successful": result.get("successful"),
            "failed": result.get("failed"),
            "best_energy": result.get("best_energy_eV"),
            "mean_energy": result.get("mean_energy_eV"),
            "std_energy": result.get("std_energy_eV"),
            "best_structure_file": result.get("best_structure_file", ""),
            "wall_clock_sec": result.get("wall_clock_sec"),
        }
        if args.kind == "random":
            row["n_random"] = result.get("n_random")
        else:
            row["n_sites"] = result.get("n_sites")
        rows.append(row)
        cases.append(result)

    if args.kind == "random":
        fieldnames = ["case_id", "n_random", *COMMON_FIELDS[1:]]
    else:
        fieldnames = ["case_id", "n_sites", *COMMON_FIELDS[1:]]
    rows.sort(key=lambda item: str(item["case_id"]).zfill(2))
    cases.sort(key=lambda item: str(item.get("case_id", "")).zfill(2))
    write_csv(baseline_dir / "summary.csv", rows, fieldnames)
    with (baseline_dir / "summary.json").open("w", encoding="utf-8") as handle:
        json.dump({"cases": cases}, handle, indent=2, ensure_ascii=False)
    print(baseline_dir / "summary.csv")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
