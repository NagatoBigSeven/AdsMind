#!/usr/bin/env python3
"""Append no_executor and no_validator rows to the CMU20 summary tables.

Writes to two places so the audit's rebuild-from-source matches the
consolidated paper table:

1. Each backend's `all_variants_summary.csv` under
   research/results/basic_experiments/cmu20/adsmind/{backend}/ — the audit
   rebuilds the consolidated table from these per-backend files.
2. The consolidated `cmu20_ablation_4backend.csv` under
   research/results/basic_experiments/summaries/ — what paper analysis reads.

Idempotent: existing rows for `no_executor`/`no_validator` are dropped
before append in both files.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SUMMARY = ROOT / "research/results/basic_experiments/summaries/cmu20_ablation_4backend.csv"
BASE = ROOT / "research/results/basic_experiments/cmu20/adsmind"

BACKENDS = {
    "gpt":    "gpt54_mace_mp0_small",
    "claude": "claude_sonnet46_mace_mp0_small",
    "gemini": "gemini25pro_mace_mp0_small",
    "grok":   "grok4_mace_mp0_small",
}
NEW_VARIANTS = ("no_executor", "no_validator")
SCHEMA = [
    "case_id", "backend_key", "backend", "llm_model", "force_field",
    "calculator_backend", "force_field_model", "force_field_size", "variant",
    "best_energy_eV", "success", "run_path", "iterations", "wasted_iterations",
    "waste_ratio", "slip_count", "dissociation_count", "tokens_used",
]


def _read_existing(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open(encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        rows = list(reader)
        fields = list(reader.fieldnames or [])
    return fields, rows


def _row_for_case(backend_key: str, backend_dir: str, variant: str, case_dir: Path) -> dict[str, object]:
    result_path = case_dir / "result.json"
    config_path = case_dir / "config.json"
    result = json.loads(result_path.read_text(encoding="utf-8"))
    config = json.loads(config_path.read_text(encoding="utf-8")) if config_path.exists() else {}
    frozen = (config or {}).get("frozen_config", {}) or {}

    llm_model = frozen.get("llm_model", "")
    if not llm_model:
        # Fallback to the canonical backend model so downstream tooling stays happy.
        llm_model = {
            "gpt54_mace_mp0_small": "gpt-5.4-2026-03-05",
            "claude_sonnet46_mace_mp0_small": "claude-sonnet-4-6",
            "gemini25pro_mace_mp0_small": "gemini-2.5-pro",
            "grok4_mace_mp0_small": "x-ai/grok-4.3",
        }[backend_dir]

    calculator_backend = frozen.get("calculator_backend", "mace")
    force_field_size = frozen.get("mace_model", "small")
    force_field_model = "mace_mp0"
    force_field = f"MACE-MP-0 {force_field_size}"

    iterations = int(result.get("iteration_count") or 0)
    wasted = int(result.get("calc_failure_count") or 0)
    waste_ratio = (wasted / iterations) if iterations else 0.0
    tokens = int(result.get("total_input_tokens") or 0) + int(result.get("total_output_tokens") or 0)
    success = result.get("status") == "success"

    best_energy = result.get("best_energy_eV") if success else None

    run_path = case_dir.relative_to(ROOT).as_posix()

    return {
        "case_id": case_dir.name,
        "backend_key": backend_key,
        "backend": backend_dir,
        "llm_model": llm_model,
        "force_field": force_field,
        "calculator_backend": calculator_backend,
        "force_field_model": force_field_model,
        "force_field_size": force_field_size,
        "variant": variant,
        "best_energy_eV": "" if best_energy is None else best_energy,
        "success": "TRUE" if success else "FALSE",
        "run_path": run_path,
        "iterations": iterations,
        "wasted_iterations": wasted,
        "waste_ratio": waste_ratio,
        "slip_count": int(result.get("chemical_slip_count") or 0),
        "dissociation_count": int(result.get("dissociation_count") or 0),
        "tokens_used": tokens,
    }


ALL_VARIANTS_SCHEMA = [
    "backend_key", "backend", "llm_model", "force_field", "calculator_backend",
    "force_field_model", "force_field_size", "case_id", "variant", "best_energy",
    "delta_vs_full", "iterations", "wasted_iterations", "waste_ratio", "success",
    "slip_count", "dissociation_count", "tokens_used",
]


def _consolidated_row_to_all_variants_row(
    row: dict[str, object], full_energy_by_case: dict[str, float],
) -> dict[str, object]:
    """Translate a consolidated-CSV row into the all_variants_summary schema."""
    energy = row["best_energy_eV"]
    energy_value: float | None
    try:
        energy_value = float(energy) if energy not in ("", None) else None
    except (TypeError, ValueError):
        energy_value = None
    delta = ""
    full_e = full_energy_by_case.get(row["case_id"])
    if energy_value is not None and full_e is not None:
        delta = energy_value - full_e
    return {
        "backend_key": row["backend_key"],
        "backend": row["backend"],
        "llm_model": row["llm_model"],
        "force_field": row["force_field"],
        "calculator_backend": row["calculator_backend"],
        "force_field_model": row["force_field_model"],
        "force_field_size": row["force_field_size"],
        "case_id": row["case_id"],
        "variant": row["variant"],
        "best_energy": "" if energy_value is None else energy_value,
        "delta_vs_full": delta,
        "iterations": row["iterations"],
        "wasted_iterations": row["wasted_iterations"],
        "waste_ratio": row["waste_ratio"],
        "success": (str(row.get("success", "")).strip().upper() == "TRUE"),
        "slip_count": row["slip_count"],
        "dissociation_count": row["dissociation_count"],
        "tokens_used": row["tokens_used"],
    }


def _write_per_variant_summary(
    backend_dir: str, variant: str,
    rows_for_variant: list[dict[str, object]],
) -> Path:
    """Write {backend}/{variant}/summary.csv matching the existing per-variant schema."""
    path = BASE / backend_dir / variant / "summary.csv"
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=ALL_VARIANTS_SCHEMA)
        writer.writeheader()
        for row in sorted(rows_for_variant, key=lambda r: r["case_id"]):
            writer.writerow(row)
    return path


def _write_all_variants_for_backend(
    backend_dir: str, new_rows_for_backend: list[dict[str, object]],
    full_energy_by_case: dict[str, float],
) -> Path:
    """Update one backend's all_variants_summary.csv with the new variant rows."""
    path = BASE / backend_dir / "all_variants_summary.csv"
    with path.open(encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        existing = list(reader)
    base = [row for row in existing if row["variant"] not in NEW_VARIANTS]
    addition = [
        _consolidated_row_to_all_variants_row(row, full_energy_by_case)
        for row in new_rows_for_backend
    ]
    merged = base + addition
    variant_order = {v: i for i, v in enumerate(
        ["full", "no_slip", "no_forbid", "no_termination", "one_shot",
         "no_executor", "no_validator"]
    )}
    merged.sort(key=lambda r: (variant_order.get(r["variant"], 99), r["case_id"]))
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=ALL_VARIANTS_SCHEMA)
        writer.writeheader()
        for row in merged:
            writer.writerow(row)
    return path


