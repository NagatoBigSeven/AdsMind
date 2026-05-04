# Datasets

Curated input slab files used by AdsMind benchmarks and the manuscript figures.
These are committed snapshots — running the agent does NOT require redownloading.
Paper-facing OCD slabs are stored as `OCD62` inputs.

| Directory | Files | Manifest | Use |
|---|---:|---|---|
| `cmu20/` | 20 | `datasets/cmu20/cmu20_manifest.csv` | CMU benchmark cases (intermetallics + monometallics, H/NNH/OH/larger adsorbates) |
| `ocd62/` | 62 | `datasets/ocd62/ocd62_manifest.csv` | OCD62 benchmark used for basic tests and the four-backend five-variant ablation matrix |
| `ocd62_overlap12/` | 12 | `datasets/ocd62_overlap12/overlap12_manifest.csv` | Reproducibility input queue for the 12 OCD62 overlap cases |
| `samples/` | 4 | — | Tiny example slabs used by docs/quickstart and the test suite (`cu_slab_211.xyz`, `CuZnO.xyz`, `NiFeO_slab.xyz`, `test_slab.xyz`) |

## Notes

- `cmu20/`: derived from FAIR-Chem/OCP via `datasets/cmu20/download_cmu20_slabs.py`
  (committed because regeneration requires network and the OCP client).
- `ocd62/`: the OCD62 benchmark used by the manuscript.
- `ocd62_overlap12/`: input queue for reproducibility runs on the 12 overlap
  cases. It is not a separate benchmark.
- `samples/`: hand-picked small test surfaces for documentation examples.
