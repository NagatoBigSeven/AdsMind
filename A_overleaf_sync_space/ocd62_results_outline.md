# OCD62 Results 写作大纲

> **总体叙事策略**
> OCD62 不是 CMU20 的"放大版成功案例"，而是**通用性边界测试**。我们刻意选择更复杂、更多样的表面（氧化物、化合物、多元素合金），以检验闭环架构在 CMU20 未覆盖的化学空间中的行为。结果确认了 CMU20 的可靠性结论，但同时暴露出更多"闭环不优于单次尝试"的案例——这些负结果恰恰界定了 AdsMind 的 **operating envelope**。
>
> **版本说明**：本大纲包含两部分内容：
> - **现有数据可写**（基于已完成的 Tier-1 和 12-case Tier-2）
> - **[PENDING] 待补全实验**（假设 Adsorb-Agent、Chemical Slip、DFT、FF Sensitivity、Convergence、Full Multiseed 全部完成后可写）

---

## 3.2 Generalization to the OCD-GMAE62 dataset

### 3.2.0 动机与数据集画像

- **内容**：为什么需要 OCD62？CMU20 仅限 20 例单金属/金属间化合物，而 OCD62 涵盖 62 例氧化物、化合物和合金表面，吸附质从单原子（H, N）到多原子（CH₂CH₂OH, [CH]=O 等）。这是真正的 out-of-distribution generalization test。
- **数据支撑**：列举 surface diversity（从 `method_comparison.csv` 提取：Hf₁₆Zn₄₈, Mo₁₈S₇₂W₁₈, Cd₂₄Pd₂₄ 等），adsorbate diversity。
- **Take-away**：OCD62 的设计意图是压力测试——如果闭环架构仅在一个狭窄领域有效，则其科学价值有限。

---

### 3.2.1 Tier 1: Full-Matrix Evaluation (62 cases, 5 variants, 4 backends)

#### 段落 A：成功率与失败分析

- **内容**：Full 245/248 (98.8%) vs 1-Shot 222/248 (89.5%)。3 例 Full 失败全部集中在 case 053（K₂₀ + C([CH₂])O），GPT-5.4/Gemini/Grok 均发生自然解离；Claude 成功——证明这是**物理结果的后端差异，非系统崩溃**。
- **数据**：从 `ablation_4backend.csv` 提取 case 053 的 4-backend 失败记录；其他失败也均为自然化学结果（dissociation/reaction），`error=None`。
- **Take-away**：Full 在 62 例 diverse 表面上维持 >98% 可靠性，证实 CMU20 结论可推广；1-Shot 的失败率（10.5%）在更复杂表面上略升于 CMU20（8.7%），说明表面多样性确实放大了开环脆弱性。

#### 段落 B：能量改进的量化与异质性

- **内容**：Mean ΔE(1-Shot − Full) = +0.329 eV (median 0.067 eV)。Wilcoxon 高度显著。但**关键转折**：这一均值掩盖了巨大的 case-level 异质性。
- **数据支撑**：
  - **正例**（闭环显著优于 1-Shot）：case 004 (-7.18 vs -6.12, gap 1.05 eV), case 005 (-10.08 vs -9.26), case 021 (-4.92 vs -4.13), case 048 (-11.66 vs -11.34 或更差)。
  - **反例**（1-Shot ≈ 或 > Full）：case 007 (-19.717 vs -19.717, 几乎相同), case 009 (-4.292 vs -4.292, 完全相同), case 050 (-3.504 vs -3.504, 完全相同), **case 008** (Full -7.48 反而比 1-Shot -8.47 差了近 1 eV!)。
- **Take-away**：1-Shot 惩罚在 OCD62 上更大（+0.329 vs CMU20 的 +0.222），但**分布更宽**——存在非 trivial 比例的 case 中，LLM 的首次猜测已足够好，迭代改进无收益。这要求我们从"平均效应"转向"条件效应"分析。

#### 段落 C：消融变体的边缘案例

- **内容**：w/o Slip, w/o Forbid, w/o Term 在 OCD62 上的行为与 CMU20 相似（median ΔE ≈ 0），但出现更多"消融反而更好"的案例。
- **数据支撑**：
  - case 007：no_slip (-19.925) 和 no_termination (-19.717) 均优于 Full (-19.717)。
  - case 008：Full 是所有变体中最差的！no_slip/no_termination/1-shot 均达到 -8.46，Full 仅 -7.48。
  - case 049：no_slip (-8.628) 优于 Full (-8.249)。
