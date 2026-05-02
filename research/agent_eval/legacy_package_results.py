"""Package benchmark and ablation outputs for handoff and SI use."""

from __future__ import annotations

import argparse
import csv
import json
import shutil
from pathlib import Path
from typing import Dict, Optional


DFT_HANDOFF_CASES = ["01", "02", "09", "10", "14"]


def load_summary(summary_path: Path) -> Dict[str, Dict[str, str]]:
    """Load a summary CSV and index it by case id."""
    if not summary_path.exists():
        return {}
    with summary_path.open("r", encoding="utf-8", newline="") as handle:
        return {row["case_id"].zfill(2): row for row in csv.DictReader(handle)}


def copy_tree_if_exists(source: Path, target: Path) -> None:
    """Copy a directory tree if it exists."""
    if not source.exists():
        return
    if target.exists():
        shutil.rmtree(target)
    shutil.copytree(source, target)


def main(argv: Optional[list[str]] = None) -> int:
    """CLI entrypoint for packaging benchmark/ablation deliverables."""
    parser = argparse.ArgumentParser(description="Package AdsMind experiment outputs.")
    parser.add_argument("--benchmark-dir", required=True, help="Benchmark run directory")
    parser.add_argument("--ablation-dir", default="", help="Optional ablation run directory")
    parser.add_argument("--output", required=True, help="Packaging output directory")
    parser.add_argument("--manifest", required=True, help="Path to cmu_manifest.csv")
    parser.add_argument("--config", required=True, help="Path to frozen_config.json")
    args = parser.parse_args(argv)

    benchmark_dir = Path(args.benchmark_dir)
    ablation_dir = Path(args.ablation_dir) if args.ablation_dir else None
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    benchmark_summary = load_summary(benchmark_dir / "summary.csv")
    dft_dir = output_dir / "dft_handoff"
    dft_dir.mkdir(parents=True, exist_ok=True)
    for case_id in DFT_HANDOFF_CASES:
        row = benchmark_summary.get(case_id)
        case_dir = dft_dir / f"case_{case_id}"
        case_dir.mkdir(parents=True, exist_ok=True)
        readme_path = case_dir / "README.md"
        if not row:
            readme_path.write_text(
                "Benchmark summary not available for this case yet.\n",
                encoding="utf-8",
            )
            continue
        best_structure = row.get("best_structure_file", "")
        energy = row.get("best_energy_eV", "")
        if best_structure and Path(best_structure).exists():
            shutil.copy2(best_structure, case_dir / "BEST_structure.xyz")
        with (case_dir / "mace_energy.json").open("w", encoding="utf-8") as handle:
            json.dump(
                {
                    "case_id": case_id,
                    "best_energy_eV": energy,
                    "source_summary": str(benchmark_dir / "summary.csv"),
                },
                handle,
                indent=2,
                ensure_ascii=False,
            )
        readme_path.write_text(
            (
                f"Case {case_id}\n"
                f"Best energy: {energy}\n"
                "Run the corresponding DFT validation from the copied BEST_structure.xyz.\n"
            ),
            encoding="utf-8",
        )

    si_root = output_dir / "si_package"
    (si_root / "SI-1_prompts").mkdir(parents=True, exist_ok=True)
    shutil.copy2(args.config, si_root / "SI-1_prompts" / Path(args.config).name)
    shutil.copy2(args.manifest, si_root / "SI-1_prompts" / Path(args.manifest).name)

    benchmark_target = si_root / "SI-2_benchmark_data"
    copy_tree_if_exists(benchmark_dir, benchmark_target)

    if ablation_dir:
        ablation_target = si_root / "SI-4_ablation_data"
        copy_tree_if_exists(ablation_dir, ablation_target)

    cost_dir = si_root / "SI-6_cost_analysis"
    cost_dir.mkdir(parents=True, exist_ok=True)
    benchmark_summary_path = benchmark_dir / "summary.csv"
    if benchmark_summary_path.exists():
        shutil.copy2(benchmark_summary_path, cost_dir / "benchmark_summary.csv")

    failure_dir = si_root / "SI-8_failure_analysis"
    failure_dir.mkdir(parents=True, exist_ok=True)
    failures = []
    for case_id, row in benchmark_summary.items():
        if row.get("status") != "success" or int(row.get("dissociation_count") or 0) > 0:
            failures.append(row)
    if failures:
        with (failure_dir / "failure_cases.csv").open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=sorted(failures[0].keys()))
            writer.writeheader()
            writer.writerows(failures)
    else:
        (failure_dir / "failure_cases.csv").write_text("case_id\n", encoding="utf-8")

    print(output_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
