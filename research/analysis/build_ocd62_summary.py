"""Build paper-facing OCD62 ablation and overlap reproducibility tables."""

from __future__ import annotations

import argparse
import csv
import json
import math
import sys
from collections import Counter
from pathlib import Path
from statistics import mean, pstdev
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from research.agent_eval.experiment_identity import BACKEND_KEYS, backend_identity, backend_result_dir, summary_metadata

RESULTS_ROOT = ROOT / "research" / "results"
BASIC_ROOT = RESULTS_ROOT / "basic_experiments"
ADVANCED_ROOT = RESULTS_ROOT / "advanced_experiments"
OCD62_SUMMARY_DIR = BASIC_ROOT / "ocd62" / "summaries"
OVERLAP12_ROOT = ADVANCED_ROOT / "reproducibility" / "ocd62_overlap12_rerun"
OVERLAP12_SUMMARY_DIR = OVERLAP12_ROOT / "summaries"
DATASET_DIR = ROOT / "datasets" / "ocd62"
OVERLAP_MANIFEST = (
    ROOT
    / "datasets"
    / "ocd62_overlap12"
    / "ocd62_overlap12_manifest.csv"
)
REPRO_RUNS_DATASET = "ocd62_overlap12_rerun"

BACKENDS = BACKEND_KEYS
VARIANTS = ("full", "no_slip", "no_forbid", "no_termination", "one_shot")
VARIANT_ALIASES = {
    "one_shot": {"one_shot", "single_shot"},
}
REPRO_RUN_DIRS = {
    1: "run1",
    2: "run2",
    3: "run3",
    4: "run4",
    5: "run5",
}
OUTLIER_KEYS = {("grok", "full", 16), ("grok", "no_forbid", 16)}
OUTLIER_THRESHOLD_EV = -10_000.0


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: Iterable[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


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


def row_success(row: dict[str, Any]) -> bool:
    value = row.get("success", row.get("status", ""))
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"true", "1", "yes", "success"}


def manifest_rows() -> list[dict[str, str]]:
    return read_csv(DATASET_DIR / "ocd62_manifest.csv")


def manifest_by_case() -> dict[str, dict[str, str]]:
    return {row["case_id"].zfill(3): row for row in manifest_rows()}


def overlap_by_case() -> dict[str, dict[str, str]]:
    return {row["case_id"].zfill(3): row for row in read_csv(OVERLAP_MANIFEST)}


def adsorbate_label(row: dict[str, str]) -> str:
    return row.get("adsorbate") or row.get("adsorbate_name") or row.get("smiles", "")


def ocd_id(row: dict[str, str]) -> str:
    return row.get("ocd_id", "")


def backend_dir(dataset: str, backend: str) -> Path:
    return BASIC_ROOT / dataset / backend_result_dir(backend)


def run_dir(dataset: str, backend: str, variant: str, case_id: str) -> Path:
    return backend_dir(dataset, backend) / variant / case_id


def summary_path(dataset: str, backend: str) -> Path:
    return backend_dir(dataset, backend) / "all_variants_summary.csv"


def repro_backend_dir(run_name: str, backend: str) -> Path:
    return OVERLAP12_ROOT / run_name / backend_result_dir(backend, run_name=run_name)


def repro_summary_path(run_name: str, backend: str) -> Path:
    return repro_backend_dir(run_name, backend) / "all_variants_summary.csv"


def repro_run_dir(run_name: str, backend: str, variant: str, case_id: str) -> Path:
    return repro_backend_dir(run_name, backend) / variant / case_id


def normalize_variant(value: str) -> str:
    return "one_shot" if value == "single_shot" else value


def load_summary(dataset: str, backend: str) -> dict[tuple[str, str], dict[str, Any]]:
    path = summary_path(dataset, backend)
    if not path.exists():
        return {}
    out: dict[tuple[str, str], dict[str, Any]] = {}
    for row in read_csv(path):
        case_id = row.get("case_id", "").zfill(3)
        variant = normalize_variant(row.get("variant", ""))
        if case_id and variant:
            normalized = dict(row)
            normalized["case_id"] = case_id
            normalized["variant"] = variant
            out[(case_id, variant)] = normalized
    return out


def load_repro_summary(run_name: str, backend: str) -> dict[tuple[str, str], dict[str, Any]]:
    path = repro_summary_path(run_name, backend)
    if not path.exists():
        return {}
    out: dict[tuple[str, str], dict[str, Any]] = {}
    for row in read_csv(path):
        case_id = row.get("case_id", "").zfill(3)
        variant = normalize_variant(row.get("variant", ""))
        if case_id and variant:
            normalized = dict(row)
            normalized["case_id"] = case_id
            normalized["variant"] = variant
            out[(case_id, variant)] = normalized
    return out


