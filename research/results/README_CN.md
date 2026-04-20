# research/results/ — 数据清单（中文版，零基础扩展版）

> 英文版：[README.md](README.md)。中文版是给中文协作者作图和审稿用的扩展导读；英文版是精简 manifest。两份文件的关键路径、variant 名称和数据口径应保持一致，但不逐段等长。除非特别说明，本文所有路径都按仓库根目录相对路径书写。

---

## 0. 先读这个：当前数据口径

### 0.1 一句话说明

**AdsMind 是一个 "LLM agent + 物理工具层" 的闭环吸附构型搜索系统**。输入一个分子（SMILES）和一个催化剂表面（slab），agent 会提出吸附构型，用 MACE 力场弛豫，然后根据 slip、解离、FORBID 违规和终止判断继续迭代，目标是找到低能吸附结构。

传统对照大致分两类：
- **人工试错**：研究员手动放置 top / bridge / hollow 等位点，再跑 DFT 或 MLFF。慢，且可能漏构型。
- **批量候选搜索（如 Adsorb-Agent）**：一次性生成许多候选构型，再用 MLFF 打分。覆盖面大，但构型数更多，也更难解释每一步为什么发生。

AdsMind 的区别是：**每轮只提议少量构型，弛豫后把物理诊断反馈给 LLM，再由 LLM 决定下一轮**。因此本文档看数据时要同时看两个维度：能量质量和搜索/诊断行为。

### 0.2 当前能被数据支持的主张

| 编号 | 主张 | 当前数据源 | 注意事项 |
|---|---|---|---|
| C1 可靠性与搜索成本 | AdsMind 在 CMU 15-case MACE 对齐比较中成功率高、构型/迭代数少；Adsorb-Agent 在其成功的可比 case 上通常能量更低。 | `adsorbagent_mace_gpt54/comparison.csv` | 不能写成 "AdsMind 能量不比 Adsorb-Agent 差"。当前 12 个可比能量对中 Adsorb-Agent 全部更低。 |
| C2 后端收敛 | 4 个 LLM 后端在 full 闭环下比 single-shot 更一致。 | 四个 CMU `*_ablation_v*/ablation_summary.csv`；`paper_tables.tex` | `analysis/cross_llm_ablation_with_openai.csv` 不是完整 4 后端 15-case 表。 |
| C3 泛化 | OCD-GMAE 10-case 独立验证集有 4 后端完整消融结果。 | `ocd_gmae_ablation_multi_backend_final.csv` 和四个 `ocd_gmae_*_ablation_v*/ablation_summary.csv` | 宽表已按当前 per-backend CSV 重建。 |
| C4 机制消融 | full 相对 `single_shot` 的收益最稳定；单独去掉 slip / FORBID / termination 的影响依赖 case 和 backend。 | `si4_ablation_statistics.tex`、`si4_ocd_gmae_ablation_statistics.tex`、各 `ablation_summary.csv` | 不要写成 "任意去掉一个机制都会显著下降"。当前单机制消融有时能量相同或更低。 |

### 0.3 三个容易踩坑的命名

| 名称 | 正确理解 |
|---|---|
| `*_one_shot/summary.csv` | 独立的 one-shot 运行目录。每个 case 只做 1 次 LLM 提议 + 1 次 MACE 弛豫。 |
| `single_shot` | 消融 CSV 里的 variant 名称，也是消融子目录名 `single_shot/`。作图过滤消融表时用 `variant == "single_shot"`，不是 `one_shot`。 |
| `analysis/cross_llm_ablation_with_openai.csv` | 历史/便捷拼接表：当前只有 3 后端（Gemini、Grok-4、GPT-5.4）× 5 cases × 5 variants = 75 行。不是完整 4 后端 15-case 数据源。 |

---

## 1. 名词对照表

### 1.1 催化 / 结构

| 术语 | 含义 |
|---|---|
| adsorbate | 被吸附的分子或片段，如 H、OH、NNH。 |
| slab / surface | 催化剂表面周期性模型，如 Pt(111)、Cu3Ag(111)。 |
| configuration | 一个具体吸附几何，包括位点、朝向和初始距离。 |
| adsorption energy / binding energy | 吸附能，单位 eV。通常越负越稳定，但不同数据集的绝对范围不同，不能只用 "-0.5 到 -3 eV" 判断是否合理。 |
| relaxation | 力场结构弛豫，把初始几何推向局部能量极小。 |

### 1.2 方法

