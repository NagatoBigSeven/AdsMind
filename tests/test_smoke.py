"""
Lightweight smoke tests for import and graph compilation.
"""

import unittest

from src.agent.agent import _prepare_initial_state, get_agent_executor


class TestSmoke(unittest.TestCase):
    """Verify that the main agent graph compiles and basic state prep works."""

    def test_prepare_initial_state_defaults(self):
        state = _prepare_initial_state(
            smiles="O",
            slab_path="/tmp/slab.xyz",
            user_request="Find a stable site",
            api_key="dummy",
            session_id="session01",
        )

        self.assertEqual(state["llm_backend"], "google")
        self.assertEqual(state["relaxation_mode"], "fast")
        self.assertEqual(state["attempted_keys"], [])

    def test_agent_executor_compiles(self):
        executor = get_agent_executor()

        self.assertIsNotNone(executor)
