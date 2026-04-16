# AdsMind 下一阶段执行计划

> 生成日期: 2026-04-14
> 目标: 补强论文论据，解决审稿人可能质疑的统计检验力和跨数据集泛化问题

---

## 当前实验覆盖状态

| 维度 | 已完成 | 缺口 |
|------|--------|------|
| 4后端 × 20案例 one-shot | ✅ 80 runs | — |
| 4后端 × 5案例 × 5变体 消融 | ✅ 100 runs | 只有5个案例，BH校正后pairwise全部p>0.05 |
| OCD-GMAE 数据集 | ❌ 未开始 | 只有CMU一个数据集 |
| DFT 验证 | ⏳ 等Bowen | 1个样本就绪，其余下周 |
| 重复实验 | ❌ 未开始 | temp=0.0所以优先级低 |

---

## Phase A: CMU 消融扩展（最高优先级）

### 目标
将消融矩阵从 5 案例扩展到 15 案例，使 Friedman/Wilcoxon 检验有更高的统计检验力。

### 案例选择理由

**推荐新增 10 个案例**（按 one-shot 4-backend range 从大到小排序）:

| Case | 吸附质 | 表面族 | One-shot 4-backend range | 选择理由 |
|------|--------|--------|--------------------------|----------|
| 20 | ONN(CH3)2 | intermetallic | 1.050 eV | 最大跨后端分歧，闭环最可能有价值 |
| 04 | NNH | intermetallic | 0.585 eV | NNH dissociation-prone，高难度 |
| 10 | OH | monometallic | 0.596 eV | 单金属但跨后端分歧大，Pt(100) facet |
| 13 | OH | monometallic | 0.449 eV | Ag(100)，one-shot分歧 |
| 12 | OH | monometallic | 0.474 eV | Au(111)，desorption边界案例 |
| 15 | CH2CH2OH | intermetallic | 0.376 eV | 大吸附质，Cu6Ga2 |
| 17 | OCHCH3 | intermetallic | 0.374 eV | 与case19同族吸附质，不同表面 |
| 16 | CH2CH2OH | intermetallic | 0.125 eV | Au2Hf，与15互补 |
| 05 | H | intermetallic | 0.119 eV | Cu3Ag，简单原子吸附对照 |
| 18 | OCHCH3 | intermetallic | 0.101 eV | Al3Zr，与17互补 |

**排除的案例**:
- 03 (range=0.005 eV): H on Pd3Cu, one-shot已近乎完美，闭环无改进空间
- 07 (range=0.039 eV): H on Ru3Mo, 同理
- 11 (range=0.040 eV): OH on Pd(111), 同理
- 06, 08: GPT-5.4/Claude one-shot失败(NNH dissociation)，无法跨4后端比较

### 执行命令

**重要**: `run_ablation.py` 没有跳过已完成案例的逻辑，会覆盖现有数据。只运行新增案例。

**前置环境设置** (在 EPFL workstation 或本地 Mac):

```bash
# 在运行任何实验前设置所有 API keys
export XAI_API_KEY="xai-MXKM57ULNbP8lnkaRvDpOiJOEPRS7taBhscs2VjpaJRuXS5mFqnDqBepcsD35GwY2QSCNfV9oLTH9aT7"
export AIHUBMIX_API_KEY="sk-auKPuBGLfwQoOCRmD1F2B7E03b05492b989cD366E0703f37"
export ANTHROPIC_API_KEY="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"
export OPENAI_API_KEY="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"
```

**Step A1: 4个后端各跑 4 变体 × 10 新案例 = 160 runs**

注意: single_shot 数据已经在 one-shot 基准目录里，不需要通过消融跑。但 `full` 变体是新案例所以需要跑。

