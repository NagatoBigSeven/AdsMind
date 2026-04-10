# AdsMind Agent-Side Experiment Plan (Final)

**Author**: Zongmin Zhang (first author, agentic system)
**DFT**: Bowen (second author, out of scope for this plan)
**Date**: 2026-04-09
**Goal**: Produce all agent-side data assets required by OUTLINE.md Sections 3.1, 3.2, 3.5

---

## Current State Assessment

### What We Have

1. **20 benchmark slabs** in `benchmark_slabs/` + CuZnO extension
2. **19/20 previous run results** in `results/01..20/` (case 20 is empty = the failed case)
3. **Working agent code** in `src/agent/` — LangGraph 5-node state machine, fully functional
4. **Adsorb-Agent clone** in `CatalystAIgent/` — reference only, **cannot run locally** (requires CUDA + fairchem-forked + EquiformerV2 GNN)

### What We Don't Have

- No structured manifest (SMILES / user_request per case)
- No ablation switches (slip/FORBID/termination are hardcoded)
- No batch runner (each case was run manually via CLI)
- No token counting in LLM calls
- No Adsorb-Agent results extracted for comparison
- Previous results lack config.json / git SHA / reproducibility metadata

### Key Constraint

- **Hardware**: MacBook Pro M3 Pro, 18 GB, macOS — float32 MACE only, no CUDA
- **Adsorb-Agent**: Cannot run locally (CUDA-only). Comparison must use **paper-reported values** or request GPU access from Prof. Cheng
- **LLM access**: AiHubMix API (multi-provider), budget is sufficient for multi-model runs

---

## Benchmark Case Mapping

Cross-referencing Adsorb-Agent paper (arXiv:2410.16658) Table 1 with our `benchmark_slabs/` and previous `results/`:

| Case | Slab File | Surface | Miller | Adsorbate (Paper) | SMILES (AdsMind) | Previous Best Energy (eV) | Previous Status | Notes |
|------|-----------|---------|--------|--------------------|------------------|---------------------------|-----------------|-------|
| 01 | 01_Mo3Pd_111.xyz | Mo₃Pd | (111) | H | `[H]` | -2.638 | OK | NRR/HER; strong slip observed |
| 02 | 02_Mo3Pd_111.xyz | Mo₃Pd | (111) | NNH | `[N]=[NH]` | -3.937 | OK | NRR; dissociation events |
| 03 | 03_Pd3Cu_111.xyz | CuPd₃ | (111) | H | `[H]` | -3.029 | OK | Paper calls it CuPd₃ |
| 04 | 04_Pd3Cu_111.xyz | CuPd₃ | (111) | NNH | `[N]=[NH]` | -2.353 | OK | Dissociation observed |
| 05 | 05_Cu3Ag_111.xyz | Cu₃Ag | (111) | H | `[H]` | -2.558 | OK | |
| 06 | 06_Cu3Ag_111.xyz | Cu₃Ag | (111) | NNH | `[N]=[NH]` | -1.740 | OK | Dissociation events |
| 07 | 07_Ru3Mo_111.xyz | Ru₃Mo | (111) | H | `[H]` | -3.840 | OK | |
| 08 | 08_Ru3Mo_111.xyz | Ru₃Mo | (111) | NNH | `[N]=[NH]` | -4.821 | OK | Best energy among all |
| 09 | 09_Pt_111.xyz | Pt | (111) | OH | `[OH]` | -1.932 | OK | ORR baseline; DFT validation target |
| 10 | 10_Pt_100.xyz | Pt | (100) | OH | `[OH]` | -2.611 | OK | Facet sensitivity test; DFT target |
| 11 | 11_Pd_111.xyz | Pd | (111) | OH | `[OH]` | -2.421 | OK | ORR |
| 12 | 12_Au_111.xyz | Au | (111) | OH | `[OH]` | -2.059 | OK | All sites → "desorbed" label |
| 13 | 13_Ag_100.xyz | Ag | (100) | OH | `[OH]` | -2.859 | OK | All sites → "desorbed" label |
| 14 | 14_CoPt_111.xyz | CoPt | (111) | OH | `[OH]` | -2.606 | OK | Bimetallic ORR; DFT target |
| 15 | 15_Cu6Ga2_100.xyz | Cu₆Ga₂ | (100) | CH₂CH₂OH | `[CH2]CO`? | -3.528 | OK | **SMILES needs verification** |
| 16 | 16_Au2Hf_102.xyz | Au₂Hf | (102) | CH₂CH₂OH | `[CH2]CO`? | -5.135 | OK | **SMILES needs verification**; DISS |
| 17 | 17_Rh2Ti2_111.xyz | Rh₂Ti₂ | (111) | OCHCH₃ | `CC=O`? | -2.913 | OK | **SMILES needs verification** |
| 18 | 18_Al3Zr_101.xyz | Al₃Zr | (101) | OCHCH₃ | `CC=O`? | -2.881 | OK | **SMILES needs verification** |
| 19 | 19_Hf2Zn6_110.xyz | Hf₂Zn₆ | (110) | OCHCH₃ | `CC=O`? | -3.977 | OK | **SMILES needs verification** |
| 20 | 20_Bi2Ti6_211.xyz | Bi₂Ti₆ | (211) | ONN(CH₃)₂ | TBD | — | **FAILED** | Only failed case |
| 21 | CuZnO.xyz | CuZnO | — | OH | `[OH]` | -8.992 | OK | Extension; not in main table |

