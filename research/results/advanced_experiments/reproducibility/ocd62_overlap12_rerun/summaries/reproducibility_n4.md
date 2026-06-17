# OCD62 overlap12-only N=4 reproducibility report

This report summarizes the 12 duplicated OCD62 cases used for run-to-run reproducibility analysis.

## Headline Counts

- Paired comparisons: 240 = 12 cases x 4 backends x 5 variants.
- Matches within 0.001 eV: 99 (41.2%).
- Matches within 0.01 eV: 106 (44.2%).
- Non-outlier mismatches above 0.01 eV: 121 (50.4%).
- Excluded numerical-collapse outliers: 2 (0.8%).
- All-N dissociated (one_shot physics): 6 (2.5%).
- Missing run energies (mixed dissoc + API failures): 5 (2.1%).
- Mean run range: 0.307 eV.
- Max run range: 4.700 eV.

## Counts By Agreement Class

| agreement_class | count |
|---|---:|
| exact_match | 99 |
| match | 7 |
| minor | 22 |
| moderate | 17 |
| divergent | 40 |
| large_divergent | 25 |
| severe | 17 |
| outlier_excluded | 2 |
| dissociation_excluded | 6 |
| missing | 5 |
