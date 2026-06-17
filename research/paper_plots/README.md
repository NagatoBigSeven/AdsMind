# Paper Plot Pipeline

This directory contains the paper-facing plotting entry points for the current
AdsMind manuscript. Prefer the canonical commands below instead of rerunning old
notebooks from earlier figure-numbering rounds.

## Current Manuscript Figures

| Manuscript asset | Canonical generator | Main data sources | Notes |
| --- | --- | --- | --- |
| `overleaf/images/figure2_vasp_validation.png` | `python research/paper_plots/scripts/regenerate_current_main_figures.py` | GPT-5.4 Full raw summaries for AA20 cases 01/02/03/04/09/10; `research/paper_plots/scripts/CMU20_results_in_paper.csv`; hard-coded VASP/PBE references | Replaces the old `figure5_vasp_validation.ipynb`. AdsMind MAE must remain 1.55 eV. |
| `overleaf/images/figure3_combined_panelabc.png` | `python research/paper_plots/scripts/regenerate_current_main_figures.py` | AA20 GPT Full summary, heuristic baseline summary, Adsorb-Agent literature values, and raw AA20 all-variant summaries | Replaces the old `figure2_llm_performance.ipynb`. The main figure intentionally excludes Random and only plots `1-Shot`/`w/o Term` in panel b/c. |
| `overleaf/images/figure4_complete.png` | `research/paper_plots/figure3/figure3_panels_updated.ipynb` | `research/results/processed/figure3/{iteration_convergence.csv, slip_analysis.json, ablation_4backend.csv}` | Regenerate processed inputs first with `prepare_figure3_data.py`. Dissociated attempts must be excluded from running-best updates upstream. |
| `overleaf/images/figure5_ocd_2tier_overview.png` | `research/paper_plots/figure4/figure4_ocd_2tier_overview.ipynb` | OCD62 all-variant summaries and `reproducibility_n3_minvar.csv` | The main figure plots `Full`, `1-Shot`, and `w/o Term`; the `Up to 1.27 eV` annotation is for these plotted variants, not all five variants. |
| `overleaf/si_figures/si_figure_S1_combined.png` | `research/paper_plots/figure_SI_1/si_figure_S1_panels.ipynb` | `research/results/processed/si_figures/...` | Regenerate processed SI inputs first with `prepare_si_data.py`. The slip CSV should contain Gemini, GPT, Claude, and Grok columns. |

## Data Preparation Commands

Run these before regenerating Figure 4 or the SI figure when raw result folders
change:

```bash
python research/paper_plots/scripts/prepare_figure3_data.py
python research/paper_plots/scripts/prepare_si_data.py
python research/paper_plots/scripts/build_n3_minvar.py
```

Run this after changing the DFT validation values, AA20 method comparison, or
AA20 ablation summaries:

```bash
python research/paper_plots/scripts/regenerate_current_main_figures.py
```

Finally, audit paper-facing tables and figure inputs:

```bash
python research/analysis/check_paper_data.py
```

When executing the remaining notebooks, run them from their own directories
(`research/paper_plots/figure3`, `figure4`, or `figure_SI_1`) because their data
paths are relative to the notebook location.

## Current Support Files

| Path | Purpose |
| --- | --- |
| `scripts/CMU20_results_in_paper.csv` | Literature Adsorb-Agent adsorption energies used as the reported EquiformerV2 reference output. |
| `scripts/regenerate_current_main_figures.py` | Canonical script for the current DFT validation figure and AA20 ablation figure. |
| `figure5/reference/*.png` | Structure thumbnails used by the DFT validation figure. |
| `figure_per_agent_ablation/` | Diagnostic per-agent ablation plots. These are not part of the current main figure pipeline unless the manuscript adds a per-agent ablation figure. |

## Removed Legacy Entrypoints

The following notebooks were removed because they could regenerate stale or
misleading figures:

- `figure2/figure2_llm_performance.ipynb`: included the removed Random baseline
  and a placeholder Adsorb-Agent reference label.
- `figure5/figure5_vasp_validation.ipynb`: superseded by
  `scripts/regenerate_current_main_figures.py`.
- `figure3/figure3_panels_iter_ref_cmu.ipynb`: used an older reference-energy
  convergence definition rather than the current iteration/full ratio definition.
