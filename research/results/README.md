# research/results/ — Data Manifest

This directory contains curated, paper-facing outputs for AdsMind experiments:
summary CSVs, joined analysis tables, diagnostic JSON files, and LaTeX exports.
Raw per-run payloads, logs, trajectories, and structures are intentionally left
out of the public release because they are regenerable from `research/agent_eval/`.

For the Chinese extended guide, see [README_CN.md](README_CN.md). The Chinese
file is longer and written as a zero-background walkthrough; this file is the
concise manifest. The key paths, variant names, and data caveats should match.
Unless otherwise noted, paths are written relative to the repository root.

---

## Current Data Caveats

Read these before plotting:

- In ablation CSVs, the one-step ablation variant is named `single_shot`, not `one_shot`.
- Directories named `*_one_shot/` are independent one-shot runs; they are separate from the `single_shot` ablation variant.
- `analysis/cross_llm_ablation_with_openai.csv` is a legacy/convenience table with 3 backends (`gemini`, `grok4`, `openai_gpt54`) × 5 cases × 5 variants = 75 rows. It is not the full 4-backend 15-case CMU ablation table.
- For full CMU 4-backend 15-case ablation plots, concatenate the four per-backend `ablation_summary.csv` files listed below.
- In `adsorbagent_mace_gpt54/comparison.csv`, `energy_diff = adsmind_best_energy - adsorbagent_best_energy`. Positive values mean AdsMind is higher energy and Adsorb-Agent is lower.
- Several diagnostic JSON files are historical snapshots. Use the current CSVs as the authoritative plotting sources unless a JSON is explicitly called out below.

---

## Supported Claims

| Claim | Current source | Caveat |
|---|---|---|
| AdsMind reliability and search cost | `adsorbagent_mace_gpt54/comparison.csv` | AdsMind succeeds on 15/15 cases with fewer iterations/configurations; Adsorb-Agent is lower energy on the 12 comparable successful energy pairs in this file. |
| Backend convergence | Four CMU per-backend `ablation_summary.csv` files; `paper_tables.tex` | `analysis/cross_llm_ablation_with_openai.csv` is not the full 4-backend 15-case source. |
| OCD-GMAE generalisation | `ocd_gmae_ablation_multi_backend_final.csv`; four OCD-GMAE per-backend ablation CSVs | The wide table has been regenerated from the current per-backend CSVs. |
| Mechanism ablation | `si4_ablation_statistics.tex`, `si4_ocd_gmae_ablation_statistics.tex`, per-backend ablation CSVs | The most stable effect is full vs `single_shot`; individual `no_slip` / `no_forbid` / `no_termination` effects are backend- and case-dependent. |

---

## Quick Start

### 1. AdsMind vs Adsorb-Agent

```python
import pandas as pd

cmp = pd.read_csv("research/results/adsorbagent_mace_gpt54/comparison.csv")
print(cmp[[
    "case_id",
    "adsmind_best_energy",
    "adsorbagent_best_energy",
    "adsmind_iterations",
    "adsorbagent_configs_tested",
    "energy_diff",
    "winner",
]])
```

Schema notes:

| Column | Meaning |
|---|---|
| `case_id` | CMU benchmark case ID. |
| `adsmind_best_energy` | AdsMind best energy, eV. |
| `adsorbagent_best_energy` | Adsorb-Agent best energy, eV. |
| `adsmind_iterations` | AdsMind MACE relaxation/agent iteration count. |
| `adsorbagent_configs_tested` | Adsorb-Agent configurations tested. |
| `energy_diff` | `adsmind_best_energy - adsorbagent_best_energy`; positive means Adsorb-Agent is lower energy. |
| `winner` | `adsmind`, `adsorbagent`, or `tie`. |

Current file shape: 15 rows, 12 comparable successful energy pairs.

### 2. CMU 4-backend × 15-case × 5-variant ablation

