"""Tests for one-shot cross-backend spread ranking."""

from __future__ import annotations

import csv
import json
import tempfile
import unittest
from pathlib import Path

from research.agent_eval.rank_one_shot_backend_spread import (
    main as rank_one_shot_backend_spread_main,
)


class TestRankOneShotBackendSpread(unittest.TestCase):
    """Validate ranking and exclusion behavior for one-shot summaries."""

    def _write_summary(self, path: Path, rows: list[dict[str, str]]) -> None:
        fieldnames = [
            "case_id",
            "slab_file",
            "smiles",
            "adsorbate_name",
            "surface_family",
            "reaction_class",
            "status",
            "best_energy_eV",
        ]
        with path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)

    def test_rank_one_shot_backend_spread_sorts_by_descending_range_and_excludes_failures(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            left = tmpdir_path / "left.csv"
            right = tmpdir_path / "right.csv"
            third = tmpdir_path / "third.csv"

            common_rows = [
                {
                    "case_id": "01",
                    "slab_file": "benchmark_slabs/01.xyz",
                    "smiles": "[H]",
                    "adsorbate_name": "H",
                    "surface_family": "intermetallic",
                    "reaction_class": "HER",
                },
                {
                    "case_id": "02",
                    "slab_file": "benchmark_slabs/02.xyz",
                    "smiles": "[OH]",
                    "adsorbate_name": "OH",
                    "surface_family": "monometallic",
                    "reaction_class": "ORR",
                },
            ]
            self._write_summary(
                left,
                [
                    {**common_rows[0], "status": "success", "best_energy_eV": "-1.0"},
                    {**common_rows[1], "status": "failed", "best_energy_eV": ""},
                ],
            )
            self._write_summary(
                right,
                [
                    {**common_rows[0], "status": "success", "best_energy_eV": "-1.7"},
                    {**common_rows[1], "status": "success", "best_energy_eV": "-2.5"},
                ],
            )
            self._write_summary(
                third,
                [
                    {**common_rows[0], "status": "success", "best_energy_eV": "-1.3"},
                    {**common_rows[1], "status": "success", "best_energy_eV": "-2.2"},
                ],
            )

            output_csv = tmpdir_path / "ranked.csv"
            output_json = tmpdir_path / "ranked.json"
            code = rank_one_shot_backend_spread_main(
                [
                    "--summary",
                    f"left={left}",
                    "--summary",
                    f"right={right}",
                    "--summary",
                    f"third={third}",
                    "--output-csv",
                    str(output_csv),
                    "--output-json",
                    str(output_json),
                    "--exclude-case-ids",
                    "99",
                    "--require-success",
                ]
            )

            self.assertEqual(code, 0)
            with output_csv.open("r", encoding="utf-8", newline="") as handle:
                rows = list(csv.DictReader(handle))
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["case_id"], "01")
            self.assertAlmostEqual(float(rows[0]["range_eV"]), 0.7)

            report = json.loads(output_json.read_text(encoding="utf-8"))
            self.assertEqual(report["included_case_count"], 1)
            self.assertEqual(report["excluded_case_count"], 1)
            self.assertEqual(report["excluded_cases"][0]["case_id"], "02")

    def test_rank_one_shot_backend_spread_honors_explicit_exclusion_list(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            left = tmpdir_path / "left.csv"
            right = tmpdir_path / "right.csv"

            rows = [
                {
                    "case_id": "01",
                    "slab_file": "benchmark_slabs/01.xyz",
                    "smiles": "[H]",
                    "adsorbate_name": "H",
                    "surface_family": "intermetallic",
                    "reaction_class": "HER",
                    "status": "success",
                    "best_energy_eV": "-1.0",
                },
                {
                    "case_id": "02",
                    "slab_file": "benchmark_slabs/02.xyz",
                    "smiles": "[OH]",
                    "adsorbate_name": "OH",
                    "surface_family": "monometallic",
                    "reaction_class": "ORR",
                    "status": "success",
                    "best_energy_eV": "-2.0",
                },
            ]
            self._write_summary(left, rows)
            self._write_summary(
                right,
                [
                    {**rows[0], "best_energy_eV": "-1.5"},
                    {**rows[1], "best_energy_eV": "-2.1"},
                ],
            )

            output_csv = tmpdir_path / "ranked.csv"
            output_json = tmpdir_path / "ranked.json"
            code = rank_one_shot_backend_spread_main(
                [
                    "--summary",
                    f"left={left}",
                    "--summary",
                    f"right={right}",
                    "--output-csv",
                    str(output_csv),
                    "--output-json",
                    str(output_json),
                    "--exclude-case-ids",
                    "01",
                    "--require-success",
                ]
            )

            self.assertEqual(code, 0)
            with output_csv.open("r", encoding="utf-8", newline="") as handle:
                rows = list(csv.DictReader(handle))
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["case_id"], "02")

            report = json.loads(output_json.read_text(encoding="utf-8"))
            self.assertEqual(report["excluded_case_ids"], ["01"])
            self.assertTrue(any(row["case_id"] == "01" and row["excluded_by_user"] for row in report["excluded_cases"]))
