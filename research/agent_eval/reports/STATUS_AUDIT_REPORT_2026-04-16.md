# Status Audit Report (2026-04-16)

## Scope

This report summarizes the current AdsMind experiment state that has been prepared for external audit. It intentionally distinguishes between:
- completed and stable results that are ready for paper use,
- in-flight recovery or representative runs that are still changing,
- code and helper scripts added to support those runs.

Sensitive local planning notes containing plaintext API credentials were intentionally excluded from version control.

## Repository Snapshot

- Branch: `main`
- Base HEAD before this update: `a5aca2b`
- Working goal of this update:
  - preserve the current OCD-GMAE tooling and summary artifacts,
  - expose the exact current state for audit,
  - push the repository snapshot so another model can review the methodology and outputs.

## Stable Completed Results

### 1. CMU cross-backend ablation

The 5-case CMU ablation summaries currently present in the repository are complete and internally consistent:

- [research/results/gemini_ablation_v1/ablation_summary.csv](/Users/nagato/workspace/AdsMind/research/results/gemini_ablation_v1/ablation_summary.csv)
- [research/results/xai_ablation_v2/ablation_summary.csv](/Users/nagato/workspace/AdsMind/research/results/xai_ablation_v2/ablation_summary.csv)
- [research/results/openai_gpt54_ablation_v1/ablation_summary.csv](/Users/nagato/workspace/AdsMind/research/results/openai_gpt54_ablation_v1/ablation_summary.csv)
- [research/results/anthropic_sonnet46_ablation_v1/ablation_summary.csv](/Users/nagato/workspace/AdsMind/research/results/anthropic_sonnet46_ablation_v1/ablation_summary.csv)

Current row/success counts at the time of this report:
- Gemini: 25 / 25 success rows
- Grok-4: 25 / 25 success rows
- GPT-5.4: 25 / 25 success rows
- Claude Sonnet 4.6: 25 / 25 success rows

### 2. OCD-GMAE top-10 hard-subset ablation

The hard-subset selection logic and multi-backend aggregation artifacts are present:

- [research/results/ocd_gmae_one_shot_range_ranking.csv](/Users/nagato/workspace/AdsMind/research/results/ocd_gmae_one_shot_range_ranking.csv)
- [research/results/ocd_gmae_one_shot_range_ranking.json](/Users/nagato/workspace/AdsMind/research/results/ocd_gmae_one_shot_range_ranking.json)
- [research/results/ocd_gmae_ablation_multi_backend_final.csv](/Users/nagato/workspace/AdsMind/research/results/ocd_gmae_ablation_multi_backend_final.csv)
- [research/results/ocd_gmae_ablation_multi_backend_final.json](/Users/nagato/workspace/AdsMind/research/results/ocd_gmae_ablation_multi_backend_final.json)
- [research/results/ocd_gmae_ablation_final_vs_one_shot_4backend.csv](/Users/nagato/workspace/AdsMind/research/results/ocd_gmae_ablation_final_vs_one_shot_4backend.csv)

Important interpretation note:
- Grok, GPT-5.4, and Claude OCD-GMAE top-10 ablation summaries are complete.
- Gemini OCD-GMAE top-10 ablation is **not final yet** in this snapshot because a recovery job is still filling failed cells.
- Therefore the current 4-backend OCD-GMAE aggregate files should be treated as a **moving snapshot**, not as the frozen paper-final table.

Current OCD-GMAE ablation row/success counts in local summaries:
- Gemini: 50 rows / 21 success
- Grok-4: 50 rows / 50 success
- GPT-5.4: 50 rows / 50 success
- Claude Sonnet 4.6: 50 rows / 50 success

## New Data Preparation Assets

### 1. OCD-GMAE 24-case subset

Added scripts and manifests:
- [research/agent_eval/prepare_ocd_gmae.py](/Users/nagato/workspace/AdsMind/research/agent_eval/prepare_ocd_gmae.py)
- [research/agent_eval/manifests/ocd_gmae_manifest.csv](/Users/nagato/workspace/AdsMind/research/agent_eval/manifests/ocd_gmae_manifest.csv)
- [research/agent_eval/manifests/ocd_gmae_manifest_selection.json](/Users/nagato/workspace/AdsMind/research/agent_eval/manifests/ocd_gmae_manifest_selection.json)