```python
import pandas as pd

sources = {
    "gemini": "research/results/gemini_ablation_v1/ablation_summary.csv",
    "grok4": "research/results/xai_ablation_v2/ablation_summary.csv",
    "openai_gpt54": "research/results/openai_gpt54_ablation_v1/ablation_summary.csv",
    "anthropic_claude": "research/results/anthropic_sonnet46_ablation_v1/ablation_summary.csv",
}

ab = pd.concat(
    [pd.read_csv(path).assign(backend=backend) for backend, path in sources.items()],
    ignore_index=True,
)
print(ab.shape)  # (300, 12)

heatmap = ab.pivot_table(
    index=["backend", "variant"],
    columns="case_id",
    values="best_energy",
)

ranges = (
    ab.pivot_table(index=["case_id", "variant"], columns="backend", values="best_energy")
      .assign(range_eV=lambda x: x.max(axis=1) - x.min(axis=1))
)
```

Filter variants with `variant == "full"` or `variant == "single_shot"`.
Do not use `variant == "one_shot"` for ablation CSVs.

### 3. OCD-GMAE 4-backend generalisation

```python
import pandas as pd

ocd = pd.read_csv("research/results/ocd_gmae_ablation_multi_backend_final.csv")
print(ocd.shape)  # (50, 30)
print(ocd.groupby("variant")["range_best_energy"].describe())

ocd[[
    "case_id",
    "variant",
    "gemini_delta_vs_full",
    "grok_delta_vs_full",
    "gpt54_delta_vs_full",
    "claude_delta_vs_full",
]]
```

Key columns:

| Column | Meaning |
|---|---|
| `case_id`, `variant` | Case ID and ablation variant. |
| `{gemini,grok,gpt54,claude}_best_energy` | Per-backend best energy, eV. |
| `{gemini,grok,gpt54,claude}_delta_vs_full` | Per-backend delta against same-backend full. |
| `{gemini,grok,gpt54,claude}_success` | Bool per backend. |
| `range_best_energy` | Max minus min energy across backends. |
| `success_backends`, `failed_backends` | Backend completion lists. |

### 4. CMU main table note

`analysis/cmu_benchmark_table.csv` is currently a CMU 20-case one-shot table
with Gemini and Grok-4 columns only. Do not use it as the full CMU 4-backend
15-case ablation table.

---

## Authoritative Plotting Sources

| Plot/table target | Recommended source |
|---|---|
| AdsMind vs Adsorb-Agent success, energy, and configuration counts | `adsorbagent_mace_gpt54/comparison.csv` |
| CMU 4-backend × 5-variant heatmap/boxplot | Concatenate the four CMU per-backend `ablation_summary.csv` files |
| CMU one-shot backend range ranking | `analysis/cmu_one_shot_range_ranking_new_cases.csv` |
| OCD-GMAE 4-backend overview | `ocd_gmae_ablation_multi_backend_final.csv` |
| OCD-GMAE full vs single-shot range improvement | `ocd_gmae_ablation_final_vs_one_shot_4backend.csv` |
| Iteration convergence | `analysis/iteration_convergence.csv` |
| Case-19 trajectory | `analysis/case19_trajectory.csv` |
| Slip event inventory | `analysis/slip_analysis.csv` |
| Pipeline/concept images | `assets/pipeline.png`, `assets/adsmind_concept.png` |

---

## CMU 15-case Ablation

| Backend | File | Rows |
|---|---|---:|
| Gemini 2.5 Pro | `gemini_ablation_v1/ablation_summary.csv` | 75 |
| Grok-4 | `xai_ablation_v2/ablation_summary.csv` | 75 |
| GPT-5.4 | `openai_gpt54_ablation_v1/ablation_summary.csv` | 75 |
| Claude Sonnet 4.6 | `anthropic_sonnet46_ablation_v1/ablation_summary.csv` | 75 |

Each file has 15 cases × 5 variants:
`full`, `no_slip`, `no_forbid`, `no_termination`, `single_shot`.

Core columns: `case_id`, `variant`, `best_energy`, `delta_vs_full`,
`iterations`, `wasted_iterations`, `waste_ratio`, `success`, `slip_count`,
`dissociation_count`, `tokens_used`.

---

## CMU 20-case One-shot