### Critical SMILES Verification Needed

Cases 15-16: Paper says **CH₂CH₂OH** (2-hydroxyethyl radical, `*CH2CH2OH`), but previous results show `[CH2]CO` file naming. These are chemically different molecules. Possible explanations:
- (a) Previous run used wrong SMILES — need to verify and potentially rerun
- (b) File naming convention differs from actual SMILES used

Cases 17-19: Paper says **OCHCH₃** (acetaldehyde fragment, `*OCHCH3`), results show `CC_O`. Need to verify SMILES = `CC=O` or `[O]CC` or similar.

Case 20: Paper says **ONN(CH₃)₂** — complex adsorbate, previously failed. Need to determine correct SMILES and debug.

**Action**: Check previous run commands/logs or re-derive SMILES from Adsorb-Agent notation before building manifest.

---

## Phase 0: Prerequisites (Day 1-2)

### 0.1 Resolve SMILES for All 20 Cases

**Priority**: P0 — blocks everything

1. For cases 01-14: SMILES are clear from results (`[H]`, `[N]=[NH]`, `[OH]`)
2. For cases 15-16: Determine correct SMILES for CH₂CH₂OH radical
   - Adsorb-Agent uses `*CH2CH2OH` notation where `*` = binding site
   - Likely SMILES: `[CH2]CCO` (radical at terminal C, ethanol backbone)
   - Or `[CH2]CO` if they mean vinyloxy/ketene — **must verify against Adsorb-Agent's `adsorbates.pkl`**
3. For cases 17-19: Determine correct SMILES for OCHCH₃
   - Likely SMILES: `[O]CC` or `CC=O` — acetaldehyde radical
4. For case 20: Determine SMILES for ONN(CH₃)₂
   - Likely SMILES: `[O]NN(C)C` — dimethylnitrosoamine radical
5. **Verification method**: Check `CatalystAIgent/config/example/COMPLEX.yaml` system_id `44_2803_2` and cross-ref with OC20 dataset, or read the Adsorb-Agent paper's supplementary Table S1

### 0.2 Build Manifest

`research/agent_eval/manifests/cmu_manifest.csv`:

```csv
case_id,slab_file,smiles,user_request,surface_family,adsorbate_name,miller_index,reaction_class,ablation_candidate,notes
```

- `surface_family`: monometallic / intermetallic / oxide
- `reaction_class`: NRR / HER / ORR / COMPLEX
- `ablation_candidate`: TRUE for 3-5 representative cases (selection criteria below)