```bash
# === Gemini 2.5 Pro (tmux session 1) ===
tmux new-session -d -s gemini_ext
tmux send-keys -t gemini_ext "cd /Users/nagato/workspace/AdsMind && export AIHUBMIX_API_KEY='sk-auKPuBGLfwQoOCRmD1F2B7E03b05492b989cD366E0703f37'" Enter
tmux send-keys -t gemini_ext "python -m research.agent_eval.run_ablation \
  --manifest research/agent_eval/manifests/cmu_manifest.csv \
  --config research/agent_eval/configs/frozen_config_gemini25pro.json \
  --output research/results/gemini_ablation_v1 \
  --cases 04,05,10,12,13,15,16,17,18,20 \
  --variants full,no_slip,no_forbid,no_termination 2>&1 | tee /tmp/gemini_ext_ablation.log" Enter

# === Grok-4 (tmux session 2) ===
tmux new-session -d -s grok4_ext
tmux send-keys -t grok4_ext "cd /Users/nagato/workspace/AdsMind && export XAI_API_KEY='xai-MXKM57ULNbP8lnkaRvDpOiJOEPRS7taBhscs2VjpaJRuXS5mFqnDqBepcsD35GwY2QSCNfV9oLTH9aT7'" Enter
tmux send-keys -t grok4_ext "python -m research.agent_eval.run_ablation \
  --manifest research/agent_eval/manifests/cmu_manifest.csv \
  --config research/agent_eval/configs/frozen_config_xai_grok4.json \
  --output research/results/xai_ablation_v2 \
  --cases 04,05,10,12,13,15,16,17,18,20 \
  --variants full,no_slip,no_forbid,no_termination 2>&1 | tee /tmp/grok4_ext_ablation.log" Enter

# === GPT-5.4 (tmux session 3) ===
tmux new-session -d -s gpt54_ext
tmux send-keys -t gpt54_ext "cd /Users/nagato/workspace/AdsMind && export OPENAI_API_KEY='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'" Enter
tmux send-keys -t gpt54_ext "python -m research.agent_eval.run_ablation \
  --manifest research/agent_eval/manifests/cmu_manifest.csv \
  --config research/agent_eval/configs/frozen_config_openai_gpt54.json \
  --output research/results/openai_gpt54_ablation_v1 \
  --cases 04,05,10,12,13,15,16,17,18,20 \
  --variants full,no_slip,no_forbid,no_termination 2>&1 | tee /tmp/gpt54_ext_ablation.log" Enter

# === Claude Sonnet 4.6 (tmux session 4) ===
tmux new-session -d -s claude_ext
tmux send-keys -t claude_ext "cd /Users/nagato/workspace/AdsMind && export ANTHROPIC_API_KEY='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'" Enter
tmux send-keys -t claude_ext "python -m research.agent_eval.run_ablation \
  --manifest research/agent_eval/manifests/cmu_manifest.csv \
  --config research/agent_eval/configs/frozen_config_anthropic_sonnet46.json \
  --output research/results/anthropic_sonnet46_ablation_v1 \
  --cases 04,05,10,12,13,15,16,17,18,20 \
  --variants full,no_slip,no_forbid,no_termination 2>&1 | tee /tmp/claude_ext_ablation.log" Enter
```

**Step A2: 完成后重建汇总** (每个后端各运行一次)

```bash
# Gemini - 需要从 one-shot 基准目录拉取 single_shot 数据
python -m research.agent_eval.rebuild_ablation_summary \
  --ablation-dir research/results/gemini_ablation_v1 \
  --one-shot-dir research/results/cmu_v1_gemini_one_shot \
  --cases 01,02,04,05,09,10,12,13,14,15,16,17,18,19,20 \
  --variants full,no_slip,no_forbid,no_termination,single_shot

# Grok-4
python -m research.agent_eval.rebuild_ablation_summary \
  --ablation-dir research/results/xai_ablation_v2 \
  --one-shot-dir research/results/cmu_v1_xai_progressive_one_shot \
  --cases 01,02,04,05,09,10,12,13,14,15,16,17,18,19,20 \
  --variants full,no_slip,no_forbid,no_termination,single_shot

# GPT-5.4
python -m research.agent_eval.rebuild_ablation_summary \
  --ablation-dir research/results/openai_gpt54_ablation_v1 \
  --one-shot-dir research/results/cmu_v1_openai_gpt54_one_shot \
  --cases 01,02,04,05,09,10,12,13,14,15,16,17,18,19,20 \
  --variants full,no_slip,no_forbid,no_termination,single_shot

# Claude
python -m research.agent_eval.rebuild_ablation_summary \
  --ablation-dir research/results/anthropic_sonnet46_ablation_v1 \
  --one-shot-dir research/results/cmu_v1_anthropic_sonnet46_one_shot \
  --cases 01,02,04,05,09,10,12,13,14,15,16,17,18,19,20 \
  --variants full,no_slip,no_forbid,no_termination,single_shot
```

