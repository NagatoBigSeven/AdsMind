# Figure 4 重新设计方案 Proposal

> 日期：2026-05-08
> 基于：notebook `figure4_three_tier_overview.ipynb`、论文正文、OCD62_DATA_AUDIT.md、ocd62_results_outline.md

---

## 当前 notebook 的问题

1. **"Three-Tier" 概念已过时。** 论文现在的实验协议是双层（Tier 1: 62-case 全矩阵；Tier 2: 12-case N=3 稳定性），但 notebook 声称三个 tier：
   - 「Tier 2 (24 cases)」是人为制造的——代码取了 case 1-24，这不是任何有意义的子集
   - 真正的 Tier 2（12-case 稳定性）在 notebook 里被叫作「Tier 3」
   
2. **Panel a 展示三个 tier 但 Tier 3 成功率是硬编码的 100%**（代码注释：`# TODO: update with actual Tier 3 success rate`）。而且 Tier 2 的稳定性数据不适合用"成功率"来呈现——Tier 2 衡量的是 run-to-run 方差，不是成功/失败。

3. **Panel b 只有均值。** 当前只显示 Tier 1 和 Tier 2（人造）的 mean ΔE。这完全掩盖了 OCD62 最核心的发现——ΔE 分布的**巨大异质性**。数据审计和写作大纲都反复强调要从「平均效应」转向「条件效应」。

4. **Panel c 用 σ 箱线图。** 按 backend 分组展示 σ 的分布，但 σ 掩盖了 Tier 2 的核心发现——**双模态分布**（稳定核心 ~54% vs 随机尾部 ~46%）。箱线图把这个最有趣的图案平滑掉了。

5. **`load_tier1_tier2_data` 和 `load_ocd62_data` 两套函数重复加载同一数据。** Panel d 用的 `load_ocd62_data` 从 `all_variants_summary.csv` 加载，Panel a/b 用的 `load_tier1_tier2_data` 从 `ablation_4backend.csv` 加载——数据源不同，可能产生微妙的数值不一致。

---

## 重新设计的核心原则

1. **双层结构**——Tier 1 = 62-case 全矩阵（可靠性 + 能量改进），Tier 2 = 12-case N=3（稳定性双模态）
2. **展示异质性而非掩盖它**——分布 > 均值
3. **负面结果可见**——case 008、053 等在图中可辨识
4. **闭环架构是叙事主语**——每个 panel 回答「闭环提供了什么」
5. **诚实**——不伪造数据，不掩盖 caveat

---

## 方案：4-Panel Figure

```
+-------------------+-------------------+
|      (a)          |      (b)          |
|   Success Rate    |  ΔE Distribution  |
|   (Tier 1)        |  (1-Shot − Full)  |
+-------------------+-------------------+
|      (c)          |      (d)          |
|  Stability Audit  |  Ablation Matrix  |
|   (Tier 2)        |   (Tier 1)        |
+-------------------+-------------------+
```

Layout: 2×2 网格。一致性好，每个 panel 信息密度适中。

---

### Panel a — Success Rate: Reliability Generalizes

**要传达的信息：** 闭环架构在 62 个 diverse 表面上维持 >98% 可靠性；1-Shot 在复杂表面上失败率上升。

**数据来源：** `ablation_4backend.csv`，Tier 1，按 variant 聚合

**可视化方案：** 水平条形图，5 个 variant

```
Variant          Success Rate
─────────────────────────────────
Full             ████████████████ 98.8%  (245/248)
w/o Slip         ████████████████ 99.6%  (247/248)
w/o Forbid        ████████████████ 99.2%  (246/248)
w/o Term          ████████████████ 99.6%  (247/248)
1-Shot            ██████████████   89.5%  (222/248)
```

- 闭环变体（前四者）用同一色系（蓝），1-Shot 用对比色（红/橙）
- Annotation 标注 "3 Full failures all in case 053 (K₂₀ + ketene)"
- 可选：旁边放 CMU20 的对比条（灰色虚线）——Full 100% → 98.8%，直观展示 gap

**为什么不按 backend 细分：** 纸面空间有限，backend 差异已在 Panel d（trapezoid）中展示。这里聚焦 variant-level 聚合。

**对比当前 notebook：** 当前 Panel a 展示 Full vs 1-Shot 按 3 个 tier 分组。新方案展示所有 5 个 variant 在 Tier 1 的成功率——更完整，且不再伪造 Tier 2/3。

---

### Panel b — Energy Improvement: Heterogeneity, Not Just Averages

