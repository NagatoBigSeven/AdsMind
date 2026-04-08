# DFT 验证实验执行细则

本文档提供 AdsKRK 论文中 DFT 验证实验的详细执行方案，包括体系选择、计算设置、工作流程、数据分析和质量保证。

---

## 一、实验总体设计

### 1.1 实验目标

- **核心目标**：验证 MACE-MP 预测的吸附结构和能量排序在 DFT 层面的可靠性
- **关键指标**：
  - 能量排序一致性 ≥ 90%（MACE-MP 和 DFT 预测的最优结构一致）
  - 能量误差 < 0.1 eV（对于同一结构的 MACE-MP vs DFT 能量差）
  - 结构偏差（RMSD）< 0.2 Å（最优结构的原子位置偏差）

### 1.2 分层验证策略

| 层级 | 体系数量 | 选择标准 | 时间估算 | 优先级 |
|------|---------|---------|---------|-------|
| **Tier 1（必需）** | 3个 | 代表性、计算可行性、高影响力 | 500-800 CPU 小时 | 最高 |
| **Tier 2（可选）** | 2个 | 边界案例、挑战性系统 | 300-500 CPU 小时 | 中等 |

**总计算资源需求**：约 800-1300 CPU 小时

---

## 二、体系选择策略

### 2.1 Tier 1 核心体系（必需）

#### 体系 1：经典金属表面小分子吸附

**选择理由**：
- 文献中有大量基准数据可供对比
- 计算成本低，易于快速验证
- 代表最基础的吸附场景

**推荐体系**：
| 分子 | 表面 | 结合模式 | 复杂度 |
|------|------|---------|-------|
| **CO** | Pt(111) | 顶位吸附（Top） | 低 |
| **H₂O** | Cu(111) | 分子吸附/解离 | 中 |

**备选分子**：NH₃、NO、O₂、H₂

**备选表面**：Pd(111)、Ni(111)、Au(111)、Ag(111)

---

#### 体系 2：复杂有机分子吸附

**选择理由**：
- 测试 MACE-MP 对复杂分子的泛化能力
- 涉及多官能团和可能的多种结合模式
- 更接近实际催化应用场景

**推荐体系**：
| 分子 | 表面 | 结合模式 | 复杂度 |
|------|------|---------|-------|
| **甲醇 (CH₃OH)** | Pt(111) | 氧原子端吸附/氢键 | 中-高 |
| **苯 (C₆H₆)** | Cu(111) | π-堆叠/平行吸附 | 中-高 |

**备选分子**：乙醇、甲酸、甲醛、乙烯

**备选表面**：Pd(111)、Ni(111)、Ru(0001)

---

#### 体系 3：多齿结合案例

**选择理由**：
- 测试 MACE-MP 处理多配位原子吸附的能力
- 涉及复杂的几何约束和能量竞争
- 评估 AutoAdsorbate 和 FORBID 约束的有效性

**推荐体系**：
| 分子 | 表面 | 结合模式 | 复杂度 |
|------|------|---------|-------|
| **甲酸 (HCOOH)** | Ru(0001) | 双齿结合（双O） | 高 |
| **乙二醇 (HOCH₂CH₂OH)** | Pt(111) | 多氢键/双O吸附 | 高 |

**备选分子**：乙酸、丙二酸、1,4-丁二醇

**备选表面**：Pd(111)、Ni(111)、Pt(211)

---

### 2.2 Tier 2 边界案例（可选）

#### 体系 4：低对称性位点吸附

**选择理由**：
- 测试方法在非标准吸附位点上的鲁棒性
- 台阶边缘、空位等缺陷位点是催化活性热点
- 评估 FORBID 约束在复杂环境下的表现

**推荐体系**：
| 分子 | 表面 | 结合模式 | 复杂度 |
|------|------|---------|-------|
| **CO** | Pt(211) | 台阶边缘吸附 | 中-高 |
| **H₂O** | Cu(211) | 台阶边缘解离 | 高 |

**备选**：金属表面空位、替代型缺陷

---

#### 体系 5：罕见/非标准结合模式

**选择理由**：
- 测试方法对非常规吸附模式的识别能力
- 挑战 MACE-MP 的化学直觉
- 评估 Chemical Slip 检测的边界

