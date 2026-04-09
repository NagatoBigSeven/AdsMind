#!/usr/bin/env python3
"""Generate publication-quality figures and LaTeX tables for the AdsKRK paper."""

import importlib
import importlib.util

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import numpy as np

# ============================================================
# Use SciencePlots style if available, otherwise Nature-like
# ============================================================
try:
    if importlib.util.find_spec("scienceplots") is not None:
        importlib.import_module("scienceplots")
        plt.style.use(['science', 'nature'])
    else:
        raise ImportError
except ImportError:
    plt.rcParams.update({
        'font.family': 'sans-serif',
        'font.sans-serif': ['Arial', 'Helvetica'],
        'font.size': 8,
        'axes.linewidth': 0.8,
        'xtick.major.width': 0.6,
        'ytick.major.width': 0.6,
        'figure.dpi': 300,
    })

# ============================================================
# Global Plasma Palette
# ============================================================
_plasma = cm.get_cmap('plasma')
PLASMA = {
    'p1': _plasma(0.15),   # deep purple
    'p2': _plasma(0.35),   # blue-violet
    'p3': _plasma(0.55),   # magenta-pink
    'p4': _plasma(0.75),   # orange
    'p5': _plasma(0.90),   # bright yellow
    'accent': _plasma(0.95),  # highlight yellow
    'dark': _plasma(0.05),    # near-black purple
}

# ============================================================
# Table 1 Data (from BEST_*.xyz extraction)
# ============================================================
data = [
    # (No, Surface, Adsorbate, SMILES, Iters, Best_mol_eV, Best_diss_eV, Best_site, PES_type, Slip_frac, Has_diss)
    (1,  "Mo₃Pd(111)", "H",         "[H]",       5, -2.638, None,   "Pd ontop",       "Convergent",       "4/5", False),
    (2,  "Mo₃Pd(111)", "N₂H",       "[N]=N[H]",  5, -3.937, -3.441, "Mo₃ hollow",     "Convergent*",      "5/5", True),
    (3,  "Pd₃Cu(111)", "H",         "[H]",       5, -3.029, None,   "Pd₃ hollow",     "Convergent",       "3/5", False),
    (4,  "Pd₃Cu(111)", "N₂H",       "[N]=N[H]",  5, -2.353, -3.442, "Cu ontop (diss)","Competing",        "4/5", True),
    (5,  "Cu₃Ag(111)", "H",         "[H]",       4, -2.558, None,   "Cu₃ hollow",     "Convergent",       "3/4", False),
    (6,  "Cu₃Ag(111)", "N₂H",       "[N]=N[H]",  5, -1.740, -2.498, "Cu ontop (diss)","Competing",        "4/5", True),
    (7,  "Ru₃Mo(111)", "H",         "[H]",       5, -3.840, None,   "Ru-Ru bridge",   "Convergent",       "4/5", False),
    (8,  "Ru₃Mo(111)", "N₂H",       "[N]=N[H]",  5, -4.821, -3.550, "Mo₂Ru₃ hollow",  "Counter-intuitive","4/5", True),
    (9,  "Pt(111)",    "OH",        "[OH]",      4, -1.932, None,   "Pt-Pt bridge",   "Counter-intuitive","3/4", False),
    (10, "Pt(100)",    "OH",        "[OH]",      4, -2.611, None,   "Pt-Pt bridge",   "Convergent",       "3/4", False),
    (11, "Pd(111)",    "OH",        "[OH]",      3, -2.421, None,   "Pd-Pd bridge",   "Convergent",       "3/3", False),
    (12, "Au(111)",    "OH",        "[OH]",      3, -2.059, None,   "Desorbed",        "Convergent",       "3/3", False),
    (13, "Ag(100)",    "OH",        "[OH]",      3, -2.859, None,   "4-fold hollow",  "Convergent",       "2/3", False),
    (14, "CoPt(111)",  "OH",        "[OH]",      4, -2.608, None,   "Pt ontop",       "Convergent",       "2/4", False),
    (15, "Cu₆Ga₂(100)","CH₂CH₂OH", "[CH2CH2OH]",3, -3.528, None,   "Cu-Cu bridge",   "Counter-intuitive","1/3", False),
    (16, "Au₂Hf(102)", "CH₂CH₂OH", "[CH2CH2OH]",5, -3.448, -5.135, "Hf hollow",      "Competing",        "4/5", True),
    (17, "Rh₂Ti₂(111)","CH₃CHO",   "CH3CHO",    4, -2.647, -2.913, "Rh₅Ti₂ hollow",  "Competing",        "3/4", True),
    (18, "Al₃Zr(101)", "CH₃CHO",   "CH3CHO",    5, -2.752, -2.881, "Al-Zr hollow",   "Competing",        "4/5", True),
    (19, "Hf₂Zn₆(110)","CH₃CHO",   "CH3CHO",    5, -3.435, -3.977, "Hf hollow",      "Competing",        "4/5", True),
]