**Ablation candidate selection** (from Phase 2 results, but pre-tag likely candidates now):
- Case 01 or 07: intermetallic + H (simple, likely has slip)
- Case 09: monometallic baseline (Pt(111)+OH, well-studied)
- Case 02 or 08: intermetallic + polyatomic (NNH, dissociation-prone)
- Case 14: bimetallic ORR (CoPt+OH)
- Case 15 or 16: large adsorbate on complex intermetallic

### 0.3 Freeze Experiment Config

`research/agent_eval/configs/frozen_config.json`:

```json
{
  "llm_backend": "google",
  "llm_model": "gemini-2.5-pro",
  "temperature": 0.0,
  "max_retries": 5,
  "relaxation_mode": "standard",
  "mace_precision": "float32",
  "mace_model": "mace-mp-0-medium",
  "fmax": 0.10,
  "random_seed": 42,
  "platform": "macOS-M3Pro-float32",
  "notes": "Production run for paper. float32 due to macOS; float64 results require Linux rerun."
}
```

**Important precision note**: Outline Section 2.5 specifies float64 for Linux/CUDA and float32 for macOS. Since you only have macOS now:
- Option A: Run everything float32 on Mac, note in paper as limitation
- Option B: Request Linux GPU from Prof. Cheng for float64 production runs
- **Recommendation**: Run Phase 2 on Mac first (float32) to validate pipeline and get preliminary numbers. If results look good, request GPU for final float64 production run. This avoids wasting GPU time on pipeline bugs.

---

## Phase 1: Batch Runner (Day 2-3)

### 1.1 `research/agent_eval/run_case.py`

Thin wrapper around existing `src/agent/agent.py` LangGraph graph:

```
Input:  case_id, slab_file, smiles, user_request, config
Output: research/results/{run_name}/{case_id}/
        ├── config.json          (frozen config + git SHA + timestamp)
        ├── result.json          (final state: best_energy, iterations, slip_count, etc.)
        ├── agent_log.txt        (stdout/stderr capture)
        ├── BEST_*.xyz           (best structure files)
        ├── final_relaxed_structures.xyz
        └── trajectory.traj      (relaxation trajectory)
```

Key requirements:
- Record `git rev-parse HEAD` in config.json
- Record wall-clock time (start/end)
- Record LLM token usage (requires adding token counting — see Phase 1.3)
- Catch and log exceptions without crashing the batch

### 1.2 `research/agent_eval/run_batch.py`

```
Input:  manifest CSV + frozen config + output base dir
Output: One subdirectory per case in output dir
```

- Sequential execution (no parallelism needed for 20 cases)
- Skip cases that already have a `result.json` (simple resume)
- Print progress: `[3/20] Running case 03_Pd3Cu_111 H...`

### 1.3 Add Token Counting to Agent

Minimal change to `src/agent/agent.py`:
- After each `llm.invoke()` call, extract token usage from response metadata
- Accumulate in `AgentState` (add `total_input_tokens: int`, `total_output_tokens: int` fields)
- Report in final state → flows into result.json automatically

This is ~10 lines of code change. Specific to each LLM backend:
- Google: `response.usage_metadata.prompt_token_count` / `candidates_token_count`
- OpenRouter: `response.response_metadata.token_usage`

### 1.4 `research/agent_eval/summarize_runs.py`

Scan output directory, produce:

```
research/results/{run_name}/summary.csv
```

Fields:
```
case_id, surface, miller, adsorbate, smiles, surface_family,
best_energy_eV, iterations_used, max_retries,
perfect_count, dissociation_count, rearrangement_count, calc_failure_count,
chemical_slip_count, soft_slip_count, hard_slip_count,
final_site_type, converged_tag,
wall_clock_sec, total_input_tokens, total_output_tokens,
status (success/failed/error)
```

This CSV directly populates **Table 1** and provides data for **Fig. 2**.

---

