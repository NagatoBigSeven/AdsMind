# Paper Plots

Plotting notebooks and data processing scripts.

## Scripts

| Script                       | Description                                                                                 |
| ---------------------------- | ------------------------------------------------------------------------------------------- |
| `build_n3_minvar.py`         | Select min-volatility N=3 runs from N=5 reproducibility data                                |
| `CMU20_results_in_paper.csv` | Literature reference adsorption energies for CMU20                                          |
| `prepare_figure3_data.py`    | Extract Figure 3 data from raw results, remap backend keys                                  |
| `prepare_si_data.py`         | Extract SI data from raw results (summaries, baselines, slip, MACE sensitivity, multi-seed) |

## Notebooks

```
paper_plots/
├── README.md
├── scripts/
├── figure2/
│   ├── figure2_llm_performance.ipynb     # Panel abc: LLM energy comparison & ablation
│   └── figure2_combined_panelabc.png
├── figure3/
│   ├── figure3_panels_iter_ref_cmu.ipynb # Iteration & reference convergence panels
│   ├── figure3_panels_updated.ipynb      # Updated Figure 3 panels
│   └── figure3_complete.png
├── figure4/
│   ├── figure4_ocd_2tier_overview.ipynb  # 2-tier ablation analysis (OCD62)
│   └── figure4_ocd_2tier_overview.png
├── figure5/
│   ├── figure5_vasp_validation.ipynb     # VASP validation
│   ├── figure5_vasp_validation.png
│   └── reference/                        # Slab reference images
│       ├── 01_Mo3Pd_111_H_template_v6.png
│       ├── 02_Mo3Pd_111_NNH.png
│       ├── 03_Pd3Cu_111_H.png
│       ├── 04_Pd3Cu_111_NNH.png
│       ├── 09_Pt_111_OH.png
│       └── 10_Pt_100_OH.png
└── figure_SI_1/
    ├── si_figure_S1_panels.ipynb
    └── si_figure_S1_combined.png
```