**推荐体系**：
| 分子 | 表面 | 结合模式 | 复杂度 |
|------|------|---------|-------|
| **苯酚 (C₆H₅OH)** | Pt(111) | 氧吸附 + π相互作用 | 极高 |
| **环己烷 (C₆H₁₂)** | Cu(111) | 立体选择性吸附 | 极高 |

**备选**：含硫分子、含氮杂环、自由基吸附

---

### 2.3 体系选择决策矩阵

| 评估维度 | 权重 | 评分标准（1-5分） |
|---------|------|------------------|
| **文献基准数据可用性** | 20% | 5=大量数据；3=部分数据；1=无数据 |
| **计算成本** | 15% | 5=低成本；3=中等成本；1=高成本 |
| **化学代表性** | 25% | 5=高度代表性；3=中等；1=边缘案例 |
| ** AdsKRK 特性测试价值** | 25% | 5=能测试核心功能；3=部分测试；1=无关 |
| **失败风险** | 15% | 5=低风险；3=中等风险；1=高风险 |

**推荐选择方法**：
1. 列出候选体系清单（至少 10-15 个）
2. 根据决策矩阵评分
3. 选择得分最高的 3-5 个体系
4. 确保体系间的化学多样性（分子类型、表面类型、结合模式）

---

## 三、DFT 计算参数设置

### 3.1 软件与代码

| 软件/库 | 推荐版本 | 用途 |
|---------|---------|------|
| **VASP** | 5.4.4 或更高 | 主DFT计算引擎 |
| **Quantum ESPRESSO** | 7.0+ | 备选DFT引擎 |
| **ASE** | 3.23+ | 原子结构操作 |
| **pymatgen** | 2024+ | 结构分析和可视化 |

---

### 3.2 交换关联泛函选择

**推荐选择**：**PBE-D3(BJ)**

**理由**：
- PBE 是金属表面吸附的标准泛函
- D3(BJ) 色散校正对分子吸附至关重要
- 广泛使用，结果可与其他研究对比

**备选泛函**：
- **RPBE-D3**：改善金属-分子结合能
- **optB86b-vdW**：非局域色散泛函
- **SCAN-rVV10**：Meta-GGA + 非局域色散（高精度但计算成本高）

---

### 3.3 计算参数详细设置

#### 3.3.1 平面波基组与截断能

| 参数 | 值 | 说明 |
|------|-----|------|
| **ENCUT** | 500 eV | 平面波截断能（确保收敛） |
| **PREC** | Accurate | 计算精度设置 |

**收敛测试建议**：
- 对 1-2 个代表性体系测试 ENCUT = 400, 450, 500, 550 eV
- 确保能量差 < 1 meV/atom

---

#### 3.3.2 k 点网格

| 体系类型 | k 点网格 | 说明 |
|---------|---------|------|
| **Pt(111)** | 6×6×1 | 3×3 表面超胞 |
| **Cu(111)** | 6×6×1 | 3×3 表面超胞 |
| **Ru(0001)** | 5×5×1 | 3×3 表面超胞 |

**通用规则**：
- Monkhorst-Pack 网格
- z 方向 1 点（真空层隔离）
- 确保能量收敛 < 1 meV/atom

---

#### 3.3.3 电子收敛标准

| 参数 | 值 | 说明 |
|------|-----|------|
| **EDIFF** | 1E-5 eV | 电子自洽收敛阈值 |
| **EDIFFG** | -0.02 eV/Å | 离子步收敛阈值（力收敛） |

**收敛测试**：
- 测试 EDIFF = 1E-4, 1E-5, 1E-6 eV
- 确保能量差 < 1 meV/atom

---

#### 3.3.4 真空层设置

| 参数 | 值 | 说明 |
|------|-----|------|
| **真空层厚度** | ≥ 15 Å | 避免周期性镜像相互作用 |
| **表面超胞** | 3×3 或 4×4 | 确保分子间隔离 |

**验证方法**：
- 测试真空层 = 12, 15, 18 Å
- 确保能量差 < 1 meV

---

#### 3.3.5 自旋极化设置

| 体系类型 | 自旋设置 | 说明 |
|---------|---------|------|
| **封闭壳层分子** | ISPIN = 1 | CO, H₂O, 苯等 |
| **开放壳层/自由基** | ISPIN = 2 | O₂, OH, CH₃ 等 |
| **磁性表面** | ISPIN = 2 + 初始磁矩 | Fe, Co, Ni 等磁性金属 |

