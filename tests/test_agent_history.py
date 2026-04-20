"""
Tests for agent history generation and routing behavior.
"""

import unittest

from adsmind.agent.agent import route_after_analysis
from adsmind.agent.history import build_history_entry


class TestAgentHistory(unittest.TestCase):
    """Validate that post-analysis state is derived without hidden mutation."""

    def test_build_history_entry_marks_new_best(self):
        plan = {
            "solution": {
                "site_type": "bridge",
                "surface_binding_atoms": ["Cu", "Cu"],
                "adsorbate_binding_indices": [0],
            }
        }
        analysis = {
            "status": "success",
            "most_stable_energy_eV": -1.234,
            "bond_change_count": 0,
            "is_dissociated": False,
            "site_analysis": {
                "actual_site_type": "bridge",
                "planned_site_type": "bridge",
                "is_chemical_slip": False,
                "planned_symbols": ["Cu", "Cu"],
                "actual_symbols": ["Cu", "Cu"],
                "site_fingerprint": "Cu10-Cu11",
            },
        }
        best = {
            "most_stable_energy_eV": -1.234,
            "analysis_json": {"site_analysis": {"site_fingerprint": "Cu10-Cu11"}},
            "plan": plan,
        }

        entry = build_history_entry(plan, analysis, best)

        self.assertIn("[🌟 New Best]", entry)
        self.assertIn("✅ Perfect Adsorption", entry)

    def test_build_history_entry_marks_known_best_convergence(self):
        current_plan = {
            "solution": {
                "site_type": "hollow",
                "surface_binding_atoms": ["Pd", "Pd", "Pd"],
                "adsorbate_binding_indices": [0],
            }
        }
        best_plan = {
            "solution": {
                "site_type": "bridge",
                "surface_binding_atoms": ["Pd", "Pd"],
                "adsorbate_binding_indices": [0],
            }
        }
        analysis = {
            "status": "success",
            "most_stable_energy_eV": -2.001,
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

        entry = build_history_entry(current_plan, analysis, best)

        self.assertIn("[🔄 Converged to known best]", entry)

    def test_route_after_analysis_uses_existing_history(self):
        state = {
            "plan": {"solution": {"action": "continue"}},
            "analysis_json": '{"status":"success"}',
            "history": ["attempt-1", "attempt-2"],
        }

        decision = route_after_analysis(state)

        self.assertEqual(decision, "planner")
        self.assertEqual(state["history"], ["attempt-1", "attempt-2"])
