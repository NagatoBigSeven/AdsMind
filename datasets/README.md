# Datasets

Curated input slab files used by AdsMind benchmarks and the manuscript figures.
These are committed snapshots — running the agent does NOT require redownloading.
The manuscript refers to the 20-case benchmark as AA20 and the 62-case benchmark
as OCD-GMAE62; the repository keeps the historical directory names `cmu20/` and
`ocd62/` for script compatibility.

| Directory | Files | Manifest | Use |
|---|---:|---|---|
| `cmu20/` | 20 | `datasets/cmu20/cmu20_manifest.csv` | AA20 benchmark cases (intermetallics + monometallics, H/NNH/OH/larger adsorbates) |
| `ocd62/` | 62 | `datasets/ocd62/ocd62_manifest.csv` | OCD-GMAE62 benchmark used for basic tests and the four-backend five-variant ablation matrix |
| `ocd62_overlap12/` | 12 | `datasets/ocd62_overlap12/ocd62_overlap12_manifest.csv` | Reproducibility input queue for the 12 OCD-GMAE62 overlap cases |
| `samples/` | 4 | — | Tiny example slabs used by docs/quickstart and the test suite (`cu_slab_211.xyz`, `CuZnO.xyz`, `NiFeO_slab.xyz`, `test_slab.xyz`) |

## Notes

See [NOTICE.md](NOTICE.md) for upstream provenance, licenses, and required
citations for these third-party-derived inputs.

- `cmu20/`: built from Materials Project bulk structures via FAIR-Chem/OCP using
  `datasets/cmu20/download_cmu20_dataset.py` (committed because regeneration
  requires network access and the OCP client).
- `ocd62/`: the OCD-GMAE62 benchmark, constructed from the OCD-GMAE dataset in
  schwallergroup/AdsMT.
- `ocd62_overlap12/`: input queue for reproducibility runs on the 12 overlap
  cases. It is not a separate benchmark.
- `samples/`: hand-picked small test surfaces for documentation examples.