**磁矩初始化**：
- 对磁性表面，使用 MAGMOM 设置初始磁矩
- 例如：MAGMOM = 10*5.0（10个表面原子，每个 5 µB）

---

#### 3.3.6 费米能级展宽

| 参数 | 值 | 说明 |
|------|-----|------|
| **ISMEAR** | 0 或 1 | 金属用 Gaussian (ISMEAR=1) |
| **SIGMA** | 0.05 - 0.2 eV | 展宽参数 |

**选择建议**：
- 金属体系：ISMEAR = 1, SIGMA = 0.1 eV
- 半导体/绝缘体：ISMEAR = 0

---

#### 3.3.7 偶极校正

| 体系类型 | 校正设置 | 说明 |
|---------|---------|------|
| **偶极矩显著体系** | LDIPOL = .TRUE. | 极性分子吸附 |
| **一般体系** | LDIPOL = .FALSE. | 非极性分子 |

**启用条件**：
- 垂直方向有显著偶极矩
- 需要计算表面功函数变化

---

### 3.4 结构弛豫策略

#### 方案 A：单点 DFT 计算（快速验证）

**适用场景**：
- Tier 1 核心体系初步验证
- 计算资源有限
- MACE-MP 预测结构已经充分弛豫

**步骤**：
1. 使用 MACE-MP 弛豫后的最优结构
2. 进行单点 DFT 能量计算
3. 对比 MACE-MP 和 DFT 能量

**优点**：计算快速，适合大批量验证
**缺点**：未验证结构弛豫一致性

---

#### 方案 B：完整 DFT 弛豫（金标准）

**适用场景**：
- Tier 2 边界案例
- 需要验证结构弛豫路径
- 计算资源充足

**步骤**：
1. 使用 MACE-MP 预测结构作为初始猜测
2. 进行完整 DFT 结构优化（EDIFFG = -0.02 eV/Å）
3. 弛豫完成后进行单点高精度计算（ENCUT = 550 eV）

**优点**：验证结构弛豫一致性，更可靠
**缺点**：计算成本高

---

#### 方案 C：混合策略（推荐）

**适用场景**：
- 平衡效率和准确性
- 资源有限但需要可靠验证

**步骤**：
1. **Tier 1 体系**：先单点计算，如果能量排序不一致，再进行完整弛豫
2. **Tier 2 体系**：直接进行完整 DFT 弛豫
3. **异常情况**：如果 MACE-MP 和 DFT 能量差 > 0.15 eV，进行完整弛豫验证

---

### 3.5 INCAR 模板文件

#### 单点计算模板（INCAR_SinglePoint）

```
# DFT 参数设置
SYSTEM = AdsKRK DFT Validation - Single Point
ENCUT = 500
PREC = Accurate

# 电子自洽
EDIFF = 1E-5
ISMEAR = 1
SIGMA = 0.1

# 结构优化（禁用）
NSW = 0
IBRION = -1

# 色散校正
IVDW = 12  # D3(BJ)
LDIPOL = .TRUE.

# 输出控制
LCHARG = .FALSE.
LWAVE = .FALSE.
```

---

#### 结构弛豫模板（INCAR_Relax）

```
# DFT 参数设置
SYSTEM = AdsKRK DFT Validation - Relaxation
ENCUT = 500
PREC = Accurate

# 电子自洽
EDIFF = 1E-5
ISMEAR = 1
SIGMA = 0.1

# 结构优化
EDIFFG = -0.02
NSW = 100
IBRION = 2
POTIM = 0.1

# 色散校正
IVDW = 12  # D3(BJ)
LDIPOL = .TRUE.

# 输出控制
LCHARG = .FALSE.
LWAVE = .FALSE.
```

---

## 四、工作流程与自动化

### 4.1 完整工作流程图

