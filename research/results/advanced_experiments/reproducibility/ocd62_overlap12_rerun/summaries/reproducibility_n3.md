# OCD62 overlap12-only N=3 reproducibility report

This report summarizes the 12 duplicated OCD62 cases used for run-to-run reproducibility analysis.

## Headline Counts

- Paired comparisons: 240 = 12 cases x 4 backends x 5 variants.
- Matches within 0.001 eV: 112 (46.7%).
- Matches within 0.01 eV: 123 (51.2%).
- Non-outlier mismatches above 0.01 eV: 105 (43.8%).
- Excluded numerical-collapse outliers: 2 (0.8%).
- All-N dissociated (one_shot physics): 6 (2.5%).
- Missing run energies (mixed dissoc + API failures): 4 (1.7%).
- Mean run range: 0.244 eV.
- Max run range: 4.671 eV.

## Counts By Agreement Class

| agreement_class | count |
|---|---:|
| exact_match | 112 |
| match | 11 |
| minor | 21 |
| moderate | 14 |
| divergent | 37 |
| large_divergent | 20 |
| severe | 13 |
| outlier_excluded | 2 |
| dissociation_excluded | 6 |
| missing | 4 |
