"""Tests for multi-backend ablation aggregation."""

from __future__ import annotations

import csv
import json
import tempfile
import unittest
from pathlib import Path

from research.agent_eval.summarize_multi_backend_ablation import (
    main as summarize_multi_backend_ablation_main,
)


class TestSummarizeMultiBackendAblation(unittest.TestCase):
    """Validate multi-summary aggregation behavior."""

    def _write_summary(self, path: Path, rows: list[dict[str, str]]) -> None:
        fieldnames = [
            "case_id",
            "variant",
            "best_energy",
            "delta_vs_full",
            "iterations",
            "wasted_iterations",
            "waste_ratio",
            "success",
            "slip_count",
            "dissociation_count",
            "tokens_used",
        ]
        with path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)

    def test_multi_backend_ablation_summary_computes_ranges(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            left = tmpdir_path / "left.csv"
            middle = tmpdir_path / "middle.csv"
            right = tmpdir_path / "right.csv"

            common = [
                {
                    "case_id": "003",
                    "variant": "full",
                    "delta_vs_full": "0.0",
                    "iterations": "5",
                    "wasted_iterations": "0",
                    "waste_ratio": "0",
                    "slip_count": "0",
                    "dissociation_count": "0",
                    "tokens_used": "100",
                },
                {
                    "case_id": "003",
                    "variant": "no_slip",
                    "delta_vs_full": "0.2",
                    "iterations": "5",
                    "wasted_iterations": "0",
                    "waste_ratio": "0",
                    "slip_count": "1",
                    "dissociation_count": "0",
                    "tokens_used": "120",
                },
            ]

            self._write_summary(
                left,
                [
                    {**common[0], "best_energy": "-10.0", "success": "true"},
                    {**common[1], "best_energy": "-9.8", "success": "true"},
                ],
            )
            self._write_summary(
                middle,
                [
                    {**common[0], "best_energy": "-10.5", "success": "true"},
                    {**common[1], "best_energy": "-9.6", "success": "false"},
                ],
            )
            self._write_summary(
                right,
                [
                    {**common[0], "best_energy": "-9.9", "success": "true"},
                    {**common[1], "best_energy": "-9.7", "success": "true"},
                ],
            )

            output_csv = tmpdir_path / "out.csv"
            output_json = tmpdir_path / "out.json"
            code = summarize_multi_backend_ablation_main(
                [
                    "--summary",
                    f"left={left}",
                    "--summary",
                    f"middle={middle}",
                    "--summary",
                    f"right={right}",
                    "--output-csv",
                    str(output_csv),
                    "--output-json",
                    str(output_json),
                ]
            )

            self.assertEqual(code, 0)
            with output_csv.open("r", encoding="utf-8", newline="") as handle:
                rows = list(csv.DictReader(handle))

            full_row = next(row for row in rows if row["variant"] == "full")
            no_slip_row = next(row for row in rows if row["variant"] == "no_slip")
            self.assertAlmostEqual(float(full_row["range_best_energy"]), 0.6)
            self.assertEqual(no_slip_row["success_backend_count"], "2")
            self.assertEqual(no_slip_row["failed_backends"], "middle")

            summary = json.loads(output_json.read_text(encoding="utf-8"))
            self.assertEqual(summary["largest_best_energy_gap"]["variant"], "full")