| 术语 | 含义 |
|---|---|
| MACE | 本项目主要使用的机器学习力场。主结果为 MACE-MP-0 small，`mace_large_gpt54/` 是 large 敏感性检查。 |
| backend | LLM 后端。CMU/OCD-GMAE 消融涉及 Gemini 2.5 Pro、Grok-4、GPT-5.4、Claude Sonnet 4.6。 |
| slip 诊断 | 判断弛豫后吸附物是否偏离 LLM 提议位点。 |
| FORBID 约束 | 基于化学合理性的禁用规则，用于排除明显不合理的构型。 |
| autonomous termination | agent 认为已经收敛时停止，避免继续跑无用迭代。 |
| variant | 消融变体：`full`、`no_slip`、`no_forbid`、`no_termination`、`single_shot`。 |

---

## 2. 数据全景

```
research/results/
├── CMU 15-case 消融（每个后端 75 行）
│   ├── gemini_ablation_v1/ablation_summary.csv
│   ├── xai_ablation_v2/ablation_summary.csv
│   ├── openai_gpt54_ablation_v1/ablation_summary.csv
│   └── anthropic_sonnet46_ablation_v1/ablation_summary.csv
├── CMU 20-case 独立 one-shot（每个后端 20 行）
│   ├── cmu_v1_gemini_one_shot/summary.csv
│   ├── cmu_v1_xai_progressive_one_shot/summary.csv
│   ├── cmu_v1_openai_gpt54_one_shot/summary.csv
│   └── cmu_v1_anthropic_sonnet46_one_shot/summary.csv
├── OCD-GMAE 10-case 消融
│   ├── ocd_gmae_*_ablation_v*/ablation_summary.csv
│   └── ocd_gmae_ablation_multi_backend_final.csv
├── OCD-GMAE rep50 one-shot
│   └── ocd_gmae_rep50_v1_*_one_shot/summary.csv
├── Adsorb-Agent 对比
│   ├── adsorbagent_mace_gpt54/comparison.csv
│   └── adsorbagent_mace_gpt54/adsorbagent_mace_summary.csv
├── 非 LLM 基线
│   ├── random_baseline_n20/summary.csv
│   └── heuristic_baseline/summary.csv
└── analysis/ 与 *.tex
    └── 拼接分析表、论文/SI 导出表、历史诊断 JSON
```

权威优先级建议：
- 画 CMU 4 后端 15-case 消融图：优先拼四个 `*_ablation_v*/ablation_summary.csv`。
- 画 OCD-GMAE 4 后端概览：优先用 `ocd_gmae_ablation_multi_backend_final.csv`。
- 画 AdsMind vs Adsorb-Agent：优先用 `adsorbagent_mace_gpt54/comparison.csv`。
- 使用 `analysis/` 或 `.tex` 前，先确认它们是否是从当前 CSV 重新导出的派生结果。

---

## 3. CSV 怎么读

### 3.1 Agent one-shot `summary.csv`

CMU/OCD-GMAE one-shot 目录里的 `summary.csv` 典型列名如下：

| 列名 | 含义 |
|---|---|
| `case_id` | case 编号。CMU 为 1-20；OCD-GMAE 可能显示为 1-50 或 3、4、5 等整数。 |
| `slab_file`, `smiles`, `adsorbate_name` | 输入体系信息。 |
| `status` | `success` 或 `failed`。 |
| `best_energy_eV` | 最佳吸附能，单位 eV。 |
| `iteration_count` | one-shot 目录中通常为 1。 |
| `chemical_slip_count`, `dissociation_count` | 诊断事件计数。 |
| `total_input_tokens`, `total_output_tokens` | LLM token 统计。 |
| `best_structure_file`, `relaxation_trajectory_file` | 本地 provenance 路径；公开检出中通常没有对应 artifact。 |

注意：非 LLM 基线的 `summary.csv` 列名不同，如 `best_energy`、`n_random`、`n_sites`、`successful`、`failed`。

### 3.2 消融 `ablation_summary.csv`

每行是一个 `(case_id, variant)` 结果。所有 CMU/OCD-GMAE 消融表的核心列一致：

| 列名 | 含义 |
|---|---|
| `case_id`, `variant` | case 编号和变体名。variant 使用 `single_shot`，不是 `one_shot`。 |
| `best_energy` | 最佳吸附能，单位 eV。 |
| `delta_vs_full` | `best_energy - 同 backend 同 case 的 full best_energy`。正值表示该 variant 比 full 更高能/更差；负值表示该 variant 更低能。 |
| `iterations` | agent 循环次数。 |
| `wasted_iterations`, `waste_ratio` | 收敛后继续运行的冗余迭代。 |
| `success` | 是否成功完成。 |
| `slip_count`, `dissociation_count` | 诊断事件计数。 |
| `tokens_used` | 总 token 数。 |

