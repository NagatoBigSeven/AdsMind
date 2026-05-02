"""Tests for summarizer report and visualization artifacts."""

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from adsmind.agent.reporting import write_summarizer_report
from adsmind.tools.visualization import (
    render_best_structure_blender,
    render_best_structure_matplotlib,
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
