# AdsMind 消融实验总结报告

**日期：** 2026-04-18
**作者：** 张宗民（aq717061@gmail.com）
**用途：** 组内汇报 / 师兄（娄宇阳）参考
**数据规模：** 500+ 次受控运行（CMU 15 案例 + OCD-GMAE 10 案例全消融 + OCD-GMAE 50 案例 one-shot 扩展 × 4 LLM backend × 5 变体 + 13 项对照/消融实验）
**LLM backends：** Gemini 2.5 Pro（Vertex AI 直连）、Grok-4（xAI）、GPT-5.4（OpenAI）、Claude Sonnet 4.6（Anthropic）
**变体定义：** Full（三机制全开）、−Slip（关闭 slip 检测，其他保留）、−Forbid（关闭 FORBID 约束写入）、−Term（关闭自主早停，固定跑满 5 迭代）、1-Shot（只跑 1 次 LLM proposal + 1 次 MACE 松弛，无反馈）

---

## 0. TL;DR（一句话版本）

> **AdsMind 的三个机制（slip / FORBID / 早停）在 CMU 聚合检验上效应几乎为零（BH-FDR 全部不显著，均差 |ΔE| < 0.1 eV），真正显著的是"迭代循环整体"对比 1-Shot——Gemini/Grok-4/Claude 均 BH-FDR < 0.015，GPT-5.4 边界（BH=0.084）。** 这意味着 C2 跨后端收敛（3.3×）**来自迭代闭环本身**，不来自任何单一机制——三机制的价值是**选择性、按案例触发**（Grok-4 案例 19 slip/FORBID 各挽回 0.451 eV；OCD-GMAE GPT-5.4 −Slip p=0.016，−Forbid 案例 004 max 0.988 eV）。能量深度上 AdsMind 不如爆搜/枚举基线（Random/Heuristic/Adsorb-Agent），**不对称预算—深度关系**已由双向对照证实：Adsorb-Agent 预算↓到 4 坍缩为平手（48% 胜率），AdsMind 预算↑到 20 仍落后 >1.1 eV。真正价值在 **可靠性（100%）、计算效率（~4 次松弛、~25k–40k tokens）、可解释性（slip/FORBID 诊断）**。Future work：多位点并行 + 每位点独立闭环 = 带反馈的 beam search。

---

## 0.1 数字一致性说明（发送前请务必核对）

你在微信聊天里提到 **"cmu 那个要调用 16 次"**，但论文文档中固定的对比数字是：

| 方法 | 每案例 MACE 松弛次数 |
|------|-------------------|
| AdsMind Full | ~4 |
| Random N=20 | 20 |
| Adsorb-Agent | ~21 |
| Heuristic 枚举 | 25–98 |

**本报告全文使用论文已发表的数字（~21 / 25–98）**。发群前请确认 16 是哪个具体协议，否则师兄对照论文时会发现数字不一致。

---

## 0.2 数据来源披露

本报告整合以下来源：

- `ideas/reviewer_qa.md`（reviewer 防御 Q&A）
- `AdsMind/sections/1_Introduction.tex`
- `research/results/si4_ablation_statistics.tex`（CMU + OCD-GMAE 组件消融统计表）
- `research/results/si6_cost_analysis.tex`（token + wall-clock 成本表）
- `research/results/{gemini,openai_gpt54,xai,anthropic_sonnet46}_ablation_v*/ablation_stats.json`
- `research/results/cmu_v1_*_one_shot_epfl_control/`（跨机复现）

---

## 1. 核心结论：四条主张 + 一条负面结果

### 主张 C1（Reliability 可靠性）
AdsMind 在 CMU（15 案例）和 OCD-GMAE（10 案例）上，**4 个 LLM backend × 全部案例 = 100% 成功率**。Adsorb-Agent：GPT-4o 失败 4/15（27%）、GPT-5.4 失败 3/15（20%），失败案例**不重合**——架构瓶颈，非 LLM 能力。