- **解释**：这些案例的共同点是 LLM 的**首次 site 猜测即接近最优 basin**，而 Full 的迭代反馈（特别是 FORBID 约束）将搜索限制在了次优区域。
- **Take-away**：FORBID 和 Slip 反馈在"首次猜测正确"的场景下可能过度约束——这是可预测的**可靠性-探索性 trade-off**。我们的方法选择是：宁可牺牲少数边缘案例的能量深度，也要保证整体可靠性。

#### 段落 D：跨后端一致性

- **内容**：Full 的 mean 4-backend range = 0.183 eV；1-Shot = 0.316 eV（1.73× 缩减）。
- **数据**：从 `ablation_4backend.csv` 计算；与 CMU20 的 2.35× 缩减比较，OCD62 的一致性提升幅度较小。
- **解释**：OCD62 表面更复杂（氧化物、多元素合金），LLM 先验的 backend-specific 偏差更难被完全压制。
- **Take-away**：跨后端一致性随表面复杂度递减，但闭环仍提供统计显著的方差缩减。

#### 段落 E：基线对比——暴力采样在深度上的统治力

- **内容**：Random (N=20) 和 Heuristic 在几乎所有 case 上都低于 AdsMind Full。
- **数据**：从 `method_comparison.csv` 提取。例如 case 001: Random -4.57, Heuristic -5.10 vs AdsMind Full best4 -4.28；case 007: Random -20.11, Heuristic -21.61 vs AdsMind -19.79。
- **关键诚实声明**：这些基线使用了 5–25× 更多 relaxations（Random 20, Heuristic median ~56 sites, range 32–126）。
- **Take-away**：OCD62 确认了 CMU20 的核心 trade-off：在固定力场下，能量深度的决定因素是**初始采样广度**，而非推理策略。AdsMind 的价值在于用 ~4 次 relaxation 实现 98.8% 的可靠收敛，而非取代暴力枚举。

#### 段落 E-bis：[PENDING] Adsorb-Agent 直接对比

> **前提**：`baselines/adsorbagent/` 目录完成（见 Data Audit §3.1）。

- **内容**：将 AdsMind Full/1-Shot 与 Adsorb-Agent（当前 SOTA 开环方法）在全部 62 例上直接对比。Adsorb-Agent 作为专业化学工具，在复杂表面上是否保持优势？
- **预期数据**：成功率、最终能量、relaxation 次数三维度对比。
- **叙事功能**：这是 **C3（计算效率）** 和 **C1（可靠性）** 的核心证据。如果 Adsorb-Agent 在 OCD62 上成功率显著下降（如低于 80%），则闭环架构的通用性优势将被放大。
- **Take-away**：AdsMind 用更少的 relaxation 次数和更高的成功率，在 diverse 表面上超越了专业化学开环工具——**通用性本身就是竞争力**。

---

### 3.2.2 Tier 2: Stability Audit

#### 段落 F：双层级设计的必要性

- **内容**：Tier 1 是单次运行；但 hosted LLM 是黑箱随机系统。我们用 OCD62 中 12 例（从 preliminary evaluation 子采样）进行 N=3 独立重复运行，量化 run-to-run 随机性。
- **数据**：`reproducibility_n3.csv`。
- **[PENDING 扩展]**：若完成 full-dataset 62-case multiseed（Data Audit §3.6），则将 12-case 结果作为"保守估计"，并用完整数据强化结论。

#### 段落 G：稳定性是双模态的

- **内容**：240 comparisons（12 cases × 4 backends × 5 variants），131/240 (54.6%) 在 0.01 eV 内一致。
- **数据**：Full only: 27/47 within 0.01 eV; median range ~0.00012 eV, mean range ~0.166 eV（outlier excluded）。
- **关键发现**：存在两个子群体——"稳定核心"（~54% 几乎无方差）和"随机尾部"（不同 run 到达不同 local minima，mean range 可达 >0.5 eV）。
- **Take-away**：Run-to-run 方差不是噪声，而是**真实的多模态势能面探索**。LLM 的随机性在这里是"特征"而非"缺陷"——它允许系统从同一 starting point 探索不同 basin。但这也意味着，单次运行报告的能量不应被过度解读为"唯一答案"。

