# VESTA 渲染操作清单

为论文 Figure 2-4 的原子结构面板准备的具体操作指南。

---

## Case Study 1: H on Mo₃Pd(111) — Figure 2

### 需要渲染的文件

| 面板 | 文件路径 | 展示内容 |
|:----:|---------|---------|
| (a) | `results/01/BEST_H_hollow_to_ontop_E-2.601.xyz` | Iter 1: Hollow→Ontop slip |
| (b) | `results/01/BEST_H_bridge_to_ontop_E-2.638.xyz` | Iter 5: Bridge→Ontop slip (**最优**) |
| (c) | `benchmark_slabs/01_Mo3Pd_111.xyz` | 裸表面（参考） |

### VESTA 设置

1. **打开** `results/01/BEST_H_bridge_to_ontop_E-2.638.xyz`
2. **视角**: 略倾斜的俯视图 (~15° tilt)，能同时看到表面原子排列和 H 原子位置
3. **原子半径**: Mo=灰色(大), Pd=银色(大), H=白色(小但高亮)
4. **标注 H-Pd 键长**: 选中 H 和最近 Pd 原子，标注距离
5. **高亮 Pd ontop 位点**: 可以用半透明圆圈标注 Pd ontop 位置
6. **背景**: 白色
7. **导出**: PNG 300dpi, 约 800×600 px

### 化学故事要点
> H 原子从所有初始位点（hollow, bridge, ontop@Mo）全部滑向 Pd ontop。
> 在图中标注箭头指示 slip 方向会很有说服力。

---

## Case Study 2: N₂H on Ru₃Mo(111) — Figure 3

### 需要渲染的文件

| 面板 | 文件路径 | 展示内容 |
|:----:|---------|---------|
| (a) | `results/08/BEST_N_NH_bridge_to_hollow_ISO_E-4.821.xyz` | 最稳定：异构化分子态 (**-4.821 eV**) |
| (b) | `results/08/BEST_N_NH_hollow_DISS_E-3.550.xyz` | 解离态 (-3.550 eV) |
| (c) | 并排对比 (a) vs (b) | 强调 N-N 键保留 vs 断裂 |

### VESTA 设置

1. **两个结构并排渲染**
2. **视角**: 侧视图，清晰展示 N-N 键
3. **原子着色**: Ru=深绿, Mo=灰蓝, N=蓝色, H=白色
4. **关键标注**:
   - (a) 中标注 N-N 键长（应该保留）
   - (b) 中标注 N...N 距离（已断裂，距离变大）
   - 两个图都标注 N-surface 键长
5. **导出**: PNG 300dpi

### 化学故事要点
> 异构化分子态（-4.821 eV）比解离态（-3.550 eV）稳定 1.27 eV。
> 这在化学上反直觉：通常解离态更稳定。渲染时强调 N-N 键在多金属环境中被保护。

---

## Case Study 3: [CH]=O on CuZnO — Figure 4

### 需要渲染的文件

| 面板 | 文件路径 | 展示内容 |
|:----:|---------|---------|
| (a) | 找到 CuZnO 的第1轮结果 | Iter 1: Cu₄ hollow 构型 A (E=-1.484 eV) |
| (b) | 找到 CuZnO 的第4轮结果 | Iter 4: Cu₄ hollow 构型 B (E=-1.497 eV) |
| (c) | 俯视图标注两个 hollow 位置 | 展示两个简并位点的空间关系 |

> **注意**: CuZnO 的结构文件可能在运行时的 `outputs/e05a0585/` 目录下，而非 `results/` 目录。
> 检查路径: `find /Users/nagato/workspace/AdsMind -name "*CuZnO*" -o -name "*e05a0585*" -type d`

### VESTA 设置

1. **视角**: 俯视图 (top view) + 一张侧视图
2. **原子着色**: Cu=棕色, Zn=灰色, O=红色, C=黑色, H=白色
3. **关键标注**:
   - C-Cu 键长（~2.01-2.02 Å）
   - 标注 4-fold hollow 的 4 个 Cu 原子
   - (c) 中标注两个简并 hollow 位点的位置差异
4. **导出**: PNG 300dpi

### 化学故事要点
> 两个不同的 Cu₄ hollow 位点（ΔE=0.013 eV）是能量简并的。
> 这揭示了合金氧化物表面的隐藏 PES 特征——LLM 无法预测，只有物理反馈能发现。

---

## 通用 VESTA 技巧

- **统一风格**: 所有结构图使用相同的原子半径比例和背景色
- **Bond 设置**: Edit → Bonds → 添加你关心的键类型和距离阈值
- **导出质量**: Utilities → Export Raster Image → 300 dpi, 白色背景
- **后处理**: 用 PowerPoint/Figma 把 VESTA 渲染图和 matplotlib 收敛曲线组合成最终多面板图