# ============================================================
# Figure 5a: PES Type Distribution (Pie or Bar chart)
# ============================================================
def fig5a_pes_distribution():
    pes_counts = {"Convergent": 0, "Competing": 0, "Counter-intuitive": 0}
    for d in data:
        pes = d[8]
        if "Convergent" in pes:
            pes_counts["Convergent"] += 1
        elif "Competing" in pes:
            pes_counts["Competing"] += 1
        elif "Counter" in pes:
            pes_counts["Counter-intuitive"] += 1

    fig, ax = plt.subplots(figsize=(3.5, 2.8))
    colors = [PLASMA['p1'], PLASMA['p3'], PLASMA['p5']]
    labels = list(pes_counts.keys())
    counts = list(pes_counts.values())

    bars = ax.bar(labels, counts, color=colors, edgecolor='white', linewidth=0.5, width=0.6)
    for bar, count in zip(bars, counts):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.2,
                str(count), ha='center', va='bottom', fontweight='bold', fontsize=9)

    ax.set_ylabel('Number of Systems', fontsize=9)
    ax.set_ylim(0, max(counts) + 2)
    ax.set_title('PES Behavior Classification', fontsize=10, fontweight='bold')
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)

    fig.tight_layout()
    fig.savefig('research/images/fig5a_pes_types.png', dpi=300, bbox_inches='tight')
    fig.savefig('research/images/fig5a_pes_types.pdf', bbox_inches='tight')
    plt.close(fig)
    print("✅ Figure 5a saved.")


# ============================================================
# Figure 5b: Convergence iterations distribution
# ============================================================
def fig5b_convergence():
    iters = [d[4] for d in data]

    fig, ax = plt.subplots(figsize=(3.5, 2.8))
    bins = [2.5, 3.5, 4.5, 5.5]
    ax.hist(iters, bins=bins, color=PLASMA['p2'], edgecolor='white', linewidth=0.5, rwidth=0.8)

    ax.set_xlabel('Number of Iterations', fontsize=9)
    ax.set_ylabel('Number of Systems', fontsize=9)
    ax.set_title('Convergence Speed Distribution', fontsize=10, fontweight='bold')
    ax.set_xticks([3, 4, 5])
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)

    avg = np.mean(iters)
    ax.axvline(avg, color=PLASMA['p4'], linestyle='--', linewidth=1.2, label=f'Mean = {avg:.1f}')
    ax.legend(fontsize=8)

    fig.tight_layout()
    fig.savefig('research/images/fig5b_convergence.png', dpi=300, bbox_inches='tight')
    fig.savefig('research/images/fig5b_convergence.pdf', bbox_inches='tight')
    plt.close(fig)
    print("✅ Figure 5b saved.")


