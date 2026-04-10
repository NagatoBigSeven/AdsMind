# Agent Eval

This directory contains the reproducible tooling and metadata for AdsMind's
agent-side benchmark and ablation work.

## Layout

- [`common.py`](/Users/nagato/workspace/AdsMind/research/agent_eval/common.py)
  Shared helpers for loading manifests/configs, serializing results, and
  computing summary statistics.
- [`run_case.py`](/Users/nagato/workspace/AdsMind/research/agent_eval/run_case.py)
  Run one benchmark case and persist a structured case directory.
- [`run_batch.py`](/Users/nagato/workspace/AdsMind/research/agent_eval/run_batch.py)
  Execute a manifest sequentially and emit a summary CSV.
- [`run_ablation.py`](/Users/nagato/workspace/AdsMind/research/agent_eval/run_ablation.py)
  Run the locked ablation variants on a selected case set.
- [`summarize_runs.py`](/Users/nagato/workspace/AdsMind/research/agent_eval/summarize_runs.py)
  Rebuild a summary table from an output directory.
- [`compare_adsorbagent.py`](/Users/nagato/workspace/AdsMind/research/agent_eval/compare_adsorbagent.py)
  Join AdsMind outputs with paper-reported Adsorb-Agent values and compute
  comparison statistics.
- [`package_results.py`](/Users/nagato/workspace/AdsMind/research/agent_eval/package_results.py)
  Build curated handoff and SI-ready result packages from local outputs.

## Metadata

- [`manifests/cmu_manifest.csv`](/Users/nagato/workspace/AdsMind/research/agent_eval/manifests/cmu_manifest.csv)
  Locked benchmark case definitions.
- [`configs/frozen_config.json`](/Users/nagato/workspace/AdsMind/research/agent_eval/configs/frozen_config.json)
  Reference experiment config.
- [`configs/frozen_config_aihubmix.json`](/Users/nagato/workspace/AdsMind/research/agent_eval/configs/frozen_config_aihubmix.json)
  AIHubMix transport variant used when direct Google quota was blocked.
- [`configs/frozen_config_xai_grok4.json`](/Users/nagato/workspace/AdsMind/research/agent_eval/configs/frozen_config_xai_grok4.json)
  xAI transport variant for multi-attempt runs.
- [`configs/frozen_config_xai_grok4_one_shot.json`](/Users/nagato/workspace/AdsMind/research/agent_eval/configs/frozen_config_xai_grok4_one_shot.json)
  xAI transport variant for one-shot runs.

## Reports

- [`reports/SMILES_RESOLUTION.md`](/Users/nagato/workspace/AdsMind/research/agent_eval/reports/SMILES_RESOLUTION.md)
- [`reports/PHASE_0_REPORT.md`](/Users/nagato/workspace/AdsMind/research/agent_eval/reports/PHASE_0_REPORT.md)
- [`reports/PHASE_2_REPORT.md`](/Users/nagato/workspace/AdsMind/research/agent_eval/reports/PHASE_2_REPORT.md)

## Notes

- Local machine-generated outputs belong under
  [`research/results`](/Users/nagato/workspace/AdsMind/research/results), which is Git-ignored by default.
- This directory is for reusable experiment logic and curated metadata, not raw
  run products.
