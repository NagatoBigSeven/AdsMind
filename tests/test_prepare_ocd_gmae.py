"""Tests for OCD-GMAE manifest preparation."""

from __future__ import annotations

import csv
import importlib.util
import json
import pickle
import tempfile
import unittest
from pathlib import Path

import lmdb
from ase.io import read

from research.agent_eval.prepare_ocd_gmae import main as prepare_ocd_gmae_main


HAS_TORCH_GEOMETRIC = importlib.util.find_spec("torch_geometric") is not None


@unittest.skipUnless(HAS_TORCH_GEOMETRIC, "torch_geometric is required for OCD-GMAE preparation tests")
class TestPrepareOcdGmae(unittest.TestCase):
    """Validate filtered manifest creation from a minimal LMDB fixture."""

    def _make_record(
        self,
        *,
        atomic_numbers,
        positions,
        tags,
        ads_smi,
        y_relaxed,
        site,
        gmae_atom_numbers,
        gmae_tags,
    ):
        import torch
        from torch_geometric.data import Data

        cell = [
            [5.0, 0.0, 0.0],
            [0.0, 5.0, 0.0],
            [0.0, 0.0, 18.0],
        ]
        gmae_positions = [[float(index), 0.0, 0.0] for index in range(len(gmae_atom_numbers))]
        return Data(
            atomic_numbers=torch.tensor(atomic_numbers, dtype=torch.float32),
            pos=torch.tensor(positions, dtype=torch.float32),
            cell=torch.tensor([cell], dtype=torch.float32),
            natoms=len(atomic_numbers),
            tags=torch.tensor(tags, dtype=torch.int64),
            ads_smi=ads_smi,
            y_relaxed=y_relaxed,
            gmae_pos=torch.tensor(gmae_positions, dtype=torch.float32),
            gmae_atom_numb=torch.tensor(gmae_atom_numbers, dtype=torch.int64),
            gmae_tags=torch.tensor(gmae_tags, dtype=torch.int64),
            site=torch.tensor(site, dtype=torch.int64),
        )

    def test_prepare_ocd_gmae_filters_and_writes_manifest(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            lmdb_path = tmpdir_path / "fixture.lmdb"
            env = lmdb.open(str(lmdb_path), map_size=1024 * 1024)
            with env.begin(write=True) as txn:
                supported_h = self._make_record(
                    atomic_numbers=[26, 29, 8, 26],
                    positions=[
                        [0.0, 0.0, 0.0],
                        [1.0, 0.0, 0.0],
                        [2.0, 0.0, 0.0],
                        [0.0, 1.0, 0.0],
                    ],
                    tags=[0, 1, 2, 1],
                    ads_smi="[H]",
                    y_relaxed=-1.23,
                    site=[0, 1],
                    gmae_atom_numbers=[26, 29, 26, 1],
                    gmae_tags=[0, 1, 1, 2],
                )
                supported_oh = self._make_record(
                    atomic_numbers=[46, 46, 46, 46],
                    positions=[
                        [0.0, 0.0, 0.0],
                        [1.0, 0.0, 0.0],
                        [0.0, 1.0, 0.0],
                        [1.0, 1.0, 0.0],
                    ],
                    tags=[1, 1, 1, 1],
                    ads_smi="[OH]",
                    y_relaxed=-2.34,
                    site=[1],
                    gmae_atom_numbers=[46, 46, 46, 46, 8, 1],
                    gmae_tags=[1, 1, 1, 1, 2, 2],
                )
                nonmetal_surface = self._make_record(
                    atomic_numbers=[6, 6, 1, 1],
                    positions=[
                        [0.0, 0.0, 0.0],
                        [1.0, 0.0, 0.0],
                        [0.0, 1.0, 0.0],
                        [1.0, 1.0, 0.0],
                    ],
                    tags=[1, 1, 1, 1],
                    ads_smi="CO",
                    y_relaxed=-0.12,
                    site=[0],
                    gmae_atom_numbers=[6, 6, 1, 1, 6, 8],
                    gmae_tags=[1, 1, 1, 1, 2, 2],
                )
                txn.put(b"0", pickle.dumps(supported_h))
                txn.put(b"1", pickle.dumps(supported_oh))
                txn.put(b"2", pickle.dumps(nonmetal_surface))
            env.close()

            manifest_path = tmpdir_path / "ocd_manifest.csv"
            slab_dir = tmpdir_path / "slabs"
            summary_path = tmpdir_path / "summary.json"
            code = prepare_ocd_gmae_main(
                [
                    "--lmdb-path",
                    str(lmdb_path),
                    "--manifest-path",
                    str(manifest_path),
                    "--slab-dir",
                    str(slab_dir),
                    "--summary-path",
                    str(summary_path),
                    "--priority-smiles",
                    "[H],[OH],CO",
                    "--max-cases",
                    "3",
                    "--per-smiles",
                    "1",
                    "--max-slab-atoms",
                    "10",
                ]
            )

            self.assertEqual(code, 0)
            self.assertTrue(manifest_path.exists())
            self.assertTrue(summary_path.exists())

            with manifest_path.open("r", encoding="utf-8", newline="") as handle:
                rows = list(csv.DictReader(handle))
            self.assertEqual(len(rows), 2)
            self.assertEqual([row["case_id"] for row in rows], ["001", "002"])
            self.assertEqual(rows[0]["smiles"], "[H]")
            self.assertEqual(rows[1]["smiles"], "[OH]")
            self.assertEqual(rows[0]["surface_family"], "intermetallic")
            self.assertEqual(rows[1]["surface_family"], "monometallic")

            first_atoms = read(rows[0]["slab_file"])
            self.assertEqual(len(first_atoms), 3)
            self.assertListEqual(first_atoms.get_tags().tolist(), [0, 1, 1])

            summary = json.loads(summary_path.read_text(encoding="utf-8"))
            self.assertEqual(summary["selected_case_count"], 2)
            self.assertEqual(summary["selected_counts_by_smiles"], {"[H]": 1, "[OH]": 1})