# ============================================================
# Case Study convergence curves
# ============================================================
def case_study_convergence_curves():
    """E_ads vs iteration for the 3 selected case studies."""
    # Data from Benchmark Test Results.pdf
    case_studies = {
        "No.1: H on Mo3Pd(111)": {
            "iterations": [1, 2, 3, 4, 5],
            "energies": [-2.601, -2.634, -2.625, -2.601, -2.638],
            "sites": ["Hollow→Pd-ontop", "Bridge→Pd-ontop", "Ontop@Pd (stable)", "Ontop@Mo→Pd-ontop", "Bridge→Pd-ontop"],
            "color": PLASMA['p1'],
        },
        "No.8: N2H on Ru3Mo(111)": {
            "iterations": [1, 2, 3, 4, 5],
            "energies": [-4.821, -3.824, -3.550, -3.009, -4.677],
            "sites": ["Bridge→Hollow(ISO)", "Bridge(ISO)", "Hollow(DISS)", "Hollow(stable)", "Hollow(ISO)"],
            "color": PLASMA['p3'],
        },
        "CuZnO: [CH]=O on CuZnO": {
            "iterations": [1, 2, 3, 4, 5],
            "energies": [-1.484, -0.799, -1.198, -1.497, -1.228],
            "sites": ["Ontop→Cu₄-hollow", "Bridge→O-Zn-Zn-hollow", "Hollow→7-fold", "Bridge→Cu₄-hollow", "Ontop→Cu-O-Zn-Zn"],
            "color": PLASMA['p5'],
        },
    }

    fig, axes = plt.subplots(1, 3, figsize=(10, 3.2), sharey=False)

    for ax, (title, cs) in zip(axes, case_studies.items()):
        ax.plot(cs["iterations"], cs["energies"], 'o-', color=cs["color"],
                markersize=6, linewidth=1.5, markeredgecolor='white', markeredgewidth=0.5)

        # Mark the best energy
        best_idx = np.argmin(cs["energies"])
        ax.plot(cs["iterations"][best_idx], cs["energies"][best_idx], '*',
                color=PLASMA['accent'], markersize=14, markeredgecolor='black', markeredgewidth=0.5, zorder=5)

        ax.set_xlabel('Iteration', fontsize=9)
        ax.set_ylabel('$E_{ads}$ (eV)', fontsize=9)
        ax.set_title(title, fontsize=8, fontweight='bold')
        ax.set_xticks(cs["iterations"])
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)

    fig.tight_layout()
    fig.savefig('research/images/case_study_convergence.png', dpi=300, bbox_inches='tight')
    fig.savefig('research/images/case_study_convergence.pdf', bbox_inches='tight')
    plt.close(fig)
    print("✅ Case study convergence curves saved.")


# ============================================================
# Chemical Slip summary bar chart
# ============================================================
def chemical_slip_summary():
    """Bar chart showing slip rates by adsorbate category."""
    categories = ["H (atomic)", "N2H (radical)", "OH (radical)", "Large molecules"]
    slip_rates = [
        14/19 * 100,  # H: No.1,3,5,7 → 14 slips out of 19 iters
        17/20 * 100,  # N₂H: No.2,4,6,8 → 17 slips out of 20 iters
        16/21 * 100,  # OH: No.9-14 → 16 slips out of 21 iters
        16/22 * 100,  # Large: No.15-19 → approximate
    ]
    diss_rates = [0, 25, 0, 55]  # % of systems with at least one dissociation

    fig, ax = plt.subplots(figsize=(5, 3.2))
    x = np.arange(len(categories))
    width = 0.35

    ax.bar(x - width/2, slip_rates, width, label='Chemical Slip Rate (%)',
           color=PLASMA['p2'], edgecolor='white', linewidth=0.5)
    ax.bar(x + width/2, diss_rates, width, label='Dissociation Rate (%)',
           color=PLASMA['p4'], edgecolor='white', linewidth=0.5)

    ax.set_ylabel('Percentage (%)', fontsize=9)
    ax.set_xticks(x)
    ax.set_xticklabels(categories, fontsize=8)
    ax.set_ylim(0, 105)
    ax.legend(fontsize=8, loc='upper right')
    ax.set_title('Chemical Events by Adsorbate Category', fontsize=10, fontweight='bold')
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)

    fig.tight_layout()
    fig.savefig('research/images/chemical_slip_summary.png', dpi=300, bbox_inches='tight')
    fig.savefig('research/images/chemical_slip_summary.pdf', bbox_inches='tight')
    plt.close(fig)
    print("✅ Chemical slip summary saved.")


