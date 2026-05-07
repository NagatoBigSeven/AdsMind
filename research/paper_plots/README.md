# Paper Plots

论文图表 notebook 及数据处理脚本。

## 图表状态

| 图表 | Notebook | 数据源 | 状态 |
|------|----------|--------|:---:|
| Figure 2 | `figure2/plot_cmu20_llm_performance_v3_panelab.ipynb` | 读取 `results/` 直接数据 | ✅ 不需要迁移 |
| Figure 3 | `figure3/figure3_panels_updated.ipynb` | → `results/processed/figure3/` | ✅ 已完成迁移 |
| SI Figure 1 | `figure_SI_1/si_figure_S1_strategies.ipynb` | → `results/processed/si_figures/` | ✅ 已完成迁移 |
| SI Figure 2 | `figure_SI_2/si_figure_S2_stability.ipynb` | → `results/processed/si_figures/` | ✅ 已完成迁移 |

## 数据管道

**处理脚本**：
- `scripts/prepare_figure3_data.py` — Figure 3 数据
- `scripts/prepare_si_data.py` — SI Figure 1 & 2 数据

**已知差异**：Gemini 后端在 `results/` 和 `results_sherry/` 之间有 15 处数值不一致（详见 `DATA_DISCREPANCY.md`），已决定以 `results/` 值为准。

## SI 图表重组说明

原 SI-1（4 panels）和 SI-2（3 panels）被重组为：

| 新图表 | Panel | 来源 | 内容 |
|--------|:-----:|------|------|
| **SI-1** `si_figure_S1_strategies.ipynb` | a | 原 SI-1 panel a | 4 策略 CMU20 best energy 柱状图 |
| **SI-2** `si_figure_S2_stability.ipynb` | a | 原 SI-1 c+d 合并 | MACE small vs large 散点图 + ΔE 直方图嵌入 |
| | b | 原 SI-2 panel a | Cross-backend slip 热力图 |
| | c | 原 SI-2 panel b | Planned → actual site 转移矩阵 |
| | d | 原 SI-2 panel c | Multi-seed 可重复性箱线图 |

## 目录结构

```
paper_plots/
├── README.md
├── DATA_DISCREPANCY.md
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
│   ├── si_figure_S1_panels.ipynb          (旧版，保留)
│   ├── si_figure_S1_panels copy.ipynb     (备份)
│   ├── si_figure_S1_strategies.ipynb      (新版)
│   └── si_figure_S1_combined.png
└── figure_SI_2/
    ├── si_figure_S2_panels.ipynb          (旧版，保留)
    ├── si_figure_S2_panels copy.ipynb     (备份)
    ├── si_figure_S2_stability.ipynb       (新版)
    └── si_figure_S2_combined.png
```