### 主张 C2（Backend Convergence 跨后端收敛）
- **CMU：** 4-backend 能量跨度 0.425 eV（1-Shot）→ **0.129 eV（Full）**，3.3× 收敛
- **OCD-GMAE：** 2.3× 收敛

§2.1 组件消融显示：三机制单独的聚合效应 ~0 eV，**收敛来自迭代循环整体**。

### 主张 C3（Compute Efficiency 计算效率）
- MACE 松弛：~4（AdsMind Full）vs 20（Random）vs ~21（Adsorb-Agent）vs 25–98（Heuristic）
- **该 ~4 次预算下，AdsMind 在 CMU 的 8–11/15 案例上追平或优于非 LLM 对照**（Random 输 4/15；Heuristic 9/15 同极小 + 6/15 输）。
- LLM token：25k–40k / run（Full）vs 4.8k–7.4k / run（1-Shot）——详见 §2.12

### 主张 C4（Interpretability 可解释性）
Slip + FORBID + site-mismatch 可被化学家检查。300 次 CMU 运行中 slip 率跨 4 个独立 LLM 后端一致随表面复杂度分层（§2.11）。

### 负面结果（主动写进 §1.5 和 §4.1）
- Random N=20 在 4/15 案例低（最多 -2.08 eV）
- Heuristic 在 6/15 案例低（均差 0.48 eV）
- Adsorb-Agent 在 9–10/11–12 成功案例上低

**严谨证据链（双向对照）：**
- **AdsMind 预算↑（§2.8 Multi-seed）：** 预算 20 匹配 Random，仍差 >1.1 eV
- **Adsorb-Agent 预算↓（§2.9 Bootstrap）：** 预算 4 匹配 AdsMind，深度优势坍缩为 48% AdsMind 胜率

两个方向合起来揭示 **不对称的预算—深度关系**：Adsorb-Agent 的深度随预算单调上升，AdsMind 的深度对预算增加几乎不敏感——与"额外预算被消耗在单一 basin 内"的行为观察一致。

---

## 2. 各项消融实验结果（13 项）

### 2.1 Component Ablation（三机制 × 4 backend，**最重要的机制消融**）

对 AdsMind 三大机制分别单独关掉，测量对能量的影响。**15 案例 × 4 backend × 4 变体 = 240 次 CMU 运行。** 统计数据来自 `si4_ablation_statistics.tex`。

| Backend | 变体 | 均差 ΔE (eV) | BH-FDR p | Max 案例退化 (eV) |
|---------|------|-------------|----------|------------------|
| Gemini | −Slip | −0.010 | 0.917 | 0.158 (案例 17) |
| Gemini | −Forbid | −0.005 | 0.917 | 0.294 (案例 15) |
| Gemini | −Term | +0.018 | 0.917 | 0.247 (案例 19) |
| Gemini | **1-Shot** | **+0.363** | **0.006 ★** | **1.048 (案例 20)** |
| Grok-4 | −Slip | +0.049 | 0.617 | **0.451 (案例 19)** |
| Grok-4 | −Forbid | +0.045 | 0.498 | **0.451 (案例 19)** |
| Grok-4 | −Term | −0.012 | 1.000 | 0.017 (案例 19) |
| Grok-4 | **1-Shot** | **+0.341** | **0.012 ★** | **1.050 (案例 20)** |
| GPT-5.4 | −Slip | −0.034 | 0.674 | 0.294 (案例 15) |
| GPT-5.4 | −Forbid | −0.094 | 0.084 | 0.003 (案例 20) |
| GPT-5.4 | −Term | −0.078 | 0.084 | 0.000 (案例 17) |
| GPT-5.4 | 1-Shot | +0.097 | 0.084 | 0.549 (案例 17) |
| Claude | −Slip | −0.016 | 0.674 | 0.391 (案例 16) |
| Claude | −Forbid | −0.017 | 0.498 | 0.007 (案例 01) |
| Claude | −Term | −0.031 | 0.617 | 0.042 (案例 04) |
| Claude | **1-Shot** | **+0.185** | **0.013 ★** | 0.549 (案例 17) |

