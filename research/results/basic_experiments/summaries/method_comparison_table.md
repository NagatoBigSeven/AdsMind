# Brute-force vs iterative search table

Raw adsorption energies are reported in eV; more negative values indicate deeper configurations.

| Dataset | Method | Class | n | Relax/case | Success | Mean E (eV) | Median E (eV) |
|---|---|---|---:|---:|---:|---:|---:|
| CMU20 | AdsMind 1-Shot | open-loop | 20 | 1.00 | 91.2% | -3.817 | -2.928 |
| CMU20 | AdsMind Full | iterative | 20 | 4.19 | 100.0% | -3.900 | -3.200 |
| CMU20 | Random N=20 | brute-force | 20 | 20.00 | 100.0% | -4.197 | -3.253 |
| CMU20 | Heuristic | brute-force | 20 | 56.85 | 100.0% | -4.217 | -3.307 |
| CMU20 | Adsorb-Agent | brute-force | 20 | 21.00 | 80.0% | -4.482 | -4.002 |
| OCD62 | AdsMind 1-Shot | open-loop | 62 | 1.00 | 89.5% | -5.768 | -4.594 |
| OCD62 | AdsMind Full | iterative | 62 | 4.67 | 98.8% | -6.072 | -5.002 |
| OCD62 | Random N=20 | brute-force | 62 | 20.00 | 100.0% | -6.241 | -5.325 |
| OCD62 | Heuristic | brute-force | 62 | 66.03 | 100.0% | -6.755 | -5.656 |