### 3.3 能量范围不要硬套

CMU 的 H/OH/NNH case 常在 -0.5 到 -7 eV；复杂吸附物和 OCD-GMAE case 可以低到 -10 eV 以下。当前汇总文件中没有正能量成功结果，但也不能把 "小于 -3 eV" 当作异常。判断异常时优先看：
- `status` / `success`
- `dissociation_count`
- `chemical_slip_count` 或 `slip_count`
- case 的 adsorbate 类型和数据集来源

---

## 4. 快速开始

### 4.1 AdsMind vs Adsorb-Agent（15 行，12 个可比能量对）

```python
import pandas as pd

cmp = pd.read_csv("research/results/adsorbagent_mace_gpt54/comparison.csv")
print(cmp[[
    "case_id",
    "adsmind_best_energy",
    "adsorbagent_best_energy",
    "adsmind_iterations",
    "adsorbagent_configs_tested",
    "energy_diff",
    "winner",
]])
```

关键口径：
- `energy_diff = adsmind_best_energy - adsorbagent_best_energy`。
- `energy_diff > 0` 表示 AdsMind 能量更高，Adsorb-Agent 更低。
- 当前文件：AdsMind 成功 15/15；Adsorb-Agent 成功 12/15；12 个可比能量对中 `winner` 均为 `adsorbagent`。
- 当前文件更适合支撑“AdsMind 成功率/搜索成本/诊断行为”对比，不适合支撑“AdsMind 能量优于 Adsorb-Agent”。

### 4.2 CMU 4 后端 × 15 case × 5 variant 消融（300 行）

```python
import pandas as pd

sources = {
    "gemini": "research/results/gemini_ablation_v1/ablation_summary.csv",
    "grok4": "research/results/xai_ablation_v2/ablation_summary.csv",
    "openai_gpt54": "research/results/openai_gpt54_ablation_v1/ablation_summary.csv",
    "anthropic_claude": "research/results/anthropic_sonnet46_ablation_v1/ablation_summary.csv",
}

ab = pd.concat(
    [pd.read_csv(path).assign(backend=backend) for backend, path in sources.items()],
    ignore_index=True,
)
print(ab.shape)  # (300, 12)

heatmap = ab.pivot_table(
    index=["backend", "variant"],
    columns="case_id",
    values="best_energy",
)

ranges = (
    ab.pivot_table(index=["case_id", "variant"], columns="backend", values="best_energy")
      .assign(range_eV=lambda x: x.max(axis=1) - x.min(axis=1))
)
```

变体过滤示例：

```python
full = ab[ab["variant"] == "full"]
single = ab[ab["variant"] == "single_shot"]
```

不要在消融表里写 `variant == "one_shot"`，当前 CSV 没有这个取值。

### 4.3 OCD-GMAE 4 后端泛化（50 行宽表）

```python
import pandas as pd

ocd = pd.read_csv("research/results/ocd_gmae_ablation_multi_backend_final.csv")
print(ocd.shape)  # (50, 30)
print(ocd.groupby("variant")["range_best_energy"].describe())

ocd[[
    "case_id",
    "variant",
    "gemini_delta_vs_full",
    "grok_delta_vs_full",
    "gpt54_delta_vs_full",
    "claude_delta_vs_full",
]]
```

关键列：
- `case_id`, `variant`
- `{gemini,grok,gpt54,claude}_best_energy`
- `{gemini,grok,gpt54,claude}_delta_vs_full`
- `{gemini,grok,gpt54,claude}_success`
- `range_best_energy`
- `success_backends`, `failed_backends`

### 4.4 CMU main table WIP

`analysis/cmu_benchmark_table.csv` 当前是 CMU 20-case one-shot 表，只含 Gemini 和 Grok-4 列。不要把它当作 CMU 4 后端 15-case 消融主表。需要 4 后端消融时用 4.2 的拼接方式。

---

## 5. 按论文表 / 图索引

### 5.1 已导出的 LaTeX 表