```
开始
  │
  ├─► 步骤 1：从 MACE-MP 获取结构
  │     - 提取 Top-K 最优结构（K = 3-5）
  │     - 格式转换为 POSCAR
  │
  ├─► 步骤 2：准备 DFT 输入文件
  │     - 生成 INCAR（单点/弛豫）
  │     - 准备 POTCAR
  │     - 设置 KPOINTS
  │     - 验证结构合理性
  │
  ├─► 步骤 3：提交计算任务
  │     - 调度系统提交（SLURM/PBS）
  │     - 监控计算进度
  │     - 错误检测与重试
  │
  ├─► 步骤 4：提取结果
  │     - 解析 OUTCAR
  │     - 提取总能量、力、原子位置
  │     - 生成分析数据
  │
  ├─► 步骤 5：数据分析与对比
  │     - MACE-MP vs DFT 能量对比
  │     - 能量排序一致性检查
  │     - 结构偏差（RMSD）计算
  │
  ├─► 步骤 6：质量检查
  │     - 收敛性检查
  │     - 异常值检测
  │     - 必要时重新计算
  │
  └─► 步骤 7：生成报告
        - 能量对比表格
        - 散点图和热图
        - 结构可视化
```

---

### 4.2 自动化脚本架构

#### 目录结构

```
DFT_Validation/
├── input/
│   ├── structures/          # MACE-MP 预测结构
│   │   ├── system_01/
│   │   │   ├── top_1.cif
│   │   │   ├── top_2.cif
│   │   │   └── top_3.cif
│   │   └── ...
│   └── references/          # 参考数据（如果有）
├── templates/               # DFT 模板文件
│   ├── INCAR_SinglePoint
│   ├── INCAR_Relax
│   └── KPOINTS
├── scripts/
│   ├── prepare_jobs.py      # 生成 DFT 输入
│   ├── submit_jobs.py       # 提交计算任务
│   ├── monitor_jobs.py      # 监控进度
│   ├── extract_results.py   # 提取结果
│   ├── analyze_results.py   # 数据分析
│   └── generate_plots.py    # 生成图表
├── output/
│   ├── dft_calculations/    # DFT 计算输出
│   └── analysis/            # 分析结果
│       ├── energy_comparison.csv
│       ├── rmsd_analysis.csv
│       └── plots/
└── logs/
    ├── job_submission.log
    ├── error_log.log
    └── convergence.log
```

---

### 4.3 Python 自动化脚本示例

#### 脚本 1：准备 DFT 输入文件

```python
#!/usr/bin/env python3
"""
prepare_jobs.py - 从 MACE-MP 结构生成 DFT 计算输入文件
"""

import os
from pathlib import Path
import numpy as np
from ase.io import read, write

def read_mace_structures(system_dir):
    """读取 MACE-MP 预测的结构"""
    structures = []
    for struct_file in sorted(Path(system_dir).glob("top_*.cif")):
        atoms = read(struct_file)
        structures.append({
            'file': struct_file,
            'rank': int(struct_file.stem.split('_')[-1]),
            'atoms': atoms
        })
    return structures

def prepare_dft_input(structure, output_dir, calc_type='single'):
    """生成 DFT 计算输入文件"""
    os.makedirs(output_dir, exist_ok=True)

    # 写入 POSCAR
    write(output_dir / 'POSCAR', structure['atoms'], format='vasp')

    # 复制 INCAR 模板
    incar_template = 'templates/INCAR_SinglePoint' if calc_type == 'single' else 'templates/INCAR_Relax'
    import shutil
    shutil.copy(incar_template, output_dir / 'INCAR')

    # 复制 KPOINTS
    shutil.copy('templates/KPOINTS', output_dir / 'KPOINTS')

    # 复制 POTCAR（需要手动准备）
    # shutil.copy('potcars/POTCAR_common', output_dir / 'POTCAR')

def prepare_system_jobs(system_name, base_dir='input/structures'):
    """为整个体系准备 DFT 计算任务"""
    system_dir = Path(base_dir) / system_name
    structures = read_mace_structures(system_dir)

    for struct in structures[:3]:  # 取 Top-3 结构
        output_dir = Path(f'output/dft_calculations/{system_name}/rank_{struct["rank"]}')
        prepare_dft_input(struct, output_dir, calc_type='single')
        print(f"Prepared: {system_name} - Rank {struct['rank']}")

if __name__ == '__main__':
    systems = ['CO_Pt111', 'H2O_Cu111', 'CH3OH_Pt111', 'HCOOH_Ru0001', 'CO_Pt211']
    for system in systems:
        prepare_system_jobs(system)
```

---

#### 脚本 2：提取 DFT 结果

