"""Tests for AdsMind rename compatibility in configuration handling."""

import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from adsmind.utils import config as config_module


class TestAdsMindRenameCompatibility(unittest.TestCase):
    """Ensure the AdsMind rename keeps old environments working."""

    def test_new_llm_backend_env_var_takes_priority(self):
        """ADSMIND_LLM_BACKEND should override the legacy variable."""
        with patch.dict(
            os.environ,
            {
                "ADSMIND_LLM_BACKEND": "ollama",
                "ADSKRK_LLM_BACKEND": "openrouter",
            },
            clear=True,
        ):
            self.assertEqual(config_module.get_llm_backend_name(), "ollama")

    def test_legacy_calculator_backend_env_var_still_supported(self):
        """Older ADSKRK_BACKEND setups should keep working."""
        with patch.dict(os.environ, {"ADSKRK_BACKEND": "openmd"}, clear=True):
            self.assertEqual(config_module.get_calculator_backend(), "openmd")

    def test_load_config_falls_back_to_legacy_path(self):
        """Legacy ~/.adskrk config should be readable when new config is absent."""
        with tempfile.TemporaryDirectory() as tmpdir:
            base_dir = Path(tmpdir)
            config_dir = base_dir / ".adsmind"
            legacy_config_dir = base_dir / ".adskrk"
            legacy_config_dir.mkdir(parents=True, exist_ok=True)

            config_path = config_dir / "config.json"
            legacy_config_path = legacy_config_dir / "config.json"
            legacy_config_path.write_text(
                json.dumps({"llm_backend": "huggingface"}),
                encoding="utf-8",
            )

            with patch.object(config_module, "CONFIG_DIR", config_dir), patch.object(
                config_module, "LEGACY_CONFIG_DIR", legacy_config_dir
            ), patch.object(
                config_module, "CONFIG_FILE_PATH", config_path
            ), patch.object(
                config_module, "LEGACY_CONFIG_FILE_PATH", legacy_config_path
            ), patch.dict(os.environ, {}, clear=True):
                self.assertEqual(
                    config_module.load_config().get("llm_backend"),
                    "huggingface",
                )
                self.assertEqual(
                    config_module.get_llm_backend_name(),
                    "huggingface",
                )

    def test_save_config_writes_to_adsmind_path(self):
        """New writes should go to ~/.adsmind, not the legacy location."""
        with tempfile.TemporaryDirectory() as tmpdir:
            base_dir = Path(tmpdir)
            config_dir = base_dir / ".adsmind"
            legacy_config_dir = base_dir / ".adskrk"
            config_path = config_dir / "config.json"
            legacy_config_path = legacy_config_dir / "config.json"

            with patch.object(config_module, "CONFIG_DIR", config_dir), patch.object(
                config_module, "LEGACY_CONFIG_DIR", legacy_config_dir
            ), patch.object(
                config_module, "CONFIG_FILE_PATH", config_path
            ), patch.object(
                config_module, "LEGACY_CONFIG_FILE_PATH", legacy_config_path
            ):
                self.assertTrue(config_module.save_llm_backend("openrouter"))
                self.assertTrue(config_path.exists())
                self.assertFalse(legacy_config_path.exists())


if __name__ == "__main__":
    unittest.main()
