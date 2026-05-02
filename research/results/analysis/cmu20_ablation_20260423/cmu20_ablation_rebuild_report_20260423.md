# CMU20 Ablation Rebuild and Failure Audit (2026-04-23)

## Scope

- Rebuilt CMU20 ablation by merging the original CMU15 directories with the newly pulled CMU extra5 directories.
- Backends: Gemini Vertex, Grok-4, GPT-5.4, Claude Sonnet 4.6.
- Variants: Full, -Slip, -Forbid, -Term, 1-Shot.
- No original CMU15 or extra5 result directories were overwritten; all merged artifacts are under this analysis directory.

## Artifacts

- `gemini_cmu20_ablation_summary.csv`
- `grok4_cmu20_ablation_summary.csv`
- `gpt54_cmu20_ablation_summary.csv`
- `claude_cmu20_ablation_summary.csv`
- `cmu20_multi_backend_ablation_summary.csv`
- `cmu20_case_best_by_variant.csv`
- `cmu20_ablation_summary.json`
- `cmu20_failure_classification.json`

## Coverage

| Variant | Success / 80 backend-runs | Failures | Success rate |
|---|---:|---:|---:|
| `full` | 80/80 | 0 | 100.0% |
| `no_slip` | 80/80 | 0 | 100.0% |
| `no_forbid` | 80/80 | 0 | 100.0% |
| `no_termination` | 80/80 | 0 | 100.0% |
| `single_shot` | 73/80 | 7 | 91.2% |

## Failure Classification

- Total failed backend-runs: 7.
- External/API/network failures: 0.
- All failures are `single_shot` natural failures: `error=None`, `calc_failure_count=0`, `dissociation_count=1`, and no best energy.
- The relaxation/analyzer itself returned a completed analysis for these attempts, but `is_dissociated=True` and `reaction_detected=True`; the run-level result correctly rejects them as invalid adsorption configurations.
- Statistical implication: these rows must be counted as failed attempts in success-rate and reach-Full metrics. Energy averages/deltas are conditional on successful runs and should be labeled as such.

| Backend | Case | Variant | Reason | Iterations | Dissociations |
|---|---:|---|---|---:|---:|
| Gemini Vertex | 06 | `single_shot` | natural_dissociation | 1 | 1 |
| Grok-4 | 06 | `single_shot` | natural_dissociation | 1 | 1 |
| Grok-4 | 08 | `single_shot` | natural_dissociation | 1 | 1 |
| GPT-5.4 | 06 | `single_shot` | natural_dissociation | 1 | 1 |
| GPT-5.4 | 08 | `single_shot` | natural_dissociation | 1 | 1 |
| Claude Sonnet 4.6 | 06 | `single_shot` | natural_dissociation | 1 | 1 |
| Claude Sonnet 4.6 | 08 | `single_shot` | natural_dissociation | 1 | 1 |

## Per-Run Variant Performance

Delta is variant energy minus same-backend Full energy. Lower is better. Failures are counted in the denominator for reach-Full counts but excluded from conditional energy/delta means.

| Variant | Success | Mean Δ vs Full, success-only (eV) | Median Δ (eV) | Better | Tie | Worse | Reach/beat Full +0.01 incl. failures |
|---|---:|---:|---:|---:|---:|---:|---:|
| `full` | 80/80 | 0.000 | 0.000 | 0 | 80 | 0 | 80/80 |
| `no_slip` | 80/80 | -0.008 | 0.000 | 15 | 56 | 9 | 71/80 |
| `no_forbid` | 80/80 | -0.007 | 0.000 | 15 | 56 | 9 | 71/80 |
| `no_termination` | 80/80 | -0.036 | 0.000 | 13 | 58 | 9 | 71/80 |
| `single_shot` | 73/80 | 0.217 | 0.125 | 3 | 23 | 47 | 26/80 |

## Case-Level Best-of-Backend Performance

For each case and variant, this uses the lowest energy found among the four backends. This is a reporting upper bound, not the cost of a single run.

| Variant | Cases with energy | No-success cases | Mean Δ vs Full-best, success-only (eV) | Median Δ (eV) | Better | Tie | Worse | Reach/beat Full +0.01 incl. failures |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `full` | 20/20 | 0 | 0.000 | 0.000 | 0 | 20 | 0 | 20/20 |
| `no_slip` | 20/20 | 0 | -0.018 | 0.000 | 3 | 17 | 0 | 20/20 |
| `no_forbid` | 20/20 | 0 | -0.003 | 0.000 | 3 | 16 | 1 | 19/20 |
| `no_termination` | 20/20 | 0 | -0.002 | 0.000 | 1 | 17 | 2 | 18/20 |
| `single_shot` | 19/20 | 1 | 0.125 | 0.001 | 0 | 11 | 8 | 11/20 |

## Full Backend Agreement

- Full succeeds in 80/80 backend-runs.
- Across four backends, per-case Full energy range: mean 0.153 eV, median 0.029 eV, maximum 0.776 eV at case 08.
- Backend Full energies agree within 0.01 eV for 8/20 cases and within 0.05 eV for 12/20 cases.

## Manuscript Implications

- It is now justified to upgrade statements from a CMU20 Full-only control to a CMU20 five-variant ablation, but only where the text explicitly distinguishes Full success from 1-Shot natural failures.
- Safe headline: Full AdsMind reaches 80/80 successful CMU backend-runs, while 1-Shot has 73/80 successful backend-runs because case 06 fails on all four backends and case 08 fails on three of four.
- Do not claim 1-Shot energy means over all 80 backend-runs; it has censored failures. Use conditional energy/delta language or success-rate language.
- The strongest robustness claim is success/recovery: iterative feedback turns the difficult extra5 cases from 1-Shot dissociation failures into successful Full searches, not that every ablation variant strictly improves energy in every case.

## Recommended Paper Update

- Update Introduction/Results/SI from “CMU20 Full control” to “CMU20 five-variant ablation” after citing the rebuilt artifacts above.
- Preserve the existing Full-control numbers as the Full row/subclaim.
- Add a short caveat in Results/SI that 1-Shot failures are physical dissociation outcomes, not API failures.
- Do not update Method in this pass.