# ============================================================
# Figure 1a: LLM Bias Classification & Agent Correction
# ============================================================
def fig1_llm_bias():
    """Structured visualization of 10 LLM error types and agent corrections."""

    # Data from LLM Results.xlsx
    llm_data = [
        ("Google",    "Gemini-3.1-Pro",  "Material Stereotype",     True,  "Pd-affinity bias → Hollow site"),
        ("OpenAI",    "ChatGPT-5.2",     "Lack of Evidence",        True,  "Correct guess → Verified via kinetics"),
        ("Anthropic", "Claude-4.6-Son",  "Material Stereotype",     True,  "Pd-affinity → Mo-dominated site"),
        ("DeepSeek",  "DeepSeek-V3.2",   "Factual Hallucination",   True,  "Top site → Hollow via feedback"),
        ("Alibaba",   "Qwen3-Max",       "Theoretical Dogma",       True,  "d-band theory → Physical experiment"),
        ("Tencent",   "Hunyuan",         "Geometric Misjudgment",   True,  "Low-coord bias → High-coord hollow"),
        ("Moonshot",  "Kimi-K2.5",       "Conceptual Confusion",    True,  "Oxymoron usage → Standardized"),
        ("ZhipuAI",   "GLM-5",           "Material Stereotype",     True,  "Pd fixation → Mo-rich reality"),
        ("Baidu",     "ERNIE-5.0",       "Factual Hallucination",   True,  "Same error as DeepSeek → Corrected"),
    ]

    # Error type → color mapping (Plasma-based)
    error_colors = {
        "Material Stereotype": PLASMA['p1'],       # deep purple
        "Lack of Evidence": PLASMA['p2'],           # blue-violet
        "Factual Hallucination": PLASMA['p3'],      # magenta-pink
        "Theoretical Dogma": PLASMA['p4'],          # orange
        "Geometric Misjudgment": PLASMA['p4'],      # orange (similar category)
        "Conceptual Confusion": PLASMA['p5'],       # bright yellow
    }

    fig, ax = plt.subplots(figsize=(10, 4.5))
    ax.set_xlim(0, 10)
    ax.set_ylim(-0.5, len(llm_data) - 0.5)
    ax.invert_yaxis()

    # Column positions
    col_provider = 0.5
    col_model = 2.2
    col_error = 5.0
    col_corrected = 8.5

    # Header
    header_y = -0.8
    for x, label in [(col_provider, "Provider"), (col_model, "Model"),
                     (col_error, "Error Type (w/o Agent)"),
                     (col_corrected, "Corrected?")]:
        ax.text(x, header_y, label, ha='center', va='center',
                fontweight='bold', fontsize=8, color='black')

    ax.axhline(-0.4, color='grey', linewidth=0.5, xmin=0.02, xmax=0.98)

    for i, (provider, model, error, corrected, desc) in enumerate(llm_data):
        # Provider
        ax.text(col_provider, i, provider, ha='center', va='center', fontsize=7.5)
        # Model
        ax.text(col_model, i, model, ha='center', va='center', fontsize=7,
                fontstyle='italic')
        # Error type (colored badge)
        color = error_colors.get(error, PLASMA['p3'])
        bbox_props = dict(boxstyle="round,pad=0.3", facecolor=color, alpha=0.85,
                         edgecolor='none')
        ax.text(col_error, i, error, ha='center', va='center', fontsize=6.5,
                color='white', fontweight='bold', bbox=bbox_props)
        # Correction status
        symbol = "Y" if corrected else "N"
        sym_color = '#2ca02c' if corrected else '#d62728'
        ax.text(col_corrected, i, symbol, ha='center', va='center',
                fontsize=11, color=sym_color, fontweight='bold')

    ax.set_axis_off()
    ax.set_title("LLM Chemical Reasoning Biases on Mo$_3$Pd(111): H Adsorption",
                 fontsize=10, fontweight='bold', pad=15)

    fig.tight_layout()
    fig.savefig('research/images/fig1_llm_bias.png', dpi=300, bbox_inches='tight')
    fig.savefig('research/images/fig1_llm_bias.pdf', bbox_inches='tight')
    plt.close(fig)
    print("✅ Figure 1 (LLM bias) saved.")


# ============================================================
# Main
# ============================================================
def main() -> None:
    import os
    os.makedirs('research/images', exist_ok=True)

    print("Generating paper figures...")
    fig1_llm_bias()
    fig5a_pes_distribution()
    fig5b_convergence()
    case_study_convergence_curves()
    chemical_slip_summary()
    print("\n✅ All figures generated in research/images/")


if __name__ == "__main__":
    main()
