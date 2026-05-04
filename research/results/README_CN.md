# research/results/ 数据清单

当前论文口径只使用两个数据集：

- `CMU20`
- `OCD62`

OCD62 是 62 个 case benchmark。12 个重复 case 只作为 `overlap12` 重复性实验保留。

## 论文主入口

优先使用这两个目录：

- `basic_tests/`：基础测试，包括 Full vs 1-Shot、后端 range、random/heuristic cost、brute-force vs iterative 表。
- `advanced_tests/`：高阶测试，包括 OCD62 四后端五变体消融矩阵、overlap12 重复性审计、Grok-4 outlier 诊断。

`analysis/` 里还有中间表和重建输出。画图和写作优先读 `basic_tests/` 与 `advanced_tests/`。

## 基础测试

| 内容 | 文件 |
|---|---|
| Full vs 1-Shot 汇总 | `basic_tests/full_vs_1shot_summary.csv` |
| 方法比较汇总 | `basic_tests/method_comparison_summary.csv` |
| CMU20 方法比较明细 | `basic_tests/cmu20_method_comparison.csv` |
| OCD62 方法比较明细 | `basic_tests/ocd62_method_comparison.csv` |
| 人读表格草稿 | `basic_tests/method_comparison_table.md`, `basic_tests/method_comparison_table.tex` |

## 高阶测试

| 内容 | 文件 |
|---|---|
| OCD62 四后端五变体矩阵 | `advanced_tests/ocd62_ablation_4backend.csv` |
| OCD62 overlap12 N=2 重复性表 | `advanced_tests/ocd62_overlap12_reproducibility_n2.csv` |
| OCD62 overlap12 N=2 报告 | `advanced_tests/ocd62_overlap12_reproducibility_n2.md` |
| Grok-4 OCD16 outlier 诊断 | `advanced_tests/grok4_ocd16_outlier_diagnosis.md` |

RUN3 目前还没有结果。结果回来后运行：

```bash
.venv/bin/python research/analysis/build_ocd62_summary.py --write-n3
```

## Raw 数据

- CMU20 raw results 在 `canonical_raw/cmu20/`。
- OCD62 raw results 在 `canonical_raw/ocd62/`。
- OCD62 overlap12 重复性实验在 `canonical_raw/ocd62_overlap12/`，
  三个目录分别是 `run1/`、`run2/` 和 `run3/`。

移动或新增 raw 目录后，重建 registry：

```bash
.venv/bin/python research/agent_eval/rebuild_canonical_raw_qc.py
.venv/bin/python research/agent_eval/rebuild_result_registries.py
```

## Variant 名称

消融 CSV 里的单步 baseline 叫 `single_shot`，不是 `one_shot`。

核心变体：

- `full`
- `no_slip`
- `no_forbid`
- `no_termination`
- `single_shot`
