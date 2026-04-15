"""Tests for representative OCD-GMAE manifest preparation."""

from __future__ import annotations

import unittest

from ase import Atoms

from research.agent_eval.prepare_ocd_gmae import OCDCandidate
from research.agent_eval.prepare_ocd_gmae_representative import (
    assign_energy_bins,
    proportional_targets,
    select_representative_candidates,
)


def _candidate(
    *,
    source_key: str,
    smiles: str,
    bucket: str,
    family: str,
    formula: str,
    y_relaxed: float,
) -> OCDCandidate:
    return OCDCandidate(
        source_key=source_key,
        raw_smiles=smiles,
        mapped_smiles=smiles,
        adsorbate_name=smiles,
        user_request="test",
        reaction_class="GENERALIZATION",
        selection_bucket=bucket,
        slab_atoms=Atoms("Cu2", positions=[[0, 0, 0], [1, 0, 0]], cell=[5, 5, 18], pbc=(True, True, False)),
        bare_slab_atoms=2,
        adsorbate_atoms=1,
        surface_formula=formula,
        surface_elements=("Cu",),
        surface_family=family,
        y_relaxed=y_relaxed,
        site_indices=(0,),
    )


class TestPrepareOcdGmaeRepresentative(unittest.TestCase):
    """Validate quota calculation and representative coverage."""

    def test_proportional_targets_respects_minimums(self):
        counts = {"[H]": 10, "[OH]": 8, "CO": 30}
        targets = proportional_targets(counts, 12, minimums={"[H]": 2, "[OH]": 2}, maximums={"CO": 5})
        self.assertEqual(sum(targets.values()), 12)
        self.assertGreaterEqual(targets["[H]"], 2)
        self.assertGreaterEqual(targets["[OH]"], 2)
        self.assertLessEqual(targets["CO"], 5)

    def test_select_representative_candidates_covers_all_smiles_and_hits_count(self):
        candidates = [
            _candidate(source_key="h1", smiles="[H]", bucket="cmu_exact", family="intermetallic", formula="Cu2", y_relaxed=-1.5),
            _candidate(source_key="h2", smiles="[H]", bucket="cmu_exact", family="compound", formula="CuO2", y_relaxed=-1.0),
            _candidate(source_key="oh1", smiles="[OH]", bucket="cmu_exact", family="intermetallic", formula="Ni2", y_relaxed=-2.5),
            _candidate(source_key="oh2", smiles="[OH]", bucket="cmu_exact", family="compound", formula="NiO2", y_relaxed=-2.0),
            _candidate(source_key="n1", smiles="[NH2]", bucket="small_n_species", family="intermetallic", formula="Fe2", y_relaxed=-3.5),
            _candidate(source_key="n2", smiles="[NH2]", bucket="small_n_species", family="compound", formula="FeN2", y_relaxed=-3.0),
            _candidate(source_key="co1", smiles="CO", bucket="small_organic", family="intermetallic", formula="Pt2", y_relaxed=-1.8),
            _candidate(source_key="co2", smiles="CO", bucket="small_organic", family="monometallic", formula="Pt4", y_relaxed=-1.2),
        ]
        tagged = assign_energy_bins(candidates, 3)
        selected, summary = select_representative_candidates(
            tagged,
            priority_smiles=["[H]", "[OH]", "[NH2]", "CO"],
            max_cases=6,
            max_per_smiles=3,
            energy_bins=3,
        )
        selected_smiles = {candidate.mapped_smiles for candidate in selected}
        self.assertEqual(len(selected), 6)
        self.assertEqual(selected_smiles, {"[H]", "[OH]", "[NH2]", "CO"})
        self.assertGreaterEqual(summary["selected_counts_by_smiles"]["[H]"], 2)
        self.assertGreaterEqual(summary["selected_counts_by_smiles"]["[OH]"], 2)

