# research/results 数据结构

当前结果目录先按实验类型组织。

```text
research/results/
  basic_experiments/
    cmu20/
      adsmind/
        gpt54_mace_mp0_small/
        claude_sonnet46_mace_mp0_small/
        gemini25pro_mace_mp0_small/
        grok4_mace_mp0_small/
          one_shot|full|no_slip|no_termination|no_forbid/
            summary.csv
            <case_id>/result.json
            <case_id>/run_config.public.json
      baselines/
    ocd62/
      adsmind/
        gpt54_mace_mp0_small/
        claude_sonnet46_mace_mp0_small/
        gemini25pro_mace_mp0_small/
        grok4_mace_mp0_small/
          one_shot|full|no_slip|no_termination|no_forbid/
            summary.csv
            <case_id>/result.json
            <case_id>/run_config.public.json
      baselines/
    summaries/
  advanced_experiments/
    ablation_and_chemical_slip_diagnostics/
    reproducibility/
    force_field_sensitivity/
    case_studies/
```

## 基础实验

基础实验是对齐后的 CMU20 和 OCD62 主评测矩阵：

- 数据集：`cmu20`, `ocd62`
- LLM/力场目录：
  `gpt54_mace_mp0_small`,
  `claude_sonnet46_mace_mp0_small`,
  `gemini25pro_mace_mp0_small`,
  `grok4_mace_mp0_small`
- 变体：`one_shot`, `full`, `no_slip`, `no_termination`, `no_forbid`

AdsMind 结果放在每个数据集的 `adsmind/` 目录下，和 `baselines/` 平级。
每个后端目录下有 `all_variants_summary.csv`，每个变体目录下也有自己的
`summary.csv`，并和 case 结果目录放在一起。

论文和协作者优先查看这个统一汇总入口：

- `basic_experiments/summaries/cmu20_method_comparison.csv`
- `basic_experiments/summaries/cmu20_ablation_4backend.csv`
- `basic_experiments/summaries/ocd62_method_comparison.csv`
- `basic_experiments/summaries/ocd62_ablation_4backend.csv`
- `basic_experiments/summaries/full_vs_one_shot_summary.csv`
- `basic_experiments/summaries/method_comparison_summary.csv`
- `basic_experiments/summaries/method_comparison_table.md`
- `basic_experiments/summaries/method_comparison_table.tex`

非 LLM baseline 放在各数据集的 `baselines/` 目录下。论文主表使用的
Adsorb-Agent 对照实验统一为 GPT-5.4、MACE-MP-0 small，并且每个 case 最多
生成 5 个候选构型：

- `basic_experiments/cmu20/baselines/adsorb-agent/adsorb-agent_gpt54_mace_mp0_small_5config/`
- `basic_experiments/ocd62/baselines/adsorb-agent/adsorb-agent_gpt54_mace_mp0_small_5config/`

旧的 CMU20 未限制候选数 Adsorb-Agent 重跑已从 curated result tree 删除；
自动生成的 method-comparison 表现在强制使用上面的 matched-budget 5-config
目录。

## 进阶实验

进阶实验不再按主矩阵展开，而是按研究问题组织：

- `ablation_and_chemical_slip_diagnostics/ablation_effects/`：Full 与消融变体的配对统计、backend
  agreement 和 reach-Full 表。
- `ablation_and_chemical_slip_diagnostics/chemical_slip_interpretability/`：
  chemical slip 的解释性表格和轨迹。
- `reproducibility/ocd62_overlap12_rerun/`：OCD62 重叠 12 个 case 的重复性实验，
  包括完整的 run1 到 run5、经审计的 run4/run5 拉取日志，以及 N=2/N=3/N=4/N=5
  汇总。
- `reproducibility/cmu20_gpt54_mace_mp0_small_multiseed/`：
  GPT-5.4 CMU20 full-run 在 MACE-MP-0 small 下的多随机种子敏感性。
- `force_field_sensitivity/mace_mp0_large_vs_mace_mp0_small/`：MACE-MP-0 large 与
  MACE-MP-0 small 的力场敏感性检查。CMU20 已完成；这个实验不定义 OCD62 子集。
- `case_studies/dft_iteration_alignment/`：用于 DFT 对齐的 CMU20 case 轨迹导出。
- `case_studies/iteration_convergence/`：迭代过程中 running-best energy 曲线。

重复性汇总可以用以下命令从 run 目录刷新：

```bash
PYTHONPATH=. .venv/bin/python research/analysis/build_ocd62_summary.py
```

## 刷新命令

```bash
.venv/bin/python research/analysis/build_method_comparison_table.py
.venv/bin/python research/analysis/build_ocd62_summary.py
```

论文结果审计所需的结构证据会通过 Git LFS 版本管理：AdsMind 的 `artifacts/`、
relaxation `traj/` 目录、`.xyz`、`.traj`、`.pkl`、精选图片以及经过审计的运行日志。
每个存在原始 `config.json` 的 run 目录旁边都有脱敏后的 `run_config.public.json`，
保留 `git_sha`、`frozen_config` 和 runtime flags 等复现实验字段，但移除 credential
source 相关信息。临时运行噪声，例如 `agent_log.txt`、原始逐进程 `config.json`、
Python bytecode 和未整理的 local scratch output 继续忽略。
