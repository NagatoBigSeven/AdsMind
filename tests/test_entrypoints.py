"""Tests for CLI and import entrypoints."""

import argparse
import importlib
import io
import sys
import types
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch

from langchain_core.messages import AIMessage, ToolMessage

from src.agent import agent
from src.utils import preflight


class FakeExecutor:
    """Minimal fake graph executor for CLI tests."""

    def stream(self, initial_state, config=None, stream_mode=None):
        yield {"messages": [ToolMessage(content="tool output", tool_call_id="tool")]}
        yield {"messages": [AIMessage(content="final report")]}


class TestEntrypoints(unittest.TestCase):
    """Validate user-facing entrypoints beyond internal helpers."""

    def test_main_cli_prints_final_report(self):
        args = argparse.Namespace(
            smiles="O",
            slab_path="/tmp/slab.xyz",
            user_request="Find a stable site",
            seed=7,
            relaxation_mode="fast",
        )

        with (
            patch("src.agent.agent.parse_args", return_value=args),
            patch("src.agent.agent.get_agent_executor", return_value=FakeExecutor()),
            patch("src.agent.agent.os.path.exists", return_value=True),
            patch("src.utils.config.get_llm_backend_name", return_value="google"),
            patch(
                "src.utils.config.get_api_key_for_backend",
                return_value=("dummy-key", "env"),
            ),
        ):
            stdout = io.StringIO()
            with redirect_stdout(stdout):
                agent.main_cli()

        output = stdout.getvalue()
        self.assertIn("AdsMind Started", output)
        self.assertIn("final report", output)

    def test_streamlit_root_entrypoint_reexports_app_module(self):
        fake_app = types.ModuleType("src.app.app")
        fake_app.EXPORTED_SENTINEL = "ok"

        original = sys.modules.get("src.app.app")
        sys.modules["src.app.app"] = fake_app
        sys.modules.pop("streamlit_app", None)
        try:
            module = importlib.import_module("streamlit_app")
            self.assertEqual(module.EXPORTED_SENTINEL, "ok")
        finally:
            sys.modules.pop("streamlit_app", None)
            if original is None:
                sys.modules.pop("src.app.app", None)
            else:
                sys.modules["src.app.app"] = original

    def test_preflight_main_json_output(self):
        report = {
            "python_version": "3.11.0",
            "platform": "test-platform",
            "configured_llm_backend": "google",
            "configured_calculator_backend": "mace",
            "available_llm_backends": ["google"],
            "available_calculator_backends": ["mace"],
            "agent_graph_compiles": True,
        }
        stdout = io.StringIO()
        with (
            patch("src.utils.preflight.run_preflight", return_value=(0, report)),
            redirect_stdout(stdout),
        ):
            code = preflight.main(["--json", "--ci"])

        self.assertEqual(code, 0)
        self.assertIn('"agent_graph_compiles": true', stdout.getvalue())
