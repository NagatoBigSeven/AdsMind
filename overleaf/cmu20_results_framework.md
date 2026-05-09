# CMU20 Results Framework: Basic vs Advanced Testing (Data-Driven)

**Purpose**: Structure CMU20 results for paper Section 3 (Results) and Figure design.  
**Last Updated**: After all figures implemented.  

---

## Data Inventory (What We Actually Have)

### Basic Testing Data ✅ (All Plotted)
| Data | File | Plot Status |
|------|------|-------------|
| 5-variant ablation (80 runs, 4 backends) | `basic_experiments/summaries/cmu20_ablation_4backend.csv` | ✅ Figure 2a+b |
| 4-backend range per case | `advanced_experiments/ablation_and_chemical_slip_diagnostics/ablation_effects/cross_backend_agreement.csv` | ✅ Figure 3c heatmap |
| Full vs 1-Shot head-to-head | `basic_experiments/summaries/full_vs_one_shot_summary.csv` | ✅ Figure 2a (trapezoid) |
| Baseline: Random (n=20) | `basic_experiments/cmu20/baselines/random_n20/summary.csv` | ✅ SI S1a |
| Baseline: Heuristic | `basic_experiments/cmu20/baselines/heuristic/summary.csv` | ✅ SI S1a |
| Baseline: Adsorb-Agent | `basic_experiments/cmu20/baselines/adsorbagent_gpt54_mace_mp0_small/summary.csv` | ✅ SI S1a |

### Advanced Testing Data ✅ (All Plotted)
| Data | File | Plot Status |
|------|------|-------------|
| Iteration convergence (per-iteration energy) | `advanced_experiments/case_studies/iteration_convergence/cmu20/all_backends/full/` | ✅ Figure 3a |
| Chemical Slip (planned vs actual site) | `advanced_experiments/ablation_and_chemical_slip_diagnostics/chemical_slip_interpretability/cmu20/slip_analysis.csv` | ✅ SI S2b |
| Slip rates by backend + surface family | `advanced_experiments/ablation_and_chemical_slip_diagnostics/chemical_slip_interpretability/cmu20/slip_analysis.json` | ✅ Figure 3b, SI S2a |
| MACE Small vs Large sensitivity | `advanced_experiments/force_field_sensitivity/mace_mp0_large_vs_mace_mp0_small/cmu20/gpt54_mace_mp0_large/full/` | ✅ SI S1c |
| Multi-seed reproducibility (5 seeds) | `advanced_experiments/reproducibility/cmu20_gpt54_mace_mp0_small_multiseed/seed{43-47}/full/` | ✅ SI S2c |
| Cost analysis (tokens, wall-clock) | `basic_experiments/cmu20/*/full/summary.csv` (tokens_used column) | ✅ SI S1b |

---

## Final Figure Design (Actual Implementation)

### Figure 2 (Basic Testing) — Main Text
**Notebook**: `research/figures/figure2_ablation/data/plot_cmu20_llm_performance_v3_panelab.ipynb`  
**Output**: `research/figures/figure2_ablation/data/figure2_combined_panelab.png`

```
Figure 2 (2 panels, side by side):
├─ Panel a: Trapezoid plot
│   └─ 4 LLM backends (Gemini 2.5 Pro, GPT-5.4, Claude 4, Grok-4)
│   └─ 5 ablation variants (Full, 1-Shot, w/o Slip, w/o Forbid, w/o Term)
│   └─ y: Energy Δ distribution (IQR boxes + mean diamond + jittered scatter)
│   └─ Data: basic_experiments/summaries/cmu20_ablation_4backend.csv
│   └─ Key message: "1-Shot is the dominant degradation; iterative ablations stay near Full in median energy"
│
└─ Panel b: Radar chart
    └─ Polar coordinates, 5 variants as axes
    └─ Metrics per variant
    └─ Data: same as Panel a
    └─ Key message: "Full variant dominates on all metrics"
```

---

### Figure 3 (Advanced Testing) — Main Text
**Notebook**: `research/figures/figure3_main_text/figure3_panels_updated.ipynb`  
**Output**: `research/figures/figure3_main_text/figure3_complete.png`

