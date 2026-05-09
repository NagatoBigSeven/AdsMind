# OCD62 overlap12-only N=2 reproducibility report

This report summarizes the 12 duplicated OCD62 cases used for run-to-run reproducibility analysis.

## Headline Counts

- Paired comparisons: 240 = 12 cases x 4 backends x 5 variants.
- Matches within 0.001 eV: 138 (57.5%).
- Matches within 0.01 eV: 150 (62.5%).
- Non-outlier mismatches above 0.01 eV: 78 (32.5%).
- Excluded numerical-collapse outliers: 2 (0.8%).
- All-N dissociated (one_shot physics): 6 (2.5%).
- Missing run energies (mixed dissoc + API failures): 4 (1.7%).
- Mean run range: 0.160 eV.
- Max run range: 4.671 eV.

## Counts By Agreement Class

| agreement_class | count |
|---|---:|
| exact_match | 138 |
| match | 12 |
| minor | 17 |
| moderate | 12 |
| divergent | 27 |
| large_divergent | 16 |
| severe | 6 |
| outlier_excluded | 2 |
| dissociation_excluded | 6 |
| missing | 4 |