#### 段落 H：变体间稳定性排序

- **内容**：1-Shot 的稳定性最差（median range 最高），Full 和 w/o Slip 最稳定。
- **数据**：从 `reproducibility_n3.csv` 提取各 variant 的 median range。
- **Take-away**：迭代架构不仅改善平均能量，还压缩了 run-to-run 方差——对 autonomous workflows 至关重要。

---

### 3.2.3 [PENDING] Tier 3: Mechanistic Deep-Dive Diagnostics

> **前提**：以下子节依赖 advanced experiments 完成（Data Audit §3.2–3.5）。
> **定位**：这些可以放入 **SI** 或作为 main text 的 supporting paragraphs，取决于数据丰富度和期刊版面。

#### 段落 I-a：Chemical Slip on Diverse Surfaces [§3.2 PENDING]

- **内容**：CMU20 的 slip 分析显示 Gemini/Grok 在特定表面家族上有较高的 site-disagreement 率。OCD62 的 oxide/compound 表面是否放大了这种现象？
- **预期数据**：`chemical_slip_interpretability/ocd62/slip_analysis.csv`
- **关键对比**：
  - CMU20 slip rate（单金属）：backend-dependent，但总体 <15%
  - OCD62 slip rate（氧化物/化合物）：预期更高，尤其是多元素合金表面（吸附质可能"滑"向不同元素位点）
- **叙事功能**：支撑 **C4（可解释性）**。Slip 不是 bug，而是**物理反馈机制**——它在复杂表面上更频繁地触发，从而更有效地纠正 LLM 的初始猜测。
- **Take-away**：Chemical Slip 的频率与表面化学复杂度正相关；闭环架构通过显式检测这种不匹配，将"错误"转化为"学习信号"。

#### 段落 I-b：Iteration Convergence on Diverse Surfaces [§3.5 PENDING]

- **内容**：CMU20 的迭代收敛曲线显示大多数 case 在前 3 次 relaxation 内达到 plateau。OCD62 的复杂表面是否需要更多迭代？是否存在"延迟收敛"案例？
- **预期数据**：`case_studies/iteration_convergence/ocd62/all_backends/full/iteration_convergence.csv`
- **分析维度**：
  - Median iterations to plateau (CMU20 ≈ 3.2 vs OCD62 expected higher)
  - Case-level outliers：哪些 case 需要 5+ iterations？
  - Backend differences：某些后端是否收敛更慢？
- **Take-away**：收敛速度是**表面复杂度**和**后端质量**的联合函数。Autonomous termination 的价值在于避免过度计算——在已经 plateau 的 case 上不会浪费 relaxation。

#### 段落 I-c：DFT Validation Beyond Single Metals [§3.4 PENDING]

- **内容**：CMU20 case 01 的 DFT 对齐显示 MACE-MP-0 small 的能量排序与 DFT 一致（rank correlation ~0.9），但绝对能量有 systematic offset。OCD62 的氧化物/化合物表面是否保持这种排序一致性？
- **预期数据**：`case_studies/dft_iteration_alignment/ocd62/caseXX/` 的 trajectory CSVs
- **关键问题**：
  - DFT 是否确认 case 053 的 dissociation 是物理真实（而非 MACE 伪影）？
  - DFT 是否验证 negative-result case 008 的能量排序（1-Shot < Full）？
- **叙事功能**：DFT 验证是 **C1（可靠性）** 的外部锚点。如果 DFT 确认 MACE 的定性结论，则力场层面的 negative result 具有物理真实性。
- **Take-away**：DFT 对齐在 OCD62 上验证了 MACE-MP-0 的**排序可靠性**，即使绝对能量存在 offset——这支持将 AdsMind 的 operating envelope 声明建立在物理基础上。

#### 段落 I-d：Force-Field Sensitivity [§3.3 PENDING]