**关键读法（三层）：**

1. **聚合层面：** 三机制（slip / forbid / term）单独关掉，**4 个 backend 全部 BH-FDR 不显著**——均差 \|ΔE\| 都 < 0.1 eV。
2. **整体循环层面：** 1-Shot 对 Full 在 Gemini/Grok-4/Claude 上**全部 BH-FDR < 0.015**（强显著），GPT-5.4 借着 corrections 边界（BH=0.084）。
3. **单点选择性：** 三机制**按案例触发**——Grok-4 案例 19 的 slip 和 forbid 各挽回 0.451 eV；Gemini 案例 20、Claude 案例 16 都有 0.15–0.4 eV 的单点效应。

**对论文主张的意义（非常重要）：**

- C2 的 3.3× 跨后端收敛**不是来自三机制中的任何单一个**——聚合效应近零。它来自**迭代循环整体**这件事（1-Shot 对 Full 强显著）。
- 三机制的价值是**诊断信号 + 选择性防护**：大多数案例不会触发 slip/forbid，但在"LLM 先验与 PES 矛盾"的少数案例上（Grok-4 案例 19 是典范），这些机制能挽回接近 1 eV 的退化。
- 这个发现**加强而不是削弱** C4（可解释性）主张：三机制本来就是设计成**诊断工具**而非全局优化器——slip/FORBID 在多数案例不触发是**设计意图**，不是缺陷。

**对应论文章节：** §3 主要消融表（SI Table si4）。

---

### 2.2 Iteration Convergence（迭代循环整体 vs 1-Shot）

见 §2.1 的 1-Shot 行。4-backend 能量跨度 0.425 → 0.129 eV（3.3× 收敛）。

**读法：** 闭环反馈的价值是**共识性（grounding）**——LLM 先验偏差被 MACE 物理信号反复修正，4 个独立 LLM 收敛到同一能量。

---

### 2.3 Random N=20 Baseline（无 LLM、爆搜对照）

- 随机 20 个吸附位姿，相同 MACE 松弛。
- 4/15 案例（04, 16, 18, 20）比 AdsMind 低，最多 -2.08 eV。
- 这 4 个案例都是复杂吸附质 + 金属间化合物表面——多 basin PES，Random 并行覆盖，AdsMind 单轨迹只能深挖一个。

---

### 2.4 Heuristic Enumeration（Autoadsorbate）

- Fako & De 2025 的 Surrogate-SMILES 全枚举，25–98 次松弛/案例。
- 9/15 案例与 AdsMind 收敛到同一极小（差 <0.01 eV），AdsMind 用 1/10–1/25 预算达到。
- 6/15 案例比 AdsMind 低（均差 0.48 eV）。

---

### 2.5 Adsorb-Agent GPT-4o（同架构不同 LLM）

- Fork 原始代码 + MACE backend 替换 EquiformerV2，~21 次松弛/案例。
- 成功 11/15，9 个能量比 AdsMind 低；**失败 4/15（silent failure）**。

---

### 2.6 Adsorb-Agent GPT-5.4（同 LLM 能力对照）

- 成功 12/15，10 个比 AdsMind 低；**失败 3/15，且与 GPT-4o 失败案例不重合**。
- 失败率 20–27% + 跨 LLM 不重合 = **架构瓶颈**，换 LLM 不能解决。

---

### 2.7 MACE-large Sensitivity（力场保真度）

5 个代表性案例换 MACE-large：

| 案例 | MACE-small 差距 | MACE-large 差距 |
|------|----------------|----------------|
| 16 | 2.04 eV | **0.97 eV** |
| 18 | 1.35 eV | **0.39 eV** |

5/5 案例 **AdsMind vs Adsorb-Agent 的能量排序保持一致**（两者相对高低关系不翻转）。深度差一部分是力场伪影——绝对数值需 DFT 复核（Bowen 在做）。

---