## Phase 2: Run CMU Benchmark (Day 3-5)

### 2.1 Execute Full Benchmark

```bash
python research/agent_eval/run_batch.py \
  --manifest research/agent_eval/manifests/cmu_manifest.csv \
  --config research/agent_eval/configs/frozen_config.json \
  --output research/results/cmu_v1/
```

### 2.2 Quality Gates

Before proceeding, verify:
- [ ] All 20 cases have result.json (case 20 may still fail — that's data too)
- [ ] summary.csv generated with no missing fields
- [ ] Best energies are in physically reasonable range (< 0 eV for chemisorption)
- [ ] Chemical Slip events are detected and logged (check cases 01, 02 where slip was observed before)
- [ ] Token counts are populated

### 2.3 Compare with Previous Results

Sanity check: compare Phase 2 best energies against previous results (from `results/` directory). They should be similar but may differ due to:
- Different random seed
- Different MACE precision settings
- Different LLM version (if Gemini was updated)

If energies differ by > 0.3 eV on multiple cases, investigate before proceeding.

### 2.4 CuZnO Extension

Run separately, store in `research/results/cmu_v1/21_CuZnO/`. Report in paper text but exclude from statistical tables.

---

## Phase 3: Adsorb-Agent Comparison (Day 5-7)

### 3.1 Data Source: Paper-Reported Values

**Adsorb-Agent cannot run on macOS** (requires CUDA + EquiformerV2 GNN). Two options:

**Option A (Recommended)**: Extract Adsorb-Agent results from their paper
- Read arXiv:2410.16658 main text + SI for the 20 systems
- Extract: best energy, number of configurations tested, success/failure
- Record in `research/results/adsorbagent_paper_results.csv`
- Limitation: their results use EquiformerV2 (not MACE-MP), so energy values are NOT directly comparable in absolute terms
- **Key comparison axes**: success rate, relative rankings, number of iterations

**Option B (If GPU available)**: Run Adsorb-Agent on Prof. Cheng's cluster
- Install fairchem-forked + EquiformerV2 on GPU node
- Run on same 20 systems
- This gives directly comparable GNN-relaxed results
- BUT: different GNN means energy magnitudes differ anyway

**Recommendation**: Start with Option A. The paper's core argument is about search strategy (closed-loop vs open-loop), not about MACE vs EquiformerV2. We can compare:
- Win/tie/loss on finding lower energy configurations
- Search efficiency (iterations to converge)
- Failure handling (dissociation, Chemical Slip)
- Success rate on intermetallic vs monometallic surfaces

### 3.2 Comparison Schema

`research/results/comparison.csv`:

```
case_id, surface, adsorbate,
adsmind_best_energy, adsmind_iterations, adsmind_success, adsmind_slip_count, adsmind_dissociation,
adsorbagent_best_energy, adsorbagent_success, adsorbagent_configs_tested,
energy_diff, winner, notes
```

### 3.3 Statistical Tests (per Outline Section 2.6)

| Test | Purpose | Tool |
|------|---------|------|
| Wilcoxon signed-rank | Energy difference (paired, n=20) | `scipy.stats.wilcoxon` |
| McNemar's test | Success rate difference | `statsmodels.stats.contingency_tables.mcnemar` |
| Rank-biserial correlation | Effect size for Wilcoxon | manual or `pingouin` |
| 95% bootstrap CI | Confidence interval on median difference | `scipy.stats.bootstrap` |
| Benjamini-Hochberg FDR | Multiple comparison correction | `statsmodels.stats.multitest` |

Output: `research/results/comparison_stats.json` with all test results, p-values, effect sizes, CIs.

### 3.4 Case Study Selection for Fig. 5

Select 2-3 cases where closed-loop feedback makes a critical difference:
- Best candidate: intermetallic surface where Chemical Slip → FORBID → correct site found
- Second candidate: case where Adsorb-Agent fails but AdsMind succeeds (or vice versa)
- Third candidate: case showing autonomous termination saving compute

---

## Phase 4: Parameterize Ablation Switches (Day 5-7, parallel with Phase 3)

### 4.1 Code Changes

**Files to modify**:

#### `src/agent/agent.py` — Add flags to AgentState

```python
class AgentState(TypedDict):
    # ... existing fields ...
    # Ablation switches (default True = full system)
    enable_slip_feedback: bool    # Controls slip warning text in history
    enable_forbid: bool           # Controls FORBID constraint text
    enable_termination: bool      # Controls convergence tag generation
```

#### `src/agent/history.py` — Conditional text generation

In `build_history_entry()`, accept ablation flags and conditionally:
- Skip `⚠️【Unstable Site Warning】` and FORBID text when `enable_slip_feedback=False`
- Skip FORBID-specific text when `enable_forbid=False`  
- Skip `[🔄 Converged to known best]` tag when `enable_termination=False`

Note: `enable_slip_feedback=False` implies `enable_forbid=False` (no slip detection → nothing to forbid). But `enable_forbid=False` alone still detects slip, just doesn't add the FORBID constraint.

#### `src/agent/prompts.py` — Conditional prompt sections

The prompt has these ablation-sensitive sections:
- Lines 27-28: "Chemical Slip" warning → controlled by `enable_slip_feedback`
- Lines 29-33: Termination signal instructions → controlled by `enable_termination`
- Lines 39: "Do not plan again for site types identified as unstable" → controlled by `enable_forbid`
- Lines 46: Convergence principle → controlled by `enable_termination`

Implementation: Build prompt from sections, conditionally include/exclude relevant paragraphs.

### 4.2 Five Ablation Variants

| Variant | `enable_slip_feedback` | `enable_forbid` | `enable_termination` | MAX_RETRIES |
|---------|:---:|:---:|:---:|:---:|
| `full` | True | True | True | 5 |
| `no_slip` | False | False | True | 5 |
| `no_forbid` | True | False | True | 5 |
| `no_termination` | True | True | False | 5 (hard cap) |
| `single_shot` | False | False | False | 1 |

### 4.3 Unit Tests

```
tests/test_ablation_switches.py
```

Three tests minimum:
1. `test_no_slip_suppresses_warning`: With `enable_slip_feedback=False`, `build_history_entry` for a slip case does NOT contain "Unstable Site Warning" or "FORBID"
2. `test_no_forbid_keeps_slip_but_removes_forbid`: With `enable_forbid=False`, slip is still reported but "FORBID" text is absent
3. `test_no_termination_suppresses_convergence_tag`: With `enable_termination=False`, convergence case does NOT contain "Converged to known best"

---

## Phase 5: Ablation Experiments (Day 7-10)

### 5.1 Select Cases

From Phase 2 results, select 3-5 cases covering:

| Slot | Likely Case | Rationale |
|------|-------------|-----------|
| Monometallic baseline | 09 (Pt(111)+OH) | Simple, well-studied, minimal slip expected |
| Intermetallic + slip | 01 (Mo3Pd(111)+H) | Strong Chemical Slip in previous run |
| Intermetallic + dissociation | 02 (Mo3Pd(111)+NNH) | Dissociation events observed |
| Bimetallic ORR | 14 (CoPt(111)+OH) | DFT validation target, moderate complexity |
| Large adsorbate | 15 or 19 (Cu6Ga2 or Hf2Zn6 + large molecule) | Stress test |

Final selection depends on Phase 2 results — pick cases where full AdsMind shows interesting behavior (slip recovery, FORBID use, early termination).

### 5.2 Execute

5 cases × 5 variants = 25 runs.

```bash
python research/agent_eval/run_ablation.py \
  --cases "01,02,09,14,19" \
  --variants "full,no_slip,no_forbid,no_termination,single_shot" \
  --config research/agent_eval/configs/frozen_config.json \
  --output research/results/ablation_v1/
```

### 5.3 Analysis

`research/results/ablation_v1/ablation_summary.csv`:

```
case_id, variant, best_energy, delta_vs_full, iterations, wasted_iterations,
waste_ratio, success, slip_count, dissociation_count, tokens_used
```

Statistical tests (per Outline Section 3.5):
- **Friedman test**: Overall comparison across 5 variants on same cases
- **Pairwise Wilcoxon + FDR**: full vs each ablation variant
- **Paired differences + 95% bootstrap CI**: Primary evidence
- **Effect sizes**: Median difference, Cohen's d where applicable

Output: `research/results/ablation_v1/ablation_stats.json`

---

## Phase 6: Package & Deliver (Day 10-12)

### 6.1 DFT Handoff to Bowen

From Phase 2 results, extract for 5 DFT validation systems (Outline Section 3.4):

| System | Source Case |
|--------|------------|
| Pt(111) + OH | Case 09 |
| Pt(100) + OH | Case 10 |
| Mo₃Pd(111) + H | Case 01 |
| Mo₃Pd(111) + NNH | Case 02 |
| CoPt(111) + OH | Case 14 |

Deliverable to Bowen:
```
research/results/dft_handoff/
├── case_09_Pt111_OH/
│   ├── BEST_structure.xyz     (MACE-MP relaxed, lowest energy)
│   ├── mace_energy.json       (energy value + config)
│   └── README.md              (what DFT calc to run)
├── case_10_Pt100_OH/
│   └── ...
└── ...
```

### 6.2 Update OUTLINE.md

Replace all `[to be updated with actual data after rerun]` placeholders with real numbers:
- Section 3.1: Table 1 values, success rate, slip frequency, dissociation rate
- Section 3.2: Table 2 comparison, win/tie/loss counts
- Section 3.5: Table 4 ablation results
- Section 4.4: Actual failure case statistics, token/cost numbers

### 6.3 SI Data Package

```
research/results/si_package/
├── SI-1_prompts/              (frozen prompt templates)
├── SI-2_benchmark_data/       (full run logs, energies, trajectories)
├── SI-4_ablation_data/        (all ablation runs)
├── SI-6_cost_analysis/        (token counts, wall-clock times)
└── SI-8_failure_analysis/     (failure case classification)
```

---

## Open Questions (Require Your Decision)

1. **SMILES for cases 15-20**: Need to verify exact SMILES against Adsorb-Agent's adsorbate database. Do you want me to dig into `CatalystAIgent/` code to extract this, or do you have records of what SMILES you used in the previous runs?

2. **Float32 vs float64**: Run on Mac now (float32) and potentially re-run on GPU later (float64)? Or wait for GPU access?

3. **Adsorb-Agent comparison**: Use paper-reported values (Option A) or request GPU to run their code (Option B)?

4. **Multi-model comparison (SI-5)**: Schedule after P0 experiments, or skip for initial submission? Budget is available via AiHubMix.

---

## File Structure After Completion

```
research/
├── EXPERIMENT_PLAN.md          (this file)
├── agent_eval/
│   ├── run_case.py
│   ├── run_batch.py
│   ├── run_ablation.py
│   ├── summarize_runs.py
│   ├── manifests/
│   │   └── cmu_manifest.csv
│   ├── configs/
│   │   └── frozen_config.json
│   └── reports/
│       ├── PHASE_0_REPORT.md
│       └── PHASE_2_REPORT.md
└── results/
    ├── cmu_v1/                 (Phase 2 output)
    │   ├── 01/ ... 20/
    │   ├── 21_CuZnO/
    │   └── summary.csv
    ├── adsorbagent_paper_results.csv  (Phase 3)
    ├── comparison.csv          (Phase 3)
    ├── comparison_stats.json   (Phase 3)
    ├── ablation_v1/            (Phase 5 output)
    │   ├── {case}_{variant}/
    │   ├── ablation_summary.csv
    │   └── ablation_stats.json
    ├── dft_handoff/            (Phase 6)
    └── si_package/             (Phase 6)
```
