"""Tests for the research-side benchmark tooling."""

import csv
import json
import os
import tempfile
import unittest
from pathlib import Path

from research.agent_eval.common import (
    DryRunExecutor,
    build_initial_state_for_case,
    load_frozen_config,
    load_manifest,
    resolve_runtime_flags,
    summarize_directory,
)
from research.agent_eval.compare_llm_ablation import main as compare_llm_ablation_main
from research.agent_eval.compare_adsorbagent import main as compare_main
from research.agent_eval.package_results import main as package_main
from research.agent_eval.run_batch import main as run_batch_main
from research.agent_eval.run_case import execute_case
from research.agent_eval.summarize_runs import main as summarize_main


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "research/agent_eval/manifests/cmu_manifest.csv"
CONFIG = ROOT / "research/agent_eval/configs/frozen_config.json"


class TestAgentEvalTools(unittest.TestCase):
    """Validate manifest/config parsing and dry-run runner behavior."""

    def test_manifest_and_frozen_config_parse(self):
        manifest = load_manifest(MANIFEST)
        config = load_frozen_config(CONFIG)
        self.assertEqual(len(manifest), 20)
        self.assertEqual(config["llm_model"], "gemini-2.5-pro")
        self.assertEqual(config["mace_model"], "small")

    def test_resolve_runtime_flags_drops_none_relaxation_values(self):
        flags = resolve_runtime_flags(load_frozen_config(CONFIG))
        self.assertEqual(flags["relaxation_config"], {"fmax": 0.10})

    def test_build_initial_state_resolves_manifest_slab_path_to_repo_root(self):
        case_row = load_manifest(MANIFEST)[0]
        state = build_initial_state_for_case(
            case_row=case_row,
            frozen_config=load_frozen_config(CONFIG),
            session_id="session01",
            api_key="dummy",
            repo_root=ROOT,
        )
        self.assertEqual(
            Path(state["slab_path"]),
            ROOT / "benchmark_slabs" / "01_Mo3Pd_111.xyz",
        )

    def test_run_case_serializes_result_with_fake_executor(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            case_row = load_manifest(MANIFEST)[0]
            run = execute_case(
                case_row=case_row,
                frozen_config=load_frozen_config(CONFIG),
                output_root=tmpdir,
                executor=DryRunExecutor(),
                dry_run=False,
                repo_root=ROOT,
            )
            self.assertEqual(run.result["status"], "success")
            self.assertTrue(run.config_path.exists())
            self.assertTrue(run.result_path.exists())
            self.assertTrue(run.log_path.exists())
            self.assertIn("best_structure_file", run.result["artifact_paths"])

    def test_run_case_keeps_partial_state_when_stream_raises(self):
        class StreamThenFailExecutor:
            def stream(self, initial_state, config=None, stream_mode="values"):
                yielded = dict(initial_state)
                yielded.update(
                    {
                        "history": ["attempt-1"],
                        "attempt_records": [
                            {
                                "status": "success",
                                "is_dissociated": False,
                                "bond_change_count": 0,
                                "is_chemical_slip": False,
                            }
                        ],
                        "best_result": {
                            "most_stable_energy_eV": -2.5,
                            "analysis_json": {
                                "site_analysis": {"actual_site_type": "bridge"},
                            },
                        },
                    }
                )
                yield yielded
                raise RuntimeError("quota exhausted")

        with tempfile.TemporaryDirectory() as tmpdir:
            case_row = load_manifest(MANIFEST)[0]
            run = execute_case(
                case_row=case_row,
                frozen_config=load_frozen_config(CONFIG),
                output_root=tmpdir,
                executor=StreamThenFailExecutor(),
                dry_run=False,
                repo_root=ROOT,
            )
            self.assertEqual(run.result["status"], "success")
            self.assertEqual(run.result["best_energy_eV"], -2.5)
            self.assertIsNone(run.result["error"])

    def test_run_batch_skip_existing_and_summary(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            code = run_batch_main(
                [
                    "--manifest",
                    str(MANIFEST),
                    "--config",
                    str(CONFIG),
                    "--output",
                    tmpdir,
                    "--case-ids",
                    "01,02",
                    "--dry-run",
                ]
            )
            self.assertEqual(code, 0)
            summary_path = Path(tmpdir) / "summary.csv"
            self.assertTrue(summary_path.exists())

            # Second run should skip and still succeed.
            code = run_batch_main(
                [
                    "--manifest",
                    str(MANIFEST),
                    "--config",
                    str(CONFIG),
                    "--output",
                    tmpdir,
                    "--case-ids",
                    "01,02",
                    "--dry-run",
                    "--skip-existing",
                ]
            )
            self.assertEqual(code, 0)

    def test_run_batch_resolves_repo_relative_manifest_and_config_from_nested_cwd(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "out"
            previous_cwd = Path.cwd()
            try:
                os.chdir(tmpdir)
                code = run_batch_main(
                    [
                        "--manifest",
                        "research/agent_eval/manifests/cmu_manifest.csv",
                        "--config",
                        "research/agent_eval/configs/frozen_config.json",
                        "--output",
                        str(output_dir),
                        "--case-ids",
                        "09",
                        "--dry-run",
                    ]
                )
            finally:
                os.chdir(previous_cwd)
            self.assertEqual(code, 0)
            self.assertTrue((output_dir / "09" / "result.json").exists())

    def test_summarize_runs_skips_missing_case_dirs(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            case_dir = Path(tmpdir) / "01"
            case_dir.mkdir(parents=True)
            payload = {
                "case_id": "01",
                "case_metadata": load_manifest(MANIFEST)[0],
                "status": "success",
                "best_energy_eV": -1.0,
                "iteration_count": 1,
                "max_attempts": 5,
                "perfect_count": 1,
                "dissociation_count": 0,
                "rearrangement_count": 0,
                "calc_failure_count": 0,
                "chemical_slip_count": 0,
                "final_site_type": "bridge",
                "converged_tag": False,
                "wall_clock_sec": 1.2,
                "total_input_tokens": 10,
                "total_output_tokens": 5,
                "artifact_paths": {},
            }
            (case_dir / "result.json").write_text(json.dumps(payload), encoding="utf-8")
            code = summarize_main(["--output", tmpdir])
            self.assertEqual(code, 0)
            rows = summarize_directory(tmpdir)
            self.assertEqual(len(rows), 1)

    def test_compare_adsorbagent_generates_stats(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            adsmind_summary = Path(tmpdir) / "summary.csv"
            adsorb_agent = Path(tmpdir) / "adsorbagent.csv"
            with adsmind_summary.open("w", encoding="utf-8", newline="") as handle:
                writer = csv.DictWriter(
                    handle,
                    fieldnames=[
                        "case_id",
                        "slab_file",
                        "adsorbate_name",
                        "best_energy_eV",
                        "iteration_count",
                        "status",
                        "chemical_slip_count",
                        "dissociation_count",
                    ],
                )
                writer.writeheader()
                writer.writerow(
                    {
                        "case_id": "01",
                        "slab_file": "benchmark_slabs/01_Mo3Pd_111.xyz",
                        "adsorbate_name": "H",
                        "best_energy_eV": "-2.5",
                        "iteration_count": "3",
                        "status": "success",
                        "chemical_slip_count": "1",
                        "dissociation_count": "0",
                    }
                )
                writer.writerow(
                    {
                        "case_id": "02",
                        "slab_file": "benchmark_slabs/02_Mo3Pd_111.xyz",
                        "adsorbate_name": "NNH",
                        "best_energy_eV": "-3.9",
                        "iteration_count": "5",
                        "status": "success",
                        "chemical_slip_count": "2",
                        "dissociation_count": "1",
                    }
                )
            with adsorb_agent.open("w", encoding="utf-8", newline="") as handle:
                writer = csv.DictWriter(
                    handle,
                    fieldnames=[
                        "case_id",
                        "adsorbagent_best_energy",
                        "adsorbagent_success",
                        "adsorbagent_configs_tested",
                        "notes",
                    ],
                )
                writer.writeheader()
                writer.writerow(
                    {
                        "case_id": "01",
                        "adsorbagent_best_energy": "-2.3",
                        "adsorbagent_success": "true",
                        "adsorbagent_configs_tested": "5",
                        "notes": "fixture-1",
                    }
                )
                writer.writerow(
                    {
                        "case_id": "02",
                        "adsorbagent_best_energy": "-3.8",
                        "adsorbagent_success": "false",
                        "adsorbagent_configs_tested": "7",
                        "notes": "fixture-2",
                    }
                )
            output_dir = Path(tmpdir) / "comparison"
            code = compare_main(
                [
                    "--adsmind-summary",
                    str(adsmind_summary),
                    "--adsorbagent-results",
                    str(adsorb_agent),
                    "--output",
                    str(output_dir),
                ]
            )
            self.assertEqual(code, 0)
            self.assertTrue((output_dir / "comparison.csv").exists())
            self.assertTrue((output_dir / "comparison_stats.json").exists())

    def test_compare_llm_ablation_generates_outputs(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            left = Path(tmpdir) / "left.csv"
            right = Path(tmpdir) / "right.csv"
            fieldnames = [
                "case_id",
                "variant",
                "best_energy",
                "delta_vs_full",
                "iterations",
                "success",
                "tokens_used",
            ]
            with left.open("w", encoding="utf-8", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerow(
                    {
                        "case_id": "01",
                        "variant": "full",
                        "best_energy": "-1.0",
                        "delta_vs_full": "0.0",
                        "iterations": "5",
                        "success": "true",
                        "tokens_used": "100",
                    }
                )
                writer.writerow(
                    {
                        "case_id": "01",
                        "variant": "single_shot",
                        "best_energy": "-0.5",
                        "delta_vs_full": "0.5",
                        "iterations": "1",
                        "success": "true",
                        "tokens_used": "10",
                    }
                )
            with right.open("w", encoding="utf-8", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerow(
                    {
                        "case_id": "01",
                        "variant": "full",
                        "best_energy": "-1.1",
                        "delta_vs_full": "0.0",
                        "iterations": "5",
                        "success": "true",
                        "tokens_used": "120",
                    }
                )
                writer.writerow(
                    {
                        "case_id": "01",
                        "variant": "single_shot",
                        "best_energy": "-0.2",
                        "delta_vs_full": "0.7",
                        "iterations": "1",
                        "success": "true",
                        "tokens_used": "12",
                    }
                )

            output_csv = Path(tmpdir) / "comparison.csv"
            output_json = Path(tmpdir) / "comparison.json"
            code = compare_llm_ablation_main(
                [
                    "--left-summary",
                    str(left),
                    "--right-summary",
                    str(right),
                    "--left-label",
                    "gemini",
                    "--right-label",
                    "grok",
                    "--output-csv",
                    str(output_csv),
                    "--output-json",
                    str(output_json),
                ]
            )
            self.assertEqual(code, 0)
            self.assertTrue(output_csv.exists())
            self.assertTrue(output_json.exists())
            data = json.loads(output_json.read_text(encoding="utf-8"))
            self.assertEqual(data["overall"]["row_count"], 2)
            self.assertEqual(data["largest_disagreement"]["variant"], "single_shot")

    def test_package_results_builds_expected_directories(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            benchmark_dir = Path(tmpdir) / "benchmark"
            benchmark_dir.mkdir()
            summary_path = benchmark_dir / "summary.csv"
            with summary_path.open("w", encoding="utf-8", newline="") as handle:
                writer = csv.DictWriter(
                    handle,
                    fieldnames=[
                        "case_id",
                        "status",
                        "best_energy_eV",
                        "best_structure_file",
                        "dissociation_count",
                    ],
                )
                writer.writeheader()
                writer.writerow(
                    {
                        "case_id": "01",
                        "status": "success",
                        "best_energy_eV": "-1.23",
                        "best_structure_file": "",
                        "dissociation_count": "0",
                    }
                )

            output_dir = Path(tmpdir) / "package"
            code = package_main(
                [
                    "--benchmark-dir",
                    str(benchmark_dir),
                    "--output",
                    str(output_dir),
                    "--manifest",
                    str(MANIFEST),
                    "--config",
                    str(CONFIG),
                ]
            )
            self.assertEqual(code, 0)
            self.assertTrue((output_dir / "dft_handoff").exists())
            self.assertTrue((output_dir / "si_package" / "SI-1_prompts").exists())
