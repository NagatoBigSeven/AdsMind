# Agent Evaluation

This directory contains the reusable benchmark tooling and locked metadata used
for AdsMind's agent-side experiments. It is intended to be reproducible public
research infrastructure, not a logbook of local runs.

## Authoritative Inputs

- `datasets/cmu20/cmu20_manifest.csv`: CMU20 benchmark case definitions.
- `datasets/ocd62/ocd62_manifest.csv`: OCD62 benchmark case definitions.
- `datasets/ocd62_overlap12/overlap12_manifest.csv`: overlap12 reproducibility input.
- `configs/frozen_config*.json`: backend-specific locked experiment configs.
  See `configs/README.md`.

## Script Map

The recommended entrypoints are grouped by role.

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
| Narrow comparison | `compare_two_backend_ablation.py` | Auxiliary CLI | Compare exactly two backend ablation tables; not the main 4-backend analysis. |
Compatibility wrappers retained for renamed analysis helpers:
`compare_llm_ablation.py`, `summarize_multi_backend_ablation.py`,
`rank_one_shot_ranges.py`, and `evaluate_ocd_gmae_ground_truth.py`.

## Core Commands

Run a manifest sequentially:

```bash
python -m research.agent_eval.run_batch \
  --manifest datasets/cmu20/cmu20_manifest.csv \
  --config research/agent_eval/configs/frozen_config_gemini25pro_vertexai_one_shot.json \
  --output research/results/example_cmu20_gemini_one_shot
```

Run an ablation matrix:

```bash
python -m research.agent_eval.run_ablation \
  --manifest datasets/cmu20/cmu20_manifest.csv \
  --config research/agent_eval/configs/frozen_config_gemini25pro_vertexai.json \
  --output research/results/example_gemini_ablation \
  --cases 01,02,09,14,19 \
  --variants full,no_slip,no_forbid,no_termination,one_shot
```

Rebuild summaries from existing result directories:

```bash
python -m research.agent_eval.summarize_runs \
  --output research/results/example_cmu20_gemini_one_shot
```

```bash
python -m research.agent_eval.rebuild_ablation_summary \
  --ablation-dir research/results/example_gemini_ablation \
  --one-shot-dir research/results/example_cmu20_gemini_one_shot
```

Aggregate a 4-backend ablation table:

```bash
python -m research.agent_eval.aggregate_ablation_across_backends \
  --summary gpt=research/results/basic_experiments/cmu20/gpt/all_variants_summary.csv \
  --summary claude=research/results/basic_experiments/cmu20/claude/all_variants_summary.csv \
  --summary gemini=research/results/basic_experiments/cmu20/gemini/all_variants_summary.csv \
  --summary grok=research/results/basic_experiments/cmu20/grok/all_variants_summary.csv \
  --output-csv research/results/basic_experiments/cmu20/summaries/ablation_4backend.csv \
  --output-json research/results/basic_experiments/cmu20/summaries/ablation_4backend.json
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
