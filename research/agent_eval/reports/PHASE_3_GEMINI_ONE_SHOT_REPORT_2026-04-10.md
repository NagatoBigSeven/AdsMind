# Phase 3 Report: Gemini 2.5 Pro 20/20 One-Shot Baseline

## Scope

This phase executed the full `20/20` CMU benchmark under the locked one-shot Gemini configuration:

- config: `/Users/nagato/workspace/AdsMind/research/agent_eval/configs/frozen_config_gemini25pro_one_shot.json`
- manifest: `/Users/nagato/workspace/AdsMind/research/agent_eval/manifests/cmu_manifest.csv`
- output: `/Users/nagato/workspace/AdsMind/research/results/cmu_v1_gemini_one_shot`

The run used:

- `AiHubMix` OpenAI-compatible transport
- model `gemini-2.5-pro`
- `MACE small`
- `cpu`
- `float32`
- `max_attempts=1`

## Completion Status

- Completed cases: `20/20`
- Successful cases: `20/20`
- Error cases: `0/20`
- Output summary: `/Users/nagato/workspace/AdsMind/research/results/cmu_v1_gemini_one_shot/summary.csv`

This establishes the first complete Gemini one-shot baseline for the current AdsMind benchmark protocol.

## Gemini One-Shot Summary

Aggregate metrics from `/Users/nagato/workspace/AdsMind/research/results/cmu_v1_gemini_one_shot/summary.csv`:

- mean adsorption energy: `-3.6000 eV`
- slip cases: `12/20`
- mean total tokens per case: `7471.1`

Representative cases:

- `01`: `-3.5663 eV`, `hollow -> bridge` slip
- `09`: `-1.8014 eV`, no slip, fully reproducible with the earlier smoke run
- `15`: `-2.8887 eV`, no slip
- `16`: `-4.5376 eV`, no slip
- `20`: `-10.6045 eV`, `ontop -> hollow` slip

## Direct Comparison to Grok-4 One-Shot

Unlike the earlier Adsorb-Agent paper comparison, this comparison is physically meaningful because both sides use the same AdsMind runtime, the same benchmark manifest, and the same MACE evaluator. The only intended backend change is the LLM.

Comparison artifacts:

- casewise comparison: `/Users/nagato/workspace/AdsMind/research/results/cmu_v1_gemini_one_shot/gemini_vs_grok4_one_shot.csv`
- aggregate stats: `/Users/nagato/workspace/AdsMind/research/results/cmu_v1_gemini_one_shot/gemini_vs_grok4_one_shot_stats.json`

Summary:

- Gemini lower than Grok-4: `8/20`
- Grok-4 lower than Gemini: `9/20`
- exact ties: `3/20`
- mean energy delta (`Gemini - Grok-4`): `+0.0667 eV`
- median energy delta: `0.0000 eV`
- mean absolute energy delta: `0.1911 eV`
- Gemini mean tokens: `7471.1`
- Grok-4 mean tokens: `6266.6`
- mean token delta (`Gemini - Grok-4`): `+1204.6`
- Gemini slip cases: `12/20`
- Grok-4 slip cases: `12/20`

Interpretation:

- Gemini does **not** dominate Grok-4 on this benchmark.
- Grok-4 has a slight edge in average energy, but the mean gap is small: `0.0667 eV`.
- The median delta is exactly `0`, which means the backend effect is modest relative to case-to-case physical variability.
- Gemini currently costs more tokens on average while not improving aggregate one-shot performance.

Largest Gemini advantages:

- `19`: `-0.4354 eV`
- `06`: `-0.3216 eV`
- `15`: `-0.3014 eV`
- `02`: `-0.1830 eV`

Largest Grok-4 advantages:

- `08`: `+0.9591 eV`
- `10`: `+0.5903 eV`
- `12`: `+0.4739 eV`
- `17`: `+0.2932 eV`

## Main Outcome

Phase 3 is complete and yields a usable backend-comparison baseline:

- AdsMind can run the full benchmark with `Gemini 2.5 Pro` in one-shot mode.
- The run is stable enough for paper-grade backend comparison tables.
- Under the current evaluator and hardware constraints, `Gemini 2.5 Pro` is competitive with `Grok-4`, but not clearly superior.

## Recommended Next Step

Proceed to Phase 4:

- run the `5 x 5` Gemini ablation matrix on cases `01, 02, 09, 14, 19`
- use the existing Grok-4 full results as a reference line
- treat the Gemini ablation as the primary agentic evidence, not the one-shot backend comparison
