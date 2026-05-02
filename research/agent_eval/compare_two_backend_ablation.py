"""Compare two backend ablation summary tables and emit merged artifacts."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from statistics import mean, median
from typing import Any, Dict, Iterable, List, Tuple


COMPARISON_FIELDS = [
    "case_id",
    "variant",
    "left_label",
    "right_label",
    "left_best_energy",
    "right_best_energy",
    "abs_energy_delta",
    "left_delta_vs_full",
    "right_delta_vs_full",
    "abs_delta_vs_full_gap",
    "left_iterations",
    "right_iterations",
    "left_tokens_used",
    "right_tokens_used",
    "token_delta",
    "left_success",
    "right_success",
]


def _load_summary(path: Path) -> Dict[Tuple[str, str], Dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    return {(row["case_id"], row["variant"]): row for row in rows}


def _as_float(value: Any) -> float | None:
    if value in ("", None):
        return None
    return float(value)


def _as_int(value: Any) -> int:
    if value in ("", None):
        return 0
    return int(float(value))


def _as_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes"}


def _summarize_rows(rows: Iterable[Dict[str, Any]]) -> Dict[str, Any]:
    row_list = list(rows)
    deltas = [row["abs_energy_delta"] for row in row_list if row["abs_energy_delta"] is not None]
    if not deltas:
        return {
            "row_count": len(row_list),
            "mean_abs_energy_delta": None,
            "median_abs_energy_delta": None,
            "exact_match_count": 0,
            "within_0_01_count": 0,
            "within_0_05_count": 0,
        }
    return {
        "row_count": len(row_list),
        "mean_abs_energy_delta": mean(deltas),
        "median_abs_energy_delta": median(deltas),
        "exact_match_count": sum(delta == 0.0 for delta in deltas),
        "within_0_01_count": sum(delta <= 0.01 for delta in deltas),
        "within_0_05_count": sum(delta <= 0.05 for delta in deltas),
    }


def compare(
    left_summary: Path,
    right_summary: Path,
    left_label: str,
    right_label: str,
) -> tuple[List[Dict[str, Any]], Dict[str, Any]]:
    left_rows = _load_summary(left_summary)
    right_rows = _load_summary(right_summary)
    if set(left_rows) != set(right_rows):
        missing_left = sorted(set(right_rows) - set(left_rows))
        missing_right = sorted(set(left_rows) - set(right_rows))
        raise ValueError(
            f"Summary key mismatch. Missing on left: {missing_left}; missing on right: {missing_right}"
        )

    comparison_rows: List[Dict[str, Any]] = []
    rows_by_variant: Dict[str, List[Dict[str, Any]]] = {}
    rows_by_case: Dict[str, List[Dict[str, Any]]] = {}

    for case_id, variant in sorted(left_rows):
        left = left_rows[(case_id, variant)]
        right = right_rows[(case_id, variant)]

        left_energy = _as_float(left.get("best_energy"))
        right_energy = _as_float(right.get("best_energy"))
        left_delta = _as_float(left.get("delta_vs_full"))
        right_delta = _as_float(right.get("delta_vs_full"))
        left_tokens = _as_int(left.get("tokens_used"))
        right_tokens = _as_int(right.get("tokens_used"))

        row = {
            "case_id": case_id,
            "variant": variant,
            "left_label": left_label,
            "right_label": right_label,
            "left_best_energy": left_energy,
            "right_best_energy": right_energy,
            "abs_energy_delta": None
            if left_energy is None or right_energy is None
            else abs(left_energy - right_energy),
            "left_delta_vs_full": left_delta,
            "right_delta_vs_full": right_delta,
            "abs_delta_vs_full_gap": None
            if left_delta is None or right_delta is None
            else abs(left_delta - right_delta),
            "left_iterations": _as_int(left.get("iterations")),
            "right_iterations": _as_int(right.get("iterations")),
            "left_tokens_used": left_tokens,
            "right_tokens_used": right_tokens,
            "token_delta": right_tokens - left_tokens,
            "left_success": _as_bool(left.get("success")),
            "right_success": _as_bool(right.get("success")),
        }
        comparison_rows.append(row)
        rows_by_variant.setdefault(variant, []).append(row)
        rows_by_case.setdefault(case_id, []).append(row)

    max_gap_row = max(
        comparison_rows,
        key=lambda row: row["abs_energy_delta"] if row["abs_energy_delta"] is not None else -1.0,
    )
    summary = {
        "left_label": left_label,
        "right_label": right_label,
        "overall": _summarize_rows(comparison_rows),
        "by_variant": {
            variant: _summarize_rows(rows) for variant, rows in sorted(rows_by_variant.items())
        },
        "by_case": {
            case_id: _summarize_rows(rows) for case_id, rows in sorted(rows_by_case.items())
        },
        "largest_disagreement": {
            "case_id": max_gap_row["case_id"],
            "variant": max_gap_row["variant"],
            "abs_energy_delta": max_gap_row["abs_energy_delta"],
        },
    }
    return comparison_rows, summary


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Compare two LLM ablation summary CSV files.")
    parser.add_argument("--left-summary", required=True)
    parser.add_argument("--right-summary", required=True)
    parser.add_argument("--left-label", default="gemini")
    parser.add_argument("--right-label", default="grok")
    parser.add_argument("--output-csv", required=True)
    parser.add_argument("--output-json", required=True)
    args = parser.parse_args(argv)

    rows, summary = compare(
        left_summary=Path(args.left_summary),
        right_summary=Path(args.right_summary),
        left_label=args.left_label,
        right_label=args.right_label,
    )

    output_csv = Path(args.output_csv)
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    with output_csv.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=COMPARISON_FIELDS)
        writer.writeheader()
        writer.writerows(rows)

    output_json = Path(args.output_json)
    output_json.parent.mkdir(parents=True, exist_ok=True)
    with output_json.open("w", encoding="utf-8") as handle:
        json.dump(summary, handle, indent=2, ensure_ascii=False)

    print(f"Comparison CSV: {output_csv}")
    print(f"Comparison JSON: {output_json}")
    print(json.dumps(summary["overall"], indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