def energy_from_result(dataset: str, backend: str, variant: str, case_id: str) -> float | None:
    path = run_dir(dataset, backend, variant, case_id) / "result.json"
    if not path.exists():
        return None
    try:
        result = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
    best = parse_float(result.get("best_energy_eV"))
    if best is not None:
        return best
    last = result.get("last_analysis") or {}
    return parse_float(last.get("most_stable_energy_eV"))


def energy_from_repro_result(run_name: str, backend: str, variant: str, case_id: str) -> float | None:
    path = repro_run_dir(run_name, backend, variant, case_id) / "result.json"
    if not path.exists():
        return None
    try:
        result = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
    best = parse_float(result.get("best_energy_eV"))
    if best is not None:
        return best
    last = result.get("last_analysis") or {}
    return parse_float(last.get("most_stable_energy_eV"))


def value_from_row(row: dict[str, Any], key: str, fallback: str = "") -> str:
    value = row.get(key, fallback)
    return "" if value is None else str(value)


def unified_rows() -> list[dict[str, Any]]:
    meta_by_case = manifest_by_case()
    rows: list[dict[str, Any]] = []
    for backend in BACKENDS:
        index = load_summary("ocd62", backend)
        for case_id in sorted(meta_by_case):
            meta = meta_by_case[case_id]
            for variant in VARIANTS:
                row = index.get((case_id, variant))
                if row is None:
                    continue
                rows.append(
                    {
                        "case_id": case_id,
                        "ocd_id": ocd_id(meta),
                        "surface_formula": meta["surface_formula"],
                        "adsorbate": adsorbate_label(meta),
                        **summary_metadata(backend_identity(backend)),
                        "variant": variant,
                        "best_energy_eV": value_from_row(row, "best_energy"),
                        "success": "TRUE" if row_success(row) else "FALSE",
                        "run_path": str(run_dir("ocd62", backend, variant, case_id).relative_to(ROOT)),
                        "iterations": value_from_row(row, "iterations", value_from_row(row, "iteration_count")),
                        "wasted_iterations": value_from_row(row, "wasted_iterations", value_from_row(row, "calc_failure_count")),
                        "waste_ratio": value_from_row(row, "waste_ratio"),
                        "slip_count": value_from_row(row, "slip_count", value_from_row(row, "chemical_slip_count")),
                        "dissociation_count": value_from_row(row, "dissociation_count"),
                        "tokens_used": value_from_row(row, "tokens_used"),
                    }
                )
    return rows


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


def paired_rows(run_count: int) -> list[dict[str, Any]]:
    if run_count not in {2, 3, 4, 5}:
        raise ValueError("run_count must be 2, 3, 4, or 5")

    overlap = overlap_by_case()
    run_names = [REPRO_RUN_DIRS[i] for i in range(1, run_count + 1)]
    rows: list[dict[str, Any]] = []
    for backend in BACKENDS:
        indexes = {
            run_name: load_repro_summary(run_name, backend)
            for run_name in run_names
        }
        for case_id in sorted(overlap):
            meta = overlap[case_id]
            current_ocd_id = int(ocd_id(meta))
            for variant in VARIANTS:
                values: list[float | None] = []
                for run_name in run_names:
                    row = indexes[run_name].get((case_id, variant), {})
                    value = parse_float(row.get("best_energy"))
                    if value is None and row:
                        value = energy_from_repro_result(run_name, backend, variant, case_id)
                    values.append(value)

                outlier = (backend, variant, current_ocd_id) in OUTLIER_KEYS
                outlier = outlier or any(value is not None and value < OUTLIER_THRESHOLD_EV for value in values)
                missing_value = any(value is None for value in values)
                clean = [value for value in values if value is not None and value >= OUTLIER_THRESHOLD_EV]
                range_ev = (max(clean) - min(clean)) if len(clean) >= 2 else None
                agreement = "missing" if missing_value else agreement_class(range_ev, outlier=outlier)
                row: dict[str, Any] = {
                    "case_id": case_id,
                    "ocd62_case_id": meta.get("ocd62_case_id") or meta.get("ocd62_seq_id"),
                    "ocd_id": current_ocd_id,
                    "surface_formula": meta["surface_formula"],
                    "adsorbate": adsorbate_label(meta),
                    **summary_metadata(backend_identity(backend, run_name=run_names[0])),
                    "variant": variant,
                    "range_eV": format_float(range_ev),
                    "agreement_class": agreement,
                }
                for idx, value in enumerate(values, start=1):
                    row[f"e_run{idx}"] = format_float(value)
                    row[f"run{idx}_backend"] = backend_result_dir(backend, run_name=REPRO_RUN_DIRS[idx])
                if run_count >= 3 and len(clean) >= 2:
                    row["e_min"] = format_float(min(clean))
                    row["std_eV"] = format_float(pstdev(clean))
                rows.append(row)
    return rows


