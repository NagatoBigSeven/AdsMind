"""Rank one-shot benchmark cases by cross-backend energy range."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional


def parse_args(argv: Optional[list[str]] = None) -> argparse.Namespace:
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser(
        description="Rank case-wise energy spread across multiple one-shot summary CSV files."
    )
    parser.add_argument(
        "--summary",
        action="append",
        required=True,
        help="Backend summary in label=path format. Repeat once per backend.",
    )
    parser.add_argument("--output-csv", required=True, help="Path for ranked CSV output")
    parser.add_argument("--output-json", required=True, help="Path for JSON report output")
    parser.add_argument(
        "--exclude-case-ids",
        default="",
        help="Optional comma-separated case ids to omit before ranking",
    )
    parser.add_argument(
        "--require-success",
        action="store_true",
        help="Exclude rows unless every backend reports status=success and a numeric energy",
    )
    return parser.parse_args(argv)


def _parse_summary_specs(specs: Iterable[str]) -> list[tuple[str, Path]]:
    """Split repeated label=path arguments into structured tuples."""
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


def _load_summary(path: Path) -> dict[str, dict[str, str]]:
    """Load a summary CSV keyed by case id."""
    with path.open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    return {row["case_id"]: row for row in rows}


def _as_float(value: Any) -> Optional[float]:
    """Best-effort numeric parsing for energy values."""
    if value in ("", None):
        return None
    return float(value)


def rank_cases(
    summaries: list[tuple[str, Path]],
    *,
    exclude_case_ids: Optional[Iterable[str]] = None,
    require_success: bool = False,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Merge backend summaries and compute case-wise energy ranges."""
    loaded = [(label, path, _load_summary(path)) for label, path in summaries]
    excluded_case_id_set = {str(case_id).strip() for case_id in (exclude_case_ids or []) if str(case_id).strip()}
    case_ids = sorted({case_id for _, _, summary in loaded for case_id in summary})
    ranked_rows: list[dict[str, Any]] = []
    excluded_rows: list[dict[str, Any]] = []

    for case_id in case_ids:
        if case_id in excluded_case_id_set:
            excluded_rows.append(
                {
                    "case_id": case_id,
                    "missing_backends": [],
                    "failed_backends": [],
                    "excluded_by_user": True,
                    "included": False,
                }
            )
            continue
        row_by_label: dict[str, dict[str, str]] = {}
        missing_labels: list[str] = []
        failed_labels: list[str] = []
        energies: dict[str, float] = {}
        metadata: dict[str, str] = {}

        for label, _, summary in loaded:
            row = summary.get(case_id)
            if row is None:
                missing_labels.append(label)
                continue
            row_by_label[label] = row
            if not metadata:
                metadata = {
                    "slab_file": row.get("slab_file", ""),
                    "smiles": row.get("smiles", ""),
                    "adsorbate_name": row.get("adsorbate_name", ""),
                    "surface_family": row.get("surface_family", ""),
                    "reaction_class": row.get("reaction_class", ""),
                }
            energy = _as_float(row.get("best_energy_eV"))
            status = row.get("status", "")
            if energy is None:
                failed_labels.append(label)
            elif require_success and status != "success":
                failed_labels.append(label)
            elif status != "success" and require_success:
                failed_labels.append(label)
            elif status != "success" and energy is None:
                failed_labels.append(label)
            else:
                energies[label] = energy
                if require_success and status != "success":
                    failed_labels.append(label)

        complete = not missing_labels and len(energies) == len(loaded) and not failed_labels
        include = complete if require_success else not missing_labels and len(energies) == len(loaded)

        base_row: dict[str, Any] = {
            "case_id": case_id,
            **metadata,
            "backend_count": len(loaded),
            "available_backend_count": len(energies),
            "missing_backends": missing_labels,
            "failed_backends": failed_labels,
            "excluded_by_user": False,
            "included": include,
        }
        for label, _, _ in loaded:
            row = row_by_label.get(label, {})
            base_row[f"{label}_status"] = row.get("status", "")
            base_row[f"{label}_energy_eV"] = energies.get(label)

        if include:
            ordered_energies = [energies[label] for label, _, _ in loaded]
            min_energy = min(ordered_energies)
            max_energy = max(ordered_energies)
            ranked_rows.append(
                {
                    **base_row,
                    "min_energy_eV": min_energy,
                    "max_energy_eV": max_energy,
                    "range_eV": max_energy - min_energy,
                }
            )
        else:
            excluded_rows.append(base_row)

    ranked_rows.sort(key=lambda row: (-row["range_eV"], row["case_id"]))
    for index, row in enumerate(ranked_rows, start=1):
        row["rank"] = index

    report = {
        "backend_labels": [label for label, _ in summaries],
        "excluded_case_ids": sorted(excluded_case_id_set),
        "included_case_count": len(ranked_rows),
        "excluded_case_count": len(excluded_rows),
        "top_cases": ranked_rows[:10],
        "excluded_cases": excluded_rows,
    }
    return ranked_rows, report


def write_outputs(rows: list[dict[str, Any]], report: dict[str, Any], output_csv: Path, output_json: Path) -> None:
    """Write CSV and JSON artifacts."""
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    output_json.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = [
        "rank",
        "case_id",
        "slab_file",
        "smiles",
        "adsorbate_name",
        "surface_family",
        "reaction_class",
        "backend_count",
        "available_backend_count",
        "min_energy_eV",
        "max_energy_eV",
        "range_eV",
    ]
    backend_labels = report["backend_labels"]
    for label in backend_labels:
        fieldnames.append(f"{label}_status")
        fieldnames.append(f"{label}_energy_eV")

    with output_csv.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key) for key in fieldnames})

    with output_json.open("w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2, ensure_ascii=False)


def main(argv: Optional[list[str]] = None) -> int:
    """CLI entrypoint."""
    args = parse_args(argv)
    summaries = _parse_summary_specs(args.summary)
    exclude_case_ids = [item.strip() for item in args.exclude_case_ids.split(",") if item.strip()]
    rows, report = rank_cases(
        summaries,
        exclude_case_ids=exclude_case_ids,
        require_success=args.require_success,
    )
    write_outputs(rows, report, Path(args.output_csv), Path(args.output_json))
    print(f"Included cases: {report['included_case_count']}")
    print(f"Excluded cases: {report['excluded_case_count']}")
    if rows:
        top = rows[0]
        print(
            json.dumps(
                {
                    "top_case": top["case_id"],
                    "top_range_eV": top["range_eV"],
                    "backend_labels": report["backend_labels"],
                },
                indent=2,
                ensure_ascii=False,
            )
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