**要传达的信息：** 1-Shot 惩罚在平均意义上是真实的（+0.329 eV, p ≈ 10⁻²⁴），但分布极宽——某些 case 第一猜测已接近最优，某些 case 中闭环大幅改进，极少数 case 中闭环反而更差。

**数据来源：** `ablation_4backend.csv`，Tier 1，variant=one_shot & full

**可视化方案：** 水平散点图 + 小提琴图叠加

```
     case 008 (Full WORSE by ~1 eV) ●
     case 007 (identical) ●
     case 050 (identical) ●
     case 009 (identical) ●
     
     ... 60+ other cases as dots ...
     
     case 004 (Full better by 1.05 eV) ●
     
     │         ●●●  ●●●● ●● ●    ●  ● ●     ●   ●●● ●  ● ●●● ●●
     │    ●●● ●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●
     │  ── violin ── 
     ─┼──────────────────────────────────────────
      -1.0         0.0    +0.329     +1.0      +2.0
                    ΔE = E(1-Shot) − E(Full)  (eV)
```

- 每个点是一个 case（4 backend 聚合后的 mean ΔE，或取 best-across-backends）
- 小提琴图展示分布的形状
- **红色标注** negative-result cases（008, 007, 009, 050）——名称直接标在图上
- **蓝色标注** large-gain cases（004, 005, 021）
- 垂直虚线在 ΔE=0
- Annotation: "mean +0.329 eV, median 0.067 eV, Wilcoxon p = 9.4×10⁻²⁴"
- 可选：case 008 加 callout box 解释"FORBID over-pruning when first guess is near-optimal"

**关键设计决策：** ΔE 究竟是「best-across-4-backends 的 1-Shot − best-across-4-backends 的 Full」，还是「per-backend 然后 mean」？我倾向于 per-case 聚合方式：对每个 case，取 4 个 backend 中 Full 的中位数和 1-Shot 的中位数，然后做差。这样每个 case 一个点，避免 backend-level 噪声。

**对比当前 notebook：** 当前 Panel b 只有两个柱状图（Tier 1 mean 和 Tier 2 mean）。新方案展示了完整的分布 + 标注边缘案例，让「条件效应」叙事可视化。

---

### Panel c — Stability Audit: Bimodal Distribution (Tier 2)

**要传达的信息：** Tier 2 的 12-case N=3 重复运行揭示了**双模态稳定性**——约 54% 的 run 几乎完全一致（<0.01 eV），其余到达不同的 local minima。这不是噪声，是 LLM 随机性驱动的真实多 basin 探索。

**数据来源：** `reproducibility_n3.csv`，variant=full，使用 `range_eV`（= max(e_run1, e_run2, e_run3) − min(...)）

**可视化方案：** 直方图 + 累计比例曲线

```
Count
  │
15│  ██
  │  ██  ← "stable core": 27/47 within 0.01 eV
10│  ██
  │  ██
 5│  ██                                      █
  │  ██                                  █   █
 0│  ██__ __ __ __ __ __ __ __ __ __ __ __ __ ██__ __ 
      0        0.01      0.1        0.5       1.0
              Run-to-run energy range (eV)
```

- 直方图 bins：0–0.001, 0.001–0.01, 0.01–0.05, 0.05–0.1, 0.1–0.5, 0.5–1.0, 1.0+
- 第一条 bin（0–0.01 eV）占 57.4%（27/47），用蓝色填充标注「stable core」
- 剩余 bin 用灰色或渐变，标注「stochastic tail」
- 累计比例曲线叠加在右侧 y 轴
- Annotation:
  - "27/47 (57.4%) within 0.01 eV"
  - "Median range: 0.00012 eV"
  - "Mean range: 0.166 eV (1 outlier excluded)"
- 可选：按 backend 做 stacked histogram，但纸面空间可能不够——建议先做聚合版

**对比当前 notebook：** 当前 Panel c 是按 backend 分组的 σ 箱线图。箱线图掩盖了双模态——这是 OCD62 最独特的发现之一。直方图直接展示两个群体。

---

### Panel d — Ablation Trapezoid: Backend × Variant Patterns (Tier 1)

**要传达的信息：** 四个消融变体在四个后端上的 ΔE 分布——闭环架构的 guardrail trade-off 是跨后端一致的。

**数据来源：** `ablation_4backend.csv` 或 `all_variants_summary.csv`

**可视化方案：** **保留当前 trapezoid 设计**——这是一个信息密度高且视觉清晰的方案。

