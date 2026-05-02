# Generated Slab Subsets

This directory stores only the OCD-GMAE slabs selected into the paper
manifests. It does not store the full OCD-GMAE dataset.

| Directory | Manifest | Meaning | Expected files |
|---|---|---|---:|
| `ocd_gmae_subset24/` | `../manifests/ocd_gmae_subset24_manifest.csv` | 24-case validation subset used for the full ablation matrix. | 24 |
| `ocd_gmae_representative50/` | `../manifests/ocd_gmae_representative50_manifest.csv` | 50-case representative subset used for broader one-shot/generalisation checks and Panel B assets. | 50 |

The full OCD-GMAE source is external and is regenerated from the LMDB path
provided through `OCD_GMAE_LMDB_PATH` or `--lmdb-path`.

> Compatibility symlinks `ocd_gmae` → `ocd_gmae_subset24` and `ocd_gmae_rep50`
> → `ocd_gmae_representative50` were removed on 2026-04-30; all in-repo
> references were rewritten to the canonical names. See
> `research/results/MIGRATION.md`.