def reproducibility_report(rows: list[dict[str, Any]], run_count: int) -> str:
    counts = Counter(row["agreement_class"] for row in rows)
    total = len(rows)
    within_001 = counts["exact_match"]
    within_01 = counts["exact_match"] + counts["match"]
    outliers = counts["outlier_excluded"]
    missing = counts["missing"]
    mismatches = total - within_01 - outliers - missing

    ranges = [parse_float(row.get("range_eV")) for row in rows]
    ranges = [value for value in ranges if value is not None]
    lines = [
        f"# OCD62 overlap12-only N={run_count} reproducibility report",
        "",
        "This report summarizes the 12 duplicated OCD62 cases used for run-to-run reproducibility analysis.",
        "",
        "## Headline Counts",
        "",
        f"- Paired comparisons: {total} = 12 cases x 4 backends x 5 variants.",
        f"- Matches within 0.001 eV: {within_001} ({within_001 / total:.1%}).",
        f"- Matches within 0.01 eV: {within_01} ({within_01 / total:.1%}).",
        f"- Non-outlier mismatches above 0.01 eV: {mismatches} ({mismatches / total:.1%}).",
        f"- Excluded numerical-collapse outliers: {outliers} ({outliers / total:.1%}).",
        f"- Missing run energies: {missing} ({missing / total:.1%}).",
    ]
    if ranges:
        lines.append(f"- Mean run range: {mean(ranges):.3f} eV.")
        lines.append(f"- Max run range: {max(ranges):.3f} eV.")

    lines.extend(["", "## Counts By Agreement Class", "", "| agreement_class | count |", "|---|---:|"])
    for key in ("exact_match", "match", "minor", "moderate", "divergent", "large_divergent", "severe", "outlier_excluded", "missing"):
        if counts[key]:
            lines.append(f"| {key} | {counts[key]} |")
    lines.append("")
    return "\n".join(lines)


def reproducibility_fieldnames(run_count: int) -> list[str]:
    fields = [
        "case_id",
        "ocd62_case_id",
        "ocd_id",
        "surface_formula",
        "adsorbate",
        "backend_key",
        "backend",
    ]
    fields.extend(f"run{idx}_backend" for idx in range(1, run_count + 1))
    fields.extend(
        [
            "llm_model",
            "force_field",
            "calculator_backend",
            "force_field_model",
            "force_field_size",
            "variant",
        ]
    )
    fields.extend(f"e_run{idx}" for idx in range(1, run_count + 1))
    fields.extend(["range_eV"])
    if run_count >= 3:
        fields.extend(["e_min", "std_eV"])
    fields.append("agreement_class")
    return fields


def ensure_repro_summaries(run_count: int) -> None:
    missing = [
        f"{REPRO_RUN_DIRS[idx]}/{backend}"
        for idx in range(1, run_count + 1)
        for backend in BACKENDS
        if not repro_summary_path(REPRO_RUN_DIRS[idx], backend).exists()
    ]
    if missing:
        raise FileNotFoundError(f"Reproducibility summaries missing for: {', '.join(missing)}")


def write_reproducibility_outputs(run_count: int) -> None:
    ensure_repro_summaries(run_count)
    rows = paired_rows(run_count)
    fieldnames = reproducibility_fieldnames(run_count)
    write_csv(OVERLAP12_SUMMARY_DIR / f"reproducibility_n{run_count}.csv", rows, fieldnames)
    report = reproducibility_report(rows, run_count)
    (OVERLAP12_SUMMARY_DIR / f"reproducibility_n{run_count}.md").write_text(report, encoding="utf-8")


def write_outputs(write_n3: bool, write_n4: bool, write_n5: bool) -> None:
    unified_fields = [
        "case_id",
        "ocd_id",
        "surface_formula",
        "adsorbate",
        "backend_key",
        "backend",
        "llm_model",
        "force_field",
        "calculator_backend",
        "force_field_model",
        "force_field_size",
        "variant",
        "best_energy_eV",
        "success",
        "run_path",
        "iterations",
        "wasted_iterations",
        "waste_ratio",
        "slip_count",
        "dissociation_count",
        "tokens_used",
    ]
    unified = unified_rows()
    write_csv(OCD62_SUMMARY_DIR / "ablation_4backend.csv", unified, unified_fields)

    write_reproducibility_outputs(2)

    if write_n3:
        write_reproducibility_outputs(3)
    if write_n4:
        write_reproducibility_outputs(4)
    if write_n5:
        write_reproducibility_outputs(5)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write-n3", action="store_true", help="Also write N=3 outputs after RUN3 is present")
    parser.add_argument("--write-n4", action="store_true", help="Also write N=4 outputs after RUN4 is present")
    parser.add_argument("--write-n5", action="store_true", help="Also write N=5 outputs after RUN5 is present")
    parser.add_argument("--policy", default="", help=argparse.SUPPRESS)
    args = parser.parse_args(argv)
    write_outputs(args.write_n3, args.write_n4, args.write_n5)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
