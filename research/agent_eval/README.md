# Agent Evaluation

This directory contains the reusable benchmark tooling and locked metadata used
for AdsMind's agent-side experiments. It is intended to be reproducible public
research infrastructure, not a logbook of local runs.

## Authoritative Inputs

- `manifests/cmu_manifest.csv`: CMU benchmark case definitions.
- `manifests/ocd_gmae_subset24_manifest.csv`: 24-case OCD-GMAE
  validation subset used for the full ablation matrix.
- `manifests/ocd_gmae_representative50_manifest.csv`: 50-case OCD-GMAE
  representative subset used for broader one-shot/generalisation checks.
- `configs/frozen_config*.json`: backend-specific locked experiment configs.
  See `configs/README.md` for public routes versus provenance-only proxy
  routes.
- `generated_slabs/`: derived slab files for OCD-GMAE manifests. This is not
  the full OCD-GMAE dataset; see `generated_slabs/README.md`.
- CMU benchmark slabs are committed under `datasets/cmu-20/` at the repo root
  (20 `.xyz` files matching `manifests/cmu_manifest.csv` rows). Older
  `cmu_manifest.csv` paths still use the `benchmark_slabs/<file>` form and
  expect a local symlink → `datasets/cmu-20/`; see
  `research/results/MIGRATION.md` for the path rewrite plan.

OCD-GMAE manifest generation expects an LMDB dataset path via
`--lmdb-path` or `OCD_GMAE_LMDB_PATH`; no machine-specific default path is
stored in the repository.

## Script Map

The recommended entrypoints are grouped by role. Older command names are kept
as compatibility wrappers when renaming would otherwise break historical notes
or external runbooks.

| Role | Script | Status | Use |
|---|---|---|---|
| Shared code | `common.py` | Core library | Manifest/config parsing, run payloads, statistics helpers. |
| Shared code | `baseline_utils.py` | Core library | Utilities used by random and heuristic non-LLM baselines. |
| Run AdsMind | `run_case.py` | Core CLI | Run one case with one frozen config. |
| Run AdsMind | `run_batch.py` | Core CLI | Run a manifest sequentially with one frozen config. |
| Run AdsMind | `run_ablation.py` | Core CLI | Run full / w/o Slip / w/o Forbid / w/o Term / 1-Shot ablations. |
| Run baselines | `run_random_baseline.py` | Core CLI | Random placement baseline. |
| Run baselines | `run_heuristic_baseline.py` | Core CLI | High-symmetry-site heuristic baseline. |
| Rebuild outputs | `summarize_runs.py` | Current CLI | Rebuild one-row-per-case summaries from result directories. |
| Rebuild outputs | `rebuild_ablation_summary.py` | Current CLI | Rebuild ablation summary/stats from persisted `result.json` files. |
| Rebuild outputs | `rebuild_baseline_summary.py` | Current CLI | Rebuild random/heuristic baseline summaries and filter abnormal energies. |
| Manuscript analysis | `aggregate_ablation_across_backends.py` | Current CLI | Aggregate ablation summaries across 4 backends. |
| Manuscript analysis | `rank_one_shot_backend_spread.py` | Current CLI | Rank one-shot cases by cross-backend energy spread. |
| Manuscript analysis | `compare_ocd_one_shot_to_reference.py` | Current CLI | Compare OCD-GMAE one-shot outputs with OCD-GMAE reference labels. |
| Manuscript analysis | `compare_adsorbagent.py` | Current CLI | Join AdsMind summaries with Adsorb-Agent reference values. |
| Manuscript analysis | `summarize_adsorbagent_mace.py` | Current CLI | Summarize Adsorb-Agent MACE reruns and paired AdsMind comparison. |
| Diagnostics | `iteration_convergence.py` | Current CLI | Extract per-iteration running-best energy curves. |
| DFT alignment | `export_dft_iteration_alignment.py` | Current CLI | Export per-iteration AdsMind trajectories for DFT comparison. |
| DFT alignment | `render_dft_alignment_snapshots.py` | Current CLI | Render quick PNG snapshots for DFT-alignment packages. |
| Figures | `render_panel_b_assets.py` | Current CLI | Render Panel B structure thumbnails/contact sheets. |
| Manifest generation | `prepare_ocd_gmae.py` | Reproducibility CLI | Build the 24-case OCD-GMAE manifest from an LMDB source. |
| Manifest generation | `prepare_ocd_gmae_representative.py` | Reproducibility CLI | Build the 50-case OCD-GMAE representative manifest from an LMDB source. |
| Narrow comparison | `compare_two_backend_ablation.py` | Auxiliary CLI | Compare exactly two backend ablation tables; not the main 4-backend analysis. |
| Maintenance | `maintenance_merge_split_result_dirs.py` | Maintenance CLI | Merge split historical result directories into `canonical_raw/`. |
| Legacy handoff | `legacy_prepare_topk_dft_handoff.py` | Legacy CLI | Older top-k DFT handoff workflow; current DFT workflow is `export_dft_iteration_alignment.py`. |
| Legacy packaging | `legacy_package_results.py` | Legacy CLI | Pre-`canonical_raw` packaging workflow; keep only for old runbooks. |

