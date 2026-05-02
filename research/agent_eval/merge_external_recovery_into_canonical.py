#!/usr/bin/env python3
"""Merge successful external-failure recovery runs into canonical raw results.

This script is intentionally conservative:

* it only replaces canonical rows that are currently marked unsuccessful;
* it only accepts source rows that are marked successful;
* it never maps across datasets, even when OCD-GMAE case IDs look similar;
* it archives the replaced failed payload before copying in the recovery run.
"""

from __future__ import annotations

import csv
import json
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
CANONICAL_ROOT = REPO_ROOT / "research" / "results" / "canonical_raw"
REMOTE_RECOVERY_ROOT = (
    CANONICAL_ROOT / "superseded_raw_sources" / "remote_recovery_20260502"
)
REPLACED_ARCHIVE_ROOT = (
    CANONICAL_ROOT
    / "superseded_raw_sources"
    / "replaced_external_failures_20260502"
)
REPORT_PATH = (
    REPO_ROOT
    / "research"
    / "results"
    / "analysis"
    / "recovery_merge_report_20260502.md"
)


@dataclass(frozen=True)
class RecoverySource:
    target: str
    source: str


RECOVERY_SOURCES = [
    RecoverySource(
        "ocd24_grok4_ablation",
        "ocd_gmae_24_extra14_grok4_openrouter_recovery_v1",
    ),
    RecoverySource(
        "ocd24_grok4_ablation",
        "ocd_gmae_24_extra14_grok4_openrouter_single_shot_case017_recovery_v1",
    ),
    RecoverySource(
        "ocd24_grok4_ablation",
        "ocd_gmae_24_extra14_grok4_openrouter_single_shot_recovery_v1",
    ),
    RecoverySource(
        "ocd24_grok4_ablation",
        "ocd_gmae_24_grok4_no_forbid_case008_recovery_v1",
    ),
    RecoverySource(
        "ocd24_grok4_ablation",
        "ocd_gmae_24_extra14_xai_grok4_ablation_v1",
    ),
    RecoverySource(
        "ocd_rep50_grok4_ablation",
        "ocd_gmae_rep50_grok4_openrouter_full_recovery_v1",
    ),
    RecoverySource(
        "ocd_rep50_grok4_ablation",
        "ocd_gmae_rep50_grok4_openrouter_mechanism_recovery_no_slip_old_epfl_v1",
    ),
    RecoverySource(
        "ocd_rep50_grok4_ablation",
        "ocd_gmae_rep50_grok4_openrouter_mechanism_recovery_v1",
    ),
    RecoverySource(
        "ocd_rep50_grok4_ablation",
        "ocd_gmae_rep50_grok4_openrouter_no_slip_023_recovery_v1",
    ),
    RecoverySource(
        "ocd_rep50_grok4_ablation",
        "ocd_gmae_rep50_grok4_openrouter_no_termination_recovery_v1",
    ),
    RecoverySource(
        "ocd_rep50_gemini_ablation",
        "ocd_gmae_rep50_gemini_openrouter_no_forbid_recovery_old_epfl_v1",
    ),
    RecoverySource(
        "ocd_rep50_gemini_ablation",
        "ocd_gmae_rep50_gemini_openrouter_no_termination_recovery_old_epfl_v1",
    ),
    RecoverySource(
        "ocd_rep50_anthropic_sonnet46_ablation",
        "ocd_gmae_rep50_anthropic_sonnet46_no_slip_recovery_v1",
    ),
]


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_rows(path: Path, rows: list[dict[str, str]], fieldnames: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def is_success(row: dict[str, str]) -> bool:
    return str(row.get("success") or row.get("status") or "").lower() in {
        "true",
        "success",
        "1",
        "yes",
    }


def row_key(row: dict[str, str]) -> tuple[str, str]:
    case_id = row.get("case_id") or row.get("case") or ""
    return str(case_id), row.get("variant") or ""


def maybe_float(value: str | None) -> float | None:
    if value in (None, ""):
        return None
    try:
        return float(value)
    except ValueError:
        return None


def replace_artifact_paths(value: Any, target_case_dir: Path) -> Any:
    if isinstance(value, dict):
        return {k: replace_artifact_paths(v, target_case_dir) for k, v in value.items()}
    if isinstance(value, list):
        return [replace_artifact_paths(v, target_case_dir) for v in value]
    if not isinstance(value, str):
        return value
    if "artifacts/" not in value:
        return value
    basename = Path(value).name
    artifact_path = target_case_dir / "artifacts" / basename
    if not artifact_path.exists():
        return value
    return str(artifact_path.relative_to(REPO_ROOT))


def rewrite_result_json(target_case_dir: Path) -> None:
    result_path = target_case_dir / "result.json"
    if not result_path.exists():
        return
    payload = json.loads(result_path.read_text(encoding="utf-8"))
    payload = replace_artifact_paths(payload, target_case_dir)
    result_path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def recompute_deltas(rows: list[dict[str, str]]) -> None:
    full_energy: dict[str, float] = {}
    for row in rows:
        if row.get("variant") != "full":
            continue
        energy = maybe_float(row.get("best_energy") or row.get("best_energy_eV"))
        if energy is not None:
            full_energy[row["case_id"]] = energy

    for row in rows:
        energy = maybe_float(row.get("best_energy") or row.get("best_energy_eV"))
        full = full_energy.get(row.get("case_id", ""))
        if energy is None or full is None:
            row["delta_vs_full"] = ""
        else:
            row["delta_vs_full"] = repr(float(energy - full))


def source_case_dir(source_dir: Path, variant: str, case_id: str) -> Path | None:
    candidates = [
        source_dir / variant / case_id,
        source_dir / variant / case_id.zfill(3),
        source_dir / variant / case_id.zfill(2),
    ]
    for candidate in candidates:
        if (candidate / "result.json").exists():
            return candidate
    return None


def merge_one(source: RecoverySource) -> list[tuple[str, str, str]]:
    target_dir = CANONICAL_ROOT / source.target
    source_dir = REMOTE_RECOVERY_ROOT / source.source
    target_summary = target_dir / "ablation_summary.csv"
    source_summary = source_dir / "ablation_summary.csv"
    if not target_summary.exists() or not source_summary.exists():
        return []

    with target_summary.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        fieldnames = list(reader.fieldnames or [])
        target_rows = list(reader)

    source_rows = read_rows(source_summary)
    target_index = {row_key(row): i for i, row in enumerate(target_rows)}
    replacements: list[tuple[str, str, str]] = []

    for source_row in source_rows:
        key = row_key(source_row)
        if not is_success(source_row) or key not in target_index:
            continue
        target_row = target_rows[target_index[key]]
        if is_success(target_row):
            continue

        case_id, variant = key
        src_case_dir = source_case_dir(source_dir, variant, case_id)
        if src_case_dir is None:
            continue

        dst_case_dir = target_dir / variant / case_id
        archive_case_dir = REPLACED_ARCHIVE_ROOT / source.target / variant / case_id
        if archive_case_dir.exists():
            shutil.rmtree(archive_case_dir)
        if dst_case_dir.exists():
            archive_case_dir.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(dst_case_dir), str(archive_case_dir))

        dst_case_dir.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(src_case_dir, dst_case_dir)
        rewrite_result_json(dst_case_dir)

        replacement = dict(target_row)
        for field in fieldnames:
            replacement[field] = source_row.get(field, replacement.get(field, ""))
        target_rows[target_index[key]] = replacement
        replacements.append((source.target, variant, case_id))

    if replacements:
        recompute_deltas(target_rows)
        write_rows(target_summary, target_rows, fieldnames)
    return replacements