```python
#!/usr/bin/env python3
"""
extract_results.py - 从 OUTCAR 提取能量和结构信息
"""

import re
from pathlib import Path
import numpy as np
from ase.io import read

def parse_outcar(outcar_path):
    """解析 VASP OUTCAR 文件"""
    with open(outcar_path, 'r') as f:
        outcar = f.read()

    # 提取总能量
    energy_match = re.search(r'energy\s+without\s+entropy=\s*(-?\d+\.\d+)', outcar)
    energy = float(energy_match.group(1)) if energy_match else None

    # 提取原子位置（最后一步）
    positions_match = re.findall(r'DIRECT\s+coordinates\s+cartesian\s+coordinates\s+[\w\s]*\s+[-\d\.]+\s+[-\d\.]+\s+[-\d\.]+\s+([\w\(\)]+)', outcar)
    if positions_match:
        atoms = read(outcar_path, format='vasp-out', index=-1)

    return {
        'energy': energy,
        'atoms': atoms,
        'converged': 'reached required accuracy' in outcar
    }

def extract_all_results(base_dir='output/dft_calculations'):
    """提取所有 DFT 计算结果"""
    results = {}
    for system_dir in Path(base_dir).iterdir():
        if not system_dir.is_dir():
            continue

        system_name = system_dir.name
        results[system_name] = []

        for rank_dir in system_dir.iterdir():
            if not rank_dir.is_dir():
                continue

            outcar_path = rank_dir / 'OUTCAR'
            if outcar_path.exists():
                rank = int(rank_dir.name.split('_')[1])
                result = parse_outcar(outcar_path)
                result['rank'] = rank
                results[system_name].append(result)

    return results

if __name__ == '__main__':
    results = extract_all_results()
    print(results)
```

---

#### 脚本 3：数据分析与对比

```python
#!/usr/bin/env python3
"""
analyze_results.py - 对比 MACE-MP 和 DFT 结果
"""

import pandas as pd
import numpy as np
from pathlib import Path
import matplotlib.pyplot as plt
from scipy.spatial.distance import cdist

def load_mace_results(csv_file='mace_results.csv'):
    """加载 MACE-MP 结果"""
    return pd.read_csv(csv_file)

def load_dft_results(results_dict):
    """将 DFT 结果转换为 DataFrame"""
    data = []
    for system, ranks in results_dict.items():
        for result in ranks:
            data.append({
                'system': system,
                'rank': result['rank'],
                'dft_energy': result['energy'],
                'converged': result['converged']
            })
    return pd.DataFrame(data)

def calculate_rmsd(atoms1, atoms2):
    """计算结构 RMSD（需要原子对齐）"""
    pos1 = atoms1.get_positions()
    pos2 = atoms2.get_positions()

    # 简单的原子顺序假设（实际需要使用 Kabsch 算法对齐）
    distances = cdist(pos1, pos2)
    rmsd = np.sqrt(np.mean(np.diag(distances)**2))
    return rmsd

def compare_mace_dft(mace_df, dft_df):
    """对比 MACE-MP 和 DFT 结果"""
    comparison = []

    for system in mace_df['system'].unique():
        mace_sys = mace_df[mace_df['system'] == system]
        dft_sys = dft_df[dft_df['system'] == system]

        for rank in range(1, 4):
            mace_row = mace_sys[mace_sys['rank'] == rank].iloc[0]
            dft_row = dft_sys[dft_sys['rank'] == rank].iloc[0]

            energy_diff = mace_row['mace_energy'] - dft_row['dft_energy']
            # rmsd = calculate_rmsd(mace_row['atoms'], dft_row['atoms'])

            comparison.append({
                'system': system,
                'rank': rank,
                'mace_energy': mace_row['mace_energy'],
                'dft_energy': dft_row['dft_energy'],
                'energy_diff': energy_diff,
                # 'rmsd': rmsd
            })

    return pd.DataFrame(comparison)

def plot_energy_comparison(comparison_df):
    """绘制能量对比散点图"""
    plt.figure(figsize=(10, 8))
    plt.scatter(comparison_df['mace_energy'], comparison_df['dft_energy'],
                s=100, alpha=0.6, edgecolors='black')

    # 绘制对角线
    min_e = min(comparison_df['mace_energy'].min(), comparison_df['dft_energy'].min())
    max_e = max(comparison_df['mace_energy'].max(), comparison_df['dft_energy'].max())
    plt.plot([min_e, max_e], [min_e, max_e], 'r--', lw=2, label='Perfect Agreement')

    # 标注误差范围
    for _, row in comparison_df.iterrows():
        if abs(row['energy_diff']) > 0.1:  # 误差 > 0.1 eV
            plt.annotate(f"{row['system']}", (row['mace_energy'], row['dft_energy']),
                       fontsize=8, ha='center')

    plt.xlabel('MACE-MP Energy (eV)', fontsize=14)
    plt.ylabel('DFT Energy (eV)', fontsize=14)
    plt.title('MACE-MP vs DFT Energy Comparison', fontsize=16)
    plt.legend(fontsize=12)
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig('output/analysis/plots/energy_comparison.png', dpi=300)
    plt.close()

def generate_summary_report(comparison_df):
    """生成汇总报告"""
    summary = {
        'Total Systems': comparison_df['system'].nunique(),
        'Energy MAE (eV)': comparison_df['energy_diff'].abs().mean(),
        'Energy Max Error (eV)': comparison_df['energy_diff'].abs().max(),
        'Systems with <0.1 eV error': (comparison_df['energy_diff'].abs() < 0.1).sum(),
        'Ranking Consistency': 'To be calculated'
    }

    report = """
    DFT 验证实验汇总报告
    =====================

    总体系数：{Total Systems}
    能量平均绝对误差 (MAE)：{Energy MAE (eV):.3f} eV
    能量最大误差：{Energy Max Error (eV):.3f} eV
    误差 < 0.1 eV 的体系数：{Systems with <0.1 eV error}/{Total Systems}

    详细数据见 CSV 文件和图表。
    """.format(**summary)

    print(report)

    return summary

if __name__ == '__main__':
    # 加载数据
    mace_df = load_mace_results('output/analysis/mace_results.csv')
    # results_dict = extract_all_results()
    # dft_df = load_dft_results(results_dict)

    # 对比分析
    # comparison_df = compare_mace_dft(mace_df, dft_df)
    # comparison_df.to_csv('output/analysis/energy_comparison.csv', index=False)

    # 绘图和报告
    # plot_energy_comparison(comparison_df)
    # summary = generate_summary_report(comparison_df)
```

