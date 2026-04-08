# AdsMind 论文综合分析与 Outline

## 一、当前状况总结

### 项目发生了什么变化

| 变化 | 旧 | 新 |
|------|---|---|
| 项目名 | AdsKRK | **AdsMind** |
| 论文位置 | `zongmin_project/main.tex` | `AdsMind/main.tex`（空壳） |
| 团队 | 你一个人写 | 你 + 博文(DFT) + 宇阳(图/写) + Sherry(管理/改) |
| PI 态度 | Philippe 不回邮件 | Philippe 给了**明确方向**（见下） |
| 目标期刊 | 不确定 | npj Comp Mat（首选）/ JCIM / Digital Discovery |
| 截止 | 模糊 | **5月底开始投稿**，12月前 accepted |

### Philippe 给的四个明确要求

1. **DFT 验证**：3-5 个关键表面做 single-point 或 full relaxation（博文负责）
2. **和 Adsorb-Agent 做 head-to-head 对比**（你负责跑）
3. **消融研究**：量化 Chemical Slip / FORBID / 自主终止各组件贡献（你负责跑）
4. **大幅增加 references + 正文图表**

### 会议纪要确定的主图方案

| 图号 | 内容 | 负责人 |
|------|------|--------|
| Fig 1 | 架构图 | 宇阳 |
| Fig 2 | CMU 测试集结果（20 表面，MLFF only） | 你 |
| Fig 3 | 上下文/工作流 | 宇阳 |
| Fig 4 | 复现高分期刊结果 + DFT 验证 | 博文 + 你 |
| Fig 5 | Adsorb-Agent 做不对但 AdsMind 能做对的 case | 你 |

---

## 二、⚠️ 发现的问题

### 1. `outline.tex` 放错了

`AdsMind/outline.tex` 的内容是**大气化学的论文大纲**（"Modeling Soft Boundaries in Atmospheric Chemistry"），不是 AdsMind 的。这是 Sherry 另一个项目的文件，**需要删除或移走**。

### 2. 所有 section 文件是空的

`AdsMind/sections/` 下的 5 个 `.tex` 文件全部为空。论文还没开始写。

### 3. Sherry 的两个 proposal 过于庞大

- `Draft_AdsKRK论文改进计划.md`：规划了 34 个 SI 图表，5 个 DFT tier——对本科毕业论文来说不现实
- `Draft_DFT验证实验执行细则.md`：1075 行的 DFT 教程——博文用得上，但体系选择需要调整

**关键矛盾**：Sherry 的 proposal 里计划的 DFT 体系（CO/Pt(111), H₂O/Cu(111), 苯酚等）和你已有的 benchmark 数据（Mo₃Pd, Ru₃Mo, CuZnO 等）**完全不重叠**。需要决定：是跑新体系还是验证旧体系。

**我的建议**：DFT 验证应该基于你**已有的 MLFF 结果**，而不是从头跑全新体系。Philippe 说的是 "Validating the putative global minima on 3–5 key surfaces"——验证你已经找到的最优结构，不是从零开始跑新体系。

---

## 三、之前工作的价值评估

### 仍然有价值的（保留）

| 文件 | 位置 | 价值 | 用途 |
|------|------|------|------|
| `results/01-19` | 项目根目录 | **核心数据** | 所有 MLFF benchmark 结果，是论文的数据基础 |
| `benchmark_slabs/*.xyz` | 项目根目录 | **必需** | 所有表面结构文件 |
| `table1_data.md` | `zongmin_project/` | **高价值** | 19 表面数据整理，可直接生成 Table 1 |
| `generate_figures.py` | 项目根目录 | **部分有价值** | 统计图脚本，需要适配新配色 |
| `CuZnO.txt` | `zongmin_project/` | **高价值** | CuZnO 案例的完整日志 |
| `LLM Results.xlsx` | `zongmin_project/` | **高价值** | 9 个 LLM 偏见测试数据 |
| `vesta_rendering_guide.md` | `zongmin_project/` | **中等** | VESTA 操作清单 |

### 部分有价值的（需要适配）

| 文件 | 价值 | 说明 |
|------|------|------|
| `zongmin_project/main.tex`（旧草稿） | **文本可参考** | 3 个 case study 叙事、Chemical Slip 概念描述、benchmark 分析——这些文字经过了仔细验证，可以作为新草稿的素材 |

### 没有价值的（不保留）

| 文件 | 说明 |
|------|------|
| `AdsMind/outline.tex` | 错误文件（大气化学），删除 |
| `zongmin_project/` 下的 Springer 模板文件 | 旧模板，现在用 revtex4-2 |

---

## 四、论文 Outline（基于所有人的意见综合）

### 整合逻辑

Philippe 的要求 + 会议纪要 + Sherry 的结构建议 + 博文的体系选择 → 以下 outline：

---

### Abstract (~150 words)
- 问题：LLM 在吸附构型预测中普遍存在化学推理偏差
- 方法：AdsMind，闭环 MLFF 反馈 + Chemical Slip 检测 + FORBID 约束
- 结果：20 表面 benchmark + DFT 验证 + 与 Adsorb-Agent head-to-head
- 亮点数字：X% 成功率，Y eV MLFF-DFT 一致性