需要修改的细节：
- 横轴标签（variant label）已经合适：1-Shot, w/o Slip, w/o Forbid, w/o Term
- 纵轴 ΔE = E(variant) − E(Full)
- 四个后端颜色保持（蓝 Gemini, 绿 Grok, 红 GPT, 黄 Claude）
- 参考线 ΔE=0（虚线）、±0.5 eV（点线）
- **新增**：在图上标注几个 outlier 案例 ID（case 008 在 1-Shot 远低于 ΔE=0 的位置，case 053 导致的失败等）

**对比当前 notebook：** 这个 panel 的设计本身没有问题。数据加载路径需要统一（用 `ablation_4backend.csv` 而非 `all_variants_summary.csv`），函数命名和注释需要清理。

---

## 数据加载方案

**统一数据源：** 所有 panel 从同一个 `ablation_4backend.csv` 和 `reproducibility_n3.csv` 加载。不再有两套重复加载逻辑。

```python
# 单一数据加载
df_ablation = pd.read_csv("ablation_4backend.csv")      # Tier 1: 1240 rows
df_repro    = pd.read_csv("reproducibility_n3.csv")     # Tier 2: 240 rows

# Panel a: df_ablation → group by variant → success rate
# Panel b: df_ablation → variant=one_shot & full → compute per-case ΔE → distribution
# Panel c: df_repro → variant=full → range_eV histogram
# Panel d: df_ablation → variant≠full → delta_eV computation → trapezoid
```

---

## 与论文正文的对齐

当前论文 Figure 4 caption（`3_Results.tex` 行 161）描述的是 3-panel 版本。需要更新为：

```latex
\caption{\textbf{Two-tier evaluation overview on OCD-GMAE62.} 
(a) Success rates across Tier~1 ablation variants, with Full achieving 98.8\% reliability on 62 diverse surfaces versus 89.5\% for 1-Shot. 
(b) Per-case energy degradation $\Delta E = E_{\mathrm{1-Shot}} - E_{\mathrm{Full}}$ (Tier~1), revealing substantial heterogeneity masked by the +0.329~eV mean; negative-result cases (007, 008, 009, 050) where 1-Shot matches or outperforms Full are highlighted. 
(c) Run-to-run stability audit on Tier~2 (12 cases, N=3 repeated runs, Full variant): 57.4\% of comparisons agree within 0.01~eV, but the distribution is bimodal---a stable core and a stochastic tail reflecting genuine multi-basin exploration. 
(d) Ablation analysis across four LLM backends and four ablated variants (Tier~1), showing $\Delta E = E_{\mathrm{variant}} - E_{\mathrm{Full}}$ distributions; trapezoid bodies span IQR, medians are solid lines, and mean values are diamonds.}
\label{fig:ocd62-two-tier}
```

---

## 优先级与实施顺序

| 步骤 | 内容 | 难度 | 依赖 |
|------|------|------|------|
| 1 | 重构数据加载——统一两个数据源，删除 `load_tier1_tier2_data` 和 `load_ocd62_data` | 低 | — |
| 2 | 重做 Panel a——5 变体成功率条形图 | 低 | 步骤 1 |
| 3 | 重做 Panel b——ΔE 分布小提琴图 + 标注负面案例 | 中 | 步骤 1 |
| 4 | 重做 Panel c——range_eV 直方图（双模态） | 低 | 步骤 1 |
| 5 | 保留 Panel d——清理 trapezoid，统一数据源 | 低 | 步骤 1 |
| 6 | 更新论文 caption | 低 | 步骤 2–5 |

---

## 备选/简化方案

如果 4-panel 对期刊来说信息过密，可考虑：

**3-panel 方案（合并 a 和 d）：**
- Panel a: Success rate + 小型 trapezoid inset
- Panel b: ΔE 分布
- Panel c: 稳定性双模态

但个人建议保留 4-panel——OCD62 有足够多的独立发现需要各自的空间。

---

## 开放问题

1. Panel b 中 ΔE 的聚合方式——per-case mean across backends？best-across-backends？median？需要你决定。当前论文正文用的 mean ΔE 是 aggregate over all successful (case, backend) pairs，所以如果 panel b 要跟正文数字对齐，每个 case 应该取 4-backend mean（或只取成功的 backend），然后对所有 case 取分布。

2. Panel c 的直方图——需要排除 outlier 吗？当前 `reproducibility_n3.csv` 的 `agreement_class` 列标记了 `severe`（如 case 001 backend gpt，range 2.7 eV）。建议排除 `agreement_class == "severe"` 的行，与论文正文的「1 outlier excluded」一致。

3. Panel d 需要标注哪些 case ID？case 008（最极端的负结果）和 case 053（失败集群）是最重要的两个。在 trapezoid 上标 case ID 可能会影响可读性——或许只保留颜色标注而不用文字。

---

*2026-05-08 下午*