This 24-case subset is the curated small-scale OCD-GMAE pool used for:
- initial four-backend one-shot screening,
- top-10 disagreement ranking,
- the hard-subset ablation.

### 2. OCD-GMAE representative 50-case subset

Added representative selection artifacts:
- [research/agent_eval/prepare_ocd_gmae_representative.py](/Users/nagato/workspace/AdsMind/research/agent_eval/prepare_ocd_gmae_representative.py)
- [research/agent_eval/manifests/ocd_gmae_rep50_manifest.csv](/Users/nagato/workspace/AdsMind/research/agent_eval/manifests/ocd_gmae_rep50_manifest.csv)
- [research/agent_eval/manifests/ocd_gmae_rep50_manifest_selection.json](/Users/nagato/workspace/AdsMind/research/agent_eval/manifests/ocd_gmae_rep50_manifest_selection.json)

Representative selection summary:
- pool candidate count: 287
- selected case count: 50
- selected counts by selection bucket:
  - `cmu_exact`: 6
  - `small_n_species`: 20
  - `small_organic`: 24
- selected counts by surface family:
  - `intermetallic`: 39
  - `compound`: 10
  - `monometallic`: 1

This 50-case set is meant for representative second-dataset one-shot validation, not ablation.

## New Automation / Execution Helpers

Added or updated helper scripts:
- [research/agent_eval/run_ocd_gmae_one_shot.sh](/Users/nagato/workspace/AdsMind/research/agent_eval/run_ocd_gmae_one_shot.sh)
- [research/agent_eval/launch_ocd_gmae_one_shot_tmux.sh](/Users/nagato/workspace/AdsMind/research/agent_eval/launch_ocd_gmae_one_shot_tmux.sh)
- [research/agent_eval/monitor_ocd_gmae_one_shot.sh](/Users/nagato/workspace/AdsMind/research/agent_eval/monitor_ocd_gmae_one_shot.sh)
- [research/agent_eval/launch_ocd_gmae_rep50_one_shot_tmux.sh](/Users/nagato/workspace/AdsMind/research/agent_eval/launch_ocd_gmae_rep50_one_shot_tmux.sh)
- [research/agent_eval/select_ocd_gmae_ablation_candidates.sh](/Users/nagato/workspace/AdsMind/research/agent_eval/select_ocd_gmae_ablation_candidates.sh)
- [research/agent_eval/rebuild_phase_a_extended.sh](/Users/nagato/workspace/AdsMind/research/agent_eval/rebuild_phase_a_extended.sh)
- [research/agent_eval/monitor_phase_a_progress.sh](/Users/nagato/workspace/AdsMind/research/agent_eval/monitor_phase_a_progress.sh)
- [research/agent_eval/recover_ocd_gmae_gemini_openrouter.sh](/Users/nagato/workspace/AdsMind/research/agent_eval/recover_ocd_gmae_gemini_openrouter.sh)
- [research/agent_eval/recover_ocd_gmae_gemini_robust.py](/Users/nagato/workspace/AdsMind/research/agent_eval/recover_ocd_gmae_gemini_robust.py)
- [research/agent_eval/watchdog_local_gemini_recovery.sh](/Users/nagato/workspace/AdsMind/research/agent_eval/watchdog_local_gemini_recovery.sh)
- [research/agent_eval/watchdog_rep50_one_shot.sh](/Users/nagato/workspace/AdsMind/research/agent_eval/watchdog_rep50_one_shot.sh)

## New Analysis Utilities

Added analysis/reduction utilities:
- [research/agent_eval/rank_one_shot_ranges.py](/Users/nagato/workspace/AdsMind/research/agent_eval/rank_one_shot_ranges.py)
- [research/agent_eval/summarize_multi_backend_ablation.py](/Users/nagato/workspace/AdsMind/research/agent_eval/summarize_multi_backend_ablation.py)
- [research/agent_eval/evaluate_ocd_gmae_ground_truth.py](/Users/nagato/workspace/AdsMind/research/agent_eval/evaluate_ocd_gmae_ground_truth.py)

## Important Bug Fixes Included In This Snapshot

### 1. Small-sample Friedman guard

Both of the following files were patched so Friedman is only attempted when at least 3 complete variants are present:
- [research/agent_eval/run_ablation.py](/Users/nagato/workspace/AdsMind/research/agent_eval/run_ablation.py)
- [research/agent_eval/rebuild_ablation_summary.py](/Users/nagato/workspace/AdsMind/research/agent_eval/rebuild_ablation_summary.py)