| 文件 | 内容 | 当前使用建议 |
|---|---|---|
| `paper_tables.tex` | CMU 4 后端消融表、cross-LLM summary、关键指标、H1 表 | 与 15-case per-backend CSV 口径一致性较高；如改 CSV 后需重导出。 |
| `ocd_gmae_paper_tables.tex` | OCD-GMAE 4 后端消融和 cross-LLM 表 | 与当前 per-backend CSV 和 `ocd_gmae_ablation_multi_backend_final.csv` 一致。 |
| `si4_ablation_statistics.tex` | CMU 消融统计表 | 与当前 15-case per-backend CSV 和 `si4_ablation_statistics.json` 一致。 |
| `si4_ocd_gmae_ablation_statistics.tex` | OCD-GMAE 消融统计表 | 可用于 SI 展示，改 CSV 后需重导出。 |
| `si6_cost_analysis.tex` | token / wall-clock 成本 | 数据来自 `si6_cost_analysis.json`。 |
| `si_adsorbagent_comparison.tex` | AdsMind vs Adsorb-Agent 对比 | 核心源是 `adsorbagent_mace_gpt54/comparison.csv`。 |
| `si_baselines_comparison.tex` | Random / Heuristic / Adsorb-Agent / AdsMind | 核心源是 `analysis/baselines_comparison.json`。 |
| `si_iteration_convergence.tex` | 迭代收敛 | 核心源是 `analysis/iteration_convergence.csv`。 |
| `si_mace_sensitivity.tex` | MACE small vs large | 核心源是 `mace_large_gpt54/ablation_summary.csv`。 |

### 5.2 作图推荐数据源

| 图主题 | 推荐数据源 |
|---|---|
| AdsMind vs Adsorb-Agent 成功率、能量、构型数 | `adsorbagent_mace_gpt54/comparison.csv` |
| CMU 4 后端 × 5 variant 热图/boxplot | 四个 CMU `*_ablation_v*/ablation_summary.csv` 拼接 |
| CMU one-shot 后端差异排名 | `analysis/cmu_one_shot_range_ranking_new_cases.csv` |
| OCD-GMAE 4 后端泛化 | `ocd_gmae_ablation_multi_backend_final.csv` |
| OCD-GMAE full vs single-shot range 改善 | `ocd_gmae_ablation_final_vs_one_shot_4backend.csv` |
| 迭代收敛曲线 | `analysis/iteration_convergence.csv` |
| Case-19 代表性轨迹 | `analysis/case19_trajectory.csv` |
| Slip 事件统计 | `analysis/slip_analysis.csv` |
| Pipeline / 概念图 | `assets/pipeline.png`、`assets/adsmind_concept.png` |

---

## 6. 按实验索引

### 6.1 CMU 15-case 消融

| 后端 | 文件 | 行数 |
|---|---|---|
| Gemini 2.5 Pro | `gemini_ablation_v1/ablation_summary.csv` | 75 |
| Grok-4 | `xai_ablation_v2/ablation_summary.csv` | 75 |
| GPT-5.4 | `openai_gpt54_ablation_v1/ablation_summary.csv` | 75 |
| Claude Sonnet 4.6 | `anthropic_sonnet46_ablation_v1/ablation_summary.csv` | 75 |

每个文件包含 15 cases × 5 variants。当前 variants 为：
`full`、`no_slip`、`no_forbid`、`no_termination`、`single_shot`。

### 6.2 CMU 20-case 独立 one-shot

| 后端 | 文件 |
|---|---|
| Gemini 2.5 Pro | `cmu_v1_gemini_one_shot/summary.csv` |
| Grok-4 | `cmu_v1_xai_progressive_one_shot/summary.csv` |
| GPT-5.4 | `cmu_v1_openai_gpt54_one_shot/summary.csv` |
| Claude Sonnet 4.6 | `cmu_v1_anthropic_sonnet46_one_shot/summary.csv` |

补充：
- `cmu_v1_openai_gpt54_one_shot_retry/summary.csv` 只含 case 06 和 08 重跑。
- `cmu_v1_gemini_one_shot_epfl_control/summary.csv` 与 `cmu_v1_xai_progressive_one_shot_epfl_control/summary.csv` 是 EPFL slab 对照，各 2 行。

### 6.3 OCD-GMAE 10-case 消融