---

### 4.4 任务提交脚本（SLURM 示例）

```bash
#!/bin/bash
# submit_jobs.sh - 提交 DFT 计算任务

#SBATCH --job-name=AdsKRK_DFT
#SBATCH --partition=compute
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=24
#SBATCH --time=48:00:00
#SBATCH --mail-type=ALL
#SBATCH --mail-user=your.email@example.com

# 模块加载
module load vasp/5.4.4
module load python/3.10

# 环境设置
export OMP_NUM_THREADS=24

# 运行计算
for system_dir in output/dft_calculations/*/rank_1; do
    cd $system_dir
    echo "Running DFT calculation in $system_dir"
    mpirun -np 24 vasp_std > vasp.log 2>&1
    cd - > /dev/null
done

echo "All calculations submitted/completed"
```

---

## 五、数据分析与可视化

### 5.1 关键分析指标

#### 能量排序一致性

**定义**：
- MACE-MP 和 DFT 预测的最优结构是否一致
- Top-K 排序的一致性程度

**计算方法**：
```python
def ranking_consistency(mace_energies, dft_energies, k=3):
    """计算 Top-K 排序一致性"""
    mace_rank = np.argsort(mace_energies)[:k]
    dft_rank = np.argsort(dft_energies)[:k]
    intersection = len(set(mace_rank) & set(dft_rank))
    consistency = intersection / k
    return consistency
```

**目标**：
- Top-1 一致性 ≥ 90%
- Top-3 一致性 ≥ 85%

---

#### 能量误差分布

**分析内容**：
- MACE-MP vs DFT 能量差的统计分布
- 平均绝对误差（MAE）、均方根误差（RMSE）
- 误差随体系复杂度的变化

**可视化**：
- 散点图（MACE-MP vs DFT）
- 能量差直方图
- 按体系类别的箱线图

---

#### 结构偏差分析

**分析内容**：
- 原子位置 RMSD（需要结构对齐）
- 键长/键角变化
- 分子取向偏差

**可视化**：
- 结构叠加示意图（ASE / VESTA）
- RMSD 热图
- 结构差异动画

---

### 5.2 推荐可视化图表

