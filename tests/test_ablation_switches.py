"""Tests for ablation-controlled history formatting."""

import unittest

from adsmind.agent.history import build_history_entry


class TestAblationSwitches(unittest.TestCase):
    """Validate slip/FORBID/termination toggles in history generation."""

    def setUp(self):
        self.plan = {
            "solution": {
                "site_type": "bridge",
                "surface_binding_atoms": ["Cu", "Pd"],
                "adsorbate_binding_indices": [0],
            }
        }
        self.slip_analysis = {
            "status": "success",
            "most_stable_energy_eV": -2.5,
            "bond_change_count": 0,
            "is_dissociated": False,
            "site_analysis": {
                "actual_site_type": "hollow",
                "planned_site_type": "bridge",
                "is_chemical_slip": True,
                "planned_symbols": ["Cu", "Pd"],
                "actual_symbols": ["Pd", "Pd", "Pd"],
                "site_fingerprint": "Pd1-Pd2-Pd3",
            },
        }
        self.best = {
            "most_stable_energy_eV": -2.5,
            "analysis_json": {"site_analysis": {"site_fingerprint": "Pd1-Pd2-Pd3"}},
            "plan": self.plan,
        }

    def test_no_slip_suppresses_warning(self):
        entry = build_history_entry(
            self.plan,
            self.slip_analysis,
            self.best,
            enable_slip_feedback=False,
            enable_forbid=False,
        )
        self.assertNotIn("Unstable Site Warning", entry)
        self.assertNotIn("FORBID", entry)

    def test_no_forbid_keeps_slip_but_removes_forbid(self):
        entry = build_history_entry(
            self.plan,
            self.slip_analysis,
            self.best,
            enable_slip_feedback=True,
            enable_forbid=False,
        )
        self.assertIn("Unstable Site Warning", entry)
        self.assertNotIn("FORBID", entry)

    def test_no_termination_suppresses_convergence_tag(self):
        best_plan = {
            "solution": {
                "site_type": "ontop",
                "surface_binding_atoms": ["Pd"],
                "adsorbate_binding_indices": [0],
            }
        }
        analysis = {
            "status": "success",
            "most_stable_energy_eV": -2.0,
            "bond_change_count": 0,
            "is_dissociated": False,
            "site_analysis": {
                "actual_site_type": "bridge",
                "planned_site_type": "hollow",
                "is_chemical_slip": False,
                "planned_symbols": ["Pd", "Pd", "Pd"],
                "actual_symbols": ["Pd", "Pd"],
                "site_fingerprint": "Pd4-Pd7",
            },
        }
        best = {
            "most_stable_energy_eV": -2.0,
            "analysis_json": {"site_analysis": {"site_fingerprint": "Pd4-Pd7"}},
            "plan": best_plan,
        }

        entry = build_history_entry(
            self.plan,
            analysis,
            best,
            enable_termination=False,
        )
        self.assertNotIn("Converged to known best", entry)

