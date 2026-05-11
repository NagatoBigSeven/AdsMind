# Paper Plots

论文图表 notebook 及数据处理脚本。

## 数据管道

| 脚本                              | 用途                                                                                           |
| --------------------------------- | ---------------------------------------------------------------------------------------------- |
| `scripts/prepare_figure3_data.py` | Figure 3：iteration_convergence, method_comparison, slip_analysis, ablation_4backend           |
| `scripts/prepare_si_data.py`      | Figure2 and SI：per-variant summaries, baselines, slip, ablation, multi-seed, MACE sensitivity |

所有处理后的数据输出到 `research/results/processed/`。

## 目录结构

```
paper_plots/
├── README.md
├── TODO.md
├── scripts/
│   ├── prepare_figure3_data.py
│   └── prepare_si_data.py
├── figure2/
│   ├── plot_cmu20_llm_performance_v3_panelabc.ipynb
│   └── figure2_combined_panelabc.png
├── figure3/
│   ├── figure3_panels_updated.ipynb
│   └── figure3_complete.png
├── figure4/
│   ├── figure4_ocd_2tier_overview.ipynb
│   └── figure4_ocd_2tier_overview.png
├── figure5/
│   ├── figure5_vasp_validation.ipynb
│   ├── figure5_vasp_validation.png
│   └── reference/
├── figure_SI_1/
    ├── si_figure_S1_panels.ipynb
    └── si_figure_S1_combined.png
```
