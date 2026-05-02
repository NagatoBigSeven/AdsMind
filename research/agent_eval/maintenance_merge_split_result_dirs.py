"""Merge split experiment result directories into canonical raw directories.

The merge is intentionally conservative:
- source directories are copied into a new canonical location;
- root summaries are rebuilt or concatenated instead of blindly reusing stale
  source-level summary files;
- source-level summaries/statistics are preserved under ``source_summaries``;
- sources are deleted only after all QC checks pass.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional


ROOT = Path(__file__).resolve().parents[2]
RESULTS = ROOT / "research/results"
CANONICAL_ROOT = RESULTS / "canonical_raw"

VARIANT_ORDER = {
    "full": 0,
    "no_slip": 1,
    "no_forbid": 2,
    "no_termination": 3,
    "single_shot": 4,
}

HOST_PREFIX_REPLACEMENTS = (
    "/data/zongmin/workspace/AdsMind/",
    "/Users/nagato/workspace/AdsMind/",
)
HOME_WORKSPACE_RE = re.compile(r"/home/[A-Za-z0-9._-]+/workspace/AdsMind/")


@dataclass(frozen=True)
class MergeSpec:
    canonical: str
    kind: str
    dataset: str
    backend: str
    expected_cases: int
    expected_variants: int
    sources: tuple[str, ...]


MERGES: tuple[MergeSpec, ...] = (
    MergeSpec(
        "cmu20_gemini_ablation",
        "ablation",
        "CMU20",
        "Gemini 2.5 Pro",
        20,
        5,
        ("cmu20_gemini_ablation", "cmu20_gemini_ablation"),
    ),
    MergeSpec(
        "cmu20_grok4_ablation",
        "ablation",
        "CMU20",
        "Grok-4",
        20,
        5,
        ("cmu20_grok4_ablation", "cmu20_grok4_ablation"),
    ),
    MergeSpec(
        "cmu20_openai_gpt54_ablation",
        "ablation",
        "CMU20",
        "GPT-5.4",
        20,
        5,
        ("cmu20_openai_gpt54_ablation", "cmu_extra5_cmu20_openai_gpt54_ablation"),
    ),
    MergeSpec(
        "cmu20_anthropic_sonnet46_ablation",
        "ablation",
        "CMU20",
        "Claude Sonnet 4.6",
        20,
        5,
        (
            "cmu20_anthropic_sonnet46_ablation",
            "cmu_extra5_cmu20_anthropic_sonnet46_ablation",
        ),
    ),
    MergeSpec(
        "ocd24_gemini_ablation",
        "ablation",
        "OCD-GMAE-24",
        "Gemini 2.5 Pro",
        24,
        5,
        ("ocd24_gemini_ablation", "ocd24_gemini_ablation"),
    ),
    MergeSpec(
        "ocd24_grok4_ablation",
        "ablation",
        "OCD-GMAE-24",
        "Grok-4",
        24,
        5,
        ("ocd24_grok4_ablation", "ocd24_grok4_ablation"),
    ),
    MergeSpec(
        "ocd24_openai_gpt54_ablation",
        "ablation",
        "OCD-GMAE-24",
        "GPT-5.4",
        24,
        5,
        ("ocd_gmae_cmu20_openai_gpt54_ablation", "ocd_gmae_24_extra14_cmu20_openai_gpt54_ablation"),
    ),
    MergeSpec(
        "ocd24_anthropic_sonnet46_ablation",
        "ablation",
        "OCD-GMAE-24",
        "Claude Sonnet 4.6",
        24,
        5,
        (
            "ocd_gmae_cmu20_anthropic_sonnet46_ablation",
            "ocd_gmae_24_extra14_cmu20_anthropic_sonnet46_ablation",
        ),
    ),
    MergeSpec(
        "cmu20_random_baseline_n20",
        "baseline_random",
        "CMU20",
        "random n=20",
        20,
        0,
        ("random_baseline_n20", "random_baseline_cmu_extra5_n20"),
    ),
    MergeSpec(
        "cmu20_heuristic_baseline",
        "baseline_heuristic",
        "CMU20",
        "heuristic",
        20,
        0,
        ("heuristic_baseline", "heuristic_baseline_cmu_extra5"),
    ),
)


def read_csv(path: Path) -> List[Dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: Iterable[Dict[str, Any]], fieldnames: List[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fieldnames})


def read_json(path: Path) -> Dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, ensure_ascii=False)


def rewrite_string_path(value: str, source: str, canonical: str) -> str:
    """Rewrite old split-run paths to the canonical result directory."""
    canonical_prefix = f"research/results/canonical_raw/{canonical}/"
    output = value
    for host_prefix in HOST_PREFIX_REPLACEMENTS:
        output = output.replace(host_prefix, "")
    output = HOME_WORKSPACE_RE.sub("", output)
    replacements = [
        (f"/data/zongmin/workspace/AdsMind/research/results/{source}/", canonical_prefix),
        (f"{ROOT}/research/results/{source}/", canonical_prefix),
        (f"research/results/{source}/", canonical_prefix),
        (f"/data/zongmin/workspace/AdsMind/research/results/canonical_raw/{canonical}/", canonical_prefix),
        (f"{ROOT}/research/results/canonical_raw/{canonical}/", canonical_prefix),
    ]
    for old, new in replacements:
        output = output.replace(old, new)
    return output


def rewrite_paths(obj: Any, source: str, canonical: str) -> Any:
    if isinstance(obj, str):
        return rewrite_string_path(obj, source, canonical)
    if isinstance(obj, list):
        return [rewrite_paths(item, source, canonical) for item in obj]
    if isinstance(obj, dict):
        return {key: rewrite_paths(value, source, canonical) for key, value in obj.items()}
    return obj


def rewrite_json_paths(path: Path, source: str, canonical: str) -> None:
    try:
        payload = read_json(path)
    except json.JSONDecodeError:
        return
    rewritten = rewrite_paths(payload, source, canonical)
    write_json(path, rewritten)


def case_sort_key(case_id: Any) -> tuple[int, str]:
    text = str(case_id)
    try:
        return int(text), text
    except ValueError:
        return 10**9, text


def copy_root_summaries(src: Path, source_summary_dir: Path, canonical: str) -> None:
    source_summary_dir.mkdir(parents=True, exist_ok=True)
    for item in sorted(src.iterdir()):
        if item.is_file() and item.suffix in {".csv", ".json", ".md", ".txt"}:
            target = source_summary_dir / f"{src.name}__{item.name}"
            shutil.copy2(item, target)
            text = target.read_text(encoding="utf-8")
            target.write_text(rewrite_string_path(text, src.name, canonical), encoding="utf-8")


def copy_ablation_tree(src: Path, dest: Path, provenance: List[Dict[str, Any]]) -> None:
    for variant_dir in sorted([p for p in src.iterdir() if p.is_dir()]):
        variant = variant_dir.name
        for case_dir in sorted([p for p in variant_dir.iterdir() if p.is_dir()]):
            target = dest / variant / case_dir.name
            if target.exists():
                raise RuntimeError(f"Refusing to overwrite duplicate ablation case: {target}")
            shutil.copytree(case_dir, target)
            for json_path in target.glob("*.json"):
                rewrite_json_paths(json_path, src.name, dest.name)
            provenance.append(
                {
                    "canonical_dir": dest.name,
                    "kind": "ablation",
                    "variant": variant,
                    "case_id": case_dir.name,
                    "source_dir": src.name,
                    "source_case_dir": str(case_dir.relative_to(RESULTS)),
                }
            )


def copy_baseline_tree(src: Path, dest: Path, provenance: List[Dict[str, Any]]) -> None:
    for case_dir in sorted([p for p in src.iterdir() if p.is_dir()]):
        target = dest / case_dir.name
        if target.exists():
            raise RuntimeError(f"Refusing to overwrite duplicate baseline case: {target}")
        shutil.copytree(case_dir, target)
        for json_path in target.glob("*.json"):
            rewrite_json_paths(json_path, src.name, dest.name)
        provenance.append(
            {
                "canonical_dir": dest.name,
                "kind": "baseline",
                "variant": "",
                "case_id": case_dir.name,
                "source_dir": src.name,
                "source_case_dir": str(case_dir.relative_to(RESULTS)),
            }
        )


def merge_ablation_summary(spec: MergeSpec, dest: Path) -> List[Dict[str, str]]:
    rows: List[Dict[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for source in spec.sources:
        summary_path = RESULTS / source / "ablation_summary.csv"
        if not summary_path.exists():
            raise FileNotFoundError(summary_path)
        for row in read_csv(summary_path):
            key = (row["case_id"], row["variant"])
            if key in seen:
                raise RuntimeError(f"Duplicate summary row for {spec.canonical}: {key}")
            seen.add(key)
            row["_source_dir"] = source
            rows.append(row)
    rows.sort(key=lambda row: (case_sort_key(row["case_id"]), VARIANT_ORDER.get(row["variant"], 99)))
    fieldnames = [field for field in rows[0] if field != "_source_dir"]
    write_csv(dest / "ablation_summary.csv", rows, fieldnames)
    return rows


def baseline_row_from_result(path: Path, kind: str) -> Dict[str, Any]:
    result = read_json(path)
    row: Dict[str, Any] = {
        "case_id": result.get("case_id", path.parent.name),
        "status": result.get("status"),
        "successful": result.get("successful"),
        "failed": result.get("failed"),
        "best_energy": result.get("best_energy_eV"),
        "mean_energy": result.get("mean_energy_eV"),
        "std_energy": result.get("std_energy_eV"),
        "best_structure_file": result.get("best_structure_file", ""),
        "wall_clock_sec": result.get("wall_clock_sec"),
    }
    if kind == "baseline_random":
        row["n_random"] = result.get("n_random")
    else:
        row["n_sites"] = result.get("n_sites")
    return row


def merge_baseline_summary(spec: MergeSpec, dest: Path) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    cases: List[Dict[str, Any]] = []
    seen: set[str] = set()
    for result_path in sorted(dest.glob("*/result.json")):
        case_id = result_path.parent.name
        if case_id in seen:
            raise RuntimeError(f"Duplicate baseline case for {spec.canonical}: {case_id}")
        seen.add(case_id)
        rows.append(baseline_row_from_result(result_path, spec.kind))
        cases.append(read_json(result_path))
    rows.sort(key=lambda row: case_sort_key(row["case_id"]))
    cases.sort(key=lambda row: case_sort_key(row.get("case_id", "")))
    if spec.kind == "baseline_random":
        fields = [
            "case_id",
            "n_random",
            "status",
            "successful",
            "failed",
            "best_energy",
            "mean_energy",
            "std_energy",
            "best_structure_file",
            "wall_clock_sec",
        ]
    else:
        fields = [
            "case_id",
            "n_sites",
            "status",
            "successful",
            "failed",
            "best_energy",
            "mean_energy",
            "std_energy",
            "best_structure_file",
            "wall_clock_sec",
        ]
    write_csv(dest / "summary.csv", rows, fields)
    write_json(dest / "summary.json", {"cases": cases})
    return rows


def summarize_status(rows: Iterable[Dict[str, Any]], field: str = "success") -> Dict[str, int]:
    counts: Dict[str, int] = {}
    for row in rows:
        key = str(row.get(field, ""))
        counts[key] = counts.get(key, 0) + 1
    return counts


def merge_one(spec: MergeSpec) -> tuple[List[Dict[str, Any]], Dict[str, Any]]:
    dest = CANONICAL_ROOT / spec.canonical
    if dest.exists():
        shutil.rmtree(dest)
    dest.mkdir(parents=True)
    source_summary_dir = dest / "source_summaries"
    provenance: List[Dict[str, Any]] = []

    for source in spec.sources:
        src = RESULTS / source
        if not src.exists():
            raise FileNotFoundError(src)
        copy_root_summaries(src, source_summary_dir, spec.canonical)
        if spec.kind == "ablation":
            copy_ablation_tree(src, dest, provenance)
        else:
            copy_baseline_tree(src, dest, provenance)

    if spec.kind == "ablation":
        summary_rows = merge_ablation_summary(spec, dest)
        observed_cases = sorted({row["case_id"] for row in summary_rows}, key=case_sort_key)
        observed_variants = sorted({row["variant"] for row in summary_rows}, key=lambda v: VARIANT_ORDER.get(v, 99))
        expected_rows = spec.expected_cases * spec.expected_variants
        notes = []
        if len(summary_rows) != expected_rows:
            notes.append(f"summary_rows {len(summary_rows)} != expected {expected_rows}")
        if len(observed_cases) != spec.expected_cases:
            notes.append(f"case_count {len(observed_cases)} != expected {spec.expected_cases}")
        if len(observed_variants) != spec.expected_variants:
            notes.append(f"variant_count {len(observed_variants)} != expected {spec.expected_variants}")
        merged_stats = {
            "canonical_dir": spec.canonical,
            "kind": spec.kind,
            "dataset": spec.dataset,
            "backend": spec.backend,
            "sources": list(spec.sources),
            "summary_rows": len(summary_rows),
            "cases": observed_cases,
            "variants": observed_variants,
            "success_counts": summarize_status(summary_rows),
            "result_json_count": len(list(dest.glob("*/*/result.json"))),
            "notes": notes,
        }
        write_json(dest / "ablation_stats_merged.json", merged_stats)
        qc = {
            **merged_stats,
            "observed_case_count": len(observed_cases),
            "observed_variant_count": len(observed_variants),
            "expected_summary_rows": expected_rows,
            "notes": "; ".join(notes),
        }
    else:
        summary_rows = merge_baseline_summary(spec, dest)
        observed_cases = sorted({row["case_id"] for row in summary_rows}, key=case_sort_key)
        notes = []
        if len(summary_rows) != spec.expected_cases:
            notes.append(f"summary_rows {len(summary_rows)} != expected {spec.expected_cases}")
        merged_stats = {
            "canonical_dir": spec.canonical,
            "kind": spec.kind,
            "dataset": spec.dataset,
            "backend": spec.backend,
            "sources": list(spec.sources),
            "summary_rows": len(summary_rows),
            "cases": observed_cases,
            "result_json_count": len(list(dest.glob("*/result.json"))),
            "notes": notes,
        }
        write_json(dest / "summary_stats_merged.json", merged_stats)
        qc = {
            **merged_stats,
            "observed_case_count": len(observed_cases),
            "observed_variant_count": "",
            "expected_summary_rows": spec.expected_cases,
            "notes": "; ".join(notes),
        }

    write_json(
        dest / "MERGED_SOURCES.json",
        {
            "canonical_dir": spec.canonical,
            "kind": spec.kind,
            "dataset": spec.dataset,
            "backend": spec.backend,
            "sources": list(spec.sources),
            "source_policy": "same-protocol split runs merged into one canonical raw result directory",
        },
    )
    return provenance, qc


def write_readme() -> None:
    text = """# Canonical Raw Result Directories

