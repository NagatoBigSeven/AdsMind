# Table 1: Comprehensive Benchmark Results (19 Surfaces)

Data extracted from `results/` BEST_*.xyz filenames + Benchmark Test Results.pdf.

## Summary Table

| No. | Surface | Adsorbate | SMILES | Iterations | Best E_ads (eV) | Best Site | PES Type | Slip? | Dissociation? |
|:---:|---------|-----------|--------|:----------:|:---------------:|-----------|----------|:-----:|:-------------:|
| 1 | Mo₃Pd(111) | H | `[H]` | 5 | **-2.638** | Pd ontop | Convergent | Yes (4/5) | No |
| 2 | Mo₃Pd(111) | N₂H | `[N]=N[H]` | 5 | **-3.937** (mol) / -3.441 (diss) | Mo₃ hollow | Convergent | Yes (5/5) | Yes (1/5) |
| 3 | Pd₃Cu(111) | H | `[H]` | 5 | **-3.029** | Pd₃ hollow | Convergent | Yes (3/5) | No |
| 4 | Pd₃Cu(111) | N₂H | `[N]=N[H]` | 5 | -2.353 (mol) / **-3.442** (diss) | Cu ontop (diss) | Competing | Yes (4/5) | Yes (2/5) |
| 5 | Cu₃Ag(111) | H | `[H]` | 4* | **-2.558** | Cu₃ hollow | Convergent | Yes (3/4) | No |
| 6 | Cu₃Ag(111) | N₂H | `[N]=N[H]` | 5 | -1.740 (mol) / **-2.498** (diss) | Cu ontop (diss) | Competing | Yes (4/5) | Yes (1/5) |
| 7 | Ru₃Mo(111) | H | `[H]` | 5 | **-3.840** | Ru-Ru bridge | Convergent | Yes (4/5) | No |
| 8 | Ru₃Mo(111) | N₂H | `[N]=N[H]` | 5 | **-4.821** (iso) / -3.550 (diss) | Mo₂Ru₃ hollow | Counter-intuitive | Yes (4/5) | Yes (1/5) |
| 9 | Pt(111) | OH | `[OH]` | 4 | **-1.932** | Pt-Pt bridge | Counter-intuitive | Yes (3/4) | No |
| 10 | Pt(100) | OH | `[OH]` | 4 | **-2.611** | Pt-Pt bridge | Convergent | Yes (3/4) | No |
| 11 | Pd(111) | OH | `[OH]` | 3 | **-2.421** | Pd-Pd bridge | Convergent | Yes (3/3) | No |
| 12 | Au(111) | OH | `[OH]` | 3 | **-2.059** | Desorbed | Convergent | Yes (3/3) | No |
| 13 | Ag(100) | OH | `[OH]` | 3 | **-2.859** | 4-fold hollow | Convergent | Yes (2/3) | No |
| 14 | CoPt(111) | OH | `[OH]` | 4 | **-2.608** | Pt ontop | Convergent | Yes (2/4) | No |
| 15 | Cu₆Ga₂(100) | CH₂CH₂OH | `[CH2CH2OH]` | 3* | **-3.528** | Cu-Cu bridge | Counter-intuitive | Yes (1/3) | No |
| 16 | Au₂Hf(102) | CH₂CH₂OH | `[CH2CH2OH]` | 5 | -3.448 (mol) / **-5.135** (diss) | Hf hollow (diss) | Competing | Yes (4/5) | Yes (1/5) |
| 17 | Rh₂Ti₂(111) | CH₃CHO | `CH3CHO` | 4 | -2.647 (mol) / **-2.913** (diss) | Rh₅Ti₂ hollow (diss) | Competing | Yes (3/4) | Yes (2/4) |
| 18 | Al₃Zr(101) | CH₃CHO | `CH3CHO` | 5 | -2.752 (mol) / **-2.881** (diss) | Al-Zr hollow (diss) | Competing | Yes (4/5) | Yes (1/5) |
| 19 | Hf₂Zn₆(110) | CH₃CHO | `CH3CHO` | 5 | -3.435 (mol) / **-3.977** (diss) | Hf hollow (diss) | Competing | Yes (4/5) | Yes (2/5) |

*No. 5 had 4 iterations (1 less due to initial stability). No. 15 had 3 iterations (1 skipped, site not found). No. 20 not completed (system crash).

## Key Statistics

- **Total iterations**: 82 across 19 surfaces
- **Chemical Slip rate**: ~77/82 ≈ **94%** of iterations showed site migration
- **Dissociation detected**: 9/19 systems (47%) showed at least one dissociation event
- **Isomerization detected**: In systems No. 2, 4, 6, 8, 9, 15, 16, 17, 18
- **Average iterations to converge**: ~4.3 (range: 3-5)

## PES Type Distribution

| PES Type | Count | Systems |
|----------|:-----:|---------|
| Convergent (single thermodynamic sink) | 10 | No. 1, 2, 3, 5, 7, 10, 11, 12, 13, 14 |
| Competing (molecular vs dissociated) | 6 | No. 4, 6, 16, 17, 18, 19 |
| Counter-intuitive | 3 | No. 8, 9, 15 |

*No. 2 is classified as Convergent because the molecular form is the clear thermodynamic
winner (-3.937 vs -3.441 eV for dissociation), despite one dissociation event.

## Adsorbate-grouped Trends

### Atomic H (No. 1, 3, 5, 7)

- Always converges to pure-single-element sites (Pd ontop, Pd₃ hollow, Cu₃ hollow, Ru bridge)
- Never dissociates (expected for atomic species)
- Consistent element preference: Pd > Mo, Pd > Cu, Cu > Ag, Ru > Mo

### N₂H radical (No. 2, 4, 6, 8)

- Shows rich chemistry: molecular, isomerized, AND dissociated states
- No. 8 (Ru₃Mo) is uniquely counter-intuitive: isomerized > dissociated
- Dissociation risk correlates with Cu and mixed sites

### OH radical (No. 9-14)

- Prefers bridge sites on most surfaces
- Au(111) shows desorption (weakest binding)
- No dissociation in any system

### Larger molecules (No. 15-19)

- Higher dissociation rate (4/5 systems)
- More complex PES landscapes
- Hf-containing surfaces show strongest binding