| 后端 | 文件 |
|---|---|
| Gemini 2.5 Pro | `ocd_gmae_gemini_ablation_v2/ablation_summary.csv` |
| Grok-4 | `ocd_gmae_xai_grok4_ablation_v1/ablation_summary.csv` |
| GPT-5.4 | `ocd_gmae_openai_gpt54_ablation_v1/ablation_summary.csv` |
| Claude Sonnet 4.6 | `ocd_gmae_anthropic_sonnet46_ablation_v1/ablation_summary.csv` |
| 宽表汇总 | `ocd_gmae_ablation_multi_backend_final.csv`、`ocd_gmae_ablation_multi_backend_final.json` |
| full vs single-shot | `ocd_gmae_ablation_final_vs_one_shot_4backend.csv` |

### 6.4 OCD-GMAE rep50 one-shot

**"rep50" 命名易误解**：不是"50 次重复"，而是 **50 个 case 每 case 跑 1 次** one-shot。case_id 为 1–50（整数连续），每个后端 50 行。6.3 的 10-case 消融是从这 50 个 case 里选的子集。

| 后端 | 文件 | 行数 |
|---|---|---|
| Gemini 2.5 Pro | `ocd_gmae_rep50_v1_gemini_one_shot/summary.csv` | 50 |
| Grok-4 | `ocd_gmae_rep50_v1_xai_grok4_one_shot/summary.csv` | 50 |
| GPT-5.4 | `ocd_gmae_rep50_v1_openai_gpt54_one_shot/summary.csv` | 50 |
| Claude Sonnet 4.6 | `ocd_gmae_rep50_v1_anthropic_sonnet46_one_shot/summary.csv` | 50 |

### 6.5 Adsorb-Agent 对比

| 文件 | 用途 |
|---|---|
| `adsorbagent_mace_gpt54/comparison.csv` | 当前主对比：15 行，12 个可比能量对。 |
| `adsorbagent_mace_gpt54/adsorbagent_mace_summary.csv` | Adsorb-Agent MACE 替代运行的 20-case 原始汇总。 |
| `adsorbagent_mace_gpt54/comparison_stats.json` | 配对统计；注意 `energy_diff_definition` 是 `adsmind_best_energy - adsorbagent_best_energy`。 |
| `adsorbagent_mace_gpt4o/` | GPT-4o 历史对照。 |
| `analysis/adsorbagent_paper_results.csv` | Adsorb-Agent 原论文 EquiformerV2 数据，不与 MACE 能量直接比较。 |
| `analysis/adsmind_vs_adsorbagent_behavioral.csv` | 行为维度对比，含 token、slip、状态等。 |

### 6.6 基线、鲁棒性和敏感性

| 实验 | 文件 |
|---|---|
| Random baseline | `random_baseline_n20/summary.csv`、`random_baseline_n20/summary.json` |
| Heuristic baseline | `heuristic_baseline/summary.csv`、`heuristic_baseline/summary.json` |
| 多种子 GPT-5.4 | `multiseed_gpt54/seed_{43,44,45,46}/ablation_summary.csv` — **不是完整消融**，每个种子只跑 `variant=full` × 3 cases（`[16, 17, 18]`），4 个种子共 12 行。仅用于 case 16/17/18 在 full 配置下的种子稳定性检查。 |
| MACE large 敏感性 | `mace_large_gpt54/ablation_summary.csv` — **只 `variant=full` × 5 cases**（`[5, 14, 16, 18, 20]`），不是 5-variant 消融；case 20 能量为 NaN（弛豫失败）。与 `openai_gpt54_ablation_v1/` 里同 case 的 small-MACE full 行 join 即得 small vs large 对比。 |

---

## 7. analysis/ 文件清单

