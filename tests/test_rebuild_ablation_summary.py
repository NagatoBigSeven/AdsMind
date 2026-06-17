"""Tests for ablation summary rebuilding."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from research.agent_eval.rebuild_ablation_summary import rebuild


def _write_result(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


class TestRebuildAblationSummary(unittest.TestCase):
    """Validate rebuild behavior on partially complete ablation matrices."""

    def test_rebuild_skips_friedman_when_fewer_than_three_complete_variants(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            ablation_dir = root / "ablation"
            one_shot_dir = root / "one_shot"
            case_ids = ["003", "004", "005"]
            variants = ["full", "no_slip", "no_forbid", "single_shot"]

            for idx, cid in enumerate(case_ids):
                _write_result(
                    ablation_dir / "full" / cid / "result.json",
                    {
                        "status": "success",
                        "best_energy_eV": -10.0 - idx,
                        "iteration_count": 3,
                        "calc_failure_count": 0,
                    },
                )
                _write_result(
                    ablation_dir / "no_slip" / cid / "result.json",
                    {
                        "status": "success",
                        "best_energy_eV": -9.5 - idx,
                        "iteration_count": 3,
                        "calc_failure_count": 0,
                    },
                )
                if cid != "005":
                    _write_result(
                        one_shot_dir / cid / "result.json",
                        {
                            "status": "success",
                            "best_energy_eV": -9.8 - idx,
                            "iteration_count": 1,
                            "calc_failure_count": 0,
                        },
                    )

            rows, stats = rebuild(ablation_dir, variants, case_ids, one_shot_dir)

            self.assertEqual(len(rows), len(case_ids) * len(variants))
            self.assertIsNone(stats["friedman"])
            self.assertIsNotNone(stats["pairwise"]["no_slip"])
            self.assertIsNone(stats["pairwise"]["single_shot"])
            self.assertIsNone(stats["pairwise"]["no_forbid"])