| Backend | File |
|---|---|
| Gemini 2.5 Pro | `cmu_v1_gemini_one_shot/summary.csv` |
| Grok-4 | `cmu_v1_xai_progressive_one_shot/summary.csv` |
| GPT-5.4 | `cmu_v1_openai_gpt54_one_shot/summary.csv` |
| Claude Sonnet 4.6 | `cmu_v1_anthropic_sonnet46_one_shot/summary.csv` |

Typical one-shot columns include `status`, `best_energy_eV`,
`iteration_count`, `chemical_slip_count`, `dissociation_count`,
`total_input_tokens`, and `total_output_tokens`.

Supplementary controls:

- `cmu_v1_openai_gpt54_one_shot_retry/summary.csv` contains case 06 and case 08 retry rows only.
- `cmu_v1_gemini_one_shot_epfl_control/summary.csv` and `cmu_v1_xai_progressive_one_shot_epfl_control/summary.csv` contain EPFL slab controls.

---

## OCD-GMAE

### 10-case ablation

| Backend | File |
|---|---|
| Gemini 2.5 Pro | `ocd_gmae_gemini_ablation_v2/ablation_summary.csv` |
| Grok-4 | `ocd_gmae_xai_grok4_ablation_v1/ablation_summary.csv` |
| GPT-5.4 | `ocd_gmae_openai_gpt54_ablation_v1/ablation_summary.csv` |
| Claude Sonnet 4.6 | `ocd_gmae_anthropic_sonnet46_ablation_v1/ablation_summary.csv` |
| Wide summary | `ocd_gmae_ablation_multi_backend_final.csv`, `ocd_gmae_ablation_multi_backend_final.json` |
| Full vs single-shot | `ocd_gmae_ablation_final_vs_one_shot_4backend.csv` |

### 50-rep one-shot

| Backend | File |
|---|---|
| Gemini 2.5 Pro | `ocd_gmae_rep50_v1_gemini_one_shot/summary.csv` |
| Grok-4 | `ocd_gmae_rep50_v1_xai_grok4_one_shot/summary.csv` |
| GPT-5.4 | `ocd_gmae_rep50_v1_openai_gpt54_one_shot/summary.csv` |
| Claude Sonnet 4.6 | `ocd_gmae_rep50_v1_anthropic_sonnet46_one_shot/summary.csv` |

---

## Adsorb-Agent Comparison

| File | Use |
|---|---|
| `adsorbagent_mace_gpt54/comparison.csv` | Main current comparison: 15 rows, 12 comparable successful energy pairs. |
| `adsorbagent_mace_gpt54/adsorbagent_mace_summary.csv` | Adsorb-Agent MACE-replacement run over 20 cases. |
| `adsorbagent_mace_gpt54/comparison_stats.json` | Paired statistics; records the `energy_diff` definition. |
| `adsorbagent_mace_gpt4o/` | Historical GPT-4o comparison. |
| `analysis/adsorbagent_paper_results.csv` | Original Adsorb-Agent paper values using EquiformerV2; not directly comparable to MACE energies. |
| `analysis/adsmind_vs_adsorbagent_behavioral.csv` | Behavioural comparison with token, slip, and status fields. |

---

## Baselines And Sensitivity Checks

| Experiment | File |
|---|---|
| Random baseline | `random_baseline_n20/summary.csv`, `random_baseline_n20/summary.json` |
| Heuristic baseline | `heuristic_baseline/summary.csv`, `heuristic_baseline/summary.json` |
| Multi-seed GPT-5.4 | `multiseed_gpt54/seed_{43,44,45,46}/ablation_summary.csv` |
| MACE large | `mace_large_gpt54/ablation_summary.csv` |

---

## LaTeX Exports

| File | Notes |
|---|---|
| `paper_tables.tex` | CMU ablation, cross-LLM summary, key metrics, and H1 table. Regenerate after CSV changes. |
| `ocd_gmae_paper_tables.tex` | OCD-GMAE paper tables. Consistent with the current per-backend CSVs and wide summary. |
| `si4_ablation_statistics.tex` | CMU ablation statistics, consistent with `si4_ablation_statistics.json`. |
| `si4_ocd_gmae_ablation_statistics.tex` | OCD-GMAE ablation statistics. |
| `si6_cost_analysis.tex` | Cost analysis from `si6_cost_analysis.json`. |
| `si_adsorbagent_comparison.tex` | AdsMind vs Adsorb-Agent comparison. |
| `si_baselines_comparison.tex` | Baseline comparison. |
| `si_iteration_convergence.tex` | Iteration convergence. |
| `si_mace_sensitivity.tex` | MACE small vs large sensitivity. |

