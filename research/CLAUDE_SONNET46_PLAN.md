# Codex Execution Plan — Claude Sonnet 4.6 Backend (Phase 7)

**Date**: 2026-04-12
**Context**: Three backends (Gemini, Grok-4, GPT-5.4) are complete. This plan adds
Claude Sonnet 4.6 as the fourth LLM backend. Frozen configs already exist.

---

## Phase 7a: 20-Case One-Shot Benchmark

**Goal**: Run all 20 CMU benchmark cases in one-shot mode with Claude Sonnet 4.6.

```bash
export ANTHROPIC_API_KEY="<key>"
python -m research.agent_eval.run_batch \
  --manifest research/agent_eval/manifests/cmu_manifest.csv \
  --config research/agent_eval/configs/frozen_config_anthropic_sonnet46_one_shot.json \
  --output research/results/cmu_v1_anthropic_sonnet46_one_shot \
  --cases 01,02,03,04,05,06,07,08,09,10,11,12,13,14,15,16,17,18,19,20
```

**After completion**, generate summary:
```bash
python -m research.agent_eval.summarize_runs \
  --input research/results/cmu_v1_anthropic_sonnet46_one_shot \
  --output research/results/cmu_v1_anthropic_sonnet46_one_shot/summary.csv
```

**Expected**: 20 runs. If any fail (especially NNH cases 02, 06, 08), retry failed
cases only:
```bash
python -m research.agent_eval.run_batch \
  --manifest research/agent_eval/manifests/cmu_manifest.csv \
  --config research/agent_eval/configs/frozen_config_anthropic_sonnet46_one_shot.json \
  --output research/results/cmu_v1_anthropic_sonnet46_one_shot_retry \
  --cases <failed_case_ids>
```

---

## Phase 7b: 5-Case Ablation Matrix

**Goal**: Run 4 ablation variants × 5 cases = 20 runs. The `single_shot` variant
is covered by Phase 7a (cases 01, 02, 09, 14, 19).

```bash
export ANTHROPIC_API_KEY="<key>"
python -m research.agent_eval.run_ablation \
  --manifest research/agent_eval/manifests/cmu_manifest.csv \
  --config research/agent_eval/configs/frozen_config_anthropic_sonnet46.json \
  --output research/results/anthropic_sonnet46_ablation_v1 \
  --cases 01,02,09,14,19 \
  --variants full,no_slip,no_forbid,no_termination
```

**After completion**, rebuild ablation summary:
```bash
python -m research.agent_eval.rebuild_ablation_summary \
  --ablation-dir research/results/anthropic_sonnet46_ablation_v1 \
  --one-shot-dir research/results/cmu_v1_anthropic_sonnet46_one_shot \
  --cases 01,02,09,14,19 \
  --variants full,no_slip,no_forbid,no_termination,single_shot
```

---

## Phase 7c: Post-Processing (after both phases complete)

### 1. One-shot status report

Create `research/results/anthropic_sonnet46_one_shot_status.json` with:
- Raw success/failure counts
- If retries were needed: corrected counts and retry case list
- Same structure as `openai_gpt54_one_shot_status.json`

### 2. Extend cross-LLM ablation comparison

Update `research/results/cross_llm_ablation_with_openai.json` → rename or create
`research/results/cross_llm_ablation_4backend.json` with Claude added as 4th backend.

Compute per-variant:
- 4-backend range (max − min) per case
- Mean 4-backend range
- Cases within 0.01 eV

### 3. Extend cross-LLM 20-case comparison

Update `research/results/cross_llm_20case_with_openai.json` → create
`research/results/cross_llm_20case_4backend.json` with pairwise Claude vs each
of the other 3 backends.

### 4. Update SI data files

All of these need Claude Sonnet 4.6 data appended (same pattern as GPT-5.4 update):

- `si4_ablation_statistics.json` + `.tex` — add `anthropic_sonnet46` pairwise stats
- `si6_cost_analysis.json` + `.tex` — add Claude ablation + one-shot cost data
- `case19_trajectory.json` + `.csv` — add Claude case 19 attempt records
- `slip_analysis.json` — add Claude one-shot slip rates

### 5. Update paper tables

- Add Table for Claude ablation energy matrix in `paper_tables.tex`
  (same format as Tables 1–3)
- Update Table 4 (cross-LLM summary) with 4-backend range
- Update Table 5 (key metrics) with Claude column
- Update Table 6 (H₁ test) with Claude column

### 6. Update gitignore

Add to `research/results/.gitignore`:
```
!anthropic_sonnet46_ablation_v1/
!cmu_v1_anthropic_sonnet46_one_shot/
!cmu_v1_anthropic_sonnet46_one_shot_retry/
!anthropic_sonnet46_ablation_v1/*/
!anthropic_sonnet46_ablation_v1/*/*/
!anthropic_sonnet46_ablation_v1/*/*/result.json
!cmu_v1_anthropic_sonnet46_one_shot/*/
!cmu_v1_anthropic_sonnet46_one_shot/*/result.json
!cmu_v1_anthropic_sonnet46_one_shot_retry/*/
!cmu_v1_anthropic_sonnet46_one_shot_retry/*/result.json
```

---

## What NOT to do

- Do NOT modify source code in `src/`
- Do NOT modify `research/agent_eval/*.py`
- Do NOT modify the existing paper section .tex files (2_Method.tex, 3_Results.tex,
  4_DiscussionConclusion.tex — those require manual review after data update)
- Do NOT delete any existing result files
- Do NOT create new Python scripts — use inline python commands
- Do NOT rerun Gemini, Grok-4, or GPT-5.4 experiments

## Key fields in result.json

Same as documented in `NEXT_STEPS_FOR_CODEX.md`.

## Estimated run count

| Phase | Runs | Expected time per run |
|-------|------|-----------------------|
| 7a: one-shot | 20 | 1–3 min |
| 7a: retry | 0–3 | 1–3 min |
| 7b: ablation | 20 | 2–10 min |
| 7c: post-processing | 0 | Computation only |
| **Total** | **40–43** | |
