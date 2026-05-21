#!/usr/bin/env python3
"""Rebuild CMU20 one-shot chemical-slip diagnostics from result.json files."""

from __future__ import annotations

import csv
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
RESULTS = ROOT / "research" / "results"
CMU20 = RESULTS / "basic_experiments" / "cmu20" / "adsmind"
OUT = (
    RESULTS
    / "advanced_experiments"
    / "ablation_and_chemical_slip_diagnostics"
    / "chemical_slip_interpretability"
    / "cmu20"
)

BACKENDS = [
    "gemini25pro_mace_mp0_small",
    "gpt54_mace_mp0_small",
    "claude_sonnet46_mace_mp0_small",
    "grok4_mace_mp0_small",
]


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def surface_from_metadata(meta: dict[str, Any]) -> str:
    slab_file = str(meta.get("slab_file", ""))
    match = re.search(r"/\d+_([^_/]+)_", slab_file)
    return match.group(1) if match else ""


def base_site(site: str) -> str:
    return (site or "").split()[0]


def slip_type(planned: str, actual: str, slipped: bool) -> str:
    if not slipped:
        return "none"
    return "soft" if base_site(planned) == base_site(actual) else "hard"


def case_row(case_id: int) -> dict[str, Any]:
    first = load_json(CMU20 / BACKENDS[0] / "one_shot" / f"{case_id:02d}" / "result.json")
    meta = first.get("case_metadata", {})
    row: dict[str, Any] = {
        "case_id": f"{case_id:02d}",
        "surface": surface_from_metadata(meta),
        "surface_family": meta.get("surface_family", ""),
        "adsorbate": meta.get("adsorbate_name", ""),
        "miller_index": meta.get("miller_index", ""),
    }

    for backend in BACKENDS:
        payload = load_json(CMU20 / backend / "one_shot" / f"{case_id:02d}" / "result.json")
        records = payload.get("attempt_records", [])
        record = records[0] if records else {}
        planned = str(record.get("planned_site_type") or "")
        actual = str(record.get("actual_site_type") or "")
        dissociated = bool(record.get("is_dissociated"))
        valid = payload.get("status") == "success" and not dissociated
        slipped = bool(record.get("is_chemical_slip")) if valid else False
        row[f"{backend}_planned_site"] = planned
        row[f"{backend}_actual_site"] = actual
        row[f"{backend}_slip"] = slipped
        row[f"{backend}_slip_type"] = slip_type(planned, actual, slipped)
        row[f"{backend}_valid"] = valid
        row[f"{backend}_dissociated"] = dissociated
    return row


def aggregate(rows: list[dict[str, Any]]) -> dict[str, Any]:
    overall: dict[str, float | str] = {}
    by_family: dict[str, dict[str, float | str]] = {}
    patterns: Counter[str] = Counter()
    all_valid_cases = 0
    unanimous_cases = 0

    families = sorted({str(row["surface_family"]) for row in rows})
    for family in families:
        by_family[family] = {}

    for backend in BACKENDS:
        valid_rows = [row for row in rows if row[f"{backend}_valid"]]
        slip_rows = [row for row in valid_rows if row[f"{backend}_slip"]]
        overall[backend] = round(len(slip_rows) / len(valid_rows), 4) if valid_rows else 0.0
        overall[f"{backend}_n"] = f"{len(slip_rows)}/{len(valid_rows)}"
        for family in families:
            family_rows = [row for row in valid_rows if row["surface_family"] == family]
            family_slips = [row for row in family_rows if row[f"{backend}_slip"]]
            by_family[family][backend] = (
                round(len(family_slips) / len(family_rows), 4) if family_rows else 0.0
            )
            by_family[family][f"{backend}_n"] = f"{len(family_slips)}/{len(family_rows)}"
        for row in slip_rows:
            planned = base_site(str(row[f"{backend}_planned_site"]))
            actual = base_site(str(row[f"{backend}_actual_site"]))
            patterns[f"{planned} -> {actual}"] += 1

    for row in rows:
        valid_flags = [row[f"{backend}_valid"] for backend in BACKENDS]
        if all(valid_flags):
            all_valid_cases += 1
            slips = [bool(row[f"{backend}_slip"]) for backend in BACKENDS]
            unanimous_cases += int(len(set(slips)) == 1)

    return {
        "overall_slip_rate": overall,
        "by_surface_family": by_family,
        "cross_backend_slip_agreement": {
            "matching_cases": unanimous_cases,
            "total_cases": all_valid_cases,
            "rate": round(unanimous_cases / all_valid_cases, 4) if all_valid_cases else 0.0,
            "definition": "unanimous slip/no-slip status across all four backends among cases with four valid one-shot runs",
        },
        "most_common_slip_pattern": patterns.most_common(1)[0][0] if patterns else "",
        "slip_type_counts": {
            backend: dict(Counter(row[f"{backend}_slip_type"] for row in rows if row[f"{backend}_valid"]))
            for backend in BACKENDS
        },
    }


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    rows = [case_row(case_id) for case_id in range(1, 21)]

    fieldnames = [
        "case_id",
        "surface",
        "surface_family",
        "adsorbate",
        "miller_index",
    ]
    for backend in BACKENDS:
        fieldnames.extend(
            [
                f"{backend}_planned_site",
                f"{backend}_actual_site",
                f"{backend}_slip",
                f"{backend}_slip_type",
                f"{backend}_valid",
                f"{backend}_dissociated",
            ]
        )

    csv_path = OUT / "slip_analysis.csv"
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    json_path = OUT / "slip_analysis.json"
    with json_path.open("w", encoding="utf-8") as handle:
        json.dump(aggregate(rows), handle, indent=2, ensure_ascii=False)
        handle.write("\n")

    print(csv_path.relative_to(ROOT))
    print(json_path.relative_to(ROOT))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
