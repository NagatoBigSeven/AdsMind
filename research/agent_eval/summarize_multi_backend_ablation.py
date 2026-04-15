"""Summarize one ablation matrix across multiple backend summary CSV files."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from statistics import mean, median
from typing import Any, Dict, Iterable, List, Optional, Tuple


SUMMARY_FIELDS = [
    "case_id",
    "variant",
    "backend_count",
    "available_backend_count",
    "success_backend_count",
    "failed_backend_count",
    "min_best_energy",
    "max_best_energy",
    "range_best_energy",
    "mean_best_energy",
    "median_best_energy",
    "min_delta_vs_full",
    "max_delta_vs_full",
    "range_delta_vs_full",
    "mean_delta_vs_full",
    "median_delta_vs_full",
    "success_backends",
    "failed_backends",
]


def parse_args(argv: Optional[list[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Aggregate ablation_summary.csv outputs across multiple backends."
    )
    parser.add_argument(
        "--summary",
        action="append",
        required=True,
        help="Repeated label=path argument for each backend summary CSV",
    )
    parser.add_argument("--output-csv", required=True)
    parser.add_argument("--output-json", required=True)
    return parser.parse_args(argv)


def _parse_summary_specs(specs: Iterable[str]) -> list[tuple[str, Path]]:
    parsed: list[tuple[str, Path]] = []
    for spec in specs:
        if "=" not in spec:
            raise ValueError(f"Invalid --summary value {spec!r}; expected label=path")
        label, raw_path = spec.split("=", 1)
        label = label.strip()
        raw_path = raw_path.strip()
        if not label or not raw_path:
            raise ValueError(f"Invalid --summary value {spec!r}; expected label=path")
        parsed.append((label, Path(raw_path)))
    return parsed


def _load_summary(path: Path) -> Dict[Tuple[str, str], Dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    return {(row["case_id"], row["variant"]): row for row in rows}


def _as_float(value: Any) -> Optional[float]:
    if value in ("", None):
        return None
    return float(value)


def _as_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes"}


def _summarize_numeric(values: list[float]) -> dict[str, Optional[float]]:
    if not values:
        return {
            "min": None,
            "max": None,
            "range": None,
            "mean": None,
            "median": None,
        }
    return {
        "min": min(values),
        "max": max(values),
        "range": max(values) - min(values),
        "mean": mean(values),
        "median": median(values),
    }


def summarize(
    summaries: list[tuple[str, Path]],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    loaded = [(label, path, _load_summary(path)) for label, path in summaries]
    all_keys = sorted({key for _, _, summary in loaded for key in summary})

    rows: list[dict[str, Any]] = []
    by_variant: dict[str, list[dict[str, Any]]] = {}
    by_case: dict[str, list[dict[str, Any]]] = {}

    for case_id, variant in all_keys:
        energy_values: list[float] = []
        delta_values: list[float] = []
        success_backends: list[str] = []
        failed_backends: list[str] = []

        row: dict[str, Any] = {
            "case_id": case_id,
            "variant": variant,
            "backend_count": len(loaded),
        }

        for label, _, summary in loaded:
            summary_row = summary.get((case_id, variant))
            if summary_row is None:
                failed_backends.append(label)
                row[f"{label}_best_energy"] = None
                row[f"{label}_delta_vs_full"] = None
                row[f"{label}_success"] = False
                continue

            best_energy = _as_float(summary_row.get("best_energy"))
            delta_vs_full = _as_float(summary_row.get("delta_vs_full"))
            success = _as_bool(summary_row.get("success"))

            row[f"{label}_best_energy"] = best_energy
            row[f"{label}_delta_vs_full"] = delta_vs_full
            row[f"{label}_success"] = success

            if best_energy is not None:
                energy_values.append(best_energy)
            if delta_vs_full is not None:
                delta_values.append(delta_vs_full)

            if success:
                success_backends.append(label)
            else:
                failed_backends.append(label)

        energy_stats = _summarize_numeric(energy_values)
        delta_stats = _summarize_numeric(delta_values)

        row.update(
            {
                "available_backend_count": len(energy_values),
                "success_backend_count": len(success_backends),
                "failed_backend_count": len(failed_backends),
                "min_best_energy": energy_stats["min"],
                "max_best_energy": energy_stats["max"],
                "range_best_energy": energy_stats["range"],
                "mean_best_energy": energy_stats["mean"],
                "median_best_energy": energy_stats["median"],
                "min_delta_vs_full": delta_stats["min"],
                "max_delta_vs_full": delta_stats["max"],
                "range_delta_vs_full": delta_stats["range"],
                "mean_delta_vs_full": delta_stats["mean"],
                "median_delta_vs_full": delta_stats["median"],
                "success_backends": ",".join(success_backends),
                "failed_backends": ",".join(failed_backends),
            }
        )
        rows.append(row)
        by_variant.setdefault(variant, []).append(row)
        by_case.setdefault(case_id, []).append(row)

    def _range_rollup(group_rows: list[dict[str, Any]], key: str) -> dict[str, Any]:
        ranges = [row[key] for row in group_rows if row[key] is not None]
        if not ranges:
            return {"row_count": len(group_rows), "mean_range": None, "max_range": None}
        return {
            "row_count": len(group_rows),
            "mean_range": mean(ranges),
            "max_range": max(ranges),
        }

    largest_energy_gap = max(
        rows,
        key=lambda row: row["range_best_energy"] if row["range_best_energy"] is not None else -1.0,
    ) if rows else None
    largest_delta_gap = max(
        rows,
        key=lambda row: row["range_delta_vs_full"] if row["range_delta_vs_full"] is not None else -1.0,
    ) if rows else None

    summary = {
        "backend_labels": [label for label, _ in summaries],
        "row_count": len(rows),
        "by_variant_best_energy_range": {
            variant: _range_rollup(group_rows, "range_best_energy")
            for variant, group_rows in sorted(by_variant.items())
        },
        "by_case_best_energy_range": {
            case_id: _range_rollup(group_rows, "range_best_energy")
            for case_id, group_rows in sorted(by_case.items())
        },
        "largest_best_energy_gap": None
        if largest_energy_gap is None
        else {
            "case_id": largest_energy_gap["case_id"],
            "variant": largest_energy_gap["variant"],
            "range_best_energy": largest_energy_gap["range_best_energy"],
        },
        "largest_delta_gap": None
        if largest_delta_gap is None
        else {
            "case_id": largest_delta_gap["case_id"],
            "variant": largest_delta_gap["variant"],
            "range_delta_vs_full": largest_delta_gap["range_delta_vs_full"],
        },
    }
    return rows, summary


def main(argv: Optional[list[str]] = None) -> int:
    args = parse_args(argv)
    summaries = _parse_summary_specs(args.summary)
    rows, summary = summarize(summaries)

    fieldnames = list(SUMMARY_FIELDS)
    for label, _ in summaries:
        fieldnames.extend(
            [
                f"{label}_best_energy",
                f"{label}_delta_vs_full",
                f"{label}_success",
            ]
        )

    output_csv = Path(args.output_csv)
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    with output_csv.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    output_json = Path(args.output_json)
    output_json.parent.mkdir(parents=True, exist_ok=True)
    with output_json.open("w", encoding="utf-8") as handle:
        json.dump(summary, handle, indent=2, ensure_ascii=False)

    print(f"Summary CSV: {output_csv}")
    print(f"Summary JSON: {output_json}")
    if summary["largest_best_energy_gap"] is not None:
        print(json.dumps(summary["largest_best_energy_gap"], indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
