"""Tests for agent runtime instrumentation."""

import unittest

from src.agent.agent import (
    _coalesce_override,
    extract_token_usage,
    get_valid_binding_indices,
    plan_validator_node,
    route_after_validation,
    route_after_analysis,
)


class DummyResponse:
    """Minimal response object for token parsing tests."""

    def __init__(self, usage_metadata=None, response_metadata=None):
        self.usage_metadata = usage_metadata
        self.response_metadata = response_metadata or {}


class UsageObject:
    """Object-style usage metadata for Google responses."""

    def __init__(self, prompt, completion):
        self.prompt_token_count = prompt
        self.candidates_token_count = completion


class TestAgentRuntimeMetrics(unittest.TestCase):
    """Validate token accounting and max-attempt routing."""

    def test_extract_token_usage_google_metadata(self):
        response = DummyResponse(usage_metadata=UsageObject(prompt=123, completion=45))
        self.assertEqual(extract_token_usage(response), (123, 45))

    def test_extract_token_usage_openrouter_metadata(self):
        response = DummyResponse(
            response_metadata={"token_usage": {"prompt_tokens": 22, "completion_tokens": 11}}
        )
        self.assertEqual(extract_token_usage(response), (22, 11))

    def test_extract_token_usage_missing_metadata_defaults_to_zero(self):
        response = DummyResponse()
        self.assertEqual(extract_token_usage(response), (0, 0))

    def test_route_after_analysis_uses_state_max_attempts(self):
        state = {
            "plan": {"solution": {"action": "continue"}},
            "analysis_json": '{"status":"success"}',
            "history": ["attempt-1", "attempt-2"],
            "validation_retry_count": 0,
            "max_attempts": 2,
        }
        self.assertEqual(route_after_analysis(state), "end")

    def test_route_after_analysis_counts_validation_retries_toward_limit(self):
        state = {
            "plan": {"solution": {"action": "continue"}},
            "analysis_json": '{"status":"success"}',
            "history": ["attempt-1"],
            "validation_retry_count": 1,
            "max_attempts": 2,
        }
        self.assertEqual(route_after_analysis(state), "end")

    def test_coalesce_override_treats_none_as_missing(self):
        self.assertEqual(_coalesce_override({"steps": None}, "steps", 200), 200)
        self.assertEqual(_coalesce_override({"steps": 50}, "steps", 200), 50)

    def test_get_valid_binding_indices_prefers_heavy_atoms(self):
        from rdkit import Chem

        mol = Chem.MolFromSmiles("[OH]")
        self.assertEqual(get_valid_binding_indices(mol), {0})

    def test_get_valid_binding_indices_falls_back_to_all_atoms_for_hydrogen(self):
        from rdkit import Chem

        mol = Chem.MolFromSmiles("[H]")
        self.assertEqual(get_valid_binding_indices(mol), {0})

    def test_plan_validator_rejects_out_of_range_binding_index(self):
        state = {
            "smiles": "[OH]",
            "plan": {
                "adsorbate_type": "ReactiveSpecies",
                "solution": {
                    "site_type": "bridge",
                    "surface_binding_atoms": ["Pt", "Pt"],
                    "adsorbate_binding_indices": [1],
                },
            },
            "attempted_keys": [],
            "enable_termination": True,
        }
        result = plan_validator_node(state)
        self.assertIn("planner-visible atoms [0]", result["validation_error"])
        self.assertEqual(result["validation_retry_count"], 1)

    def test_plan_validator_allows_atomic_hydrogen_index_zero(self):
        state = {
            "smiles": "[H]",
            "plan": {
                "adsorbate_type": "ReactiveSpecies",
                "solution": {
                    "site_type": "ontop",
                    "surface_binding_atoms": ["Mo"],
                    "adsorbate_binding_indices": [0],
                },
            },
            "attempted_keys": [],
            "enable_termination": True,
        }
        result = plan_validator_node(state)
        self.assertIsNone(result["validation_error"])
        self.assertEqual(result["validation_retry_count"], 0)

    def test_route_after_validation_ends_when_validation_budget_exhausted(self):
        state = {
            "validation_error": "False, Termination is disabled for this run.",
            "validation_retry_count": 5,
            "max_attempts": 5,
        }
        self.assertEqual(route_after_validation(state), "final_analyzer")
