"""Tests for summarizer report and visualization artifacts."""

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import numpy as np

from adsmind.agent.reporting import build_terminal_tldr, write_summarizer_report
from adsmind.tools.visualization import (
    infer_bonds,
    normalize_render_style,
    render_best_structure_blender,
    render_best_structure_matplotlib,
    render_best_structure_ovito,
    render_best_structure_png,
)


class TestSummarizerReporting(unittest.TestCase):
    """Validate deterministic report generation outside the LLM graph."""

    def test_render_best_structure_png_writes_nonempty_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            xyz = root / "best.xyz"
            xyz.write_text(
                "3\nfixture\n"
                "Pt 0.0 0.0 0.0\n"
                "Pt 2.7 0.0 0.0\n"
                "H 1.35 0.0 1.05\n",
                encoding="utf-8",
            )
            out = root / "best.png"

            render_best_structure_png(xyz, out)

            self.assertTrue(out.exists())
            self.assertGreater(out.stat().st_size, 0)

    def test_render_best_structure_prefers_blender_then_falls_back(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            xyz = root / "best.xyz"
            xyz.write_text(
                "3\nfixture\n"
                "Pt 0.0 0.0 0.0\n"
                "Pt 2.7 0.0 0.0\n"
                "H 1.35 0.0 1.05\n",
                encoding="utf-8",
            )
            out = root / "best.png"

            with patch("adsmind.tools.visualization.render_best_structure_blender") as blender:
                blender.side_effect = RuntimeError("no blender")
                with patch(
                    "adsmind.tools.visualization.render_best_structure_matplotlib"
                ) as fallback:
                    fallback.return_value = out

                    result = render_best_structure_png(xyz, out)

            self.assertEqual(result, out)
            blender.assert_called_once()
            fallback.assert_called_once()

    def test_render_style_env_aliases(self):
        with patch.dict("os.environ", {"ADSMIND_VIS_RENDER_STYLE": "ball-and-stick"}):
            self.assertEqual(normalize_render_style(), "ballstick")
        with patch.dict("os.environ", {"ADSMIND_VIS_RENDER_STYLE": "space_fill"}):
            self.assertEqual(normalize_render_style(), "spacefill")
        with patch.dict("os.environ", {"ADSMIND_VIS_RENDER_STYLE": "ovito"}):
            self.assertEqual(normalize_render_style(), "ovito")
        with patch.dict("os.environ", {"ADSMIND_VIS_RENDER_STYLE": "catdt"}):
            self.assertEqual(normalize_render_style(), "panelb")
        with patch.dict("os.environ", {"ADSMIND_VIS_RENDER_STYLE": "unknown"}):
            self.assertEqual(normalize_render_style(), "panelb")

    def test_only_ballstick_style_infers_bonds(self):
        symbols = ["Pt", "Pt", "H"]
        coords = np.array(
            [
                [0.0, 0.0, 0.0],
                [2.7, 0.0, 0.0],
                [1.35, 0.0, 1.05],
            ],
            dtype=float,
        )

        self.assertGreaterEqual(len(infer_bonds(symbols, coords, style="ballstick")), 1)
        self.assertEqual(infer_bonds(symbols, coords, style="panelb"), [])
        self.assertEqual(infer_bonds(symbols, coords, style="ovito"), [])
        self.assertEqual(infer_bonds(symbols, coords, style="spacefill"), [])

    def test_ovito_style_tries_native_renderer_then_panelb_fallback(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            xyz = root / "best.xyz"
            xyz.write_text(
                "3\nfixture\n"
                "Pt 0.0 0.0 0.0\n"
                "Pt 2.7 0.0 0.0\n"
                "H 1.35 0.0 1.05\n",
                encoding="utf-8",
            )
            out = root / "best.png"

            with patch.dict("os.environ", {"ADSMIND_VIS_RENDER_STYLE": "ovito"}):
                with patch("adsmind.tools.visualization.render_best_structure_ovito") as ovito:
                    ovito.side_effect = RuntimeError("no ovito")
                    with patch("adsmind.tools.visualization.render_best_structure_blender") as blender:
                        blender.return_value = out

                        result = render_best_structure_png(xyz, out)

            self.assertEqual(result, out)
            ovito.assert_called_once()
            blender.assert_called_once()

    def test_blender_renderer_reports_missing_executable(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            xyz = root / "best.xyz"
            xyz.write_text(
                "3\nfixture\n"
                "Pt 0.0 0.0 0.0\n"
                "Pt 2.7 0.0 0.0\n"
                "H 1.35 0.0 1.05\n",
                encoding="utf-8",
            )
            with self.assertRaises(RuntimeError):
                render_best_structure_blender(
                    xyz,
                    root / "best.png",
                    blender_executable="/definitely/missing/blender",
                )

    def test_ovito_renderer_reports_missing_script_or_runtime(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            xyz = root / "best.xyz"
            xyz.write_text(
                "1\nfixture\n"
                "H 0.0 0.0 0.0\n",
                encoding="utf-8",
            )
            with self.assertRaises(RuntimeError):
                render_best_structure_ovito(
                    xyz,
                    root / "best.png",
                    ovito_python="/definitely/missing/python",
                )

    def test_matplotlib_renderer_still_writes_nonempty_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            xyz = root / "best.xyz"
            xyz.write_text(
                "3\nfixture\n"
                "Pt 0.0 0.0 0.0\n"
                "Pt 2.7 0.0 0.0\n"
                "H 1.35 0.0 1.05\n",
                encoding="utf-8",
            )
            out = root / "fallback.png"

            render_best_structure_matplotlib(xyz, out)

            self.assertTrue(out.exists())
            self.assertGreater(out.stat().st_size, 0)

    def test_success_report_contains_image_and_energy_curve(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            fake_output_root = root / "outputs"
            xyz = root / "best.xyz"
            xyz.write_text(
                "3\nfixture\n"
                "Pt 0.0 0.0 0.0\n"
                "Pt 2.7 0.0 0.0\n"
                "H 1.35 0.0 1.05\n",
                encoding="utf-8",
            )
            state = {
                "session_id": "report-session",
                "user_request": "Find H on Pt.",
                "smiles": "[H]",
                "slab_path": "slabs/pt.xyz",
                "attempt_records": [
                    {
                        "attempt_index": 1,
                        "status": "success",
                        "most_stable_energy_eV": -1.0,
                        "planned_site_type": "ontop",
                        "actual_site_type": "bridge",
                        "is_chemical_slip": True,
                        "is_dissociated": False,
                    },
                    {
                        "attempt_index": 2,
                        "status": "success",
                        "most_stable_energy_eV": -1.2,
                        "planned_site_type": "bridge",
                        "actual_site_type": "bridge",
                        "is_chemical_slip": False,
                        "is_dissociated": False,
                    },
                ],
            }
            target_data = {
                "most_stable_energy_eV": -1.2,
                "best_structure_file": str(xyz),
            }

            with patch("adsmind.tools.common.OUTPUT_ROOT", fake_output_root):
                artifacts = write_summarizer_report(
                    state=state,
                    final_text="The bridge site is best.",
                    target_data=target_data,
                    plan_used={"solution": {"site_type": "bridge"}},
                    source_type="success",
                )

            report = Path(artifacts["summary_report_file"])
            best_png = Path(artifacts["best_configuration_png"])
            curve_png = Path(artifacts["iteration_energy_curve_png"])
            self.assertTrue(report.exists())
            self.assertTrue(best_png.exists())
            self.assertTrue(curve_png.exists())
            text = report.read_text(encoding="utf-8")
            self.assertIn("![Best configuration](best_configuration.png)", text)
            self.assertIn("![Iteration energy curve](iteration_energy_curve.png)", text)
            self.assertIn("-1.200 eV", text)

    def test_failure_report_does_not_require_structure_image(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            fake_output_root = Path(tmpdir) / "outputs"
            state = {
                "session_id": "failure-session",
                "user_request": "Find adsorption.",
                "smiles": "O",
                "slab_path": "slabs/example.xyz",
                "attempt_records": [],
            }

            with patch("adsmind.tools.common.OUTPUT_ROOT", fake_output_root):
                artifacts = write_summarizer_report(
                    state=state,
                    final_text="No stable structure was found.",
                    target_data=None,
                    plan_used=None,
                    source_type="failure",
                )

            report = Path(artifacts["summary_report_file"])
            self.assertTrue(report.exists())
            self.assertIsNone(artifacts["best_configuration_png"])
            self.assertIn("No stable structure was found.", report.read_text(encoding="utf-8"))

    def test_round_section_renders_planner_reasoning_and_tool_logs(self):
        """Each round must surface the LLM's chain of thought and the executor's log lines."""
        with tempfile.TemporaryDirectory() as tmpdir:
            fake_output_root = Path(tmpdir) / "outputs"
            state = {
                "session_id": "reasoning-session",
                "user_request": "Find H on Pt.",
                "smiles": "[H]",
                "slab_path": "slabs/pt.xyz",
                "llm_backend": "openrouter",
                "calculator_backend": "mace",
                "random_seed": 42,
                "relaxation_mode": "fast",
                "max_attempts": 3,
                "attempt_records": [
                    {
                        "attempt_index": 1,
                        "status": "success",
                        "most_stable_energy_eV": -1.5,
                        "planned_site_type": "ontop",
                        "actual_site_type": "ontop",
                        "is_chemical_slip": False,
                        "is_dissociated": False,
                        "bond_change_count": 0,
                        "planner_reasoning": "REASONING_TOKEN_42: I picked ontop because Pt loves H.",
                        "tool_logs": [
                            "Success: Read slab atoms",
                            "Success: E_surface = -1234.5 eV",
                            "Success: Analysis tool executed.",
                        ],
                        "plan": {
                            "reasoning": "REASONING_TOKEN_42: I picked ontop because Pt loves H.",
                            "adsorbate_type": "ReactiveSpecies",
                            "solution": {
                                "action": "continue",
                                "site_type": "ontop",
                                "surface_binding_atoms": ["Pt"],
                                "adsorbate_binding_indices": [0],
                            },
                        },
                        "history_entry": "Round 1 verdict line",
                    },
                ],
            }

            with patch("adsmind.tools.common.OUTPUT_ROOT", fake_output_root):
                artifacts = write_summarizer_report(
                    state=state,
                    final_text="H prefers ontop on Pt.",
                    target_data={"most_stable_energy_eV": -1.5},
                    plan_used=state["attempt_records"][0]["plan"],
                    source_type="success",
                )

            text = Path(artifacts["summary_report_file"]).read_text(encoding="utf-8")
            self.assertIn("REASONING_TOKEN_42", text)
            self.assertIn("Success: E_surface = -1234.5 eV", text)
            self.assertIn("Round 1 verdict line", text)
            self.assertIn("**🧠 Planner reasoning**", text)
            self.assertIn("**⚙️ Execution**", text)

    def test_validation_failure_block_renders_raw_llm_output(self):
        """When the planner emitted invalid JSON, the raw text must appear in the report."""
        with tempfile.TemporaryDirectory() as tmpdir:
            fake_output_root = Path(tmpdir) / "outputs"
            state = {
                "session_id": "raw-output-session",
                "user_request": "Find adsorption.",
                "smiles": "O",
                "slab_path": "slabs/example.xyz",
                "attempt_records": [],
                "validation_attempt_records": [
                    {
                        "for_round": 1,
                        "validation_index": 1,
                        "failed_plan_reasoning": None,
                        "failed_plan": None,
                        "failed_raw_output": "RAW_LLM_BLURB_999 not actually JSON",
                        "error": "Planner output format error",
                    },
                ],
            }

            with patch("adsmind.tools.common.OUTPUT_ROOT", fake_output_root):
                artifacts = write_summarizer_report(
                    state=state,
                    final_text="Failed.",
                    target_data=None,
                    plan_used=None,
                    source_type="failure",
                )

            text = Path(artifacts["summary_report_file"]).read_text(encoding="utf-8")
            self.assertIn("Validation retry 1", text)
            self.assertIn("RAW_LLM_BLURB_999 not actually JSON", text)
            self.assertIn("Raw LLM output", text)

    def test_termination_record_renders_as_dedicated_round(self):
        """When the planner emits action=terminate, its reasoning must be visible."""
        with tempfile.TemporaryDirectory() as tmpdir:
            fake_output_root = Path(tmpdir) / "outputs"
            state = {
                "session_id": "terminate-session",
                "user_request": "Find adsorption.",
                "smiles": "O",
                "slab_path": "slabs/example.xyz",
                "attempt_records": [
                    {
                        "attempt_index": 1,
                        "status": "success",
                        "most_stable_energy_eV": -1.0,
                        "planned_site_type": "ontop",
                        "actual_site_type": "ontop",
                        "is_chemical_slip": False,
                        "is_dissociated": False,
                        "bond_change_count": 0,
                        "planner_reasoning": "First round.",
                        "tool_logs": ["Success"],
                        "plan": {"solution": {"site_type": "ontop"}},
                        "history_entry": "round 1 ok",
                    },
                ],
                "termination_record": {
                    "round": 2,
                    "reasoning": "TERMINATION_REASON_123: All viable sites converged.",
                    "plan": {"solution": {"action": "terminate"}, "reasoning": "..."},
                },
            }

            with patch("adsmind.tools.common.OUTPUT_ROOT", fake_output_root):
                artifacts = write_summarizer_report(
                    state=state,
                    final_text="Done.",
                    target_data={"most_stable_energy_eV": -1.0},
                    plan_used=state["attempt_records"][0]["plan"],
                    source_type="success",
                )

            text = Path(artifacts["summary_report_file"]).read_text(encoding="utf-8")
            self.assertIn("Agent decided to terminate", text)
            self.assertIn("TERMINATION_REASON_123", text)
            self.assertIn("Agent terminated early", text)  # TL;DR mention

    def test_setup_section_includes_reproducibility_metadata(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            fake_output_root = Path(tmpdir) / "outputs"
            state = {
                "session_id": "repro-session",
                "user_request": "Find H on Pt.",
                "smiles": "[H]",
                "slab_path": "slabs/pt.xyz",
                "llm_backend": "openrouter",
                "llm_config": {"model": "google/gemini-2.5-pro"},
                "calculator_backend": "mace",
                "calculator_config": {"model": "small"},
                "random_seed": 137,
                "relaxation_mode": "standard",
                "max_attempts": 5,
                "attempt_records": [],
            }

            with patch("adsmind.tools.common.OUTPUT_ROOT", fake_output_root):
                artifacts = write_summarizer_report(
                    state=state,
                    final_text="No result.",
                    target_data=None,
                    plan_used=None,
                    source_type="failure",
                )

            text = Path(artifacts["summary_report_file"]).read_text(encoding="utf-8")
            self.assertIn("openrouter", text)
            self.assertIn("google/gemini-2.5-pro", text)
            self.assertIn("mace", text)
            self.assertIn("`small`", text)
            self.assertIn("`137`", text)
            self.assertIn("standard", text)
            self.assertIn("`5`", text)

    def test_terminal_tldr_includes_best_energy_and_per_round_verdicts(self):
        state = {
            "session_id": "tldr-session",
            "smiles": "O",
            "slab_path": "slabs/example.xyz",
            "user_request": "Find water adsorption.",
            "llm_backend": "openrouter",
            "attempt_records": [
                {
                    "attempt_index": 1,
                    "status": "success",
                    "most_stable_energy_eV": -1.0,
                    "history_entry": "round 1 verdict text",
                },
                {
                    "attempt_index": 2,
                    "status": "success",
                    "most_stable_energy_eV": -1.4,
                    "history_entry": "round 2 verdict text",
                },
            ],
            "validation_attempt_records": [],
        }
        tldr = build_terminal_tldr(
            state=state,
            target_data={"most_stable_energy_eV": -1.4},
            plan_used={"solution": {"site_type": "bridge", "surface_binding_atoms": ["Rh", "Ti"]}},
            source_type="success",
        )
        self.assertIn("TL;DR", tldr)
        self.assertIn("-1.400", tldr)
        self.assertIn("bridge", tldr)
        self.assertIn("round 1 verdict text", tldr)
        self.assertIn("round 2 verdict text", tldr)
