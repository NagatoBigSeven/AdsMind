# Paper Plots

论文图表 notebook 及数据处理脚本。

## 图表状态

| 图表 | Notebook | 数据源 | 状态 |
|------|----------|--------|:---:|
| Figure 2 | `figure2/plot_cmu20_llm_performance_v3_panelab.ipynb` | `results/` 直接数据 | ✅ |
| Figure 3 | `figure3/figure3_panels_updated.ipynb` | `results/processed/figure3/` | ✅ |
| SI Figure 1 | `figure_SI_1/si_figure_S1_panels.ipynb` | `results/processed/si_figures/` | ✅ |
| SI Figure 2 | `figure_SI_2/si_figure_S2_panels.ipynb` | `results/processed/si_figures/` | ✅ |

## 数据管道

| 脚本 | 用途 |
|------|------|
| `scripts/prepare_figure3_data.py` | Figure 3：iteration_convergence, method_comparison, slip_analysis, ablation_4backend |
| `scripts/prepare_si_data.py` | SI Figures：per-variant summaries, baselines, slip, ablation, multi-seed, MACE sensitivity |

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
│   ├── plot_cmu20_llm_performance_v3_panelab.ipynb
│   └── figure2_combined_panelab.png
├── figure3/
│   ├── figure3_panels_updated.ipynb
│   └── figure3_complete.png
├── figure_SI_1/
│   ├── si_figure_S1_panels.ipynb
│   └── si_figure_S1_single.png
└── figure_SI_2/
    ├── si_figure_S2_panels.ipynb
    └── si_figure_S2_combined.png
```
