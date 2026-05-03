# Benchmark Slab Datasets

Curated input slab files used by AdsMind benchmarks and the manuscript figures.
These are committed snapshots — running the agent does NOT require redownloading.
Each subdir matches a manifest under `research/agent_eval/manifests/`.

| Directory | Files | Manifest | Use |
|---|---:|---|---|
| `cmu-20/` | 20 | `research/agent_eval/manifests/cmu_manifest.csv` | CMU benchmark cases (intermetallics + monometallics, H/NNH/OH/larger adsorbates) |
| `ocd_gmae_subset24/` | 24 | `research/agent_eval/manifests/ocd_gmae_subset24_manifest.csv` | OCD-GMAE 24-case validation subset for the full 4-backend × 5-variant ablation matrix |
| `ocd_gmae_representative50/` | 50 | `research/agent_eval/manifests/ocd_gmae_representative50_manifest.csv` | OCD-GMAE 50-case representative slice for the broader Full-vs-1-Shot generalisation study and Panel B assets |
| `samples/` | 4 | — | Tiny example slabs used by docs/quickstart and the test suite (`cu_slab_211.xyz`, `CuZnO.xyz`, `NiFeO_slab.xyz`, `test_slab.xyz`) |

## Source provenance

- `cmu-20/`: derived from FAIR-Chem/OCP via `research/generate_slabs.py`
  (committed because regeneration requires network and the OCP client).
- `ocd_gmae_subset24/` and `ocd_gmae_representative50/`: extracted from the
  external OCD-GMAE LMDB via
  `research/agent_eval/prepare_ocd_gmae{,_representative}.py`. The full LMDB
  is NOT in the repo; point the scripts at it via `OCD_GMAE_LMDB_PATH` or
  `--lmdb-path` if you need to regenerate.
- `samples/`: hand-picked small test surfaces for documentation examples.

## Path migration notes (2026-04-30+)

- The OCD-GMAE selections used to live under
  `research/agent_eval/generated_slabs/{ocd_gmae_subset24,ocd_gmae_representative50}/`
  with `ocd_gmae` and `ocd_gmae_rep50` compatibility symlinks. Those have been
  removed; the canonical home is now `datasets/`.
- CMU-20 used to live under `slabs/benchmark/cmu_dataset/` and was symlinked
  as `benchmark_slabs/`. The slab files moved here; **`research/agent_eval/manifests/cmu_manifest.csv` still lists `benchmark_slabs/<file>` paths** and
  expects either a local symlink or a manifest path rewrite. See
  `research/results/MIGRATION.md` for the full path-migration history.
