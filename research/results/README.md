# research/results/ — Data Manifest

This directory contains curated, paper-facing outputs for AdsMind experiments:
summary CSVs, joined analysis tables, diagnostic JSON files, and LaTeX exports.
Canonical per-case `result.json` payloads are retained under `canonical_raw/`.
Most transient logs, trajectories, and generated structures are regenerable from
`research/agent_eval/`; active controls and figure-audit cases may retain small
trajectory/artifact payloads when those files are directly used for validation.

For the Chinese extended guide, see [README_CN.md](README_CN.md). The Chinese
file is longer and written as a zero-background walkthrough; this file is the
concise manifest. The key paths, variant names, and data caveats should match.
Unless otherwise noted, paths are written relative to the repository root.

---

## Current Data Caveats

Read these before plotting:

- In ablation CSVs, the one-step ablation variant is named `single_shot`, not `one_shot`.
- Directories named `*_one_shot/` are independent one-shot runs; they are separate from the `single_shot` ablation variant.
- Ablation directories use `ablation_summary.csv`; independent one-shot and baseline directories use `summary.csv`. OCD-GMAE rep50 ablation directories additionally keep independent one-shot results in `single_shot_summary.csv`.
- `canonical_raw/MERGE_QC.csv` is the active machine-readable inventory for canonical raw sources. It also tracks artifact completeness through fields such as `xyz_count`, `traj_count`, and `missing_artifact_ref_count`. Rebuild it with `python3 research/agent_eval/rebuild_canonical_raw_qc.py` after moving or adding raw-result directories.
- `RUN_REGISTRY.csv` and `ANALYSIS_REGISTRY.csv` resolve compact backend/date labels into machine-readable metadata. Rebuild them with `python3 research/agent_eval/rebuild_result_registries.py`; see `REGISTRY.md`.
- Treat directory tokens such as `gpt54`, `sonnet46`, `grok4`, and date suffixes like `20260428` as stable labels, not complete reproducibility metadata. Use the registries for exact model IDs, config references, manifest paths, role, and citation policy.
- OCD-GMAE `subset24` and `representative50` are independent selections, not a parent/child split. They overlap on 12 `source_key` records only; never join them by `case_id`. Use `research/agent_eval/manifests/ocd_gmae_subset24_vs_representative50_overlap.csv` for cross-manifest checks.
- `analysis/cross_llm_ablation_with_openai.csv` is a legacy/convenience table with 3 backends (`gemini`, `grok4`, `openai_gpt54`) × 5 cases × 5 variants = 75 rows. It is not the full 4-backend 20-case CMU ablation table.
- For full CMU 4-backend 20-case ablation plots, concatenate the four canonical per-backend `ablation_summary.csv` files listed below.
- In `adsorbagent_mace_gpt54/comparison.csv`, `energy_diff = adsmind_best_energy - adsorbagent_best_energy`. Positive values mean AdsMind is higher energy and Adsorb-Agent is lower.
- `canonical_raw/controls/adsorbagent_single_config_gpt54_cmu20/` is an active AA single-config control. It uses CatalystAIgent-style `summary.csv` / `result.pkl` / `traj` files, not the AdsMind `result.json` layout.
- Raw structure layouts are intentionally not uniform. AdsMind ablations usually store per-variant/per-case `artifacts/` with multiple relaxed candidates; random/heuristic baselines store only top structures; CatalystAIgent controls use `.pkl`/`.traj`; several early Gemini/Grok CMU runs have `result.json` only because the original LIAC source directories did not retain artifacts.
- Several diagnostic JSON files are historical snapshots. Use the current CSVs as the authoritative plotting sources unless a JSON is explicitly called out below.

---

## Supported Claims

| Claim | Current source | Caveat |
|---|---|---|
| AdsMind reliability and search cost | `adsorbagent_mace_gpt54/comparison.csv` | AdsMind succeeds on 15/15 cases with fewer iterations/configurations; Adsorb-Agent is lower energy on the 12 comparable successful energy pairs in this file. |
| Backend convergence | Four canonical CMU20 per-backend `ablation_summary.csv` files | `analysis/cross_llm_ablation_with_openai.csv` is not the full 4-backend 20-case source; regenerate LaTeX exports after CSV changes. |
| OCD-GMAE generalisation | `analysis/ocd_gmae_ablation_multi_backend_final.csv`; four OCD-GMAE per-backend ablation CSVs | The wide table has been regenerated from the current per-backend CSVs. |
| Mechanism ablation | Canonical per-backend ablation CSVs and regenerated SI tables | The most stable effect is full vs `single_shot`; individual `no_slip` / `no_forbid` / `no_termination` effects are backend- and case-dependent. |
| Active controls | `canonical_raw/controls/` | This contains the authoritative AA single-config, MACE-large, and multi-seed controls. Incomplete earlier control runs are archived under `canonical_raw/superseded_raw_sources/incomplete_controls/` and should not be used for analysis. |

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

