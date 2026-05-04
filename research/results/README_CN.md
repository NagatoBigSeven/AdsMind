# research/results 数据结构

当前结果目录先按实验类型组织。

```text
research/results/
  basic_experiments/
    cmu20/
      gpt|claude|gemini|grok/
        one_shot|full|no_slip|no_termination|no_forbid/
          summary.csv
          <case_id>/result.json
      baselines/
      summaries/
    ocd62/
      gpt|claude|gemini|grok/
        one_shot|full|no_slip|no_termination|no_forbid/
          summary.csv
          <case_id>/result.json
      baselines/
      summaries/
    summaries/
  advanced_experiments/
```

## 基础实验

基础实验是对齐后的 CMU20 和 OCD62 主评测矩阵：

- 数据集：`cmu20`, `ocd62`
- LLM 后端：`gpt`, `claude`, `gemini`, `grok`
- 变体：`one_shot`, `full`, `no_slip`, `no_termination`, `no_forbid`

每个后端目录下有 `all_variants_summary.csv`，每个变体目录下也有自己的
`summary.csv`，并和 case 结果目录放在一起。

数据集和跨数据集汇总：

- `basic_experiments/cmu20/summaries/method_comparison.csv`
- `basic_experiments/ocd62/summaries/method_comparison.csv`
- `basic_experiments/ocd62/summaries/ablation_4backend.csv`
- `basic_experiments/summaries/full_vs_one_shot_summary.csv`
- `basic_experiments/summaries/method_comparison_summary.csv`
- `basic_experiments/summaries/method_comparison_table.md`
- `basic_experiments/summaries/method_comparison_table.tex`

非 LLM baseline 放在各数据集的 `baselines/` 目录下。CMU20 的
Adsorb-Agent 对照实验在
`basic_experiments/cmu20/baselines/adsorbagent_mace_mp0_small_gpt54/`。

注意：CMU20 的 `one_shot` summary 表包含 20 个 case。部分失败或历史缺失的
one-shot run 没有对应 artifact 目录；完整 case 统计以 `summary.csv` 为准。

## 进阶实验

进阶实验包含主矩阵之外的小规模或更深入研究：

- `ocd62_overlap12_reproducibility/`：OCD62 重叠 12 个 case 的重复性实验。
- `mace_force_field_sensitivity/`：MACE-MP-0 large 力场敏感性检查。
- `adsorbagent_single_config_stress/`：Adsorb-Agent 单构型压力测试。
- `gpt54_multiseed_cmu20/`：GPT-5.4 full-run 多随机种子敏感性。

远程 RUN3 完成后，结果应进入
`advanced_experiments/ocd62_overlap12_reproducibility/run3/`。随后运行：

```bash
.venv/bin/python research/analysis/build_ocd62_summary.py --write-n3
```

## 刷新命令

```bash
.venv/bin/python research/analysis/build_method_comparison_table.py
.venv/bin/python research/analysis/build_ocd62_summary.py
```

本地可能保留 `.xyz`、`.traj`、日志和 per-run config 等大文件，但 Git 默认不跟踪它们。