- **内容**：MACE-MP-0 large 是否改变 OCD62 的定性结论？在 12-case stratified subsample 上对比 small vs. large。
- **预期数据**：`force_field_sensitivity/mace_mp0_large_vs_mace_mp0_small/ocd62/gpt54_mace_mp0_large/full/summary.csv`
- **分析维度**：
  - Success rate consistency
  - Energy ranking correlation (small vs. large)
  - Case-level flips（哪些 case 的能量排序被 model size 改变？）
- **Take-away**：如果 large model 不改变核心结论（Full > 1-Shot, reliability maintained），则 AdsMind 的闭环逻辑是**模型无关的**——这是架构层面的鲁棒性。

---

### 3.2.4 Synthesis: Operating Envelope of Closed-Loop Search

#### 段落 J：OCD62 告诉我们的新东西

- **内容**：总结 OCD62 相对于 CMU20 的新发现。
- **要点**：
  1. 可靠性结论通用化（98.8% vs 100%），但 gap 来自更复杂的解离化学。
  2. "负结果"案例比例上升：OCD62 中约有 X% 的案例（如 007, 008, 009, 050）显示 1-Shot ≈ Full，甚至 1-Shot > Full。
  3. 基线差距扩大：Heuristic 在 OCD62 上优势更明显（更复杂的表面有更多 high-symmetry sites 可供枚举）。
  4. 稳定性是双模态的，这是 OCD62 特有的发现。
  5. **[PENDING]** Chemical slip 频率与表面复杂度正相关（若 §3.2 完成）。
  6. **[PENDING]** DFT 验证了排序可靠性（若 §3.4 完成）。
- **Take-away**：OCD62 将 AdsMind 的 operating envelope 界定为：**适用于需要可靠、化学安全、低计算成本的场景；不适用于追求全局能量最小值、可容忍失败的高通量筛选**。这不是缺陷，而是**架构选择**。

---

## 配套图表/表格建议

### Main Text Figures

| 项目 | 内容 | 数据来源 | 状态 |
|------|------|----------|------|
| **Figure 4** | OCD62 双层级总览：Panel a (success rate), Panel b (energy degradation), Panel c (stability bimodal), Panel d (trapezoid ablation) | `ablation_4backend.csv` + `reproducibility_n3.csv` | ✅ 可绘制 |
| **Figure 5** | OCD62 方法对比（含 Adsorb-Agent） | `method_comparison.csv` + `adsorbagent/` [PENDING] | ⏳ 待 Adsorb-Agent 数据 |

### Main Text Tables

| 项目 | 内容 | 数据来源 | 状态 |
|------|------|----------|------|
| **Table X** | OCD62 Tier 1 五变体消融汇总（成功率、Mean ΔE、Median ΔE、Backend range） | `ablation_4backend.csv` | ✅ 可制作 |

### SI Figures & Tables

| 项目 | 内容 | 数据来源 | 状态 |
|------|------|----------|------|
| **SI Table S-X** | Per-case 能量矩阵（4 backends × 5 variants），特别标注"反例"（1-Shot ≥ Full） | `ablation_4backend.csv` | ✅ 可制作 |
| **SI Table S-Y** | Tier 2 N=3 重复运行详细数据 | `reproducibility_n3.csv` | ✅ 可制作 |
| **[PENDING] SI Figure S-Z** | OCD62 Chemical Slip 位点对比图（planned vs. relaxed） | `chemical_slip_interpretability/ocd62/` [PENDING] | ⏳ 待 §3.2 |
| **[PENDING] SI Figure S-W** | OCD62 迭代收敛曲线（4 backends） | `iteration_convergence/ocd62/` [PENDING] | ⏳ 待 §3.5 |
| **[PENDING] SI Figure S-V** | OCD62 DFT 对齐能量曲线 | `dft_iteration_alignment/ocd62/` [PENDING] | ⏳ 待 §3.4 |
| **[PENDING] SI Table S-U** | FF Sensitivity（small vs. large）12-case 对比 | `force_field_sensitivity/ocd62/` [PENDING] | ⏳ 待 §3.3 |
| **[PENDING] SI Table S-T** | Full-dataset multiseed 稳定性统计（若 §3.6 完成） | `reproducibility/ocd62_full_multiseed/` [PENDING] | ⏳ 待 §3.6 |

---

## 写作风格要点（venue-templates + peer-review skills 融合）

