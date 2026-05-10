# OCD62 overlap12-only N=5 reproducibility report

This report summarizes the 12 duplicated OCD62 cases used for run-to-run reproducibility analysis.

## Headline Counts

- Paired comparisons: 240 = 12 cases x 4 backends x 5 variants.
- Matches within 0.001 eV: 78 (32.5%).
- Matches within 0.01 eV: 86 (35.8%).
- Non-outlier mismatches above 0.01 eV: 140 (58.3%).
- Excluded numerical-collapse outliers: 2 (0.8%).
- All-N dissociated (one_shot physics): 6 (2.5%).
- Missing run energies (mixed dissoc + API failures): 6 (2.5%).
- Mean run range: 0.379 eV.
- Max run range: 4.700 eV.

## Counts By Agreement Class

| agreement_class | count |
|---|---:|
| exact_match | 78 |
| match | 8 |
| minor | 26 |
| moderate | 17 |
| divergent | 45 |
| large_divergent | 31 |
| severe | 21 |
| outlier_excluded | 2 |
| dissociation_excluded | 6 |
| missing | 6 |