Compatibility wrappers retained for older commands:
`compare_llm_ablation.py`, `summarize_multi_backend_ablation.py`,
`rank_one_shot_ranges.py`, `evaluate_ocd_gmae_ground_truth.py`,
`merge_split_result_dirs.py`, `prepare_dft_validation.py`, and
`package_results.py`.

## Core Commands

Run a manifest sequentially:

```bash
python -m research.agent_eval.run_batch \
  --manifest research/agent_eval/manifests/cmu_manifest.csv \
  --config research/agent_eval/configs/frozen_config_gemini25pro_vertexai_one_shot.json \
  --output research/results/canonical_raw/legacy_raw_sources/cmu20_gemini_one_shot
```

Run an ablation matrix:

```bash
python -m research.agent_eval.run_ablation \
  --manifest research/agent_eval/manifests/cmu_manifest.csv \
  --config research/agent_eval/configs/frozen_config_gemini25pro_vertexai.json \
  --output research/results/example_gemini_ablation \
  --cases 01,02,09,14,19 \
  --variants full,no_slip,no_forbid,no_termination,single_shot
```

Rebuild summaries from existing result directories:

```bash
python -m research.agent_eval.summarize_runs \
  --output research/results/canonical_raw/legacy_raw_sources/cmu20_gemini_one_shot
```

```bash
python -m research.agent_eval.rebuild_ablation_summary \
  --ablation-dir research/results/example_gemini_ablation \
  --one-shot-dir research/results/canonical_raw/legacy_raw_sources/cmu20_gemini_one_shot
```

Aggregate a 4-backend ablation table:

```bash
python -m research.agent_eval.aggregate_ablation_across_backends \
  --summary gemini=research/results/canonical_raw/cmu20_gemini_ablation/ablation_summary.csv \
  --summary grok4=research/results/canonical_raw/cmu20_grok4_ablation/ablation_summary.csv \
  --summary gpt54=research/results/canonical_raw/cmu20_openai_gpt54_ablation/ablation_summary.csv \
  --summary claude=research/results/canonical_raw/cmu20_anthropic_sonnet46_ablation/ablation_summary.csv \
  --output-csv research/results/analysis/cmu20_multi_backend_ablation_summary.csv \
  --output-json research/results/analysis/cmu20_multi_backend_ablation_summary.json
```

## Results

Paper-facing outputs live in `research/results/`. Start with
`research/results/README.md` before using any CSV/JSON file, because several
intermediate tables have similar names and some superseded tables were removed
during public-release cleanup.

## Public-Release Policy

- Do not commit API keys, provider credentials, local shell profiles, or private
  workstation details.
- Do not commit transient run logs, tmux/watchdog notes, local status reports,
  per-run `config.json`, `agent_log.txt`, trajectories, or generated structures.
- Keep historical execution plans and local recovery notes outside version
  control. Reproducibility should come from manifests, frozen configs, scripts,
  and the curated result manifest.