| 文件 | 当前用途 |
|---|---|
| `analysis/cmu_benchmark_table.csv` | CMU 20-case one-shot 表，只有 Gemini/Grok-4 列。 |
| `analysis/cross_llm_20case_with_openai.csv` / `.json` | CMU 20-case one-shot 拼接，**只含 3 后端**（OpenAI GPT-5.4、Gemini、Grok-4）。无 Claude 列。宽表，22 列。 |
| `analysis/cross_llm_20case_4backend.json` | CMU 20-case one-shot 的 4 后端版本（含 Claude）。嵌套 JSON：`metadata`（backends、total_cases）/ `per_case` / `summary`。需要 Claude one-shot 数据时用这个，不是 `.csv`。 |
| `analysis/cross_llm_ablation_with_openai.csv` / `.json` | 3 后端 × 5 cases × 5 variants 的历史/便捷拼接。不要当 4 后端 15-case 权威源。 |
| `analysis/cross_llm_unified_range_table.csv` | 当前 CMU 15-case 与 OCD-GMAE 10-case 的统一 range 表。 |
| `analysis/cross_llm_unified_summary.json` | 当前 CMU 15-case 与 OCD-GMAE 10-case 的跨 LLM summary。 |
| `analysis/cmu_one_shot_range_ranking_new_cases.csv` / `.json` | CMU one-shot 后端 range 排名。 |
| `analysis/ocd_gmae_one_shot_range_ranking.csv` / `.json` | OCD-GMAE one-shot 后端 range 排名。 |
| `analysis/ocd_gmae_one_shot_top_10_case_ids.txt` | OCD-GMAE Top 10 case ID。 |
| `analysis/iteration_convergence.csv` / `.json` / `.png` | 迭代收敛数据、summary 和现成图。 |
| `analysis/slip_analysis.csv` / `.json` | Slip 事件清单。 |
| `analysis/case19_trajectory.csv` / `.json` | Case-19 逐步轨迹。 |
| `analysis/baselines_comparison.json` | 基线 vs AdsMind 拼接。 |
| `analysis/adsmind_vs_adsorbagent_behavioral.csv` | AdsMind vs Adsorb-Agent 行为对比。 |
| `analysis/adsorbagent_paper_results.csv` | Adsorb-Agent 原论文 EquiformerV2 结果。 |

---

## 8. 顶层 JSON 和派生表注意事项

| 文件 | 注意事项 |
|---|---|
| `cross_llm_ablation_4backend.json` | 4 后端 × 5 cases × 5 variants 的消融快照（含 Claude）；不是 15-case 全量。需要含 Claude 的消融数据时，首选拼接 4 个 per-backend CSV（见 4.2），这个 JSON 只作补充。 |
| `hypothesis_test.json` | 早期 H0/H1 假设检验记录。`notes` 字段明确写 "locked 5-case ablation subset"，`backend_results` **只有 Gemini、Grok-4 两个后端**，不含 GPT-5.4 / Claude。不要直接当当前论文主表源。 |
| `key_evaluation_metrics.json` | 早期关键指标快照。子字段用 `*_full_5case` 与 `*_1shot_20case` 命名，**只覆盖 Gemini、Grok-4 两个后端**。不要直接当当前 15-case / 4 后端权威源。 |
| `si4_ablation_statistics.json` | CMU 15-case 消融统计源，与 `si4_ablation_statistics.tex` 同口径。 |
| `si4_ocd_gmae_ablation_statistics.json` | OCD-GMAE 10-case 统计源。 |
| `si6_cost_analysis.json` | 成本分析源。 |

---

## 9. 公开版瘦身说明

仓库保留论文相关的汇总表、拼接分析文件和 LaTeX 导出表。原始 `result.json`、agent 日志、轨迹和结构文件已从公开树移除；需要完整审计链路时，从 `research/agent_eval/` 重跑 manifest。

2026-04-19 移除或不再跟踪的内容包括：
- `analysis/cross_llm_20case.{csv,json}`，由 `analysis/cross_llm_20case_with_openai.{csv,json}` 取代。
- `analysis/cross_llm_ablation_comparison.{csv,json}`，由 `analysis/cross_llm_ablation_with_openai.{csv,json}` 取代。
- `analysis/cmu_one_shot_range_ranking.{csv,json}`，由 `analysis/cmu_one_shot_range_ranking_new_cases.{csv,json}` 取代。
- `ocd_gmae_gemini_ablation_v1/`，由 `ocd_gmae_gemini_ablation_v2/` 取代。
- 各运行目录下的 `result.json`、agent log、结构和轨迹文件。

Summary CSV 中的 artifact 路径只作为 provenance 标记；公开仓库中默认不存在这些 artifact 文件。

---

## 10. 给作图者的检查清单

画图前先确认：
- 用消融表时，variant 过滤值是 `single_shot`。
- 用 CMU 4 后端 15-case 消融时，从四个 per-backend CSV 拼接，不用 `analysis/cross_llm_ablation_with_openai.csv`。
- 用 Adsorb-Agent 对比时，`energy_diff > 0` 表示 Adsorb-Agent 能量更低。
- 用 `.tex` 或诊断 JSON 时，先确认它是不是从当前 CSV 重新导出的最新派生结果。
- 能量图标注单位为 eV，并说明越负越稳定。

---

## 11. 有问题问谁

- 数据 / 统计 / 消融逻辑：Nagato
- DFT 校验：Bowen 师兄
- 方法 / 理论：HKUST + EPFL 导师
- 图的视觉呈现：娄宇阳师兄