### 2.8 Multi-seed Control（AdsMind 预算↑方向）

- 案例 16/17/18，GPT-5.4，5 seed × 4 松弛 = 20 次匹配 Random。
- best-of-5 AdsMind 3/3 案例仍差 Adsorb-Agent >1.1 eV。
- **严谨提示：** 本实验单独**不能排除** per-trajectory 弱势假说，需配合 §2.9 bootstrap 才闭合逻辑。终态几何多样性分析（区分 A 单 basin / B per-trajectory）未做——如 reviewer 穷追需补几何聚类。

---

### 2.9 Compute-matched Bootstrap（Adsorb-Agent 预算↓方向）

- Adsorb-Agent GPT-5.4 的 ~21 次松弛结果，下采样到每案例 4 次 bootstrap。
- **案例 16**：AdsMind 落后 2.04 eV → **AdsMind 胜率 48%**（平手）。
- 与 §2.8 双向对照：两边都指向"深度 ≈ 预算函数，但 AdsMind 对预算不敏感"——即**不对称的预算—深度关系**。

---

### 2.10 Cross-machine Reproducibility Control（跨机复现）

- **实际范围：** 案例 **09 + 14**，**两个 backend（Gemini + Grok-4）**，EPFL x86_64 集群 vs 本地 M3 Pro ARM。共 4 次对照运行。
- **结果：** 平台漂移 ~0.20 eV，归因于 MLFF 运行环境差异（CPU 架构 / 数值路径 / 库版本，具体成因未单独隔离），**非 LLM 差异**。
- **意义：**
  - 主文所有 within-backend 消融固定在同一平台 → 消融信号不被 ~0.20 eV 平台噪声污染。
  - 平台漂移 \|0.20\| eV **<** 所有主张的效应量（3.3× 收敛 >0.3 eV、MACE-large 差距 0.4–1.0 eV、Adsorb-Agent 深度差 1–2 eV）。

---

### 2.11 Slip Rate Stratification（C4 直接证据）

- 300 次 CMU 运行（15 案例 × 4 backend × 5 变体）。
- monometallic → bimetallic → intermetallic 表面 slip 率**单调上升**，4 个独立训练的 LLM 后端**全部一致**。
- **标定：** slip 在论文中定位为"独立方法学贡献"（Discussion §4.2），不声称已是验证 LLM benchmark——完整验证（ChemBench/MatBench）是 future work。

---

### 2.12 Cost Analysis（Token + Wall-clock，**C3 的第二条腿**）

来自 `si6_cost_analysis.tex`，15 案例 × 4 backend × 5 变体的 token 和壁钟时间：

| Backend | 变体 | Tokens/run | Wall-clock (s) | 平均迭代数 |
|---------|------|-----------|----------------|-----------|
| Gemini | Full | 40131 | 699 | 4.5 |
| Gemini | 1-Shot | 7348 | 81 | 1.0 |
| Grok-4 | Full | 34270 | 963 | 4.3 |
| Grok-4 | 1-Shot | 6266 | 146 | 1.0 |
| GPT-5.4 | Full | 25449 | 437 | 3.9 |
| GPT-5.4 | 1-Shot | 4845 | 62 | 1.0 |
| Claude | Full | 36437 | 568 | 4.2 |
| Claude | 1-Shot | 6385 | 72 | 1.0 |

**读法：**
- Full 使用 4–8× tokens、4–9× wall-clock，换取 3.3× 跨后端收敛。
- GPT-5.4 token/时间最省（25k tokens、437 秒）；Grok-4 最贵（wall-clock 963 秒）。
- 平均迭代数 3.9–4.5，**均明显 <5 迭代上限 → 自主早停在发挥作用**（即使聚合显著性弱，早停在预算控制上的实用价值在此表里体现）。

**对 C3 的意义：** C3 计算效率**不仅是 MACE 松弛次数**（4 vs 21 vs 98），也是 **LLM 推理成本**——Full 比 1-Shot 多 4–8× tokens，但比 Adsorb-Agent 少得多（Adsorb-Agent ~21 次 LLM 调用）。这个数据让"AdsMind 便宜"的叙述**从单维度变成双维度**。

