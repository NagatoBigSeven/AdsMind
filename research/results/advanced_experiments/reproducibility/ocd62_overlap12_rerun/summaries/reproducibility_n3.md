# OCD62 overlap12-only N=3 reproducibility report

This report summarizes the 12 duplicated OCD62 cases used for run-to-run reproducibility analysis.

## Headline Counts

- Paired comparisons: 240 = 12 cases x 4 backends x 5 variants.
- Matches within 0.001 eV: 117 (48.8%).
- Matches within 0.01 eV: 128 (53.3%).
- Non-outlier mismatches above 0.01 eV: 109 (45.4%).
- Excluded numerical-collapse outliers: 2 (0.8%).
- Missing run energies: 1 (0.4%).
- Mean run range: 0.269 eV.
- Max run range: 4.671 eV.

## Counts By Agreement Class

| agreement_class | count |
|---|---:|
| exact_match | 117 |
| match | 11 |
| minor | 21 |
| moderate | 14 |
| divergent | 37 |
| large_divergent | 20 |
| severe | 17 |
| outlier_excluded | 2 |
| missing | 1 |
