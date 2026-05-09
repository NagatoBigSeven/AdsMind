# OCD62 overlap12-only N=4 reproducibility report

This report summarizes the 12 duplicated OCD62 cases used for run-to-run reproducibility analysis.

## Headline Counts

- Paired comparisons: 240 = 12 cases x 4 backends x 5 variants.
- Matches within 0.001 eV: 104 (43.3%).
- Matches within 0.01 eV: 111 (46.2%).
- Non-outlier mismatches above 0.01 eV: 126 (52.5%).
- Excluded numerical-collapse outliers: 2 (0.8%).
- Missing run energies: 1 (0.4%).
- Mean run range: 0.339 eV.
- Max run range: 4.700 eV.

## Counts By Agreement Class

| agreement_class | count |
|---|---:|
| exact_match | 104 |
| match | 7 |
| minor | 22 |
| moderate | 17 |
| divergent | 40 |
| large_divergent | 25 |
| severe | 22 |
| outlier_excluded | 2 |
| missing | 1 |
