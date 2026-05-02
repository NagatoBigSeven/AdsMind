# Ablation Insights for Writing

## Core Claim

The clean ablation data support a reliability-first interpretation of AdsMind. Full is not guaranteed to find the deepest basin, but it is substantially more reliable than one-shot planning across both CMU20 and broader OCD-GMAE chemistry.

## Clean Coverage

| Dataset | Attempts | Successful | Natural failures | External failures |
| --- | --- | --- | --- | --- |
| CMU20 | 400 | 393 | 7 | 0 |
| OCD24 | 480 | 465 | 15 | 0 |
| OCD-GMAE rep50 Full vs 1-Shot | 400 | 375 | 25 | 0 |

## Success-Rate Summary

### CMU20

| variant_label | attempts | successful_runs | natural_failures | success_rate |
| --- | --- | --- | --- | --- |
| Full | 80 | 80 | 0 | 1.0 |
| w/o Slip | 80 | 80 | 0 | 1.0 |
| w/o Forbid | 80 | 80 | 0 | 1.0 |
| w/o Term | 80 | 80 | 0 | 1.0 |
| 1-Shot | 80 | 73 | 7 | 0.9125 |

### OCD24

| variant_label | attempts | successful_runs | natural_failures | success_rate |
| --- | --- | --- | --- | --- |
| Full | 96 | 96 | 0 | 1.0 |
| w/o Slip | 96 | 96 | 0 | 1.0 |
| w/o Forbid | 96 | 96 | 0 | 1.0 |
| w/o Term | 96 | 95 | 1 | 0.9896 |
| 1-Shot | 96 | 82 | 14 | 0.8542 |

### OCD-GMAE rep50 Full vs 1-Shot

| variant_label | attempts | successful_runs | natural_failures | success_rate |
| --- | --- | --- | --- | --- |
| Full | 200 | 197 | 3 | 0.985 |
| 1-Shot | 200 | 178 | 22 | 0.89 |

## Success-only Energy Delta Summary

`Delta E = E_variant - E_full`; positive values mean the variant is worse than Full.

### CMU20

| variant_label | paired_successes | mean_delta_E_variant_minus_full_eV | median_delta_E_variant_minus_full_eV | full_lower_by_gt_0p05eV | variant_lower_by_gt_0p05eV | within_pm_0p05eV |
| --- | --- | --- | --- | --- | --- | --- |
| w/o Slip | 80 | -0.008477 | 0.0 | 9 | 11 | 60 |
| w/o Forbid | 80 | -0.007232 | 0.0 | 6 | 10 | 64 |
| w/o Term | 80 | -0.035681 | 0.0 | 5 | 10 | 65 |
| 1-Shot | 73 | 0.216976 | 0.125332 | 41 | 2 | 30 |

### OCD24

| variant_label | paired_successes | mean_delta_E_variant_minus_full_eV | median_delta_E_variant_minus_full_eV | full_lower_by_gt_0p05eV | variant_lower_by_gt_0p05eV | within_pm_0p05eV |
| --- | --- | --- | --- | --- | --- | --- |
| w/o Slip | 96 | 0.013203 | 0.0 | 14 | 11 | 71 |
| w/o Forbid | 96 | 0.015007 | 0.0 | 10 | 6 | 80 |
| w/o Term | 95 | -0.012586 | 0.0 | 7 | 7 | 81 |
| 1-Shot | 82 | 0.3048 | 0.03124 | 40 | 0 | 42 |

### OCD-GMAE rep50 Full vs 1-Shot

| variant_label | paired_successes | mean_delta_E_variant_minus_full_eV | median_delta_E_variant_minus_full_eV | full_lower_by_gt_0p05eV | variant_lower_by_gt_0p05eV | within_pm_0p05eV |
| --- | --- | --- | --- | --- | --- | --- |
| 1-Shot | 178 | 0.36442 | 0.071932 | 97 | 7 | 74 |

## Recommended Manuscript Interpretation

- Strong statement: Full has the best reliability profile: 80/80 CMU20 Full successes, 96/96 OCD24 Full successes, and 197/200 rep50 Full successes.
- Strong statement: 1-Shot is consistently weaker: 73/80 CMU20, 82/96 OCD24, and 178/200 rep50 successes, with success-only mean penalties of +0.217, +0.305, and +0.364 eV.
- Cautious statement: w/o Slip, w/o Forbid, and w/o Term have median deltas near 0 eV. These mechanisms should be framed as reliability/feedback/interpretability controls rather than as mechanisms that always lower final energy.
- Cautious statement: backend-specific behavior exists, but the most defensible cross-backend insight is that the closed loop stabilizes all four backends rather than proving one backend is universally best.
- Failure statement: natural failures are chemistry/structure outcomes after execution, not external service failures. They should be counted in success rates and excluded from success-only energy deltas.

## Avoid Saying

- Do not call the Full reference line `ground truth`; DFT/PBE is the only appropriate ground-truth/reference language when DFT data are used.
- Do not say every ablation mechanism independently improves energy depth.
- Do not hide natural failures by filtering them out without reporting counts.
- Do not mix raw external failures into scientific success/failure statistics.
