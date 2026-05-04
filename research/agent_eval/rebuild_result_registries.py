#!/usr/bin/env python3
"""Rebuild machine-readable registries for result naming governance."""

from __future__ import annotations

import argparse
import csv
import json
import re
from pathlib import Path
from typing import Any, Iterable


REPO_ROOT = Path(__file__).resolve().parents[2]
RESULTS = REPO_ROOT / "research/results"
CANONICAL_ROOT = RESULTS / "canonical_raw"
ANALYSIS_ROOT = RESULTS / "analysis"
QC_PATH = CANONICAL_ROOT / "MERGE_QC.csv"
RUN_REGISTRY = RESULTS / "RUN_REGISTRY.csv"
ANALYSIS_REGISTRY = RESULTS / "ANALYSIS_REGISTRY.csv"

DATE_TOKEN_RE = re.compile(r"20\d{6}")
OPAQUE_VERSION_RE = re.compile(r"(^|[/_-])v\d+($|[/_-])")
HOST_PATH_RE = re.compile(r"/(data/zongmin|Users/nagato|home/[A-Za-z0-9._-]+)/workspace/AdsMind")

CSV_SUFFIXES = {".csv", ".tsv"}

BACKEND_DISPLAY = {
    "adsorbagent": "Adsorb-Agent",
    "anthropic_sonnet46": "Claude Sonnet 4.6",
    "gemini": "Gemini 2.5 Pro",
    "grok4": "Grok-4",
    "heuristic": "heuristic baseline",
    "openai_gpt54": "GPT-5.4",
    "random": "random baseline",
}

BACKEND_MODEL_FALLBACK = {
    "adsorbagent": "not_applicable_external_baseline",
    "anthropic_sonnet46": "claude-sonnet-4-6",
    "gemini": "gemini-2.5-pro; google/gemini-2.5-pro",
    "grok4": "grok-4-0709; x-ai/grok-4",
    "heuristic": "not_applicable_heuristic_baseline",
    "openai_gpt54": "gpt-5.4-2026-03-05",
    "random": "not_applicable_random_baseline",
}

FROZEN_CONFIG_REFS = {
    "anthropic_sonnet46": "research/agent_eval/configs/frozen_config_anthropic_sonnet46.json",
    "gemini": (
        "research/agent_eval/configs/frozen_config.json; "
        "research/agent_eval/configs/frozen_config_gemini25pro_vertexai.json; "
        "research/agent_eval/configs/frozen_config_gemini25pro_openrouter.json"
    ),
    "grok4": (
        "research/agent_eval/configs/frozen_config_xai_grok4.json; "
        "research/results/run_configs/frozen_config_grok4_openrouter_recovery.json"
    ),
    "openai_gpt54": "research/agent_eval/configs/frozen_config_openai_gpt54.json",
}

DATASET_MANIFESTS = {
    "CMU20": "datasets/cmu20/cmu20_manifest.csv",
    "CMU20-case01": "datasets/cmu20/cmu20_manifest.csv",
    "OCD62": "datasets/ocd62/ocd62_manifest.csv",
}

REPRO_MANIFESTS = {
    "ocd62_overlap12": "datasets/ocd62_overlap12/overlap12_manifest.csv",
}

AUTHORITATIVE_ANALYSIS = {
    "adsmind_vs_adsorbagent_behavioral.csv",
    "baselines_comparison.json",
    "case19_trajectory.csv",
    "case19_trajectory.json",
    "cmu_one_shot_range_ranking_new_cases.csv",
    "cmu_one_shot_range_ranking_new_cases.json",
    "cross_llm_20case_4backend.json",
    "cross_llm_ablation_4backend.json",
    "hypothesis_test.json",
    "iteration_convergence.csv",
    "iteration_convergence.png",
    "iteration_convergence_summary.json",
    "key_evaluation_metrics.json",
    "ocd62_ablation_4backend.csv",
    "ocd62_unified_ablation.csv",
    "ocd62_overlap12_reproducibility_n2.csv",
    "ocd62_overlap12_reproducibility_n2.md",
    "ocd62_overlap12_reproducibility_n3.csv",
    "ocd62_overlap12_reproducibility_n3.md",
    "paper_tables.tex",
    "si4_ablation_statistics.json",
    "si4_ablation_statistics.tex",
    "si6_cost_analysis.json",
    "si6_cost_analysis.tex",
    "si_adsorbagent_comparison.tex",
    "si_baselines_comparison.tex",
    "si_iteration_convergence.tex",
    "si_mace_sensitivity.tex",
    "slip_analysis.csv",
    "slip_analysis.json",
}