def remaining_failures(target: str) -> list[tuple[str, str]]:
    rows = read_rows(CANONICAL_ROOT / target / "ablation_summary.csv")
    return [row_key(row) for row in rows if not is_success(row)]


def main() -> int:
    all_replacements: list[tuple[str, str, str]] = []
    for source in RECOVERY_SOURCES:
        all_replacements.extend(merge_one(source))

    affected_targets = sorted({target for target, _, _ in all_replacements})
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Recovery Merge Report - 2026-05-02",
        "",
        "Merged only successful recovery rows into canonical rows that were still marked unsuccessful.",
        "",
        "## Replacements",
    ]
    if all_replacements:
        lines.append("")
        lines.append("| target | variant | case_id |")
        lines.append("|---|---|---|")
        for target, variant, case_id in sorted(all_replacements):
            lines.append(f"| {target} | {variant} | {case_id} |")
    else:
        lines.append("")
        lines.append("No replacements were needed.")

    lines.extend(["", "## Remaining Failures"])
    for target in affected_targets or [
        "ocd24_grok4_ablation",
        "ocd_rep50_grok4_ablation",
        "ocd_rep50_gemini_ablation",
        "ocd_rep50_anthropic_sonnet46_ablation",
    ]:
        failures = remaining_failures(target)
        lines.append("")
        lines.append(f"### {target}")
        if failures:
            for case_id, variant in failures:
                lines.append(f"- {case_id} / {variant}")
        else:
            lines.append("- none")

    REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Merged {len(all_replacements)} recovery rows")
    print(f"Report: {REPORT_PATH.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
