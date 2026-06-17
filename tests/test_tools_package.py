"""Tests for the reorganized tools package surface."""

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import adsmind.tools as tools
from adsmind.tools.common import ensure_output_dir, sanitize_smiles_for_filename
from adsmind.tools.constants import RelaxationMode

ROOT = Path(__file__).resolve().parents[1]


class TestToolsPackage(unittest.TestCase):
    """Verify the public package surface after modularization."""

    def test_public_exports_are_available(self):
        self.assertTrue(callable(tools.prepare_slab))
        self.assertTrue(callable(tools.read_atoms_object))
        self.assertTrue(callable(tools.relax_atoms))
        self.assertTrue(callable(tools.analyze_relaxation_results))
        self.assertIs(tools.RelaxationMode, RelaxationMode)

    def test_sanitize_smiles_for_filename(self):
        self.assertEqual(sanitize_smiles_for_filename("C=C#N"), "C_C_N")
        self.assertEqual(
            sanitize_smiles_for_filename("[CH3][O]", strip_brackets=True),
            "CH3O",
        )

    def test_ensure_output_dir_creates_session_subdir(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            fake_root = Path(tmpdir) / "outputs"
            with patch("adsmind.tools.common.OUTPUT_ROOT", fake_root):
                session_dir = ensure_output_dir("session01")

            self.assertTrue(session_dir.exists())
            self.assertEqual(session_dir, fake_root / "session01")

    def test_analyze_surface_sites_returns_inventory(self):
        analysis = tools.analyze_surface_sites(
            str(ROOT / "datasets" / "cmu20" / "01_Mo3Pd_111.xyz")
        )
        self.assertIn("surface_composition", analysis)
        self.assertIn("available_sites_description", analysis)
        self.assertTrue(analysis["available_sites_description"])
