# OCD-GMAE 24-Case GPT-5.4 Interim Analysis (2026-04-23)

## Scope

- Combines the existing 10-case OCD-GMAE GPT-5.4 ablation with the newly pulled 14-case extra set.
- This is a single-backend interim analysis only. It must not be presented as the final four-backend OCD24 result until Claude, Gemini, and Grok-4 complete.
- All extra14 result rows were checked against local `result.json`; no API/network/calculator external failures were detected.

## Coverage

| Variant | Attempts | Success | Failures | Success rate | Mean Δ vs Full, success-only (eV) | Median Δ (eV) | Reach/beat Full +0.01 incl. failures |
|---|---:|---:|---:|---:|---:|---:|---:|
| `full` | 24 | 24 | 0 | 100.0% | 0.000 | 0.000 | 24/24 |
| `no_slip` | 24 | 24 | 0 | 100.0% | 0.110 | 0.000 | 15/24 |
| `no_forbid` | 24 | 24 | 0 | 100.0% | 0.110 | 0.000 | 17/24 |
| `no_termination` | 24 | 23 | 1 | 95.8% | 0.024 | 0.000 | 19/24 |
| `single_shot` | 24 | 19 | 5 | 79.2% | 0.317 | 0.015 | 8/24 |

## Failure Audit

- Failed attempts: 6 / 120.
- External/API/network failures: 0.
- All failures are natural dissociation/reaction outcomes and should remain in success-rate denominators.

| Case | Variant | Reason | Dissociation count | Slip count |
|---:|---|---|---:|---:|
| 008 | `no_termination` | natural | 5 | 4 |
| 002 | `single_shot` | natural | 1 | 1 |
| 009 | `single_shot` | natural | 1 | 1 |
| 011 | `single_shot` | natural | 1 | 0 |
| 017 | `single_shot` | natural | 1 | 0 |
| 022 | `single_shot` | natural | 1 | 1 |

## Interpretation

- GPT-5.4 Full remains robust on the combined OCD24 set: 24/24 successful Full runs.
- 1-Shot is much less reliable on the extra14 chemistry: combined GPT-5.4 1-Shot succeeds on 18/24 cases, with six natural failures.
- The mean success-conditioned 1-Shot penalty is large, so the closed-loop benefit on the expanded OCD chemistry is at least as strong as in the original 10-case set; however, final cross-backend conclusions must wait for Claude/Gemini/Grok-4.
- The `no_termination` failure on case 008 is important: disabling termination can expose the run to repeated unstable/dissociative attempts, so the termination module is not only a compute-control device on this expanded set.

## Artifacts

- `gpt54_ocd24_ablation_summary.csv`
- `gpt54_ocd24_case_variant_matrix.csv`
- `gpt54_ocd24_summary.json`
