#!/usr/bin/env python3
"""Rebuild the canonical raw-result QC manifest.

The CSV is intentionally derived from files on disk instead of maintained by
hand. It records row counts, case counts, variant counts, and the presence of
raw `result.json`/trajectory payloads for every active canonical result set.
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1] / "results" / "canonical_raw"
OUT = ROOT / "MERGE_QC.csv"


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="") as handle:
        return list(csv.DictReader(handle))


def count_rows(path: Path) -> str:
    if not path.exists():
        return ""
    return str(max(0, sum(1 for _ in path.open()) - 1))


def cases_from_csv(path: Path) -> set[str]:
    if not path.exists():
        return set()
    cases: set[str] = set()
    for row in read_csv_rows(path):
        case_id = row.get("case_id") or row.get("case") or row.get("case_name") or ""
        if case_id:
            cases.add(str(case_id).zfill(2) if str(case_id).isdigit() and len(str(case_id)) < 3 else str(case_id))
    return cases


def variants_from_csv(path: Path) -> set[str]:
    if not path.exists():
        return set()
    return {row.get("variant", "") for row in read_csv_rows(path) if row.get("variant", "")}


def result_json_count(path: Path) -> int:
    return sum(1 for _ in path.rglob("result.json"))


def traj_count(path: Path) -> int:
    return sum(1 for _ in path.rglob("*.traj"))


def xyz_count(path: Path) -> int:
    return sum(1 for _ in path.rglob("*.xyz"))


def _artifact_like(value: str) -> bool:
    return (
        ("artifacts/" in value or value.endswith(".traj") or value.endswith(".xyz"))
        and "generated_slabs/" not in value
    )


def _collect_result_artifact_refs(payload: object) -> list[str]:
    refs: list[str] = []

    def walk(value: object) -> None:
        if isinstance(value, dict):
            for child in value.values():
                walk(child)
        elif isinstance(value, list):
            for child in value:
                walk(child)
        elif isinstance(value, str) and _artifact_like(value):
            refs.append(value)

    if isinstance(payload, dict):
        walk(payload.get("artifact_paths", {}))
        for key in ("best_structure_file", "relaxation_trajectory_file"):
            value = payload.get(key)
            if isinstance(value, str) and _artifact_like(value):
                refs.append(value)
        for item in payload.get("top_structures", []) or []:
            if isinstance(item, dict):
                for key in ("structure_file", "best_structure_file", "relaxation_trajectory_file"):
                    value = item.get(key)
                    if isinstance(value, str) and _artifact_like(value):
                        refs.append(value)
    return refs


def result_artifact_ref_stats(path: Path) -> dict[str, int]:
    stats = {
        "artifact_ref_count": 0,
        "missing_artifact_ref_count": 0,
        "zero_artifact_ref_result_json_count": 0,
        "missing_artifact_ref_result_json_count": 0,
    }
    for result_path in path.rglob("result.json"):
        try:
            payload = json.loads(result_path.read_text())
        except json.JSONDecodeError:
            continue
        refs = _collect_result_artifact_refs(payload)
        if not refs:
            stats["zero_artifact_ref_result_json_count"] += 1
            continue
        missing = 0
        for ref in refs:
            ref_path = Path(ref)
            if not ref_path.is_absolute():
                ref_path = Path.cwd() / ref_path
            if not ref_path.exists():
                missing += 1
        stats["artifact_ref_count"] += len(refs)
        stats["missing_artifact_ref_count"] += missing
        if missing:
            stats["missing_artifact_ref_result_json_count"] += 1
    return stats


def infer_kind(name: str, rel: Path) -> str:
    if "controls" in rel.parts:
        return "active_control"
    if rel.parts[0] == "cmu20" and name.endswith("_ablation"):
        return "ablation"
    if rel.parts[0] == "cmu20" and "random_baseline" in name:
        return "baseline_random"
    if rel.parts[0] == "cmu20" and "heuristic_baseline" in name:
        return "baseline_heuristic"
    if rel.parts[0] == "ocd62" and name.endswith("_ablation"):
        return "ablation"
    if rel.parts[0] == "ocd62_overlap12" and name.endswith("_ablation"):
        return "reproducibility_ablation"
    if rel.parts[0] == "ocd62" and "random_baseline" in name:
        return "baseline_random"
    if rel.parts[0] == "ocd62" and "heuristic_baseline" in name:
        return "baseline_heuristic"
    if name.endswith("_ablation"):
        return "ablation"
    if name.endswith("_one_shot"):
        return "independent_one_shot"
    if "random_baseline" in name:
        return "baseline_random"
    if "heuristic_baseline" in name:
        return "baseline_heuristic"
    return "other"


def infer_dataset(name: str, rel: Path) -> str:
    if rel.parts[0] == "cmu20" or name.startswith("cmu20") or "_cmu20" in name:
        return "CMU20"
    if rel.parts[0] == "ocd62" or "_ocd62" in name:
        return "OCD62"
    if rel.parts[0] in {"ocd62", "ocd62_overlap12"}:
        return "OCD62"
    return ""


def infer_backend(name: str) -> str:
    mapping = [
        ("gemini", "gemini"),
        ("grok4", "grok4"),
        ("openai_gpt54", "openai_gpt54"),
        ("gpt54", "openai_gpt54"),
        ("anthropic_sonnet46", "anthropic_sonnet46"),
        ("sonnet46", "anthropic_sonnet46"),
        ("random", "random"),
        ("heuristic", "heuristic"),
        ("adsorbagent", "adsorbagent"),
    ]
    for key, value in mapping:
        if key in name:
            return value
    return ""


def expected_summary_rows(name: str, rel: Path, summary_file: str) -> str:
    if rel.parts[0] == "cmu20" and name.endswith("_ablation"):
        return "100"
    if rel.parts[0] == "cmu20" and ("baseline" in name or name.endswith("_one_shot")):
        return "20"
    if "controls" in rel.parts and rel.parts[0] == "cmu20":
        if name.startswith("mace_large_gpt54"):
            return "20"
        if name.startswith("multiseed_gpt54"):
            return "20"
        if name.startswith("adsorbagent_single_config_gpt54"):
            return "20"
    if "controls" in rel.parts and rel.parts[0] == "ocd62":
        if name.startswith("mace_large_gpt54"):
            return "10"
    if rel.parts[0] == "ocd62":
        if name.endswith("_ablation"):
            return "310"
        if name == "random_baseline_n20":
            return "62"
        if name == "heuristic_baseline":
            return "62"
    if rel.parts[0] == "ocd62_overlap12" and name.endswith("_ablation"):
        return "60"
    return ""


def add_entry(data_dir: Path, rows: list[dict[str, str]]) -> None:
    rel = data_dir.relative_to(ROOT)
    name = data_dir.name
    if "source_summaries" in rel.parts:
        return

    summary_candidates = [
        path
        for path in (data_dir / "ablation_summary.csv", data_dir / "summary.csv", data_dir / "single_shot_summary.csv")
        if path.exists()
    ]
    if not summary_candidates and not any(data_dir.rglob("result.json")) and not any(data_dir.glob("*.json")):
        return

    if not summary_candidates:
        summary_file = "summary.json" if (data_dir / "summary.json").exists() else ""
        artifact_stats = result_artifact_ref_stats(data_dir)
        rows.append(
            {
                "canonical_dir": str(rel),
                "kind": infer_kind(name, rel),
                "dataset": infer_dataset(name, rel),
                "backend": infer_backend(name),
                "summary_file": summary_file,
                "summary_rows": "",
                "expected_summary_rows": "",
                "single_shot_summary_rows": "",
                "observed_case_count": "",
                "observed_variant_count": "",
                "result_json_count": str(result_json_count(data_dir)),
                "xyz_count": str(xyz_count(data_dir)),
                "traj_count": str(traj_count(data_dir)),
                "artifact_ref_count": str(artifact_stats["artifact_ref_count"]),
                "missing_artifact_ref_count": str(artifact_stats["missing_artifact_ref_count"]),
                "zero_artifact_ref_result_json_count": str(
                    artifact_stats["zero_artifact_ref_result_json_count"]
                ),
                "missing_artifact_ref_result_json_count": str(
                    artifact_stats["missing_artifact_ref_result_json_count"]
                ),
                "notes": "JSON/artifact auxiliary source; no row-wise CSV summary",
            }
        )
        return

    main = data_dir / "ablation_summary.csv" if (data_dir / "ablation_summary.csv").exists() else data_dir / "summary.csv"
    cases = cases_from_csv(main)
    variants = variants_from_csv(main)
    single_rows = count_rows(data_dir / "single_shot_summary.csv") if (data_dir / "single_shot_summary.csv").exists() else ""

    note = ""
    if rel.parts[0] == "cmu20" and name.endswith("_ablation"):
        note = (
            "CMU20 ablation result set with 20 cases and five variants; "
            "single-shot rows are also mirrored in single_shot_summary.csv."
        )
    if rel.parts[0] == "ocd62" and name.endswith("_ablation"):
        note = (
            "OCD62 ablation result set with 62 cases and five variants; "
            "single-shot rows are also mirrored in single_shot_summary.csv."
        )
    if rel.parts[0] == "ocd62_overlap12":
        note = "OCD62 overlap12-only reproducibility repeat; not a separate benchmark."
    if name.startswith("adsorbagent_single_config"):
        note = "Active AA single-config control; CatalystAIgent-style raw files, not AdsMind result.json layout."
    artifact_stats = result_artifact_ref_stats(data_dir)

    rows.append(
        {
            "canonical_dir": str(rel),
            "kind": infer_kind(name, rel),
            "dataset": infer_dataset(name, rel),
            "backend": infer_backend(name),
            "summary_file": main.name,
            "summary_rows": count_rows(main),
            "expected_summary_rows": expected_summary_rows(name, rel, main.name),
            "single_shot_summary_rows": single_rows,
            "observed_case_count": str(len(cases)),
            "observed_variant_count": str(len(variants)),
            "result_json_count": str(result_json_count(data_dir)),
            "xyz_count": str(xyz_count(data_dir)),
            "traj_count": str(traj_count(data_dir)),
            "artifact_ref_count": str(artifact_stats["artifact_ref_count"]),
            "missing_artifact_ref_count": str(artifact_stats["missing_artifact_ref_count"]),
            "zero_artifact_ref_result_json_count": str(
                artifact_stats["zero_artifact_ref_result_json_count"]
            ),
            "missing_artifact_ref_result_json_count": str(
                artifact_stats["missing_artifact_ref_result_json_count"]
            ),
            "notes": note,
        }
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=OUT, help="QC CSV path to write.")
    args = parser.parse_args()

    rows: list[dict[str, str]] = []
    for data_dir in sorted(path for path in ROOT.iterdir() if path.is_dir()):
        if data_dir.name in {"cmu20", "ocd62", "ocd62_overlap12"}:
            if data_dir.name in {"cmu20", "ocd62"}:
                for child in sorted(path for path in data_dir.iterdir() if path.is_dir()):
                    if child.name == "controls":
                        for control in sorted(path for path in child.iterdir() if path.is_dir()):
                            add_entry(control, rows)
                    else:
                        add_entry(child, rows)
            else:
                for run_dir in sorted(path for path in data_dir.iterdir() if path.is_dir()):
                    for child in sorted(path for path in run_dir.iterdir() if path.is_dir()):
                        add_entry(child, rows)
        else:
            add_entry(data_dir, rows)

    fieldnames = [
        "canonical_dir",
        "kind",
        "dataset",
        "backend",
        "summary_file",
        "summary_rows",
        "expected_summary_rows",
        "single_shot_summary_rows",
        "observed_case_count",
        "observed_variant_count",
        "result_json_count",
        "xyz_count",
        "traj_count",
        "artifact_ref_count",
        "missing_artifact_ref_count",
        "zero_artifact_ref_result_json_count",
        "missing_artifact_ref_result_json_count",
        "notes",
    ]
    output = args.output
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    try:
        display_path = output.relative_to(Path.cwd())
    except ValueError:
        display_path = output
    print(f"wrote {display_path} rows={len(rows)}")


if __name__ == "__main__":
    main()