### 2. CMU 4-backend × 20-case × 5-variant ablation

```python
import pandas as pd

sources = {
    "gemini": "research/results/canonical_raw/cmu20_gemini_ablation/ablation_summary.csv",
    "grok4": "research/results/canonical_raw/cmu20_grok4_ablation/ablation_summary.csv",
    "openai_gpt54": "research/results/canonical_raw/cmu20_openai_gpt54_ablation/ablation_summary.csv",
    "anthropic_claude": "research/results/canonical_raw/cmu20_anthropic_sonnet46_ablation/ablation_summary.csv",
}

ab = pd.concat(
    [pd.read_csv(path).assign(backend=backend) for backend, path in sources.items()],
    ignore_index=True,
)
print(ab.shape)  # (400, 12)

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

ocd = pd.read_csv("research/results/analysis/ocd_gmae_ablation_multi_backend_final.csv")
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
20-case ablation table.

---

## Authoritative Plotting Sources

| Plot/table target | Recommended source |
|---|---|
| AdsMind vs Adsorb-Agent success, energy, and configuration counts | `adsorbagent_mace_gpt54/comparison.csv` |
| CMU 4-backend × 5-variant heatmap/boxplot | Concatenate the four canonical CMU20 per-backend `ablation_summary.csv` files |
| CMU one-shot backend range ranking | `analysis/cmu_one_shot_range_ranking_new_cases.csv` |
| OCD-GMAE 4-backend overview | `analysis/ocd_gmae_ablation_multi_backend_final.csv` |
| OCD-GMAE full vs single-shot range improvement | `analysis/ocd_gmae_ablation_final_vs_one_shot_4backend.csv` |
| Iteration convergence | `analysis/iteration_convergence.csv` |
| Case-19 trajectory | `analysis/case19_trajectory.csv` |
| Slip event inventory | `analysis/slip_analysis.csv` |
| Pipeline/concept images | `assets/pipeline.png`, `assets/adsmind_concept.png` |

---

## CMU 20-case Ablation

| Backend | File | Rows |
|---|---|---:|
| Gemini 2.5 Pro | `canonical_raw/cmu20_gemini_ablation/ablation_summary.csv` | 100 |
| Grok-4 | `canonical_raw/cmu20_grok4_ablation/ablation_summary.csv` | 100 |
| GPT-5.4 | `canonical_raw/cmu20_openai_gpt54_ablation/ablation_summary.csv` | 100 |
| Claude Sonnet 4.6 | `canonical_raw/cmu20_anthropic_sonnet46_ablation/ablation_summary.csv` | 100 |

Each file has 20 cases × 5 variants:
`full`, `no_slip`, `no_forbid`, `no_termination`, `single_shot`.

Core columns: `case_id`, `variant`, `best_energy`, `delta_vs_full`,
`iterations`, `wasted_iterations`, `waste_ratio`, `success`, `slip_count`,
`dissociation_count`, `tokens_used`.

---

## CMU 20-case One-shot

| Backend | File |
|---|---|
| Gemini 2.5 Pro | `canonical_raw/legacy_raw_sources/cmu20_gemini_one_shot/summary.csv` |
| Grok-4 | `canonical_raw/legacy_raw_sources/cmu20_grok4_progressive_one_shot/summary.csv` |
| GPT-5.4 | `canonical_raw/legacy_raw_sources/cmu20_openai_gpt54_one_shot/summary.csv` |
| Claude Sonnet 4.6 | `canonical_raw/legacy_raw_sources/cmu20_anthropic_sonnet46_one_shot/summary.csv` |

Typical one-shot columns include `status`, `best_energy_eV`,
`iteration_count`, `chemical_slip_count`, `dissociation_count`,
`total_input_tokens`, and `total_output_tokens`.

Supplementary controls:

- `canonical_raw/legacy_raw_sources/cmu20_openai_gpt54_one_shot_retry/summary.csv` contains case 06 and case 08 retry rows only.
- `canonical_raw/legacy_raw_sources/cmu20_gemini_one_shot_epfl_control/summary.csv` and `canonical_raw/legacy_raw_sources/cmu20_grok4_progressive_one_shot_epfl_control/summary.csv` contain EPFL slab controls.

---

## OCD-GMAE

### 24-case ablation

This manifest is the full-mechanism OCD-GMAE validation set. It is selected for
the complete four-backend five-variant ablation matrix, not as a prefix or
subset of the 50-case representative set.

| Backend | File |
|---|---|
| Gemini 2.5 Pro | `canonical_raw/ocd24_gemini_ablation/ablation_summary.csv` |
| Grok-4 | `canonical_raw/ocd24_grok4_ablation/ablation_summary.csv` |
| GPT-5.4 | `canonical_raw/ocd24_openai_gpt54_ablation/ablation_summary.csv` |
| Claude Sonnet 4.6 | `canonical_raw/ocd24_anthropic_sonnet46_ablation/ablation_summary.csv` |
| Wide summary | `analysis/ocd_gmae_ablation_multi_backend_final.csv`, `analysis/ocd_gmae_ablation_multi_backend_final.json` |
| Full vs single-shot | `analysis/ocd_gmae_ablation_final_vs_one_shot_4backend.csv` |

### 50-case representative set

This manifest is a separately selected representative slice for broader
generalisation and figure assets. It is not a superset of OCD24. Use
`source_key`, not `case_id`, when checking the 12 overlapping source records.

| Backend | File |
|---|---|
| Gemini 2.5 Pro | `canonical_raw/ocd_rep50_gemini_ablation/ablation_summary.csv`, `canonical_raw/ocd_rep50_gemini_ablation/single_shot_summary.csv` |
| Grok-4 | `canonical_raw/ocd_rep50_grok4_ablation/ablation_summary.csv`, `canonical_raw/ocd_rep50_grok4_ablation/single_shot_summary.csv` |
| GPT-5.4 | `canonical_raw/ocd_rep50_openai_gpt54_ablation/ablation_summary.csv`, `canonical_raw/ocd_rep50_openai_gpt54_ablation/single_shot_summary.csv` |
| Claude Sonnet 4.6 | `canonical_raw/ocd_rep50_anthropic_sonnet46_ablation/ablation_summary.csv`, `canonical_raw/ocd_rep50_anthropic_sonnet46_ablation/single_shot_summary.csv` |

Each rep50 ablation directory contains raw 5-variant outputs:
`full`, `no_slip`, `no_forbid`, `no_termination`, and `single_shot`.
The row-wise `ablation_summary.csv` currently covers the four non-one-shot
variants (200 rows = 50 cases × 4 variants); independent one-shot rows are kept
separately in `single_shot_summary.csv` (50 rows). The manuscript currently uses
rep50 conservatively as a Full-versus-1-Shot generalisation check; upgrading it
to a full 5-variant mechanism analysis requires regenerating the paper
statistics and figure captions.

---

## Adsorb-Agent Comparison

| File | Use |
|---|---|
| `adsorbagent_mace_gpt54/comparison.csv` | Main current comparison: 15 rows, 12 comparable successful energy pairs. |
| `adsorbagent_mace_gpt54/adsorbagent_mace_summary.csv` | Adsorb-Agent MACE-replacement run over 20 cases. |
| `adsorbagent_mace_gpt54/comparison_stats.json` | Paired statistics; records the `energy_diff` definition. |
| `canonical_raw/auxiliary_raw/adsorbagent_mace_gpt4o/` | Historical GPT-4o comparison. |
| `analysis/adsorbagent_paper_results.csv` | Original Adsorb-Agent paper values using EquiformerV2; not directly comparable to MACE energies. |
| `analysis/adsmind_vs_adsorbagent_behavioral.csv` | Behavioural comparison with token, slip, and status fields. |
| `canonical_raw/controls/adsorbagent_single_config_gpt54_cmu20/summary.csv` | Active AA single-config control over 20 CMU cases; used for the breadth-versus-depth control discussion. |

---

## Baselines And Sensitivity Checks

| Experiment | File |
|---|---|
| Random baseline | `canonical_raw/cmu20_random_baseline_n20/summary.csv`, `canonical_raw/cmu20_random_baseline_n20/summary.json` |
| Heuristic baseline | `canonical_raw/cmu20_heuristic_baseline/summary.csv`, `canonical_raw/cmu20_heuristic_baseline/summary.json` |
| OCD24 random baseline | `canonical_raw/ocd24_random_baseline_n20/summary.csv`, `canonical_raw/ocd24_random_baseline_n20/summary.json` |
| OCD24 heuristic baseline | `canonical_raw/ocd24_heuristic_baseline/summary.csv`, `canonical_raw/ocd24_heuristic_baseline/summary.json` |
| OCD rep50 random baseline | `canonical_raw/ocd_rep50_random_baseline_n20/summary.csv`, `canonical_raw/ocd_rep50_random_baseline_n20/summary.json` |
| OCD rep50 heuristic baseline | `canonical_raw/ocd_rep50_heuristic_baseline/summary.csv`, `canonical_raw/ocd_rep50_heuristic_baseline/summary.json` |
| Multi-seed GPT-5.4 | `canonical_raw/controls/multiseed_gpt54_cmu20_seed{43,44,45,46,47}_full/ablation_summary.csv` |
| MACE large, CMU20 | `canonical_raw/controls/mace_large_gpt54_cmu20_full/ablation_summary.csv` |
| MACE large, OCD rep10 | `canonical_raw/controls/mace_large_gpt54_ocd_rep10_full/ablation_summary.csv` |
| AA single-config control | `canonical_raw/controls/adsorbagent_single_config_gpt54_cmu20/summary.csv` |

---

## LaTeX Exports

| File | Notes |
|---|---|
| `analysis/paper_tables.tex` | Legacy/generated CMU table export. Regenerate after CSV changes before using in manuscript. |
| `analysis/ocd_gmae_paper_tables.tex` | Legacy/generated OCD-GMAE table export. Regenerate after CSV changes before using in manuscript. |
| `analysis/si4_ablation_statistics.tex` | Legacy/generated CMU ablation statistics export. Regenerate after CSV changes before using in manuscript. |
| `analysis/si4_ocd_gmae_ablation_statistics.tex` | Legacy/generated OCD-GMAE ablation statistics export. Regenerate after CSV changes before using in manuscript. |
| `analysis/si6_cost_analysis.tex` | Cost analysis from `analysis/si6_cost_analysis.json`. |
| `analysis/si_adsorbagent_comparison.tex` | AdsMind vs Adsorb-Agent comparison. |
| `analysis/si_baselines_comparison.tex` | Baseline comparison. |
| `analysis/si_iteration_convergence.tex` | Iteration convergence. |
| `analysis/si_mace_sensitivity.tex` | MACE small vs large sensitivity. |

---

## analysis/ Files

| File | Current use |
|---|---|
| `analysis/cmu_benchmark_table.csv` | CMU 20-case one-shot table with Gemini/Grok-4 columns only. |
| `analysis/cross_llm_20case_with_openai.csv` / `.json` | 4-backend one-shot join. |
| `analysis/cross_llm_20case_4backend.json` | One-shot summary snapshot. |
| `analysis/cross_llm_ablation_with_openai.csv` / `.json` | 3-backend × 5-case × 5-variant legacy/convenience ablation join. |
| `analysis/cross_llm_unified_range_table.csv` | Current unified range table for CMU20 and OCD-GMAE-24 ablations. |
| `analysis/cross_llm_unified_summary.json` | Current cross-LLM summary for CMU20 and OCD-GMAE-24 ablations. |
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
| `analysis/cross_llm_ablation_4backend.json` | 5-case snapshot, not the full 20-case ablation. |
| `analysis/hypothesis_test.json` | Early H0/H1 record with a 5-case scope. |
| `analysis/key_evaluation_metrics.json` | Early metric snapshot with `*_5case` fields. |
| `analysis/si4_ablation_statistics.json` | CMU20 ablation statistics source. |
| `analysis/si4_ocd_gmae_ablation_statistics.json` | OCD-GMAE-24 statistics source. |
| `analysis/si6_cost_analysis.json` | Cost analysis source. |

---

## Public-release Slimming Notes

The repository keeps paper-facing summary tables, joined analysis files, LaTeX
exports, and canonical per-case `result.json` payloads. Large agent logs,
trajectories, and generated structures are normally excluded from the public
tree; small active controls and figure-audit cases may retain them when they are
part of the evidence trail. Regenerate omitted artifacts through
`research/agent_eval/` when a full audit trail is needed.

On 2026-04-19, the following superseded, raw, or purely derived outputs were
removed instead of archived in-tree:

- `analysis/cross_llm_20case.{csv,json}` was superseded by `analysis/cross_llm_20case_with_openai.{csv,json}`.
- `analysis/cross_llm_ablation_comparison.{csv,json}` was superseded by `analysis/cross_llm_ablation_with_openai.{csv,json}`.
- `analysis/cmu_one_shot_range_ranking.{csv,json}` was superseded by `analysis/cmu_one_shot_range_ranking_new_cases.{csv,json}`.
- Split CMU15+extra5 and OCD10+extra14 raw directories were merged into `canonical_raw/`.
- Agent logs, trajectories, and generated structures under `research/results/` remain ignored.

Artifact path columns in summary CSVs are provenance labels for local,
regenerable files; they are not expected to resolve in a clean public checkout.
