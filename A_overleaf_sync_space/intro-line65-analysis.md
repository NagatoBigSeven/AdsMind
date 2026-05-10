# Introduction 行65批注 — 完成度分析与待修改项

> **批注原文**（Introduction line 65）：
> "我依旧认为这后续的有关本文亮点的内容是有失偏颇的，我建议你根据后续结果和discussion的内容，重新思考这部分是应该highlight我们的closed loop框架，简单mention这些小技术就可以，但我们需要在method里面定义这些东西"

---

## 一、批注的三层显性要求——已完成

| # | 要求 | 状态 | 对应改动 |
|---|------|------|----------|
| ① | highlight 闭环框架（而非机制细节） | ✅ | enumerate 3机制 → 5-agent 流动段，闭环=叙事主语 |
| ② | 简要 mention 三个机制 | ✅ | slip / FORBID / termination 各一句话 |
| ③ | 机制在 Method 中定义 | ✅ | Summarizer 新增小节；5 agent 全覆盖 |

---

## 二、批注的隐含第四层——未完成

> "根据后续结果和discussion的内容，重新思考"

### 2.1 Discussion 的核心框架

Discussion 用 **四个属性的协同出现（co-occurrence）** 定义贡献，而非"修复三种失败模式"：

| Discussion 的 C₁–C₄ | 内容 |
|---------------------|------|
| **C₁ 可靠性** | CMU20 100%、OCD-GMAE62 98.8%、320/320 iterative |
| **C₂ 后端收敛** | 2.3× 方差缩减（0.153 vs 0.359 eV） |
| **C₃ 计算效率** | ~4 relaxations/case vs 20–98（5–25×） |
| **C₄ 可解释性** | slip events、forbid constraints、site-mismatch fingerprints；Chemical Slip 作为独立评估信号 |

Discussion 的核心叙事句：

> "closed-loop reasoning provides a **different axis of improvement**—reliability, efficiency, and interpretability simultaneously—that brute-force methods cannot match"
>
> "AdsMind's novelty is their **co-occurrence**"

### 2.2 Introduction 当前对应的叙事

Introduction 行 70–75：

> "closing the feedback loop systematically mitigates the **three failure modes** of single-pass planning"
>
> "LLM-driven reasoning can detect and recover from its own errors"

**差距：**

1. **叙事框架不同** — Introduction 用"修复三种失败模式"（反应式、bug-fix 叙事）；Discussion 用"四个属性协同出现，开辟新轴"（贡献式、contribution 叙事）
2. **后端收敛和计算效率在 Introduction 结尾完全缺失** — Introduction 只提了可靠性+负面结果，C₂ 和 C₃ 没有出现
3. **"自修复错误"的语言** — 这是 bug-fix 框架，不如 Discussion 的"新轴贡献"有力

### 2.3 孤儿概念

Introduction 的"three failure modes"在 Discussion 中从未被援引。Discussion 有自己的框架（C₁–C₄），不使用这个语言。

> scientific-writing skill："Orphaned concept — idea introduced in one section but never used elsewhere"

---

## 三、需要修改的具体内容

**文件**：`1_Introduction.tex`
**范围**：行 70–75（Introduction 结尾段）

**原则**：不是重写，是重新定位——把同样的事实，用 Discussion 的框架说出来。

### 3.1 当前文本

```latex
We demonstrate this framework across 44 surfaces spanning monometallic, intermetallic, oxide, and compound systems, evaluated with four distinct LLM backends (Gemini~2.5~Pro, Grok~4, GPT~5.4, and Claude~Sonnet~4.6) under matched MACE-MP-0 physics, and benchmarked against conventional baselines (random enumeration, heuristic enumeration) and the open-loop LLM baseline Adsorb-Agent~\cite{ock2026adsorbagent}.
The results show that closing the feedback loop systematically mitigates the three failure modes of single-pass planning, achieving consistent reliability gains across surfaces where open-loop approaches prove brittle.
This work establishes AdsMind as a generalizable foundation for autonomous adsorption configuration search, demonstrating that LLM-driven reasoning, when coupled with physical feedback, can detect and recover from its own errors without requiring exhaustive enumeration.
Explicit reporting of negative results on energy depth clarifies the operating envelope---the conditions under which closed-loop LLM reasoning improves reliability without necessarily finding the global energy minimum---in which this architecture adds value.
```

### 3.2 修改方向

四个改动：

| 序号 | 改动 | 说明 |
|------|------|------|
| 1 | "mitigates the three failure modes" → 替换 | 改为 co-occurrence of four properties 的叙事，对齐 C₁–C₄ |
| 2 | 补充后端收敛和计算效率 | 2.3× 方差缩减 + 5–25× 弛豫减少，这两个在 Introduction 末尾目前缺失 |
| 3 | "detect and recover from its own errors" → 替换 | 改为"provides a different axis of improvement" 的贡献式语言 |
| 4 | Operating envelope 保留但调整衔接 | 保留负面结果的自律表述，但改为从"新轴"框架自然引出 |

### 3.3 拟改写方向（讨论后可实施）

核心思路：把四个属性写成一两句（不要枚举），operating envelope 保留为收尾。

关键叙事要素：
- 四个协同属性：100% 可靠性 + 2.3× 后端收敛 + 5–25× 效率 + 物理可解释性
- 新轴贡献：不是替代 brute-force，而是提供 brute-force 做不到的
- 负面结果自律：operating envelope 框架（已好，保留）

---

## 四、其他已完成的修改（本日汇总）

### 4.1 Introduction

- 科学动机扩充（1句→4句段落）
- 5-agent + 3机制 enumerate → 流动段
- (i)(ii)(iii) 贡献列表 → 流动文
- AI 修改草稿采纳，旧注释删除
- `44 surfaces` 标记 `% [REVIEW: 44 vs 82]`

### 4.2 Method

- Summarizer 新增小节（之前缺失——Intro 提 5 agent，Method 只定义 4 个）
- Planner 段收敛逻辑 → 归位到 Summarizer 段
- N=5 修正

### 4.3 Results

- OCD-GMAE62 两层级协议表格 → 正文（按 AI 批注）
- Adsorb-Agent 移到 ablation 前面
- Adsorb-Agent: 5 `\paragraph` + `\textbf{First/Second/Third}` → 2 个流畅段落
- Ablation: 8 `\paragraph` → 4 个流畅段落
- 全部 `\textbf{Take-away}:` → 融入自然收尾句
- 统计段：碎句 → 过渡连接
- 闭环为叙事主语的强化（四刀）
- Caption 精简

---

## 五、待处理

| 项目 | 位置 | 优先级 |
|------|------|--------|
| Introduction 结尾对齐 Discussion co-occurrence 框架 | Intro 行 70–75 | 🔴 高 |
| `44 surfaces` 数字验证 | Intro 行 71 | 🟡 中 |
| `1.4O28` 笔误确认 | Results Adsorb-Agent 段 | 🟡 中 |
| Introduction 行 65 的 `%[AI...` 批注是否删除 | Intro 行 65 | 🟢 低（验证后删） |

---

*2026-05-07 深夜*
