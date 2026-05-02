# Benchmark Manifests

These CSV files define the exact benchmark subsets used by the research
scripts. They are not raw dataset dumps.

| Manifest | Cases | Use |
|---|---:|---|
| `cmu_manifest.csv` | 20 | CMU-style benchmark cases. |
| `ocd_gmae_subset24_manifest.csv` | 24 | OCD-GMAE validation subset for the full ablation matrix. |
| `ocd_gmae_representative50_manifest.csv` | 50 | OCD-GMAE representative subset for broader one-shot/generalisation analysis. |
| `ocd_gmae_subset24_vs_representative50_overlap.csv` | 24 | Source-key overlap audit between the two OCD-GMAE subsets. |

The two OCD-GMAE manifests are not nested. They are separate selections from
the same source pool with different purposes: `subset24` keeps the full
four-backend five-variant ablation matrix tractable, while `representative50`
prioritizes broader chemistry coverage for the Full-versus-1-Shot
generalisation study and panel-B structure assets. They overlap on 12
`source_key` records. Treat `case_id` as local to each manifest; use
`source_key` or the `ocd_XXX` token in the slab filename for any cross-manifest
join.

Selection metadata is stored next to each OCD-GMAE manifest:

- `ocd_gmae_subset24_manifest_selection.json`
- `ocd_gmae_representative50_manifest_selection.json`

> Compatibility symlinks `ocd_gmae_manifest{.csv,_selection.json}` and
> `ocd_gmae_rep50_manifest{.csv,_selection.json}` were removed on 2026-05-02
> together with the parallel `generated_slabs/` symlinks; no in-repo references
> remained. See `research/results/MIGRATION.md`.
