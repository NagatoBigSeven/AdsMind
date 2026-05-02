"""
Lightweight smoke tests for import and graph compilation.
"""

import unittest

from adsmind.agent.agent import _prepare_initial_state, get_agent_executor
from adsmind.calculators.mace_backend import _ensure_torch_compiler_compat


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
        self.assertEqual(state["max_attempts"], 5)
        self.assertEqual(state["total_input_tokens"], 0)

    def test_agent_executor_compiles(self):
        executor = get_agent_executor()

        self.assertIsNotNone(executor)
        graph = executor.get_graph()
        self.assertIn("summarizer", graph.nodes)
        self.assertNotIn("final_analyzer", graph.nodes)

    def test_mace_torch_compiler_compat_shim(self):
        import torch

        had_attr = hasattr(torch.compiler, "is_compiling")
        original = getattr(torch.compiler, "is_compiling", None)
        if had_attr:
            delattr(torch.compiler, "is_compiling")
        try:
            _ensure_torch_compiler_compat()
            self.assertTrue(hasattr(torch.compiler, "is_compiling"))
            self.assertFalse(torch.compiler.is_compiling())
        finally:
            if had_attr:
                torch.compiler.is_compiling = original
            elif hasattr(torch.compiler, "is_compiling"):
                delattr(torch.compiler, "is_compiling")