This directory contains same-protocol split runs merged into canonical raw
result directories.  It is a storage cleanup layer: paper-facing analysis
tables remain under `research/results/analysis/`.

Merged sources are recorded in each directory's `MERGED_SOURCES.json`, and
global coverage checks are recorded in `MERGE_QC.csv`.

The merge intentionally preserves source summaries under `source_summaries/`
and rebuilds canonical root summaries from per-case rows or `result.json`.
Per-case JSON payloads are path-rewritten so artifact references point to this
canonical directory rather than the deleted split-run directories.  Summary-row
counts, not `result.json` counts, define ablation completion because natural
failed runs may have summary rows without a per-case result payload.
"""
    (CANONICAL_ROOT / "README.md").write_text(text, encoding="utf-8")


def delete_sources(specs: Iterable[MergeSpec]) -> None:
    for spec in specs:
        for source in spec.sources:
            path = RESULTS / source
            if path.exists():
                shutil.rmtree(path)


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--delete-sources",
        action="store_true",
        help="Delete split source directories after all QC checks pass.",
    )
    args = parser.parse_args(argv)

    CANONICAL_ROOT.mkdir(parents=True, exist_ok=True)
    all_provenance: List[Dict[str, Any]] = []
    qc_rows: List[Dict[str, Any]] = []
    for spec in MERGES:
        provenance, qc = merge_one(spec)
        all_provenance.extend(provenance)
        qc_rows.append(qc)

    write_csv(
        CANONICAL_ROOT / "MERGE_PROVENANCE.csv",
        all_provenance,
        ["canonical_dir", "kind", "variant", "case_id", "source_dir", "source_case_dir"],
    )
    write_csv(
        CANONICAL_ROOT / "MERGE_QC.csv",
        qc_rows,
        [
            "canonical_dir",
            "kind",
            "dataset",
            "backend",
            "summary_rows",
            "expected_summary_rows",
            "observed_case_count",
            "observed_variant_count",
            "result_json_count",
            "notes",
        ],
    )
    write_readme()

    bad = [row for row in qc_rows if row.get("notes")]
    if bad:
        for row in bad:
            print(f"QC_FAILED {row['canonical_dir']}: {row['notes']}")
        return 1

    if args.delete_sources:
        delete_sources(MERGES)
    print(CANONICAL_ROOT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
