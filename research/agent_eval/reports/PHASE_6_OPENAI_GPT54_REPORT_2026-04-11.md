# Phase 6 Report: OpenAI GPT-5.4 Backend Evidence

Date: 2026-04-11
Source branch: `origin/openai`
Source commits: `079da20` (raw GPT-5.4 run), `7722809` (retry package)
Runtime git SHA recorded in configs: `292f4661dad5c5468a4cccf0fa984d1e1b1ea04b`
Model: `gpt-5.4-2026-03-05` via official OpenAI endpoint (`https://api.openai.com/v1`)
Physics protocol: MACE small, CPU, float32, no dispersion, standard relaxation, fmax=0.10

## Executive Summary

The OpenAI GPT-5.4 experiment is usable, but it must be reported with a retry-aware provenance policy rather than as a naive 20/20 raw one-shot success.

- Raw GPT-5.4 one-shot: 18/20 valid adsorption structures.
- Failed raw cases: 06, 08. Both are NNH systems that dissociated during the only one-shot attempt.
- Retry set: 1/2 valid. Case 08 recovered; case 06 reproduced the dissociation failure.
- Retry-corrected GPT-5.4 one-shot: 19/20 valid, with case 06 retained as failed.
- GPT-5.4 ablation matrix: 25/25 successful runs.

## Data Quality Checks

The raw tarballs were unpacked and converted into lightweight tracked results. The repository now tracks only structured summaries and `result.json` files; binary structures, trajectories, per-run configs, and agent logs remain excluded from the main result package.

Checks performed:

- All tracked `result.json` files parse successfully.
- All referenced artifacts exist in the source tarballs.
- No plaintext OpenAI API key was detected in the imported result files.
- OpenAI run configs record the expected model snapshot and endpoint.
- Ablation flags match the locked protocol for all five variants.

## One-Shot Results

The raw one-shot run failed on cases 06 and 08 because the only attempted NNH configuration dissociated. These are physics/agent outcomes, not API errors: the LLM call, MACE relaxation, and final analyzer all completed.

Retry outcome:

- Case 06: failed again with the same `ontop` Cu NNH dissociation pattern. This should be treated as a reproducible GPT-5.4 one-shot failure.
- Case 08: recovered with a valid hollow adsorption structure at -6.427181 eV, with chemical slip but no dissociation.

Recommended reporting policy:

- Use `openai_gpt54_one_shot_raw_summary.csv` for raw protocol accounting.
- Use `openai_gpt54_one_shot_corrected_summary.csv` only when explicitly stating that one retry was allowed for failed cases.
- Do not use the dissociated case 06 energy as a valid adsorption energy.

## Cross-LLM Agreement

Using the retry-corrected OpenAI table, valid OpenAI energy comparisons are available for 19/20 cases.

OpenAI vs Gemini:

- Mean absolute delta: 0.208345 eV
- Median absolute delta: 0.080742 eV
- Within 0.05 eV: 8/19
- Within 0.10 eV: 10/19

OpenAI vs Grok-4:

- Mean absolute delta: 0.272731 eV
- Median absolute delta: 0.170198 eV
- Within 0.05 eV: 5/19
- Within 0.10 eV: 6/19

The cross-model agreement is comparable in scale to the existing Gemini/Grok spread, but the site choices are not identical. This supports backend robustness as a qualitative claim, not exact trajectory determinism.

## Ablation Results

The GPT-5.4 ablation matrix completed all 25 runs and is suitable for the main agentic-system ablation comparison.

Full vs single-shot mean energy deltas, where positive means single-shot is worse than full:

- Gemini: 0.176347 eV
- Grok-4: 0.287669 eV
- GPT-5.4: 0.131232 eV

For GPT-5.4 specifically:

- Single-shot is worse than full on cases 01, 02, 14.
- Single-shot is better than full on cases none.
- Wilcoxon p-value: 0.25
- BH-adjusted p-value: 1.0

Interpretation: GPT-5.4 follows the same broad pattern as Gemini and Grok-4: multi-step closed-loop search improves the difficult subset on average, but the sample is too small for strong standalone significance claims. The result should be presented as converging evidence across backends.

## Recommended Manuscript Wording

A precise wording is:

"For GPT-5.4, the raw one-shot protocol produced valid adsorption structures for 18/20 CMU benchmark cases; the two failures were NNH dissociation outcomes rather than API/runtime failures. A single retry recovered case 08 but reproduced the case 06 dissociation, yielding a retry-corrected 19/20 valid set. The 5-case ablation matrix completed 25/25 runs and shows the same qualitative closed-loop benefit observed with Gemini and Grok-4."

Avoid writing:

- "GPT-5.4 achieved 20/20 one-shot success."
- "Case 06 has a valid GPT-5.4 one-shot adsorption energy."
- "The retry-corrected table is a pure one-shot baseline" unless the retry policy is explicitly disclosed.

## Output Files

- `research/results/openai_gpt54_one_shot_raw_summary.csv`
- `research/results/openai_gpt54_one_shot_retry_summary.csv`
- `research/results/openai_gpt54_one_shot_corrected_summary.csv`
- `research/results/openai_gpt54_one_shot_status.json`
- `research/results/cross_llm_20case_with_openai.csv`
- `research/results/cross_llm_20case_with_openai.json`
- `research/results/cross_llm_ablation_with_openai.csv`
- `research/results/cross_llm_ablation_with_openai.json`
- `research/results/openai_gpt54_paper_tables.tex`