---

## analysis/ Files

| File | Current use |
|---|---|
| `analysis/cmu_benchmark_table.csv` | CMU 20-case one-shot table with Gemini/Grok-4 columns only. |
| `analysis/cross_llm_20case_with_openai.csv` / `.json` | 4-backend one-shot join. |
| `analysis/cross_llm_20case_4backend.json` | One-shot summary snapshot. |
| `analysis/cross_llm_ablation_with_openai.csv` / `.json` | 3-backend × 5-case × 5-variant legacy/convenience ablation join. |
| `analysis/cross_llm_unified_range_table.csv` | Current unified range table for CMU 15-case and OCD-GMAE 10-case ablations. |
| `analysis/cross_llm_unified_summary.json` | Current cross-LLM summary for CMU 15-case and OCD-GMAE 10-case ablations. |
| `analysis/cmu_one_shot_range_ranking_new_cases.csv` / `.json` | CMU one-shot backend range ranking. |
| `analysis/ocd_gmae_one_shot_range_ranking.csv` / `.json` | OCD-GMAE one-shot backend range ranking. |
| `analysis/ocd_gmae_one_shot_top_10_case_ids.txt` | OCD-GMAE top-10 case IDs. |
| `analysis/iteration_convergence.csv` / `.json` / `.png` | Iteration convergence data, summary, and rendered figure. |
| `analysis/slip_analysis.csv` / `.json` | Slip event inventory. |
| `analysis/case19_trajectory.csv` / `.json` | Case-19 trajectory. |
| `analysis/baselines_comparison.json` | Baseline vs AdsMind join. |
| `analysis/adsmind_vs_adsorbagent_behavioral.csv` | Behavioural AdsMind vs Adsorb-Agent comparison. |
| `analysis/adsorbagent_paper_results.csv` | Original Adsorb-Agent EquiformerV2 results. |

---

## Diagnostic JSON Caveats

| File | Caveat |
|---|---|
| `cross_llm_ablation_4backend.json` | 5-case snapshot, not the full 15-case ablation. |
| `hypothesis_test.json` | Early H0/H1 record with a 5-case scope. |
| `key_evaluation_metrics.json` | Early metric snapshot with `*_5case` fields. |
| `si4_ablation_statistics.json` | CMU 15-case ablation statistics source. |
| `si4_ocd_gmae_ablation_statistics.json` | OCD-GMAE 10-case statistics source. |
| `si6_cost_analysis.json` | Cost analysis source. |

---

## Public-release Slimming Notes

The repository keeps paper-facing summary tables, joined analysis files, and
LaTeX exports. Raw `result.json` payloads, agent logs, trajectories, and
structures are excluded from the public tree; regenerate them through
`research/agent_eval/` when a full audit trail is needed.

On 2026-04-19, the following superseded, raw, or purely derived outputs were
removed instead of archived in-tree:

- `analysis/cross_llm_20case.{csv,json}` was superseded by `analysis/cross_llm_20case_with_openai.{csv,json}`.
- `analysis/cross_llm_ablation_comparison.{csv,json}` was superseded by `analysis/cross_llm_ablation_with_openai.{csv,json}`.
- `analysis/cmu_one_shot_range_ranking.{csv,json}` was superseded by `analysis/cmu_one_shot_range_ranking_new_cases.{csv,json}`.
- `ocd_gmae_gemini_ablation_v1/` was superseded by `ocd_gmae_gemini_ablation_v2/`.
- Per-run `result.json`, logs, trajectories, and structures under `research/results/` were removed from the release tree.

Artifact path columns in summary CSVs are provenance labels for local,
regenerable files; they are not expected to resolve in a clean public checkout.