```
Figure 3 (2 rows):
├─ Row 1: Panel a (left) + Panel b (right)
│   ├─ Panel a: Iteration Convergence of dE
│   │   └─ x: Iteration (1-5), y: Mean dE (eV)
│   │   └─ dE = running-best energy change across AdsMind iterations
│   │   └─ 4 backends as colored lines, y starts at 0
│   │   └─ Vertical dashed line at Iter 2 (80% improvement)
│   │   └─ Data: advanced_experiments/case_studies/iteration_convergence/cmu20/all_backends/full/
│   │
│   └─ Panel b: Chemical Slip Analysis
│       └─ Grouped bar chart: Backend (4) × Slip rate
│       └─ Grouped by surface family (Intermetallic vs Monometallic)
│       └─ Data: advanced_experiments/ablation_and_chemical_slip_diagnostics/chemical_slip_interpretability/cmu20/slip_analysis.json
│
└─ Row 2: Panel c (full width)
    └─ Panel c: 4-Backend Agreement Heatmap
        └─ x: Case ID (01-20), y: Backend (4)
        └─ Heatmap colored by Adsorption Energy (RdYlBu_r)
        └─ Annotated with energy values
        └─ Data: basic_experiments/summaries/cmu20_ablation_4backend.csv
```

---

### SI Figure S1: Performance Analysis (Supplementary)
**Notebook**: `research/figures/si_figure_S1_panels.ipynb`  
**Output**: `research/figures/si_figure_S1_combined.png`

```
SI Figure S1 (2 rows):
├─ Row 1: Panel a (full width)
│   └─ Panel a: Method Comparison
│       └─ Grouped bar chart (20 cases, 4 methods)
│       └─ Methods: AdsMind Full, Random (n=20), Heuristic, Adsorb-Agent
│       └─ Data: basic_experiments/cmu20/adsmind/gpt54_mace_mp0_small/full/summary.csv + baselines/*
│       └─ Key message: "AdsMind trades raw energy depth for fewer relaxations and higher closed-loop reliability"
│
└─ Row 2: Panel b (left) + Panel c (right, c1 scatter + c2 histogram)
    ├─ Panel b: Cost-Accuracy Trade-off
    │   └─ Scatter: Tokens (x) vs Energy (y)
    │   └─ 4 backends × 5 variants, annotated key points
    │   └─ Data: basic_experiments/cmu20/{be}/{var}/summary.csv
    │
    └─ Panel c: MACE Force Field Sensitivity
        ├─ c1: MACE Small vs Large scatter (diagonal line)
        └─ c2: Δ energy histogram (Large − Small)
        └─ Data: advanced_experiments/force_field_sensitivity/mace_mp0_large_vs_mace_mp0_small/cmu20/
```

---

### SI Figure S2: Slip & Reproducibility (Supplementary)
**Notebook**: `research/figures/si_figure_S2_panels.ipynb`  
**Output**: `research/figures/si_figure_S2_combined.png`

```
SI Figure S2 (1 row, 3 columns):
├─ Panel a: Cross-Backend Slip Agreement
│   └─ Heatmap: Case ID (20) × Backend (Gemini, Grok-4)
│   └─ Color: slip (red) / no slip (gray)
│   └─ Highlight disagreement cases (1, 15) with black border
│   └─ Data: advanced_experiments/ablation_and_chemical_slip_diagnostics/chemical_slip_interpretability/cmu20/slip_analysis.csv
│   └─ Key: 18/20 cases agreement (90%)
│
├─ Panel b: Site Transition Matrix
│   └─ Heatmap: Planned site (y) × Actual site (x)
│   └─ Count annotations, color = transition count
│   └─ Data: slip_analysis.csv (gemini + grok4 planned/actual site columns)
│   └─ Key: Most common pattern: ontop → hollow
│
└─ Panel c: Multi-Seed Reproducibility
    └─ Box plot: Case ID (20) × Energy (5 seeds: seed43-47)
    └─ Overlay: Primary GPT-5.4 reference points
    └─ Data: advanced_experiments/reproducibility/cmu20_gpt54_mace_mp0_small_multiseed/seed{43-47}/full/summary.csv
    └─ Key: Additional seeds probe stochastic basin selection on difficult cases
```

---

## Implementation Notes

### Output Files Summary
| Figure | File | Size |
|--------|------|------|
| Figure 2 | `research/figures/figure2_ablation/data/figure2_combined_panelab.png` | 785 KB |
| Figure 3 | `research/figures/figure3_main_text/figure3_complete.png` | 505 KB |
| SI S1 | `research/figures/si_figure_S1_combined.png` | 430 KB |
| SI S2 | `research/figures/si_figure_S2_combined.png` | 372 KB |

### All figures saved as both PNG (300 DPI) + PDF (vector)

---

## What Is NOT Plotted (Deferred / Optional)

| Feature | Reason | Priority |
|---------|--------|----------|
| Multi-seed box plot (full detail) | ✅ Done in SI S2c | Done |
| Slip Sankey diagram | Replaced by transition matrix in SI S2b | Done |
| 4-Backend range violin (Full vs 1-Shot) | Deferred; Figure 3c heatmap shows backend agreement differently | Low |
| Baseline comparison bar (Figure 2d) | Deferred; SI S1a covers this in detail | Low |
