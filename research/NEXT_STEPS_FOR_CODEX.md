# Codex Execution Plan — Supplementary Evidence Generation

**Date**: 2026-04-10
**Context**: All 85 experiment runs are complete. This plan produces supplementary
analysis artifacts from existing data. No experiments to run.

**Previous Codex tasks** (Task 1–4) are done. Their outputs:
- `research/results/key_evaluation_metrics.json` — verified correct
- `research/results/hypothesis_test.json` — verified correct
- `research/results/cmu_benchmark_table.csv` — verified correct
- `research/results/paper_tables.tex` (Tables 4–5 appended) — verified correct

---

## Task 5: SI-4 — Full Ablation Statistics Table

**Goal**: Generate a complete statistics supplement covering all pairwise comparisons,
effect sizes, and confidence intervals for the ablation study.

**Output**: `research/results/si4_ablation_statistics.json`

### What to compute

For **each backend** (gemini, grok4), for **each ablated variant** (no_slip, no_forbid,
no_termination, single_shot), compute vs the `full` variant:

```json
{
  "backend": "gemini",
  "variant": "no_slip",
  "per_case_delta_eV": [
    {"case_id": "01", "full_energy": -3.632, "variant_energy": -3.632, "delta": 0.000},
    ...
  ],
  "mean_delta_eV": ...,
  "median_delta_eV": ...,
  "wilcoxon_statistic": ...,
  "wilcoxon_p": ...,
  "bh_adjusted_p": ...,
  "rank_biserial": ...,
  "bootstrap_ci_95": {"low": ..., "high": ...},
  "cases_where_variant_worse": [...],
  "cases_where_variant_better": [...],
  "max_degradation_eV": ...,
  "max_degradation_case": ...
}
```