### 预估耗时
- 每个 run ~2-10 分钟（取决于案例复杂度）
- 每个后端 40 runs ≈ 2-6 小时
- 4 个后端并行 ≈ 总计 2-6 小时实际时间
- 如果在 EPFL workstation 上跑则可以 4 个 tmux 并行

### 期望收益
- 15 案例的 Friedman 检验将有更高统计检验力
- BH 校正后 pairwise 比较有望达显著
- 跨案例效应一致性更可信

---

## Phase B: OCD-GMAE 数据集验证（中等优先级）

### 目标
在独立数据集上验证 agent 的泛化能力，回应"只在一个数据集上测试"的质疑。

### 前置条件
OCD-GMAE 数据已下载到 `/Users/nagato/workspace/AdsMT/datasets/OCD-GMAE/data.lmdb`。
数据格式: LMDB with 973 条 `torch_geometric.data.Data` 记录，每条包含:
- `atomic_numbers`, `pos`, `cell`, `natoms`, `tags` (bare slab 结构)
- `ads_smi` (吸附质 SMILES)
- `y_relaxed` (DFT GMAE 能量，作为 ground truth)
- `gmae_pos`, `gmae_atom_numb`, `gmae_tags` (最优吸附构型)
- `site` (最优吸附位点信息)

### Step B1: 编写数据转换脚本

需要创建 `research/agent_eval/prepare_ocd_gmae.py`，功能:

1. 读取 OCD-GMAE LMDB (需要 torch, torch_geometric)
2. 对每条记录:
   - 用 `tags` 区分 slab 原子和 adsorbate 原子 (OC20 convention: tag=0 为 subsurface, tag=1 为 surface, tag=2 为 adsorbate)
   - 提取 bare slab (tags != 2 的原子)
   - 用 ASE 写出 `.xyz` 文件
   - 将 `ads_smi` 映射到 AdsMind 支持的 SMILES
3. 生成 `research/agent_eval/manifests/ocd_gmae_manifest.csv`
4. 筛选标准:
   - 排除 AdsMind 不支持的吸附质（比如超大分子）
   - 排除表面原子数过多（>200）的体系
   - 优先选择与 CMU 数据集吸附质相同/相似的条目（H, OH, NNH, 小有机分子）

**初步筛选策略**: 从 973 条中挑选 ~20-30 条代表性案例，覆盖:
- 不同吸附质类型
- 不同表面组成
- 不同能量范围

### Step B2: 在筛选后的 OCD-GMAE 子集上运行 one-shot 基准

```bash
# 先用 1 个后端（如 Gemini）做试运行，确认管线正常
python -m research.agent_eval.run_batch \
  --manifest research/agent_eval/manifests/ocd_gmae_manifest.csv \
  --config research/agent_eval/configs/frozen_config_gemini25pro.json \
  --output research/results/ocd_gmae_v1_gemini_one_shot
```

### Step B3: 在 OCD-GMAE 子集上选择 5-10 个案例运行消融

选择 one-shot 4-backend range 最大的案例进入消融矩阵。

### 实施难度
- **高**: 需要安装 torch_geometric 环境来读取 LMDB
- 需要理解 OC20 的 tags convention
- 需要验证 slab 提取的正确性
- SMILES 映射可能不完美

