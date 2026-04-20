# Agent Evaluation

This directory contains the reusable benchmark tooling and locked metadata used
for AdsMind's agent-side experiments. It is intended to be reproducible public
research infrastructure, not a logbook of local runs.

## Authoritative Inputs

- `manifests/cmu_manifest.csv`: CMU benchmark case definitions.
- `manifests/ocd_gmae_manifest.csv`: OCD-GMAE validation subset.
- `manifests/ocd_gmae_rep50_manifest.csv`: 50-case OCD-GMAE one-shot subset.
- `configs/frozen_config*.json`: backend-specific locked experiment configs.
  See `configs/README.md` for public routes versus provenance-only proxy
  routes.
- `generated_slabs/`: derived slab files for OCD-GMAE manifests.

OCD-GMAE manifest generation expects an LMDB dataset path via
`--lmdb-path` or `OCD_GMAE_LMDB_PATH`; no machine-specific default path is
stored in the repository.

## Core Commands

Run a manifest sequentially:

```bash
python -m research.agent_eval.run_batch \
  --manifest research/agent_eval/manifests/cmu_manifest.csv \
  --config research/agent_eval/configs/frozen_config_gemini25pro_vertexai_one_shot.json \
  --output research/results/cmu_v1_gemini_one_shot
```

Run an ablation matrix:

```bash
python -m research.agent_eval.run_ablation \
  --manifest research/agent_eval/manifests/cmu_manifest.csv \
  --config research/agent_eval/configs/frozen_config_gemini25pro_vertexai.json \
  --output research/results/gemini_ablation_v1 \
  --cases 01,02,09,14,19 \
  --variants full,no_slip,no_forbid,no_termination
```

Rebuild summaries from existing result directories:

```bash
python -m research.agent_eval.summarize_runs \
  --input research/results/cmu_v1_gemini_one_shot \
  --output research/results/cmu_v1_gemini_one_shot/summary.csv
```

```bash
python -m research.agent_eval.rebuild_ablation_summary \
  --ablation-dir research/results/gemini_ablation_v1 \
  --one-shot-dir research/results/cmu_v1_gemini_one_shot
```

## Useful Utilities

- `compare_adsorbagent.py`: joins AdsMind outputs with Adsorb-Agent reference values.
- `compare_llm_ablation.py`: compares ablation summaries across backends.
- `rank_one_shot_ranges.py`: ranks cases by cross-backend one-shot energy spread.
- `summarize_multi_backend_ablation.py`: builds multi-backend ablation tables.
- `evaluate_ocd_gmae_ground_truth.py`: compares OCD-GMAE predictions with reference values.
- `package_results.py`: creates curated result packages from local outputs.

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
