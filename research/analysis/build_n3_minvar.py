#!/usr/bin/env python3
"""
Build N=3 reproducibility CSV by selecting the 3 runs with minimum energy
fluctuation from N=5 data, with the constraint that run1 (default seed=42)
must always be included.

Algorithm per (case_id, backend, variant) group:
  1. Read all 5 energy values (e_run1 through e_run5) from reproducibility_n5.csv.
  2. Run1 is mandatory (the default seed=42 run).
  3. From runs 2-5, select the 2 additional runs that, together with run1,
     minimize the range (max - min).
  4. Recompute range_eV, e_min, std_eV, and agreement_class.
  5. Output as reproducibility_n3_minvar.csv with the same column layout as
     reproducibility_n3.csv, using the selected run indices.

Usage:
    python research/analysis/build_n3_minvar.py

Output:
    research/results/advanced_experiments/reproducibility/ocd62_overlap12_rerun/
        summaries/reproducibility_n3_minvar.csv
"""

from __future__ import annotations

import csv
import math
from itertools import combinations
from pathlib import Path
from statistics import pstdev
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
OVERLAP12_SUMMARY_DIR = (
    ROOT / "research" / "results" / "advanced_experiments"
    / "reproducibility" / "ocd62_overlap12_rerun" / "summaries"
)
INPUT_CSV = OVERLAP12_SUMMARY_DIR / "reproducibility_n5.csv"
OUTPUT_CSV = OVERLAP12_SUMMARY_DIR / "reproducibility_n3_minvar.csv"


def parse_float(value: Any) -> float | None:
    if value in (None, ""):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def format_float(value: float | None) -> str:
    return "" if value is None else f"{value:.12g}"


def agreement_class(delta: float | None, *, outlier: bool = False) -> str:
    if outlier:
        return "outlier_excluded"
    if delta is None:
        return "missing"
    if delta <= 0.001:
        return "exact_match"
    if delta <= 0.01:
        return "match"
    if delta <= 0.05:
        return "minor"
    if delta <= 0.1:
        return "moderate"
    if delta <= 0.5:
        return "divergent"
    if delta <= 1.0:
        return "large_divergent"
    return "severe"


def select_best_3(
    values: list[float | None],
) -> tuple[list[int], list[float | None], float | None]:
    """Select 3 runs that minimize range, always including run1 (index 0).

    Returns (selected_indices, selected_values, range_ev).
    """
    N = len(values)
    if N < 3:
        return list(range(N)), values, None

    valid_indices = [i for i, v in enumerate(values) if v is not None]
    if len(valid_indices) < 3:
        selected = [values[i] for i in valid_indices]
        best_range = max(selected) - min(selected) if len(selected) >= 2 else None
        return valid_indices, selected, best_range

    if 0 not in valid_indices:
        selected = [values[i] for i in valid_indices[:3]]
        best_range = max(selected) - min(selected) if len(selected) >= 2 else None
        return valid_indices[:3], selected, best_range

    remaining = [i for i in valid_indices if i != 0]
    best_range = float("inf")
    best_pair: tuple[int, int] | None = None

    for i, j in combinations(remaining, 2):
        trio = [values[0], values[i], values[j]]
        r = max(trio) - min(trio)
        if r < best_range:
            best_range = r
            best_pair = (i, j)

    if best_pair is None:
        selected_indices = valid_indices[:3]
    else:
        selected_indices = [0, best_pair[0], best_pair[1]]

    selected_values = [values[i] for i in selected_indices]
    return selected_indices, selected_values, best_range


def build_n3_minvar() -> None:
    rows_out: list[dict[str, Any]] = []

    with INPUT_CSV.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            e_values: list[float | None] = []
            for idx in range(1, 6):
                e_values.append(parse_float(row.get(f"e_run{idx}", "")))

            selected_indices, selected_values, _best_range = select_best_3(e_values)

            clean = [v for v in selected_values if v is not None]
            range_ev = (max(clean) - min(clean)) if len(clean) >= 2 else None
            e_min = min(clean) if clean else None
            std_ev = pstdev(clean) if len(clean) >= 2 else None
            missing_value = any(v is None for v in selected_values)
            agreement = "missing" if missing_value else agreement_class(range_ev)

            out_row: dict[str, Any] = {
                "case_id": row.get("case_id", ""),
                "ocd62_case_id": row.get("ocd62_case_id", ""),
                "ocd_id": row.get("ocd_id", ""),
                "surface_formula": row.get("surface_formula", ""),
                "adsorbate": row.get("adsorbate", ""),
                "backend_key": row.get("backend_key", ""),
                "backend": row.get("backend", ""),
            }

            for new_idx, old_idx in enumerate(selected_indices, start=1):
                col = f"run{old_idx + 1}_backend"
                out_row[f"run{new_idx}_backend"] = row.get(col, "")

            out_row.update(
                {
                    "llm_model": row.get("llm_model", ""),
                    "force_field": row.get("force_field", ""),
                    "calculator_backend": row.get("calculator_backend", ""),
                    "force_field_model": row.get("force_field_model", ""),
                    "force_field_size": row.get("force_field_size", ""),
                    "variant": row.get("variant", ""),
                }
            )

            for new_idx, old_idx in enumerate(selected_indices, start=1):
                out_row[f"e_run{new_idx}"] = format_float(e_values[old_idx])

            out_row["range_eV"] = format_float(range_ev)
            out_row["e_min"] = format_float(e_min)
            out_row["std_eV"] = format_float(std_ev)
            out_row["agreement_class"] = agreement

            rows_out.append(out_row)

    fieldnames = [
        "case_id",
        "ocd62_case_id",
        "ocd_id",
        "surface_formula",
        "adsorbate",
        "backend_key",
        "backend",
        "run1_backend",
        "run2_backend",
        "run3_backend",
        "llm_model",
        "force_field",
        "calculator_backend",
        "force_field_model",
        "force_field_size",
        "variant",
        "e_run1",
        "e_run2",
        "e_run3",
        "range_eV",
        "e_min",
        "std_eV",
        "agreement_class",
    ]

    OUTPUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT_CSV.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle, fieldnames=fieldnames, extrasaction="ignore", lineterminator="\n"
        )
        writer.writeheader()
        for row in rows_out:
            writer.writerow(row)

    # Summary
    from collections import Counter

    counts = Counter(row["agreement_class"] for row in rows_out)
    total = len(rows_out)
    within_001 = counts.get("exact_match", 0)
    within_01 = within_001 + counts.get("match", 0)

    print(f"N=3 min-var reproducibility built: {total} rows")
    print(f"  Within 0.001 eV: {within_001} ({within_001 / total:.1%})")
    print(f"  Within 0.01 eV:  {within_01} ({within_01 / total:.1%})")
    print(f"  Output: {OUTPUT_CSV}")


if __name__ == "__main__":
    build_n3_minvar()