### 建议
Phase B 可以在 Phase A 跑着的同时并行开发数据转换脚本。但运行实验应在 Phase A 完成并验证后再开始。

---

## Phase C: 重复实验（低优先级）

### 目标
量化 LLM 采样方差，证明实验可重复性。

### 设计
- 选择 5 个核心消融案例 (01, 02, 09, 14, 19)
- 每个 full 配置跑 3 次
- 所有后端都是 temperature=0.0，理论上应该是确定性的
- 如果结果完全一致，本身就是一个有意义的发现
- 如果有差异，可以量化 API-level 不确定性

### 命令模板

```bash
# 需要为重复实验创建独立的输出目录
for rep in 1 2 3; do
  python -m research.agent_eval.run_ablation \
    --manifest research/agent_eval/manifests/cmu_manifest.csv \
    --config research/agent_eval/configs/frozen_config_gemini25pro.json \
    --output research/results/gemini_ablation_v1_rep${rep} \
    --cases 01,02,09,14,19 \
    --variants full
done
```

### 优先级说明
这个 Phase 在 temperature=0.0 下价值有限。如果时间紧张可以跳过，论文中 "LLM reproducibility" 段落已经做了足够的 caveat。

---

## 执行优先级总结

```
Phase A (CMU 消融扩展)  >>  Phase B (OCD-GMAE)  >>  Phase C (重复实验)
      最高优先级                 中等优先级              低优先级
    直接提升统计检验力         泛化性论据            temperature=0所以次要
      ~160 runs               需要数据转换            ~60 runs
     预计 2-6 小时             预计 1-2 天开发          预计 2-6 小时
```

---

## EPFL Workstation 执行指南（主执行环境）

连接方式: `~/.ssh/LIACPC12` expect 脚本 (user=zongmin, host=128.178.38.24)

### 预检 (Phase A 开始前必须执行)

```bash
# 1. SSH 到 EPFL workstation
~/.ssh/LIACPC12

# 2. 进入 repo 并拉取最新代码（包含 Claude Sonnet 4.6 config 等）
cd ~/workspace/AdsMind   # 确认实际路径
git pull origin main

# 3. 确认 Python 环境
python -c "from research.agent_eval.run_ablation import main; print('run_ablation OK')"
python -c "from ase.io import read; print('ASE OK')"
python -c "import mace; print('MACE OK')"

# 4. 确认已有消融数据没丢（5案例 × 4变体应各有5个子目录）
ls research/results/gemini_ablation_v1/full/
ls research/results/xai_ablation_v2/full/
ls research/results/openai_gpt54_ablation_v1/full/
ls research/results/anthropic_sonnet46_ablation_v1/full/
```

### Phase A 主执行命令 (4 tmux sessions 并行)