This matters because the Gemini recovery workflow may temporarily produce matrices where only `full` plus `single_shot` are complete. Before the patch, those states could crash the rebuild step.

### 2. Gemini provider preference

`recover_ocd_gmae_gemini_robust.py` now prefers:
- OpenRouter first
- AiHubMix second

This matches the current execution policy used during recovery.

## Ground-Truth Evaluation Status

A new evaluator was added for OCD-GMAE `y_relaxed` comparison:
- [research/agent_eval/evaluate_ocd_gmae_ground_truth.py](/Users/nagato/workspace/AdsMind/research/agent_eval/evaluate_ocd_gmae_ground_truth.py)

Important interpretation note:
- the currently committed 24-case one-shot ground-truth comparisons show large absolute errors,
- so if future representative-50 results look similar, the paper should emphasize robustness / variance reduction rather than DFT-accuracy parity.

## In-Flight Jobs At Report Time

### 1. Local Gemini recovery

The local Gemini OCD-GMAE recovery is still running under watchdog supervision.
Its current purpose is to reduce the remaining failed Gemini top-10 ablation cells.
Therefore these files are still moving targets:
- [research/results/ocd_gmae_gemini_ablation_v1/ablation_summary.csv](/Users/nagato/workspace/AdsMind/research/results/ocd_gmae_gemini_ablation_v1/ablation_summary.csv)
- [research/results/ocd_gmae_gemini_ablation_v1/ablation_stats.json](/Users/nagato/workspace/AdsMind/research/results/ocd_gmae_gemini_ablation_v1/ablation_stats.json)
- [research/results/ocd_gmae_gemini_ablation_failed_cells.csv](/Users/nagato/workspace/AdsMind/research/results/ocd_gmae_gemini_ablation_failed_cells.csv)
- [research/results/ocd_gmae_ablation_multi_backend_final.csv](/Users/nagato/workspace/AdsMind/research/results/ocd_gmae_ablation_multi_backend_final.csv)
- [research/results/ocd_gmae_ablation_multi_backend_final.json](/Users/nagato/workspace/AdsMind/research/results/ocd_gmae_ablation_multi_backend_final.json)

### 2. Remote representative 50-case one-shot

The representative 50-case OCD-GMAE four-backend one-shot run is active on the EPFL workstation.
The remote sessions active at the time of the last check were:
- `ocd_rep50_gemini_os`
- `ocd_rep50_grok_os`
- `ocd_rep50_gpt54_os`
- `ocd_rep50_claude_os`
- `ocd_rep50_guard`
- `ocd_rep50_rank_wait`
- `ocd_rep50_eval_wait`

These outputs are not committed in this snapshot because they are still in progress.

## Test Coverage Added In This Update

- [tests/test_prepare_ocd_gmae.py](/Users/nagato/workspace/AdsMind/tests/test_prepare_ocd_gmae.py)
- [tests/test_prepare_ocd_gmae_representative.py](/Users/nagato/workspace/AdsMind/tests/test_prepare_ocd_gmae_representative.py)
- [tests/test_rank_one_shot_ranges.py](/Users/nagato/workspace/AdsMind/tests/test_rank_one_shot_ranges.py)
- [tests/test_summarize_multi_backend_ablation.py](/Users/nagato/workspace/AdsMind/tests/test_summarize_multi_backend_ablation.py)
- [tests/test_evaluate_ocd_gmae_ground_truth.py](/Users/nagato/workspace/AdsMind/tests/test_evaluate_ocd_gmae_ground_truth.py)
- [tests/test_rebuild_ablation_summary.py](/Users/nagato/workspace/AdsMind/tests/test_rebuild_ablation_summary.py)

## Audit Questions Worth Checking

For Claude audit, the highest-value checks are:
- whether the representative-50 selection policy is sufficiently defensible for JCIM,
- whether the hard-subset top-10 OCD-GMAE ablation should be described as stress-test rather than representative validation,
- whether any currently committed aggregate table is incorrectly treated as final despite Gemini recovery still being in flight,
- whether the watchdog scripts are robust enough for long unattended runs,
- whether the paper claims should be phrased around backend robustness rather than absolute adsorption-energy accuracy.
