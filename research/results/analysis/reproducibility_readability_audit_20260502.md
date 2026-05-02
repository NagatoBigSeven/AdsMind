# Reproducibility and Readability Audit -- 2026-05-02

## Scope

This audit covers the current public-facing experiment organization after the
`canonical_raw/` cleanup, OCD-GMAE manifest renaming, Overleaf wording updates,
and result-registry rebuilds. It focuses on whether another collaborator can:

1. find the authoritative input manifests;
2. identify the canonical raw-result directories;
3. reproduce the paper-facing CSV/JSON registries;
4. avoid confusing legacy paths, version suffixes, and local case IDs;
5. compile the Overleaf draft without unresolved references.

No experimental raw data or scientific result values were changed during this
audit.

## Checks Performed

| Check | Result |
|---|---|
| Manifest slab paths | PASS: `cmu_manifest.csv`, `ocd_gmae_subset24_manifest.csv`, and `ocd_gmae_representative50_manifest.csv` all point to existing slab files. |
| OCD subset relation | PASS: `subset24=24`, `rep50=50`, overlap is 12 `source_key` records, and all overlapping slab SHA256 hashes match. |
| Canonical ablation row counts | PASS: CMU20 = 4 x 100 rows, OCD24 = 4 x 120 rows, rep50 = 4 x 200 non-one-shot rows plus 4 x 50 `single_shot_summary.csv` rows. |
| Baseline/control row counts | PASS: CMU20/OCD24/rep50 random and heuristic baselines have expected case counts; AA single-config control has 20 rows. |
| `MERGE_QC.csv` rebuild | PASS: rebuilt copy has 41 rows and is byte-identical to `research/results/canonical_raw/MERGE_QC.csv`. |
| `RUN_REGISTRY.csv` / `ANALYSIS_REGISTRY.csv` rebuild | PASS: rebuilt copies have 42 and 65 rows and are byte-identical after the registry warning patch. |
| Host-specific absolute paths | PASS: `sanitize_canonical_paths.py --dry-run` scanned 5904 files and found 0 replacements. |
| Stale path search | PASS after fixes: remaining hits are historical migration notes, wrapper names, registry warning labels, or old analysis reports explicitly marked as legacy. |
| Python test suite | PASS with project environment: `uv run pytest` gives 95 passed, 1 skipped, 2 ASE extxyz warnings. |
| System Python caveat | Expected failure: `/opt/homebrew/bin/python3` is Python 3.14 and lacks project deps; do not use it for reproducibility. |
| Overleaf compile | PASS: `latexmk -pdf -interaction=nonstopmode -halt-on-error main_new.tex` builds a 34-page PDF after fixes. |

## Fixes Applied

1. Added `research/agent_eval/manifests/ocd_gmae_subset24_vs_representative50_overlap.csv` to make the OCD24/rep50 relationship machine-readable.
2. Updated `research/agent_eval/manifests/README.md`, `research/results/README.md`, and `research/results/README_CN.md` to state that OCD24 and rep50 are independent selections, not nested subsets.
3. Fixed README example paths that still loaded `research/results/ocd_gmae_ablation_multi_backend_final.csv` instead of `research/results/analysis/ocd_gmae_ablation_multi_backend_final.csv`.
4. Updated `research/results/MIGRATION.md` so MACE-large, multiseed, and AA single-config controls point to the active `canonical_raw/controls/` locations.
5. Patched `research/agent_eval/rebuild_result_registries.py` to flag embedded historical manifest labels such as `ocd_gmae_manifest` and `ocd_gmae_rep50_manifest`; regenerated the registries.
6. Fixed Overleaf unresolved references by adding `\label{sec:methods}` to the Method section and removing main-text references to labels that live only in standalone `si.tex`.
7. Updated Overleaf wording so rep50 is described as separately/independently selected rather than an extension or superset of OCD24.

## Remaining Notes

- The working tree is intentionally dirty and contains a large staged/unstaged cleanup. Do not use broad reset or checkout commands.
- `overleaf/sections/1_Introduction_old.tex` is untracked and not included by `overleaf/main_new.tex`; it should be reviewed before any commit decision.
- Overleaf still has layout warnings, not build blockers: one overfull backend/model-ID line in Method, several underfull table cells, and a long Anthropic URL in the bibliography.
- The abstract and visible placeholders were not filled or removed, following the current collaboration rule that those are owned by the advisor/senior coauthor.
- `RUN_REGISTRY.csv` preserves embedded historical manifest labels as provenance. The canonical path to use is the `manifest_paths` column.

## Reproducible Commands

```bash
python3 research/agent_eval/rebuild_canonical_raw_qc.py --output /tmp/MERGE_QC.audit.csv
python3 research/agent_eval/rebuild_result_registries.py --run-output /tmp/RUN_REGISTRY.audit.csv --analysis-output /tmp/ANALYSIS_REGISTRY.audit.csv
python3 research/agent_eval/sanitize_canonical_paths.py --dry-run
uv run pytest
cd overleaf && latexmk -pdf -interaction=nonstopmode -halt-on-error main_new.tex
```
