"""
Tests for configuration persistence and backend preference handling.
"""

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from adsmind.utils import config as config_module


class TestConfigPersistence(unittest.TestCase):
    """Verify that configuration reads and writes stay isolated and predictable."""

    def test_save_and_load_backend_config(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            config_dir = Path(tmpdir)
            legacy_config_dir = config_dir / "legacy"
            config_file = config_dir / "config.json"
            legacy_config_file = legacy_config_dir / "config.json"

            with patch.object(config_module, "CONFIG_DIR", config_dir), patch.object(
                config_module, "CONFIG_FILE_PATH", config_file
            ), patch.object(
                config_module, "LEGACY_CONFIG_DIR", legacy_config_dir
            ), patch.object(
                config_module, "LEGACY_CONFIG_FILE_PATH", legacy_config_file
            ):
                self.assertTrue(config_module.save_llm_backend("ollama"))
                self.assertTrue(config_module.save_api_key_for_backend("google", "secret"))

                loaded = config_module.load_config()

        self.assertEqual(loaded["llm_backend"], "ollama")
        self.assertEqual(loaded["google_api_key"], "secret")

    def test_environment_backend_takes_priority_over_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            config_dir = Path(tmpdir)
            legacy_config_dir = config_dir / "legacy"
            config_file = config_dir / "config.json"
            legacy_config_file = legacy_config_dir / "config.json"
            config_dir.mkdir(parents=True, exist_ok=True)
            config_file.write_text(json.dumps({"llm_backend": "openrouter"}), encoding="utf-8")

            with patch.object(config_module, "CONFIG_DIR", config_dir), patch.object(
                config_module, "CONFIG_FILE_PATH", config_file
            ), patch.object(
                config_module, "LEGACY_CONFIG_DIR", legacy_config_dir
            ), patch.object(
                config_module, "LEGACY_CONFIG_FILE_PATH", legacy_config_file
            ), patch.dict("os.environ", {"ADSMIND_LLM_BACKEND": "huggingface"}):
                backend = config_module.get_llm_backend_name()

        self.assertEqual(backend, "huggingface")