**Data sources**:
- `research/results/gemini_ablation_v1/ablation_summary.csv`
- `research/results/xai_ablation_v2/ablation_summary.csv`
- Existing stats from `ablation_stats.json` (verify, don't recompute from scratch)

Also produce a **human-readable LaTeX table** version at
`research/results/si4_ablation_statistics.tex`:

```latex
\begin{table}[h]
\caption{Full pairwise ablation statistics...}
% Columns: Backend, Variant, Mean ΔE, Median ΔE, Wilcoxon p, BH-adj p,
%          Rank-biserial r, 95% CI, Max degradation
\end{table}
```

---

## Task 6: SI-6 — Cost Analysis

**Goal**: Comprehensive cost breakdown across all 85 runs.

**Output**: `research/results/si6_cost_analysis.json` + `research/results/si6_cost_analysis.tex`

### What to compute

For **each dataset** (gemini_ablation, grok4_ablation, gemini_1shot, grok4_1shot),
and within ablation datasets for **each variant**:

```json
{
  "dataset": "gemini_ablation",
  "variant": "full",
  "n_runs": 5,
  "total_input_tokens": ...,
  "total_output_tokens": ...,
  "mean_input_tokens_per_run": ...,
  "mean_output_tokens_per_run": ...,
  "mean_total_tokens_per_run": ...,
  "mean_wall_clock_sec": ...,
  "mean_iterations_per_run": ...,
  "tokens_per_iteration": ...
}
```

**Key derived metrics to highlight**:
- Token cost ratio: full / single_shot (how much more does the loop cost?)
- Wall-clock ratio: full / single_shot
- no_termination token overhead vs full (the "termination saves compute" claim)
- Cross-backend comparison: Gemini vs Grok-4 tokens for the same work

**Data sources**: all `result.json` files. Fields: `total_input_tokens`,
`total_output_tokens`, `wall_clock_sec`, `iteration_count`.

**LaTeX table**: summary with rows = {Full, -Slip, -Forbid, -Term, 1-Shot} ×
{Gemini, Grok-4}, columns = {mean tokens, mean wall-clock, mean iterations}.

---

## Task 7: Case 19 Deep-Dive — Attempt-Level Trajectory Data

**Goal**: Extract the full attempt-by-attempt search trajectory for case 19 across
all variants and both backends. This is the data behind Fig. 5 in the paper — the
case study showing when closed-loop feedback makes the critical difference.

**Output**: `research/results/case19_trajectory.csv` + `research/results/case19_trajectory.json`

### What to extract

For case 19, for each of the 10 variant×backend combinations (5 variants × 2 backends):

From `result.json` → `attempt_records` array, extract per attempt:
```
backend, variant, attempt_index, planned_site_type, actual_site_type,
energy_eV, is_chemical_slip, is_dissociated, bond_change_count,
running_best_energy_eV
```

Where `running_best_energy_eV` = best non-dissociated energy seen up to and
including this attempt.

**For single_shot** variants, the data comes from:
- Gemini: `research/results/cmu_v1_gemini_one_shot/19/result.json`
- Grok-4: `research/results/cmu_v1_xai_progressive_one_shot/19/result.json`

**For all other variants**, the data comes from:
- Gemini: `research/results/gemini_ablation_v1/{variant}/19/result.json`
- Grok-4: `research/results/xai_ablation_v2/{variant}/19/result.json`

### Key narrative to verify from the data

The deep-dive should confirm this story (already observed manually):

1. **Grok-4 full** (3 attempts): ontop→hollow slip on attempt 0 **accidentally finds
   the best energy** (−4.045 eV). The slip feedback tells the LLM this site is
   unstable, so it stops exploring hollow and terminates early. Paradoxically, the
   "mistake" was the winning move.

2. **Grok-4 no_slip** (5 attempts): without slip feedback, the agent doesn't know
   hollow was found accidentally. It tries ontop (−3.13), bridge (−3.07), bridge
   (−3.59), hollow→dissociates (−1.32), hollow→bridge (−3.10). Wasted the budget
   and ended 0.45 eV worse.

3. **Gemini full** (5 attempts): ontop (−3.13), bridge-slip (−3.08), bridge (−3.84),
   ontop→dissociates (−4.46 but invalid), hollow→dissociates (−1.32). Best valid
   energy is −3.84.

4. **Gemini no_forbid** (5 attempts): finds −4.04 eV — **better** than full. The
   FORBID constraint in full prevented re-exploring a site that would have worked
   on this specific surface. This is the "negative result" for FORBID.

Include a `narrative_summary` field in the JSON output.

---

## Task 8: 20-Case Slip Analysis — Per-Iteration Breakdown

**Goal**: The outline (Section 4.1) frames Chemical Slip as a proxy for LLM reasoning
quality. Generate the supporting data.

**Output**: `research/results/slip_analysis.json` + `research/results/slip_analysis.csv`

### What to compute

For **each of the 20 one-shot cases** (from both Gemini and Grok-4):

```
case_id, surface, surface_family, adsorbate, miller_index,
gemini_planned_site, gemini_actual_site, gemini_slip, gemini_slip_type,
grok4_planned_site, grok4_actual_site, grok4_slip, grok4_slip_type
```

Where `slip_type` is:
- `none` if no slip
- `soft` if planned_site_type == actual_site_type but coordinating atoms differ
  (approximation: if `is_chemical_slip=True` but site type string matches)
- `hard` if site type changed entirely

**Data source**: `attempt_records[0]` from each one-shot result.json (only 1 attempt
in one-shot runs).

**Aggregate statistics to include in JSON**:

```json
{
  "overall_slip_rate": {"gemini": 0.6, "grok4": 0.6},
  "by_surface_family": {
    "monometallic": {"gemini": 0.2, "grok4": 0.2},
    "intermetallic": {"gemini": 0.733, "grok4": 0.733}
  },
  "cross_backend_slip_agreement": ...,
  "most_common_slip_pattern": "planned ontop/bridge → actual hollow",
  "slip_vs_energy_correlation": {
    "description": "Do slipped cases have better or worse energy?",
    "slipped_mean_energy": ...,
    "non_slipped_mean_energy": ...,
    "note": "Slip does not necessarily mean worse energy — it means the PES disagreed with the LLM's intuition"
  }
}
```

---

## Task 9: Cross-LLM Agreement on 20-Case Benchmark

**Goal**: Extend the cross-LLM robustness analysis from the 5-case ablation subset
to the full 20-case benchmark (one-shot only).

**Output**: `research/results/cross_llm_20case.json` + `research/results/cross_llm_20case.csv`

### What to compute

For each of 20 cases, compare Gemini vs Grok-4 one-shot:

```
case_id, surface, adsorbate, gemini_energy, grok4_energy, abs_delta,
gemini_site, grok4_site, site_agreement, both_slipped
```

**Aggregate stats**:
```json
{
  "exact_match_count": ...,
  "within_0_01_count": ...,
  "within_0_05_count": ...,
  "within_0_10_count": ...,
  "mean_abs_delta": ...,
  "median_abs_delta": ...,
  "by_surface_family": {
    "monometallic": {"mean_abs_delta": ..., "within_0_01": ...},
    "intermetallic": {"mean_abs_delta": ..., "within_0_01": ...}
  },
  "site_agreement_rate": ...,
  "largest_disagreement": {"case_id": ..., "delta": ..., "note": ...}
}
```

**Why this matters**: The 5-case cross-LLM comparison (already done) shows 4/5
convergence under iterative search. This task shows how much the two backends diverge
in one-shot mode on the full 20-case set — strengthening the "iterative loop as
backend-robustness mechanism" argument.

---

## What NOT to do

- Do NOT rerun any experiments or modify experiment scripts
- Do NOT modify source code in `src/`
- Do NOT modify `AdsMind/sections/*.tex` (paper LaTeX — requires manual review)
- Do NOT modify `research/agent_eval/*.py`
- Do NOT modify the existing 5 tables in `paper_tables.tex`
- Do NOT delete any existing files
- Do NOT create new Python scripts — use inline python commands

## File locations

| Data | Path |
|------|------|
| Gemini ablation (5×5) | `research/results/gemini_ablation_v1/` |
| Grok-4 ablation (4×5 + single_shot fallback) | `research/results/xai_ablation_v2/` |
| Gemini 20-case 1-shot | `research/results/cmu_v1_gemini_one_shot/` |
| Grok-4 20-case 1-shot | `research/results/cmu_v1_xai_progressive_one_shot/` |
| Ablation stats | `{ablation_dir}/ablation_stats.json` |
| Ablation summary | `{ablation_dir}/ablation_summary.csv` |
| Cross-LLM 5×5 comparison | `research/results/cross_llm_ablation_comparison.{csv,json}` |
| Behavioral comparison | `research/results/adsmind_vs_adsorbagent_behavioral.csv` |
| Key metrics (Task 1 output) | `research/results/key_evaluation_metrics.json` |
| H₁ test (Task 2 output) | `research/results/hypothesis_test.json` |
| CMU table (Task 3 output) | `research/results/cmu_benchmark_table.csv` |
| Paper tables | `research/results/paper_tables.tex` |

## Key fields in result.json

Every result.json contains:
- `status`, `best_energy_eV`, `iteration_count`, `max_attempts`
- `chemical_slip_count`, `dissociation_count`, `calc_failure_count`
- `total_input_tokens`, `total_output_tokens`, `wall_clock_sec`
- `final_site_type`, `converged_tag`
- `case_metadata`: `{case_id, surface_family, adsorbate_name, miller_index, ...}`
- `attempt_records`: array of per-attempt dicts with `{attempt_index, planned_site_type,
  actual_site_type, most_stable_energy_eV, is_chemical_slip, is_dissociated,
  bond_change_count, ...}`

## Expected outputs summary

| Task | Output file(s) | Rows/entries |
|------|----------------|--------------|
| 5 | `si4_ablation_statistics.{json,tex}` | 8 variant×backend combos |
| 6 | `si6_cost_analysis.{json,tex}` | ~14 dataset×variant combos |
| 7 | `case19_trajectory.{csv,json}` | ~35 attempt records |
| 8 | `slip_analysis.{json,csv}` | 20 cases × 2 backends |
| 9 | `cross_llm_20case.{json,csv}` | 20 cases |

All outputs go to `research/results/`.