| 图表类型 | 内容 | 用途 | 工具 |
|---------|------|------|------|
| **散点图** | MACE-MP vs DFT 能量对比 | 整体一致性评估 | Matplotlib / Plotly |
| **热图** | 能量差矩阵 | 体系间误差模式 | Seaborn |
| **箱线图** | 按分子类别的误差分布 | 化学依赖性分析 | Matplotlib |
| **结构对比图** | MACE-MP vs DFT 结构叠加 | 结构偏差可视化 | ASE / VESTA |
| **相关性图** | 能量差 vs 体系特征 | 误差来源分析 | Matplotlib |

---

### 5.3 异常值检测与处理

#### 异常情况类型

| 异常类型 | 触发条件 | 处理方案 |
|---------|---------|---------|
| **能量差 > 0.15 eV** | MACE-MP 和 DFT 能量差异大 | 检查收敛性；必要时重新弛豫 |
| **收敛失败** | DFT 未达到收敛阈值 | 调整参数；使用更精确设置 |
| **结构突变** | 弛豫过程中原子位置异常 | 检查初始结构；增加约束 |
| **排序不一致** | Top-1 结构不同 | 分析差异原因；报告局限性 |

#### 异常处理流程

```
检测到异常值
    │
    ├─► 检查收敛性（OUTCAR）
    │     - 是否达到 EDIFF/EDIFFG？
    │     - 电子步数是否异常？
    │
    ├─► 检查输入文件
    │     - POSCAR 是否正确？
    │     - POTCAR 是否匹配？
    │
    ├─► 重新计算
    │     - 增加截断能 ENCUT
    │     - 使用更严格收敛标准
    │     - 添加偶极校正
    │
    ├─► 必要时人工检查
    │     - 可视化结构
    │     - 检查物理合理性
    │
    └─► 记录并报告
          - 在 SI 中说明异常
          - 分析可能原因
```

---

## 六、质量保证与验证

### 6.1 计算收敛性检查清单

| 检查项 | 通过标准 | 工具 |
|-------|---------|------|
| **能量收敛** | EDIFF < 1E-5 eV | OUTCAR 分析 |
| **力收敛** | 最大力 < 0.02 eV/Å | OUTCAR 分析 |
| **电子步数** | < 100 步（正常） | OUTCAR 分析 |
| **离子步数** | < 50 步（正常） | OUTCAR 分析 |

---

### 6.2 与文献数据对比

**验证步骤**：
1. 搜索相同体系在文献中的 DFT 计算数据
2. 对比吸附能、结合位点、键长等
3. 分析差异来源（泛函、赝势、设置等）

**推荐数据库**：
- **OC20**：开放催化数据库（包含 DFT 数据）
- **CatHub**：催化数据库
- **Materials Project**：材料项目数据库

---

### 6.3 内部一致性验证

**验证方法**：
1. 使用不同泛函计算同一体系（如 PBE-D3 vs RPBE-D3）
2. 检查能量排序一致性
3. 如果排序不一致，报告泛函敏感性

---

### 6.4 代码和数据备份

**备份策略**：
- 计算输入输出文件备份到云端/备份服务器
- 使用 Git 版本控制管理脚本和配置文件
- 记录所有随机种子和环境变量

**建议目录结构**：
```
backup/
├── calculations_YYYYMMDD/
│   ├── input/
│   └── output/
├── scripts/
└── documentation/
```

---

## 七、时间规划与里程碑

### 7.1 详细时间表（假设 Tier 1 + Tier 2）

| 阶段 | 任务 | 时间 | 里程碑 |
|------|------|------|-------|
| **第 1 周** | 体系选择与准备 | 3 天 | 确定 5 个测试体系 |
| | 模板文件准备 | 2 天 | INCAR/KPOINTS 就绪 |
| **第 2 周** | MACE-MP 结构提取 | 2 天 | 获取 Top-K 结构 |
| | DFT 输入文件生成 | 3 天 | 完成任务准备 |
| **第 3-4 周** | Tier 1 DFT 计算 | 10 天 | 完成核心体系计算 |
| | Tier 2 DFT 计算 | 5 天 | 完成边界体系计算 |
| **第 5 周** | 结果提取与分析 | 3 天 | 生成对比数据 |
| | 异常值处理 | 2 天 | 解决异常计算 |
| **第 6 周** | 可视化与报告 | 4 天 | 生成图表和报告 |
| | 论文图表准备 | 3 天 | 完成 Fig. 3 和 Table S1 |