### Nature/Science 叙事风格
- **每个 subsection 以一个可独立理解的 take-away 结尾**，便于 skim reading。
- **Story-driven**：OCD62 不是"更大的 CMU20"，而是"边界测试"——这个叙事弧线必须清晰。
- **Broad significance**：解释为什么 operating envelope 的界定对 autonomous materials discovery 领域有意义。

### 负结果的诚实呈现（peer-review skill: objectivity & completeness）
- 不将 case 008（Full 最差）隐藏在 aggregate statistics 中，而是**显式命名**并给出物理解释（"当首次猜测已接近最优 basin 时，FORBID 约束可能过度剪枝"）。
- 在 Figure 4 的 trapezoid plot 中，用不同颜色标注 negative-result cases（007, 008, 009, 050），不让它们淹没在 aggregate 中。
- **Failure cases are data too**：case 053 的 dissociation 不是污点，而是证明框架能安全处理危险化学事件的证据。

### 条件效应分析（venue-templates: condition-specific reasoning）
- 从"平均而言 Full 更好"转向"在什么条件下 Full 更好/不重要/更差"。
- 建议增加一个 **conditional effect diagram**（流程图或决策树）：
  - IF 首次猜测接近最优 basin → 1-Shot ≈ Full（甚至 1-Shot > Full）
  - IF 表面复杂（oxide/compound）AND 吸附质多原子 → Full >> 1-Shot
  - IF 表面有多个 competing sites → Full 通过 FORBID 避免重复探索
- 这种条件化叙事比平均效应更科学，也更诚实。

### 透明度与可复现性（peer-review skill: reproducibility & transparency）
- **数据可用性声明**：明确列出所有 CSV 文件路径（`ablation_4backend.csv`、`method_comparison.csv`、`reproducibility_n3.csv`）。
- **代码可用性**：引用分析脚本版本（`build_ocd62_summary.py`、`build_method_comparison_table.py`）。
- **PENDING 实验的标注**：在 draft 中，所有 pending 数据用 `[PENDING]` 或灰色占位符标注，不混入已验证数据。
- **Error bar 定义**：所有图表必须声明 error bar 类型（SD / SEM / CI）。建议对 backend range 使用 IQR 或 95% CI，对 reproducibility 使用 run range。

### 统计报告规范（peer-review skill: statistical rigor）
- Wilcoxon signed-rank test 报告 **exact p-value**（如 p = 2.3×10⁻⁵），不是 "p < 0.05"。
- 报告 **effect size**（如 median ΔE = 0.067 eV） alongside significance。
- 对非正态分布数据（energy differences 通常是 skewed），明确声明使用了非参数检验。
- 对 multiple comparisons（4 backends × 5 variants），考虑 Bonferroni 或 FDR 校正——若不校正，需声明并解释为什么 uncorrected p-values 仍然有意义（因为方向一致）。

### 图表可访问性（venue-templates + peer-review: accessibility）
- **Colorblind-safe palette**：避免红-绿对比；使用蓝-橙或紫-黄。
- **高对比度**：文字与背景对比度 ≥ 4.5:1。
- **独立可读性**：每个 Figure panel 必须有独立的 title/label，不依赖正文理解。

---

## 写作优先级与依赖关系

```
Tier 1 (可立即写作):
├── 3.2.0 动机与数据集画像
├── 3.2.1 A-E (成功率、能量改进、消融、跨后端一致性、基线)
├── 3.2.2 F-H (12-case 稳定性)
└── 3.2.4 J (综合，不含 pending 要点)

Tier 2 (待 Adsorb-Agent 完成后):
├── 3.2.1 E-bis (Adsorb-Agent 对比)
└── Figure 5 (方法对比)

Tier 3 (待 Advanced Experiments 完成后):
├── 3.2.3 I-a (Chemical Slip)
├── 3.2.3 I-b (Iteration Convergence)
├── 3.2.3 I-c (DFT Alignment)
├── 3.2.3 I-d (FF Sensitivity)
└── 3.2.4 J (扩展 pending 要点 5-6)

Tier 4 (待 Full Multiseed 完成后):
├── 3.2.2 F-H (扩展为 62-case 统计)
└── SI Table S-T
```

---

*End of Outline — v2.0 (Assumed-Complete Expansion)*
