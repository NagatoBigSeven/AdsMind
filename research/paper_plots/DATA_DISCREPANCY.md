# Figure 3 数据处理 — 完整记录

**更新日期**: 2026-05-07
**状态**: 四文件全部处理完毕，notebook 已更新

---

## Gemini 后端数据不一致（已解决）

在 `research/results/` 和 `research/results_sherry/` 之间，涉及 **Gemini 2.5 Pro 后端** 的吸附能数据存在系统性差异。

| 文件 | 受影响列/行 | 差异量级 |
|------|------------|---------|
| `ablation_4backend.csv` | gemini one_shot + full，15/400 行 | 0.06 ~ 1.05 eV |
| `method_comparison.csv` | `adsmind_*_gemini_*` 及聚合列 | 同上 |

**决定（2026-05-07）**：以 `research/results/` 的值为准。

**可能原因**：Sherry 对 gemini 做了 re-run、或使用了不同时间点的 API 响应、或手动修正过异常值。

---

## 四个文件处理状态

| 文件 | 数据一致性 | 备注 |
|------|:---:|------|
| `iteration_convergence.csv` | ✅ 逐行一致 | 与 Sherry 原件完全相同 |
| `method_comparison.csv` | ⚠️ | notebook 只用 `adsorbagent_energy`（该列一致）；gemini 聚合列有差异但不影响出图 |
| `slip_analysis.json` | ✅ 完全一致 | 与 Sherry 原件完全相同 |
| `ablation_4backend.csv` | ✅ | 使用 `results/` 原始值（包括 gemini），列结构与 Sherry 格式匹配 |

---

## 文件位置

### 处理脚本
```
research/paper_plots/scripts/prepare_figure3_data.py
```

### 输入（原始数据）
```
research/results/
  advanced_experiments/case_studies/iteration_convergence/.../iteration_convergence.csv
  advanced_experiments/.../slip_analysis.json
  basic_experiments/cmu20/summaries/method_comparison.csv
  basic_experiments/cmu20/summaries/ablation_4backend.csv
```

### 输出（处理后数据）
```
research/results/processed/figure3/
  iteration_convergence.csv
  method_comparison.csv
  slip_analysis.json
  ablation_4backend.csv
```

### Notebook（已更新路径）
```
research/paper_plots/figure3/figure3_panels_updated.ipynb
```
所有 `results_sherry/` 引用已替换为 `results/processed/figure3/`。