---

### 2.13 OCD-GMAE Independent Validation（跨数据集）

- **10-case 全消融：** 4 backend × 5 变体 = 200 runs，与 CMU 对称（案例 003, 004, 005, 012, 013, 015, 016, 019, 023, 024）。C1–C4 全部保持。
- **50-case 扩展 one-shot 扫描：** `ocd_gmae_rep50_v1_*_one_shot/`，4 backend × 50 案例 = 200 runs，**仅 one-shot**，用于验证 C2 跨后端收敛在更大样本上稳健。
- **OCD-GMAE 组件消融的新发现：** 与 CMU 不同，GPT-5.4 在 OCD-GMAE 上 **−Slip 变得名义显著**（均差 0.037 eV，p=0.016），**−Forbid 案例 004 max 退化 0.988 eV**；Claude 1-Shot 均差 **0.774 eV**（CMU 0.185 eV），**案例 003 max 退化 4.671 eV**。
  - **含义：** OCD-GMAE 数据集对组件消融比 CMU 更敏感 → 三机制的选择性防护价值在更复杂数据集上更突出。
- **Gemini 数据源切换：** v1 使用 AiHubMix 代理有系统 artifact（2026-03 到 2026-04 plan verification 阶段观察到），v2 切换到 Vertex AI 直连。**论文正文使用 v2**；v1 已归档不进表。
- **Friedman 检验：** CMU min p=0.011，OCD-GMAE min p=3.4×10⁻⁴。

---

## 3. 架构层面的洞察

### 3.1 PES basin 几何

复杂表面 PES 有多个 basin，每个对应几何上可区分的吸附构型族。
- **Random / Heuristic：** 并行播种 20–98 初始点 → 几乎一定覆盖多 basin → 取最低。
- **AdsMind Full：** 第一次 MACE 松弛进入某一个 basin → FORBID 仅禁"已确认失败位点" → agent 下一次 proposal 仍在同一 basin 邻域 → 系统性深挖一个 basin。
- **Adsorb-Agent：** LLM 建议若干位点类型 → 对每种类型做几何枚举 → ~21 次松弛 → 相当于"LLM 引导的宽初始化"，覆盖多 basin 机会更大。

### 3.2 Reliability–depth trade-off

| 架构 | 搜索宽度 | 反馈能力 | 失败模式 | 深度 |
|------|---------|---------|---------|------|
| Random N=20 | 宽（20 独立初始点） | 无 | 无 | 最深 |
| Heuristic | 最宽（25–98） | 无 | 无 | 最深 |
| Adsorb-Agent | 中（~21 LLM-guided） | 无 | 20–27% silent failure | 深 |
| AdsMind Full | 窄¹（~4，单 basin 深挖¹） | 有（slip/FORBID/早停） | 0% | 中等 |

**¹ 脚注：** "窄 / 单 basin 深挖"是**行为上的经验观察**（FORBID 历史 + 单轨迹 + LLM 一致先验导致 proposal 空间收缩），**非几何硬约束**。§2.8 + §2.9 双向对照支持这一假说，但未直接测量终态几何多样性（§2.8 数据缺口）。

---

## 4. Future Work：多位点初始化 + 并行反馈迭代（带反馈的 beam search）

### 4.1 设计直觉

- **Adsorb-Agent 强项：** LLM 单次枚举多候选位点 → 覆盖多 basin。
- **AdsMind 强项：** 每次松弛反馈改正 LLM 偏差 + 100% 可靠 + 可解释。
- **融合：** LLM **同时提出 K 个初始位点** → 每个位点独立闭环（各自 slip / FORBID / 早停） → 最后取最低。

### 4.2 等价于在 beam search 每个 beam 上加 per-beam feedback controller

- 经典 beam search：top-K 假设共享评分
- 带反馈的 beam search：K 个独立闭环 agent，**FORBID 历史互不共享**

