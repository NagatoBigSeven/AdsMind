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

from adsmind.agent import agent
from adsmind.utils import preflight


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
            patch("adsmind.agent.agent.parse_args", return_value=args),
            patch("adsmind.agent.agent.get_agent_executor", return_value=FakeExecutor()),
            patch("adsmind.agent.agent.os.path.exists", return_value=True),
            patch("adsmind.utils.config.get_llm_backend_name", return_value="openrouter"),
            patch(
                "adsmind.utils.config.get_api_key_for_backend",
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
        fake_app = types.ModuleType("adsmind.app.app")
        fake_app.EXPORTED_SENTINEL = "ok"

        original = sys.modules.get("adsmind.app.app")
        sys.modules["adsmind.app.app"] = fake_app
        sys.modules.pop("streamlit_app", None)
        try:
            module = importlib.import_module("streamlit_app")
            self.assertEqual(module.EXPORTED_SENTINEL, "ok")
        finally:
            sys.modules.pop("streamlit_app", None)
            if original is None:
                sys.modules.pop("adsmind.app.app", None)
            else:
                sys.modules["adsmind.app.app"] = original

    def test_packaged_streamlit_launcher_targets_app_module(self):
        from adsmind.app import launcher

        captured = {}

        def fake_main():
            captured["argv"] = list(sys.argv)

        fake_cli = types.ModuleType("streamlit.web.cli")
        fake_cli.main = fake_main
        fake_web = types.ModuleType("streamlit.web")
        fake_web.cli = fake_cli
        fake_streamlit = types.ModuleType("streamlit")
        fake_streamlit.web = fake_web

        with (
            patch.dict(
                sys.modules,
                {
                    "streamlit": fake_streamlit,
                    "streamlit.web": fake_web,
                    "streamlit.web.cli": fake_cli,
                },
            ),
            patch.object(sys, "argv", ["adsmind-ui", "--server.port=9999"]),
        ):
            launcher.main()

        self.assertEqual(captured["argv"][0:2], ["streamlit", "run"])
        self.assertTrue(captured["argv"][2].endswith("adsmind/app/app.py"))
        self.assertIn("--server.port=9999", captured["argv"])

    def test_preflight_main_json_output(self):
        report = {
            "python_version": "3.11.0",
            "platform": "test-platform",
            "configured_llm_backend": "openrouter",
            "configured_calculator_backend": "mace",
            "available_llm_backends": ["openrouter"],
            "available_calculator_backends": ["mace"],
            "agent_graph_compiles": True,
        }
        stdout = io.StringIO()
        with (
            patch("adsmind.utils.preflight.run_preflight", return_value=(0, report)),
            redirect_stdout(stdout),
        ):
            code = preflight.main(["--json", "--ci"])

        self.assertEqual(code, 0)
        self.assertIn('"agent_graph_compiles": true', stdout.getvalue())