```bash
# ========================================
# Session 1: Gemini 2.5 Pro
# ========================================
tmux new-session -d -s gem_ext
tmux send-keys -t gem_ext "cd ~/workspace/AdsMind" Enter
tmux send-keys -t gem_ext "export AIHUBMIX_API_KEY='sk-auKPuBGLfwQoOCRmD1F2B7E03b05492b989cD366E0703f37'" Enter
tmux send-keys -t gem_ext "python -m research.agent_eval.run_ablation \
  --manifest research/agent_eval/manifests/cmu_manifest.csv \
  --config research/agent_eval/configs/frozen_config_gemini25pro.json \
  --output research/results/gemini_ablation_v1 \
  --cases 04,05,10,12,13,15,16,17,18,20 \
  --variants full,no_slip,no_forbid,no_termination \
  2>&1 | tee /tmp/gem_ext.log" Enter

# ========================================
# Session 2: Grok-4
# ========================================
tmux new-session -d -s grok_ext
tmux send-keys -t grok_ext "cd ~/workspace/AdsMind" Enter
tmux send-keys -t grok_ext "export XAI_API_KEY='xai-MXKM57ULNbP8lnkaRvDpOiJOEPRS7taBhscs2VjpaJRuXS5mFqnDqBepcsD35GwY2QSCNfV9oLTH9aT7'" Enter
tmux send-keys -t grok_ext "python -m research.agent_eval.run_ablation \
  --manifest research/agent_eval/manifests/cmu_manifest.csv \
  --config research/agent_eval/configs/frozen_config_xai_grok4.json \
  --output research/results/xai_ablation_v2 \
  --cases 04,05,10,12,13,15,16,17,18,20 \
  --variants full,no_slip,no_forbid,no_termination \
  2>&1 | tee /tmp/grok_ext.log" Enter

# ========================================
# Session 3: GPT-5.4
# ========================================
tmux new-session -d -s gpt_ext
tmux send-keys -t gpt_ext "cd ~/workspace/AdsMind" Enter
tmux send-keys -t gpt_ext "export OPENAI_API_KEY='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'" Enter
tmux send-keys -t gpt_ext "python -m research.agent_eval.run_ablation \
  --manifest research/agent_eval/manifests/cmu_manifest.csv \
  --config research/agent_eval/configs/frozen_config_openai_gpt54.json \
  --output research/results/openai_gpt54_ablation_v1 \
  --cases 04,05,10,12,13,15,16,17,18,20 \
  --variants full,no_slip,no_forbid,no_termination \
  2>&1 | tee /tmp/gpt_ext.log" Enter

# ========================================
# Session 4: Claude Sonnet 4.6
# ========================================
tmux new-session -d -s claude_ext
tmux send-keys -t claude_ext "cd ~/workspace/AdsMind" Enter
tmux send-keys -t claude_ext "export ANTHROPIC_API_KEY='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'" Enter
tmux send-keys -t claude_ext "python -m research.agent_eval.run_ablation \
  --manifest research/agent_eval/manifests/cmu_manifest.csv \
  --config research/agent_eval/configs/frozen_config_anthropic_sonnet46.json \
  --output research/results/anthropic_sonnet46_ablation_v1 \
  --cases 04,05,10,12,13,15,16,17,18,20 \
  --variants full,no_slip,no_forbid,no_termination \
  2>&1 | tee /tmp/claude_ext.log" Enter
```

### 监控进度

```bash
# 查看各 session 状态
tmux ls

# 查看某个 session 的实时输出
tmux attach -t gem_ext    # Ctrl+b d 退出但不中断

# 查看 log 进度
tail -20 /tmp/gem_ext.log
tail -20 /tmp/grok_ext.log
tail -20 /tmp/gpt_ext.log
tail -20 /tmp/claude_ext.log

# 检查已完成的 case 数量
for d in gemini_ablation_v1 xai_ablation_v2 openai_gpt54_ablation_v1 anthropic_sonnet46_ablation_v1; do
  echo "=== $d ==="
  for v in full no_slip no_forbid no_termination; do
    echo "  $v: $(ls research/results/$d/$v/ 2>/dev/null | wc -l) cases"
  done
done
```

### Phase A 完成后: 重建汇总

```bash
# 所有 15 案例 (原5 + 新10) 的汇总重建
for pair in \
  "gemini_ablation_v1:cmu_v1_gemini_one_shot" \
  "xai_ablation_v2:cmu_v1_xai_progressive_one_shot" \
  "openai_gpt54_ablation_v1:cmu_v1_openai_gpt54_one_shot" \
  "anthropic_sonnet46_ablation_v1:cmu_v1_anthropic_sonnet46_one_shot"; do
  IFS=: read abldir osdir <<< "$pair"
  echo "=== Rebuilding $abldir ==="
  python -m research.agent_eval.rebuild_ablation_summary \
    --ablation-dir "research/results/$abldir" \
    --one-shot-dir "research/results/$osdir" \
    --cases 01,02,04,05,09,10,12,13,14,15,16,17,18,19,20 \
    --variants full,no_slip,no_forbid,no_termination,single_shot
done
```

### 每日推送

```bash
cd ~/workspace/AdsMind
git add research/results/
git status
git commit -m "data: extended ablation [DATE] - [N] new cases completed"
git push origin main
```