### 1. Introduction
- 1.1 吸附构型搜索的重要性（催化、能源）
- 1.2 传统方法（枚举/启发式）的局限
- 1.3 LLM 驱动方法的兴起 → Adsorb-Agent 及其局限（开环、过滤异常、无反馈）
- 1.4 我们的贡献：AdsMind（闭环、物理反馈、自纠正）
- **关键措辞**：不攻击 Adsorb-Agent，而是说"互补" → 他们做了 search space reduction，我们做了 iterative refinement

### 2. Methods
- 2.1 AdsMind 框架概述（→ Fig 1 架构图）
  - LLM Planner → AutoAdsorbate → MACE-MP relaxation → Analysis → Feedback loop
- 2.2 Chemical Slip 检测
  - 定义：初始预测位点 vs 弛豫后位点的位移
  - 阈值和分类
- 2.3 FORBID 约束
  - 避免重复探索已知次优区域
- 2.4 自主终止逻辑
  - 收敛判据：连续 N 轮无改善
- 2.5 计算细节
  - MACE-MP-0 medium, float64, FIRE optimizer, fmax=0.01
  - DFT: PBE-D3(BJ), ENCUT=500, EDIFFG=-0.02（博文的部分）

### 3. Results
- **3.1 CMU Benchmark 复现**（→ Fig 2 + Table 1）
  - 20 表面（同 Adsorb-Agent），AdsMind 结果
  - 以你 `table1_data.md` 的 19 表面数据为基础
  - 加上博文建议的重点体系：Mo₃Pd(H + NNH), CuPd₃(NNH), Pt(111+100)(OH), CoPt(OH), Al₃Zr(OCHCH₃)

- **3.2 与 Adsorb-Agent 的 Head-to-Head 对比**（→ Fig 5 + Table 2）
  - 能量对比：AdsMind 找到更低能量的比例
  - 迭代次数对比
  - 关键差异：AdsMind 能处理解离/异构化，Adsorb-Agent 过滤掉
  - Case study：Adsorb-Agent 失败但 AdsMind 成功的具体案例

- **3.3 DFT 验证**（→ Fig 4 散点图）
  - 3-5 个代表性表面：博文选的 Mo₃Pd(H), Mo₃Pd(NNH), Pt(111)(OH), Pt(100)(OH), CoPt(OH)
  - MACE-MP vs DFT 能量排序一致性
  - RMSD 结构偏差

- **3.4 消融研究**（→ Fig 或 Table）
  - 完整 AdsMind vs 去掉 Chemical Slip vs 去掉 FORBID vs 去掉自主终止
  - 2×2 或单因素设计
  - 选 3-5 个代表体系

- **3.5 LLM 偏见分析**（→ SI 或正文简述）
  - 9 个 LLM 在 Mo₃Pd 上的偏见类型
  - 会议纪要说"用什么模型放 SI，4-5 个模型"

### 4. Discussion
- 4.1 Chemical Slip 作为 LLM 化学推理局限性的诊断工具
- 4.2 闭环 vs 开环的根本差异
- 4.3 MLFF 作为 surrogate 的可靠性（DFT 验证结果讨论）
- 4.4 局限性：MACE-MP 精度边界、LLM API 成本、复杂表面

### 5. Conclusion

### Data Availability
- GitHub repo: https://github.com/AI4QC/AdsMind
- 所有结构文件和日志

---

## 五、你现在该做什么（按优先级）

### 🔴 今天/明天

1. **把这个 outline 发群里**让 Sherry 看
2. **删掉 `AdsMind/outline.tex`**（大气化学的，放错了）
3. **把旧数据整理到 `AdsMind/assets/`**：
   - 复制 `table1_data.md` → `AdsMind/assets/`
   - 复制 `LLM Results.xlsx` → `AdsMind/assets/`

### 🟡 本周

4. **跑消融实验**：选 3 个体系（Mo₃Pd/H, Ru₃Mo/NNH, CoPt/OH），分别跑：
   - 完整 AdsMind
   - 去掉 Chemical Slip
   - 去掉 FORBID
   - 单轮（无迭代，模拟 Adsorb-Agent 的开环模式）
5. **给博文提供 DFT 输入**：从 `results/` 中提取 BEST_*.xyz，转换为 POSCAR

### 🟠 下周

6. **开始写 Introduction 和 Methods**（基于旧草稿改写）
7. **跑 OC20-Dense 扩展 benchmark**（20-50 纯金属表面）

---

## 六、关于 Sherry 的两个 proposal 的评价

### `Draft_AdsKRK论文改进计划.md`
**结构设计是好的**，5 图 + 3 表的方案合理。但 SI 规划的 34 个图表太多了。建议：砍到必需的 ~10 个 SI 图表。

### `Draft_DFT验证实验执行细则.md`
**对博文有参考价值**（VASP 参数、INCAR 模板等）。但体系选择需要改：
- ❌ 不要从零跑 CO/Pt(111)、H₂O/Cu(111) 这些没有 MLFF 对比数据的体系
- ✅ 应该验证 `results/` 里已有的 BEST_*.xyz 结构

**建议**：把这个文档转发给博文，让他参考计算参数，但体系按博文自己建议的选：Mo₃Pd(H+NNH), Pt(111+100)(OH), CoPt(OH)。
