"""Evaluate AdsMind one-shot outputs against OCD-GMAE ground-truth adsorption energies."""

from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path
from statistics import mean, median
from typing import Any, Iterable, Optional


THRESHOLDS = (0.1, 0.2, 0.5)


def parse_args(argv: Optional[list[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Compare one-shot adsorption energies against OCD-GMAE y_relaxed labels."
    )
    parser.add_argument("--manifest", required=True, help="Representative OCD-GMAE manifest CSV")
    parser.add_argument(
        "--summary",
        action="append",
        required=True,
        help="Backend summary in label=path format. Repeat once per backend.",
    )
    parser.add_argument("--output-csv", required=True, help="Merged per-case comparison CSV")
    parser.add_argument("--output-json", required=True, help="JSON metrics report")
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


def _load_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _as_float(value: Any) -> Optional[float]:
    if value in ("", None):
        return None
    return float(value)


def _mean(values: list[float]) -> Optional[float]:
    return None if not values else mean(values)


def _median(values: list[float]) -> Optional[float]:
    return None if not values else median(values)


def _rmse(values: list[float]) -> Optional[float]:
    if not values:
        return None
    return math.sqrt(sum(value * value for value in values) / len(values))


def evaluate(
    manifest_path: Path,
    summaries: list[tuple[str, Path]],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    manifest_rows = {row["case_id"]: row for row in _load_csv_rows(manifest_path)}
    summary_rows = {
        label: {row["case_id"]: row for row in _load_csv_rows(path)}
        for label, path in summaries
    }

    per_case_rows: list[dict[str, Any]] = []
    by_backend_errors: dict[str, list[float]] = {label: [] for label, _ in summaries}
    by_backend_signed: dict[str, list[float]] = {label: [] for label, _ in summaries}
    by_backend_success: dict[str, int] = {label: 0 for label, _ in summaries}
    by_backend_bucket_errors: dict[str, dict[str, list[float]]] = {label: {} for label, _ in summaries}
    within_threshold_counts: dict[str, dict[str, int]] = {
        label: {str(threshold): 0 for threshold in THRESHOLDS}
        for label, _ in summaries
    }

    for case_id, manifest_row in sorted(manifest_rows.items()):
        y_relaxed = _as_float(manifest_row.get("y_relaxed"))
        if y_relaxed is None:
            raise ValueError(f"Manifest row {case_id} is missing y_relaxed")
        bucket = manifest_row.get("selection_bucket", "")
        row: dict[str, Any] = {
            "case_id": case_id,
            "smiles": manifest_row.get("smiles", ""),
            "adsorbate_name": manifest_row.get("adsorbate_name", ""),
            "surface_family": manifest_row.get("surface_family", ""),
            "selection_bucket": bucket,
            "y_relaxed_eV": y_relaxed,
        }
        for label, _ in summaries:
            summary_row = summary_rows[label].get(case_id, {})
            status = summary_row.get("status", "missing")
            predicted = _as_float(summary_row.get("best_energy_eV"))
            signed_error = None if predicted is None else predicted - y_relaxed
            abs_error = None if signed_error is None else abs(signed_error)

            row[f"{label}_status"] = status
            row[f"{label}_best_energy_eV"] = predicted
            row[f"{label}_signed_error_eV"] = signed_error
            row[f"{label}_abs_error_eV"] = abs_error

            if status == "success" and abs_error is not None:
                by_backend_success[label] += 1
                by_backend_errors[label].append(abs_error)
                by_backend_signed[label].append(signed_error)
                by_backend_bucket_errors[label].setdefault(bucket, []).append(abs_error)
                for threshold in THRESHOLDS:
                    if abs_error <= threshold:
                        within_threshold_counts[label][str(threshold)] += 1
        per_case_rows.append(row)

    total_cases = len(manifest_rows)
    metrics: dict[str, Any] = {
        "manifest_path": str(manifest_path),
        "total_case_count": total_cases,
        "backend_metrics": {},
    }

    for label, _ in summaries:
        abs_errors = by_backend_errors[label]
        signed_errors = by_backend_signed[label]
        bucket_metrics = {}
        for bucket, values in sorted(by_backend_bucket_errors[label].items()):
            bucket_metrics[bucket] = {
                "count": len(values),
                "mae_eV": _mean(values),
                "median_ae_eV": _median(values),
            }
        metrics["backend_metrics"][label] = {
            "success_case_count": by_backend_success[label],
            "success_rate": by_backend_success[label] / total_cases if total_cases else None,
            "mae_eV": _mean(abs_errors),
            "median_ae_eV": _median(abs_errors),
            "rmse_eV": _rmse(abs_errors),
            "mean_signed_error_eV": _mean(signed_errors),
            "within_threshold": {
                key: {
                    "count": count,
                    "fraction": count / total_cases if total_cases else None,
                }
                for key, count in within_threshold_counts[label].items()
            },
            "by_selection_bucket": bucket_metrics,
        }

    return per_case_rows, metrics


def write_outputs(
    rows: list[dict[str, Any]],
    report: dict[str, Any],
    output_csv: Path,
    output_json: Path,
    labels: list[str],
) -> None:
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    output_json.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = [
        "case_id",
        "smiles",
        "adsorbate_name",
        "surface_family",
        "selection_bucket",
        "y_relaxed_eV",
    ]
    for label in labels:
        fieldnames.extend(
            [
                f"{label}_status",
                f"{label}_best_energy_eV",
                f"{label}_signed_error_eV",
                f"{label}_abs_error_eV",
            ]
        )

    with output_csv.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows({key: row.get(key) for key in fieldnames} for row in rows)

    with output_json.open("w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2, ensure_ascii=False)


def main(argv: Optional[list[str]] = None) -> int:
    args = parse_args(argv)
    summaries = _parse_summary_specs(args.summary)
    rows, report = evaluate(Path(args.manifest), summaries)
    labels = [label for label, _ in summaries]
    write_outputs(rows, report, Path(args.output_csv), Path(args.output_json), labels)
    print(f"Evaluated {report['total_case_count']} cases across {len(labels)} backends.")
    print(json.dumps(report["backend_metrics"], indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
