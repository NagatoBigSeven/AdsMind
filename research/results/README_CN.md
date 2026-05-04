# research/results 数据结构

当前结果目录先按实验类型组织。

```text
research/results/
  basic_experiments/
    cmu20/
      openai_gpt54_mace_mp0_small/
      anthropic_claude_sonnet46_mace_mp0_small/
      google_vertexai_gemini25pro_mace_mp0_small/
      xai_grok4_0709_mace_mp0_small/
        one_shot|full|no_slip|no_termination|no_forbid/
          summary.csv
          <case_id>/result.json
      baselines/
      summaries/
    ocd62/
      openai_gpt54_mace_mp0_small/
      anthropic_claude_sonnet46_mace_mp0_small/
      google_vertexai_gemini25pro_mace_mp0_small/
      xai_grok4_0709_mace_mp0_small/
        one_shot|full|no_slip|no_termination|no_forbid/
          summary.csv
          <case_id>/result.json
      baselines/
      summaries/
    summaries/
  advanced_experiments/
    mechanism/
    reproducibility/
    model_sensitivity/
    case_studies/
```

## 基础实验

基础实验是对齐后的 CMU20 和 OCD62 主评测矩阵：

- 数据集：`cmu20`, `ocd62`
- LLM/力场目录：
  `openai_gpt54_mace_mp0_small`,
  `anthropic_claude_sonnet46_mace_mp0_small`,
  `google_vertexai_gemini25pro_mace_mp0_small`,
  `xai_grok4_0709_mace_mp0_small`
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
`basic_experiments/cmu20/baselines/adsorbagent_openai_gpt54_mace_mp0_small/`。

注意：CMU20 的 `one_shot` summary 表包含 20 个 case。部分失败或历史缺失的
one-shot run 没有对应 artifact 目录；完整 case 统计以 `summary.csv` 为准。

## 进阶实验

进阶实验不再按主矩阵展开，而是按研究问题组织：

- `mechanism/ablation_effects/`：Full 与消融机制变体的配对统计、backend
  agreement 和 reach-Full 表。
- `mechanism/chemical_slip_interpretability/`：chemical slip 的解释性表格和轨迹。
- `reproducibility/ocd62_overlap12/`：OCD62 重叠 12 个 case 的重复性实验，
  包括远程 RUN3 的落盘目录。
- `reproducibility/cmu20_openai_gpt54_mace_mp0_small_multiseed/`：
  GPT-5.4 CMU20 full-run 在 MACE-MP-0 small 下的多随机种子敏感性。
- `model_sensitivity/mace_mp0_large/`：MACE-MP-0 large 力场敏感性检查，内部再按
  dataset/backend/variant 拆分。
  `ocd62_sample10` 是 manifest 明确列出的 OCD62 子集，10 个 case 都已经在
  OCD62 基础实验矩阵中完成。
- `case_studies/dft_iteration_alignment/`：用于 DFT 对齐的 CMU20 case 轨迹导出。
- `case_studies/iteration_convergence/`：迭代过程中 running-best energy 曲线。

远程 RUN3 完成后，结果应进入
`advanced_experiments/reproducibility/ocd62_overlap12/run3/`。随后运行：

```bash
.venv/bin/python research/analysis/build_ocd62_summary.py --write-n3
```

## 刷新命令

```bash
.venv/bin/python research/analysis/build_method_comparison_table.py
.venv/bin/python research/analysis/build_ocd62_summary.py
```

本地可能保留 `.xyz`、`.traj`、日志和 per-run config 等大文件，但 Git 默认不跟踪它们。
