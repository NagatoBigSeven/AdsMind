"""Add explicit protocol provenance columns to existing result summary CSVs."""

from __future__ import annotations

import csv
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from research.agent_eval.experiment_identity import identity_from_path, summary_metadata


PROVENANCE_FIELDS = [
    "backend_key",
    "backend",
    "llm_model",
    "force_field",
    "calculator_backend",
    "force_field_model",
    "force_field_size",
]


def update_csv(path: Path) -> bool:
    identity = identity_from_path(path)
    if identity is None:
        return False
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)
        old_fields = list(reader.fieldnames or [])
    metadata = summary_metadata(identity)
    fields = PROVENANCE_FIELDS + [field for field in old_fields if field not in PROVENANCE_FIELDS]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({**row, **metadata})
    return True


def main() -> int:
    changed = []
    for path in sorted((ROOT / "research" / "results").rglob("*.csv")):
        if path.name not in {"summary.csv", "all_variants_summary.csv", "ablation_summary.csv"}:
            continue
        if update_csv(path):
            changed.append(path)
    for path in changed:
        print(path.relative_to(ROOT))
    print(f"updated={len(changed)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
