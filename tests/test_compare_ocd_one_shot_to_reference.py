"""Tests for OCD-GMAE one-shot reference comparison."""

from __future__ import annotations

import csv
import json
import tempfile
import unittest
from pathlib import Path

from research.agent_eval.compare_ocd_one_shot_to_reference import main as compare_main


class TestCompareOcdOneShotToReference(unittest.TestCase):
    """Validate per-backend error aggregation against y_relaxed labels."""

    def _write_csv(self, path: Path, fieldnames: list[str], rows: list[dict[str, str]]) -> None:
        with path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)

    def test_compare_reference_report(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            manifest = tmpdir_path / "manifest.csv"
            left = tmpdir_path / "left.csv"
            right = tmpdir_path / "right.csv"

            self._write_csv(
                manifest,
                [
                    "case_id",
                    "smiles",
                    "adsorbate_name",
                    "surface_family",
                    "selection_bucket",
                    "y_relaxed",
                ],
                [
                    {
                        "case_id": "001",
                        "smiles": "[H]",
                        "adsorbate_name": "H",
                        "surface_family": "intermetallic",
                        "selection_bucket": "cmu_exact",
                        "y_relaxed": "-1.0",
                    },
                    {
                        "case_id": "002",
                        "smiles": "CO",
                        "adsorbate_name": "CO",
                        "surface_family": "compound",
                        "selection_bucket": "small_organic",
                        "y_relaxed": "-2.0",
                    },
                ],
            )
            summary_fields = ["case_id", "status", "best_energy_eV"]
            self._write_csv(
                left,
                summary_fields,
                [
                    {"case_id": "001", "status": "success", "best_energy_eV": "-1.2"},
                    {"case_id": "002", "status": "failed", "best_energy_eV": ""},
                ],
            )
            self._write_csv(
                right,
                summary_fields,
                [
                    {"case_id": "001", "status": "success", "best_energy_eV": "-0.9"},
                    {"case_id": "002", "status": "success", "best_energy_eV": "-2.4"},
                ],
            )

            out_csv = tmpdir_path / "report.csv"
            out_json = tmpdir_path / "report.json"
            code = compare_main(
                [
                    "--manifest",
                    str(manifest),
                    "--summary",
                    f"left={left}",
                    "--summary",
                    f"right={right}",
                    "--output-csv",
                    str(out_csv),
                    "--output-json",
                    str(out_json),
                ]
            )
            self.assertEqual(code, 0)

            report = json.loads(out_json.read_text(encoding="utf-8"))
            self.assertEqual(report["total_case_count"], 2)
            self.assertEqual(report["backend_metrics"]["left"]["success_case_count"], 1)
            self.assertAlmostEqual(report["backend_metrics"]["left"]["mae_eV"], 0.2)
            self.assertEqual(report["backend_metrics"]["right"]["within_threshold"]["0.5"]["count"], 2)