**总耗时**：约 6 周（可并行压缩至 4 周）

---

### 7.2 关键里程碑

| 里程碑 | 完成标准 | 检查方式 |
|-------|---------|---------|
| **M1：体系确定** | 5 个体系评分完成 | 决策矩阵评分表 |
| **M2：模板就绪** | INCAR/KPOINTS 通过测试 | 测试体系计算成功 |
| **M3：计算完成** | 所有体系 DFT 计算收敛 | OUTCAR 检查通过 |
| **M4：分析完成** | 能量排序一致性 ≥ 90% | 自动化脚本报告 |
| **M5：图表就绪** | Fig. 3 和 Table S1 完成 | 图表文件生成 |

---

## 八、常见问题与故障排除

### 8.1 常见问题

| 问题 | 可能原因 | 解决方案 |
|------|---------|---------|
| **计算不收敛** | 截断能太低、初始结构差、泛函问题 | 增加 ENCUT、使用弛豫、切换泛函 |
| **能量异常高/低** | POSCAR 错误、POTCAR 不匹配 | 检查原子种类、重新生成 POTCAR |
| **KPOINTS 错误** | 超胞尺寸不匹配 | 重新计算 k 点网格 |
| **内存溢出** | 体系过大、并行设置不当 | 减少节点、调整 OMP_NUM_THREADS |

---

### 8.2 故障排除流程图

```
计算失败
    │
    ├─► 检查错误信息
    │     - OUTCAR 错误代码
    │     - 系统日志
    │
    ├─► 诊断问题类型
    │     - 收敛问题？
    │     - 参数错误？
    │     - 资源限制？
    │
    ├─► 实施解决方案
    │     - 调整参数
    │     - 修复输入文件
    │     - 申请更多资源
    │
    └─► 重新提交
          - 记录问题
          - 更新文档
```

---

### 8.3 优化建议

**计算效率优化**：
1. 使用预计算的 POTCAR 缓存
2. 启用 VASP 并行优化（NCORE, KPAR）
3. 对相似体系使用相同初始化设置

**精度优化**：
1. 对关键体系使用更高精度（ENCUT = 550 eV）
2. 测试不同色散校正方法
3. 使用更高阶泛函（如 meta-GGA）验证

---

## 九、附录：参考资源

### 9.1 推荐阅读

1. **VASP Manual**：https://www.vasp.at/wiki/
2. **DFT 最佳实践**：
   - Kresse, G., & Hafner, J. (1993). Phys. Rev. B.
   - Grimme, S., et al. (2010). J. Chem. Phys. (D3 correction)
3. **色散校正**：
   - Grimme, S. (2010). J. Chem. Phys. 132, 154104 (D3)
   - Grimme, S., et al. (2011). J. Chem. Phys. 134, 154108 (D3(BJ))

---

### 9.2 在线工具

- **VASP Wiki**：官方文档和示例
- **Materials Project**：材料数据库
- **ASE Documentation**：原子模拟环境
- **pymatgen Documentation**：材料分析库

---

### 9.3 社区支持

- **VASP Forum**：https://www.vasp.at/forum/
- **ASE GitHub Issues**：https://github.com/ase/ase/issues
- **Materials Project Discourse**：https://materialsproject.discourse.group/

---

## 十、总结与检查清单

### 10.1 实验前检查清单

- [ ] 确定测试体系（3-5 个）
- [ ] 准备 DFT 模板文件（INCAR, KPOINTS, POTCAR）
- [ ] 编写/测试自动化脚本
- [ ] 申请计算资源
- [ ] 准备 MACE-MP 结构数据

---

### 10.2 实验中检查清单

- [ ] 监控计算进度
- [ ] 检查收敛性
- [ ] 记录异常情况
- [ ] 及时处理失败计算

---

### 10.3 实验后检查清单

- [ ] 提取所有计算结果
- [ ] 进行能量排序一致性分析
- [ ] 生成可视化图表
- [ ] 编写实验报告
- [ ] 备份数据和代码
- [ ] 准备论文图表（Fig. 3, Table S1）

---

**文档版本**：v1.0
**创建日期**：2026-03-28
**维护者**：AdsKRK 项目组

---

通过遵循本执行细则，DFT 验证实验将能够高效、可靠地完成，为 AdsKRK 论文提供坚实的实证基础。