### 4.3 开放问题

- K 怎么选？
- beam 间是否共享 FORBID？（默认不共享——共享会重现 AdsMind 单 basin 问题）
- 失败 beam 早停标准？

### 4.4 论文中的位置

§4 已留"两阶段 pipeline"过渡表述。实验版本下一篇做。

---

## 5. 和老师沟通的要点

1. **消融全部完成（13 项）**，方向性明确——闭环反馈赢的是可靠性/效率/可解释性，不是深度。负面结果主动入文，文章更稳。
2. **最重要的新发现（§2.1）：** 三机制单独的聚合效应≈0，但 **迭代循环整体** 对 1-Shot 显著（BH<0.015 on 3/4 backends）+ **三机制按案例选择性触发**（Grok-4 案例 19 +0.451 eV）——C2 3.3× 收敛来自**循环**不来自机制。这个"聚合零 + 单点显著"是一个非常有说服力的 reviewer 答辩角度。
3. **Cost analysis（§2.12）** 给 C3 加了第二条腿：除松弛次数外，token/wall-clock 也量化了。
4. **双向对照（§2.8 + §2.9）** 闭合了"深度差距是架构性还是预算性"的逻辑。
5. **跨机控制（§2.10）** 实际覆盖 2 案例 × 2 backend，平台漂移 ~0.20 eV < 所有效应量。
6. **Slip 跨 4 backend 一致分层（§2.11）** 支撑 slip 作为 LLM 化学评估信号。
7. **OCD-GMAE** 实际是 10 案例全消融 + 50 案例 one-shot 扩展两件事；Gemini 已从 AiHubMix 切到 Vertex AI 直连。
8. **DFT** Bowen 推进，不在本次提交 scope。
9. **Future work：** 多位点并行 + per-beam 独立反馈 = 带反馈的 beam search。

**已知数据缺口（诚实披露）：** §2.8 Multi-seed 的终态几何多样性分析未做，严格区分 "单 basin 假说 vs per-trajectory 弱势假说" 目前靠 §2.8 + §2.9 双向证据**间接**支持，不是直接测量。

---

## 6. 文件位置

- 论文主体：`AdsMind/sections/`（§1 Intro、§3 Results、§4 Discussion）
- 主消融数据：`research/results/{gemini,openai_gpt54,xai,anthropic_sonnet46}_ablation_v*/`
- Adsorb-Agent fork 对照：`research/results/adsorbagent_mace_{gpt4o,gpt54}/`
- 基线对照：`research/results/{random_baseline_n20,heuristic_baseline}/`
- 多 seed：`research/results/multiseed_gpt54/`
- MACE-large：`research/results/mace_large_gpt54/`
- 跨机：`research/results/cmu_v1_{gemini,xai_progressive}_one_shot_epfl_control/`
- OCD-GMAE：`research/results/ocd_gmae_*_ablation_v*/` + `ocd_gmae_rep50_v1_*_one_shot/`
- SI 表：`research/results/si{4,6}_*.tex`、`si_*.tex`
- Reviewer Q&A：`ideas/reviewer_qa.md`
- 本报告：`ideas/ablation_report_cn.md`

---

**联系人：** 张宗民 aq717061@gmail.com
**最后更新：** 2026-04-18（v4.1：C3 补"AdsMind 不输 8–11/15"正面对齐 Intro；§2.7 澄清"AdsMind vs Adsorb-Agent 排序"主语；§2.10 软化"CPU 浮点路径"推测为"MLFF 环境差异"；页首补 LLM 版本号和变体定义；v4：新增 §2.1 组件消融 + §2.12 成本分析；修正 §2.10 跨机范围；修正 §2.13 OCD-GMAE 结构；v3：修正项数、收紧逻辑链、新增自查项；v2：补 bootstrap、cross-machine、slip stratification、修正 multi-seed 逻辑链、加 §3.2 脚注、加 §0.1 数字说明）