def rel(path: Path) -> str:
    return str(path.relative_to(REPO_ROOT))


def display(path: Path) -> str:
    try:
        return rel(path)
    except ValueError:
        return str(path)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: Iterable[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fieldnames})


def unique_join(values: Iterable[Any]) -> str:
    cleaned = sorted({str(value) for value in values if value not in {None, ""}})
    return "; ".join(cleaned)


def parse_json(path: Path) -> dict[str, Any]:
    try:
        with path.open(encoding="utf-8") as handle:
            payload = json.load(handle)
    except (OSError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def collect_embedded_configs(data_dir: Path) -> dict[str, str]:
    llm_backends: set[str] = set()
    llm_models: set[str] = set()
    transports: set[str] = set()
    manifest_versions: set[str] = set()
    platforms: set[str] = set()
    calculator_protocols: set[str] = set()
    config_count = 0

    for config_path in sorted(data_dir.rglob("config.json")):
        payload = parse_json(config_path)
        frozen = payload.get("frozen_config")
        if not isinstance(frozen, dict):
            frozen = payload
        config_count += 1
        llm_backends.add(str(frozen.get("llm_backend", "")))
        llm_models.add(str(frozen.get("llm_model", "")))
        transports.add(str(frozen.get("transport_variant", "")))
        manifest_versions.add(str(frozen.get("manifest_version", "")))
        platforms.add(str(frozen.get("platform", "")))

        calculator = frozen.get("calculator_backend", "")
        mace_model = frozen.get("mace_model", "")
        mace_device = frozen.get("mace_device", "")
        mace_precision = frozen.get("mace_precision", "")
        use_dispersion = frozen.get("mace_use_dispersion", "")
        fmax = frozen.get("fmax", "")
        if calculator or mace_model:
            calculator_protocols.add(
                f"{calculator}:model={mace_model}:device={mace_device}:"
                f"precision={mace_precision}:dispersion={use_dispersion}:fmax={fmax}"
            )

    return {
        "embedded_config_count": str(config_count),
        "llm_backends": unique_join(llm_backends),
        "exact_llm_models": unique_join(llm_models),
        "transport_variants": unique_join(transports),
        "manifest_versions": unique_join(manifest_versions),
        "platforms": unique_join(platforms),
        "calculator_protocols": unique_join(calculator_protocols),
    }


def paper_cited_policy(kind: str, canonical_dir: str) -> str:
    if kind in {"ablation", "baseline_random", "baseline_heuristic", "independent_one_shot", "active_control"}:
        return "yes"
    return "review_required"


def governance_flags(result_dir: str, backend: str, manifest_versions: str, exact_models: str) -> tuple[str, str]:
    flags: list[str] = []
    notes: list[str] = []
    if backend in {"adsorbagent", "anthropic_sonnet46", "gemini", "grok4", "openai_gpt54"} and backend in result_dir:
        flags.append("backend_short_label")
        notes.append("Directory backend slug is resolved by exact_llm_models and frozen_config_refs.")
    if ";" in exact_models and not exact_models.startswith("not_applicable"):
        flags.append("mixed_model_ids")
        notes.append("Embedded config snapshots contain multiple model IDs; inspect per-case config.json before aggregating.")
    if DATE_TOKEN_RE.search(result_dir):
        flags.append("date_token")
        notes.append("Date token marks a historical snapshot; prefer registry role/status over date ordering.")
    if OPAQUE_VERSION_RE.search(result_dir) or "retry" in result_dir or "dryrun" in result_dir:
        flags.append("opaque_version_or_retry")
        notes.append("Opaque retry/dryrun/version label marks legacy context; do not treat as canonical without paper_cited_policy.")
    if manifest_versions and any("_v" in token for token in manifest_versions.split("; ")):
        flags.append("manifest_version_label")
        notes.append("Manifest version label is documented here; use manifest_paths for the actual frozen file.")
    if any(token in manifest_versions for token in ("ocd_gmae_manifest",)):
        flags.append("legacy_manifest_label")
        notes.append(
            "Embedded config snapshots may retain earlier OCD manifest labels; "
            "use manifest_paths for the current canonical manifest filenames."
        )
    return "; ".join(flags), " ".join(notes)


def run_row_from_qc(qc_row: dict[str, str]) -> dict[str, Any]:
    canonical_dir = qc_row["canonical_dir"]
    data_dir = CANONICAL_ROOT / canonical_dir
    embedded = collect_embedded_configs(data_dir)
    backend = qc_row.get("backend", "")
    exact_models = embedded["exact_llm_models"] or BACKEND_MODEL_FALLBACK.get(backend, "")
    flags, note = governance_flags(canonical_dir, backend, embedded["manifest_versions"], exact_models)
    root_dir = canonical_dir.split("/", 1)[0]
    manifest_path = REPRO_MANIFESTS.get(root_dir, DATASET_MANIFESTS.get(qc_row.get("dataset", ""), ""))

    return {
        "result_dir": f"research/results/canonical_raw/{canonical_dir}",
        "data_layer": "canonical_raw",
        "role": qc_row.get("kind", ""),
        "dataset": qc_row.get("dataset", ""),
        "backend_slug": backend,
        "backend_display": BACKEND_DISPLAY.get(backend, backend),
        "exact_llm_models": exact_models,
        "llm_backends": embedded["llm_backends"],
        "transport_variants": embedded["transport_variants"],
        "frozen_config_refs": FROZEN_CONFIG_REFS.get(backend, ""),
        "embedded_config_count": embedded["embedded_config_count"],
        "manifest_versions": embedded["manifest_versions"],
        "manifest_paths": manifest_path,
        "calculator_protocols": embedded["calculator_protocols"],
        "summary_file": qc_row.get("summary_file", ""),
        "summary_rows": qc_row.get("summary_rows", ""),
        "observed_case_count": qc_row.get("observed_case_count", ""),
        "observed_variant_count": qc_row.get("observed_variant_count", ""),
        "result_json_count": qc_row.get("result_json_count", ""),
        "traj_count": qc_row.get("traj_count", ""),
        "paper_cited_policy": paper_cited_policy(qc_row.get("kind", ""), canonical_dir),
        "naming_flags": flags,
        "governance_note": note or qc_row.get("notes", ""),
    }


def adsorbagent_root_row() -> dict[str, Any]:
    summary = RESULTS / "adsorbagent_mace_gpt54" / "comparison.csv"
    row_count = ""
    if summary.exists():
        row_count = str(max(0, sum(1 for _ in summary.open(encoding="utf-8")) - 1))
    return {
        "result_dir": "research/results/adsorbagent_mace_gpt54",
        "data_layer": "root_paper_source",
        "role": "paper_facing_adsorbagent_comparison",
        "dataset": "CMU20",
        "backend_slug": "adsorbagent",
        "backend_display": BACKEND_DISPLAY["adsorbagent"],
        "exact_llm_models": BACKEND_MODEL_FALLBACK["adsorbagent"],
        "llm_backends": "",
        "transport_variants": "",
        "frozen_config_refs": "",
        "embedded_config_count": "0",
        "manifest_versions": "",
        "manifest_paths": DATASET_MANIFESTS["CMU20"],
        "calculator_protocols": "Adsorb-Agent comparison source; see comparison_stats.json",
        "summary_file": "comparison.csv",
        "summary_rows": row_count,
        "observed_case_count": row_count,
        "observed_variant_count": "",
        "result_json_count": "0",
        "traj_count": "",
        "paper_cited_policy": "yes",
        "naming_flags": "backend_short_label",
        "governance_note": "Root-level path is intentionally retained because README and paper-facing sources cite it.",
    }


def rebuild_run_registry(output: Path) -> None:
    rows = [run_row_from_qc(row) for row in read_csv(QC_PATH)]
    if (RESULTS / "adsorbagent_mace_gpt54").exists():
        rows.append(adsorbagent_root_row())
    rows.sort(key=lambda row: row["result_dir"])

    write_csv(
        output,
        rows,
        [
            "result_dir",
            "data_layer",
            "role",
            "dataset",
            "backend_slug",
            "backend_display",
            "exact_llm_models",
            "llm_backends",
            "transport_variants",
            "frozen_config_refs",
            "embedded_config_count",
            "manifest_versions",
            "manifest_paths",
            "calculator_protocols",
            "summary_file",
            "summary_rows",
            "observed_case_count",
            "observed_variant_count",
            "result_json_count",
            "traj_count",
            "paper_cited_policy",
            "naming_flags",
            "governance_note",
        ],
    )


def count_rows(path: Path) -> str:
    if path.suffix not in CSV_SUFFIXES:
        return ""
    try:
        with path.open(encoding="utf-8") as handle:
            return str(max(0, sum(1 for _ in handle) - 1))
    except OSError:
        return ""


def count_host_path_matches(path: Path) -> str:
    if path.is_dir():
        files = [child for child in path.rglob("*") if child.is_file() and child.suffix in {".csv", ".json", ".md"}]
    else:
        files = [path] if path.suffix in {".csv", ".json", ".md"} else []

    count = 0
    for file_path in files:
        try:
            count += len(HOST_PATH_RE.findall(file_path.read_text(encoding="utf-8", errors="ignore")))
        except OSError:
            continue
    return str(count)


def classify_analysis(path: Path) -> tuple[str, str, str]:
    name = path.name
    historical_dir_tokens = ("snapshot", "pulled", "delivery", "clean" + "_ablation")
    if path.is_dir() and any(token in name for token in historical_dir_tokens):
        return (
            "historical_snapshot_or_delivery",
            "legacy_context",
            "Date-stamped bundle; use only when reproducing that historical analysis pass.",
        )
    if path.is_dir() and name.startswith("panel_b_assets_"):
        return ("figure_asset_bundle", "paper_facing_auxiliary", "Generated Panel B assets with date token for audit.")
    if path.is_dir() and name == "dft_iteration_alignment":
        return ("diagnostic_case_study", "paper_facing_auxiliary", "Case-study alignment outputs.")
    if name in AUTHORITATIVE_ANALYSIS:
        return ("paper_facing_analysis", "authoritative", "Preferred paper-facing analysis artifact.")
    if DATE_TOKEN_RE.search(name):
        if path.is_dir():
            return (
                "historical_snapshot_or_delivery",
                "legacy_context",
                "Date-stamped bundle; use only when reproducing that historical analysis pass.",
            )
        return ("date_stamped_analysis", "legacy_or_diagnostic", "Date-stamped file; prefer an authoritative undated table when one exists.")
    if name.startswith("cross_llm") or name.startswith("cmu_") or name.startswith("ocd_"):
        return ("analysis_table", "review_required", "Useful analysis artifact; check README recommended source before citing.")
    return ("analysis_artifact", "review_required", "Not classified as authoritative by registry heuristics.")


def analysis_row(path: Path) -> dict[str, Any]:
    category, preferred_status, note = classify_analysis(path)
    date_tokens = unique_join(DATE_TOKEN_RE.findall(path.name))
    naming_flags = []
    if date_tokens:
        naming_flags.append("date_token")
    if OPAQUE_VERSION_RE.search(path.name):
        naming_flags.append("opaque_version_label")

    return {
        "analysis_path": rel(path),
        "artifact_type": "directory" if path.is_dir() else path.suffix.lstrip("."),
        "category": category,
        "preferred_status": preferred_status,
        "date_tokens": date_tokens,
        "naming_flags": "; ".join(naming_flags),
        "row_count": count_rows(path) if path.is_file() else "",
        "file_count": str(sum(1 for child in path.rglob("*") if child.is_file())) if path.is_dir() else "1",
        "host_path_match_count": count_host_path_matches(path),
        "governance_note": note,
    }


def rebuild_analysis_registry(output: Path) -> None:
    if not ANALYSIS_ROOT.exists():
        write_csv(output, [], [])
        return
    rows = [analysis_row(path) for path in sorted(ANALYSIS_ROOT.iterdir())]
    write_csv(
        output,
        rows,
        [
            "analysis_path",
            "artifact_type",
            "category",
            "preferred_status",
            "date_tokens",
            "naming_flags",
            "row_count",
            "file_count",
            "host_path_match_count",
            "governance_note",
        ],
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-output", type=Path, default=RUN_REGISTRY)
    parser.add_argument("--analysis-output", type=Path, default=ANALYSIS_REGISTRY)
    args = parser.parse_args()

    rebuild_run_registry(args.run_output)
    rebuild_analysis_registry(args.analysis_output)
    print(f"wrote {display(args.run_output)}")
    print(f"wrote {display(args.analysis_output)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