def main() -> int:
    fields, existing_rows = _read_existing(SUMMARY)
    if fields != SCHEMA:
        raise SystemExit(f"summary schema mismatch:\nexpected: {SCHEMA}\nfound:    {fields}")

    new_rows: list[dict[str, object]] = []
    for backend_key, backend_dir in BACKENDS.items():
        for variant in NEW_VARIANTS:
            for case_dir in sorted((BASE / backend_dir / variant).glob("*")):
                if not (case_dir.is_dir() and (case_dir / "result.json").exists()):
                    continue
                if not case_dir.name.isdigit():
                    continue
                new_rows.append(_row_for_case(backend_key, backend_dir, variant, case_dir))

    # Step 1: update each backend's per-variant summary.csv and all_variants_summary.csv.
    for backend_key, backend_dir in BACKENDS.items():
        backend_new_rows = [r for r in new_rows if r["backend_key"] == backend_key]
        # delta_vs_full needs each backend's own `full` energies.
        full_energy_by_case: dict[str, float] = {}
        for row in existing_rows:
            if row["backend_key"] != backend_key or row["variant"] != "full":
                continue
            try:
                full_energy_by_case[row["case_id"]] = float(row["best_energy_eV"])
            except (TypeError, ValueError):
                continue
        for variant in NEW_VARIANTS:
            translated = [
                _consolidated_row_to_all_variants_row(r, full_energy_by_case)
                for r in backend_new_rows
                if r["variant"] == variant
            ]
            sub_path = _write_per_variant_summary(backend_dir, variant, translated)
            print(f"wrote {sub_path.relative_to(ROOT)} : {len(translated)} rows")
        path = _write_all_variants_for_backend(backend_dir, backend_new_rows, full_energy_by_case)
        print(f"wrote {path.relative_to(ROOT)} : +{len(backend_new_rows)} rows")

    # Step 2: regenerate the consolidated CMU20 summary via the canonical builder,
    # so its row ordering matches what the audit expects.
    import importlib, sys
    sys.path.insert(0, str(ROOT / "research/analysis"))
    builder = importlib.import_module("build_method_comparison_table")
    df = builder.build_ablation_4backend("cmu20")
    df.to_csv(SUMMARY, index=False)
    print(f"wrote {SUMMARY.relative_to(ROOT)} : {len(df)} rows (via canonical builder)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
