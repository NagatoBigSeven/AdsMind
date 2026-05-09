# OCD62 overlap12-only N=5 reproducibility report

This report summarizes the 12 duplicated OCD62 cases used for run-to-run reproducibility analysis.

## Headline Counts

- Paired comparisons: 240 = 12 cases x 4 backends x 5 variants.
- Matches within 0.001 eV: 83 (34.6%).
- Matches within 0.01 eV: 91 (37.9%).
- Non-outlier mismatches above 0.01 eV: 145 (60.4%).
- Excluded numerical-collapse outliers: 2 (0.8%).
- Missing run energies: 2 (0.8%).
- Mean run range: 0.409 eV.
- Max run range: 4.700 eV.

## Counts By Agreement Class

| agreement_class | count |
|---|---:|
| exact_match | 83 |
| match | 8 |
| minor | 26 |
| moderate | 17 |
| divergent | 45 |
| large_divergent | 31 |
| severe | 26 |
| outlier_excluded | 2 |
| missing | 2 |
