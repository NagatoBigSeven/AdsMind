# Phase 2 Report

## Scope

Phase 2 covered the first real benchmark execution work after the runner and
instrumentation pipeline were in place.

## What Was Done

1. Added an AIHubMix OpenAI-compatible transport path without mutating the
   direct-Google reference config:
   - [frozen_config_aihubmix.json](/Users/nagato/workspace/AdsMind/research/agent_eval/configs/frozen_config_aihubmix.json)
2. Extended the `openrouter` backend so experiment-time `base_url` and transport
   headers can be injected from config.
3. Fixed two real execution blockers discovered during the first live run:
   - null relaxation overrides causing `int(None)` in
     [agent.py](/Users/nagato/workspace/AdsMind/src/agent/agent.py)
   - MACE / torch compatibility on macOS in
     [mace_backend.py](/Users/nagato/workspace/AdsMind/src/calculators/mace_backend.py)
4. Re-ran the first official case (`01`, Mo3Pd(111) + H) through the full live
   stack: `LLM -> planner -> validator -> MACE relaxation -> analysis`.
5. Generated structured comparison assets from historical AdsMind outputs and
   Adsorb-Agent paper values.
6. Ran the first official multi-case batch (`01, 02, 09, 14, 19`) and produced
   an interpreted summary even though the batch was interrupted by quota.
7. Hardened the runner so it now preserves the last streamed state on runtime
   exceptions instead of discarding all partial success information.
8. Verified a native xAI route with a completed one-shot case so the benchmark
   no longer depends on AIHubMix availability to continue.

## Problems Encountered

1. Direct Google API access could not be used because the current Google quota
   for `gemini-3.1-pro-preview` was unavailable at runtime.
2. The first AIHubMix smoke run failed because the ambient
   `OPENROUTER_API_KEY` was not a valid AIHubMix token for chat completions.
3. The first real tool-execution path exposed a `None` relaxation override bug.
4. The first successful MACE initialization exposed a torch compatibility issue:
   `torch.compiler.is_compiling` is absent in `torch==2.2.1`.
5. AIHubMix then ran into `insufficient_user_quota`, which blocked the rest of
   batch1 after partial progress on case `01`.

## Resolutions

1. Switched the experiment transport to AIHubMix while preserving the target
   model ID.
2. Used the provided AIHubMix key only for runtime execution, not in committed
   repository files.
3. Filtered `None` relaxation values and added a fallback override helper.
4. Added a compatibility shim so MACE can run on this macOS torch stack.
5. Updated [run_case.py](/Users/nagato/workspace/AdsMind/research/agent_eval/run_case.py)
   to stream graph states and retain the last good state when a later exception
   occurs.
6. Added xAI-native experiment configs so the same runner can target the xAI
   endpoint without changing product defaults:
   - [frozen_config_xai_grok4.json](/Users/nagato/workspace/AdsMind/research/agent_eval/configs/frozen_config_xai_grok4.json)
   - [frozen_config_xai_grok4_one_shot.json](/Users/nagato/workspace/AdsMind/research/agent_eval/configs/frozen_config_xai_grok4_one_shot.json)

## Data Obtained So Far

### Historical structured baseline

Files:

- [historical_adsmind_results.csv](/Users/nagato/workspace/AdsMind/research/results/historical_adsmind_results.csv)
- [historical_vs_adsorbagent.csv](/Users/nagato/workspace/AdsMind/research/results/historical_vs_adsorbagent.csv)
- [historical_summary_primary_set.json](/Users/nagato/workspace/AdsMind/research/results/historical_summary_primary_set.json)

Primary-set summary (`19` cases, excluding anomalous case `20`):

- AdsMind lower-energy cases vs Adsorb-Agent paper: `16`
- Adsorb-Agent paper lower-energy cases: `3`
- mean energy delta: `-2.2453 eV`

### Official rerun data

Live run directory:

- [cmu_v1_aihubmix_smoke](/Users/nagato/workspace/AdsMind/research/results/cmu_v1_aihubmix_smoke)

Current provisional artifact:

- [provisional_result.json](/Users/nagato/workspace/AdsMind/research/results/cmu_v1_aihubmix_smoke/01/provisional_result.json)

Current status for case `01`:

- run is still in progress under the locked `max_attempts=5` setting
- `3` successful attempts have already been logged
- current provisional best adsorption energy: `-3.6317 eV`
- current provisional best structure:
  [BEST_H_bridge_to_hollow_HCP-Subsurf-Atom_E-3.632.xyz](/Users/nagato/workspace/AdsMind/outputs/01-7cbfd5dd/BEST_H_bridge_to_hollow_HCP-Subsurf-Atom_E-3.632.xyz)

### Batch 1

Batch directory:

- [cmu_v1_aihubmix_batch1](/Users/nagato/workspace/AdsMind/research/results/cmu_v1_aihubmix_batch1)

Key outputs:

- [summary.csv](/Users/nagato/workspace/AdsMind/research/results/cmu_v1_aihubmix_batch1/summary.csv)
- [interpreted_summary.json](/Users/nagato/workspace/AdsMind/research/results/cmu_v1_aihubmix_batch1/interpreted_summary.json)
- [salvaged_result.json](/Users/nagato/workspace/AdsMind/research/results/cmu_v1_aihubmix_batch1/01/salvaged_result.json)

Batch 1 outcome:

- `01`: partial success, then quota blocked
- `02`: quota blocked before physics
- `09`: quota blocked before physics
- `14`: quota blocked before physics
- `19`: quota blocked before physics

### Native xAI validation run

Files:

- [cmu_v1_xai_one_shot](/Users/nagato/workspace/AdsMind/research/results/cmu_v1_xai_one_shot)
- [summary.csv](/Users/nagato/workspace/AdsMind/research/results/cmu_v1_xai_one_shot/summary.csv)
- [result.json](/Users/nagato/workspace/AdsMind/research/results/cmu_v1_xai_one_shot/01/result.json)
- [comparison_snapshot.json](/Users/nagato/workspace/AdsMind/research/results/cmu_v1_xai_one_shot/01/comparison_snapshot.json)

Case `01` native xAI result:

- status: `success`
- model: `grok-4-0709`
- best adsorption energy: `-3.6312 eV`
- iteration count: `1`
- chemical slip count: `0`
- total tokens: `6419`
- wall time: `94.15 s`

Comparison for case `01`:

- vs historical AdsMind: `-0.9932 eV` lower
- vs Adsorb-Agent paper: `-2.8672 eV` lower

This result confirms that the native xAI route can be used to continue official
agent-side reruns when AIHubMix quota is unavailable.

## What I Need From You

Nothing is blocking me at the information level right now.

Nothing is blocking continuation right now at the transport level.

The next decision is operational:

1. continue official reruns on native xAI, or
2. switch back to the locked Gemini route later if fresh quota becomes available.
