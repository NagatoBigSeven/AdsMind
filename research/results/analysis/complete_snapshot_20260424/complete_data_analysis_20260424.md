# Complete Data Snapshot Analysis (2026-04-24)

## Scope

- This report is based on a full local mirror of `/data/zongmin/workspace/AdsMind/research/results` and `/data/zongmin/CatalystAIgent/results` synchronized on 2026-04-24.
- Formal statistics include only completed datasets without external-failure contamination in the analyzed backend set.
- Grok-4 OCD24 and Grok-4 rep50 Full are explicitly excluded from formal statistics because they are externally blocked by xAI credit/spending-limit 429 failures.

## Readiness Matrix

| Track | Status | What is safe to claim now |
|---|---|---|
| CMU20 five-variant ablation (4 backends) | Formal-ready | Full 80/80, iterative variants 320/320, 1-Shot 73/80 with 7 natural failures |
| OCD24 five-variant ablation (GPT-5.4 + Claude + Gemini) | Formal-ready | 3-backend failure-aware expanded OCD24 analysis |
| OCD24 Grok-4 extra14 | Blocked | Do not use in formal stats; 9 external 429 failures |
| rep50 Full (GPT-5.4 + Claude + Gemini) | Formal-ready | 3-backend Full generalization and 3-backend Full-vs-1-Shot comparison |
| rep50 Full Grok-4 | Blocked | Do not use in formal stats; 50/50 external 429 failures |
| rep50 mechanism (OpenAI/Claude/Gemini) | Partial/in-progress | Progress only, no formal claims yet |
| rep50 mechanism Grok-4 | Blocked | 150/150 external 429 failures |
| MACE-large CMU20 / OCD-rep10 | Completed, unchanged | Previous sensitivity conclusions still hold |
| CMU20 random control | Completed, unchanged | Previous random-vs-Full conclusions still hold |
| CMU heuristic extra5 | Partial | Keep heuristic claims on 15-case only |
| P6 multiseed seed43 | Partial | Not analyzable yet |
| Adsorb-Agent GPT-5.4 single-config | Completed, unchanged | Previous stress-test conclusions still hold |

## CMU20 Carry-Forward (unchanged since 2026-04-23)

- Full succeeds on 80/80; iterative variants succeed on 320/320; 1-Shot succeeds on 73/80.
- Full backend agreement: mean range 0.153 eV, median 0.029 eV, 8/20 within 0.01 eV, 12/20 within 0.05 eV.
- Random vs AdsMind Full best-of-four: mean random-minus-AdsMind delta -0.232 eV; random lower on 6/20, tie on 10/20, AdsMind lower on 4/20.
- Adsorb-Agent single-config stress test: 6/20 no-selected-config failures; among 12 comparable pairs, single-config is worse than original multi-config on all cases (mean +1.109 eV).
- MACE-large sensitivity (unchanged): CMU20 mean absolute shift 1.255 eV (0.834 eV excluding case 20); OCD-rep10 succeeds on 9/10.

## OCD24 Expanded Ablation (formal 3-backend set: GPT-5.4, Claude, Gemini)

Grok-4 is excluded from this formal analysis because the extra14 run is contaminated by external xAI 429 failures.

Provenance note: the formal OCD24 table is assembled from the audited locked10 subset (`003, 004, 005, 012, 013, 015, 016, 019, 023, 024`) plus the extra14 extension (`001, 002, 006, 007, 008, 009, 010, 011, 014, 017, 018, 020, 021, 022`). For `single_shot`, this locked10+extra14 partition is used intentionally, rather than blindly pooling every historical one-shot rerun, so the 24-case table has a single non-duplicated provenance path.

| Variant | Attempts | Success | Failures | Success rate | Mean Δ vs Full, success-only (eV) | Median Δ (eV) | Reach/beat Full +0.01 incl. failures |
|---|---:|---:|---:|---:|---:|---:|---:|
| `full` | 72 | 72 | 0 | 100.0% | 0.000 | 0.000 | 72/72 |
| `no_slip` | 72 | 72 | 0 | 100.0% | 0.026 | 0.000 | 57/72 |
| `no_forbid` | 72 | 72 | 0 | 100.0% | 0.041 | 0.000 | 58/72 |
| `no_termination` | 72 | 71 | 1 | 98.6% | 0.009 | 0.000 | 59/72 |
| `single_shot` | 72 | 61 | 11 | 84.7% | 0.337 | 0.063 | 24/72 |

- OCD24 3-backend Full succeeds on 72/72 runs.
- OCD24 3-backend 1-Shot succeeds on 61/72 runs; all failures are natural dissociation/reaction outcomes.
- OCD24 3-backend `no_termination` is no longer purely a compute-control ablation on the expanded chemistry: it contains 1 natural failure (case 008 on GPT-5.4) with repeated dissociation attempts.
- Full 3-backend range across the 24 OCD cases: mean 0.201 eV. One-Shot range, conditioned on cases with at least two successful backends, is 0.406 eV over 20 cases.
- In the case-level best-of-3 view, 1-Shot reaches or beats Full within 0.01 eV on only 8/24 cases; `no_slip` reaches that threshold on 21/24; `no_forbid` on 22/24; `no_termination` on 20/24.

## Grok-4 Blocked Batches

- OCD24 extra14 Grok-4: 9 failed runs are external xAI 429 credit/spending-limit failures. These runs are blocked, not scientific failures, and should not be pooled with GPT-5.4/Claude/Gemini.
- rep50 Full Grok-4: 50/50 runs failed externally with xAI 429; the batch is unusable for formal analysis.
- rep50 mechanism Grok-4: 150/150 runs failed externally with xAI 429; the batch is unusable for formal analysis.

## rep50 Full Generalization (formal 3-backend set: GPT-5.4, Claude, Gemini)

- Full success rate: 148/150 = 98.7%.
- One-Shot success rate on the same 3 backends: 132/150 = 88.0%.
- Full failures are limited to case 043 on GPT-5.4 and Gemini, both natural dissociation/reaction outcomes; no external failures occur in the 3-backend Full set.
- Across backend-case pairs where both Full and One-Shot succeed, the mean one-shot-minus-full energy gap is 0.345 eV and the median is 0.067 eV; positive means Full is lower (better).
- In the case-level best-of-3 view, over the 48 comparable cases with both a successful Full and a successful One-Shot among the three clean backends, Full vs One-Shot mean gap is 0.251 eV and median 0.030 eV. Cases 025 and 043 are excluded from this best-of-3 comparison because no clean-backend One-Shot success is available.
- Full 3-backend agreement on cases with at least two successful backends: mean range 0.120 eV over 49 cases.

| Backend | Paired success count | Mean (1-Shot - Full) eV | Median eV | Full lower | Tie | 1-Shot lower |
|---|---:|---:|---:|---:|---:|---:|
| GPT-5.4 | 44 | 0.264 | 0.032 | 23 | 17 | 4 |
| Claude Sonnet 4.6 | 45 | 0.357 | 0.035 | 26 | 19 | 0 |
| Gemini Vertex | 43 | 0.414 | 0.113 | 28 | 11 | 4 |

| Surface family | Full success | One-Shot success |
|---|---:|---:|
| compound | 30/30 | 29/30 |
| intermetallic | 117/117 | 103/117 |
| monometallic | 1/3 | 0/3 |

## Partial / In-Progress Datasets (do not use formally yet)

- rep50 mechanism GPT-5.4: 64 completed rows so far; 1 ambiguous non-API failure on `no_slip/043` (`error=None`, `calc_failure_count=1`, `dissociation_count=1`).
- rep50 mechanism Claude: 42 completed rows so far; current failures are external 529 overloaded API errors, so this partial batch is not statistically usable yet.
- rep50 mechanism Gemini: 20 completed rows so far; no observed failures in the completed subset.
- CMU heuristic extra5: 2/5 completed; keep heuristic claims on the original 15-case set for now.
- P6 multiseed seed43: 1/20 completed; not analyzable yet.

## Bottom Line

- The local mirror is now complete enough for a serious multi-dataset snapshot analysis.
- The strongest new formal addition since the last CMU20 report is the OCD expanded chemistry result: OCD24 is now analyzable on three clean backends, and the closed-loop advantage remains strong when natural failures are counted rather than hidden.
- rep50 Full is also now analyzable on three clean backends and substantially outperforms rep50 1-Shot on both reliability and energy depth.
- Grok-4 should be treated as blocked infrastructure, not as a scientific negative result, until the new key arrives and the affected batches are rerun.

## Artifacts

- `inventory.csv`
- `ocd24_three_backend_variant_summary.csv`
- `ocd24_three_backend_case_variant_summary.csv`
- `ocd24_three_backend_casebest_variant_summary.csv`
- `rep50_full_three_backend_rows.csv`
- `rep50_one_shot_three_backend_rows.csv`
- `rep50_full_vs_one_shot_three_backend_backend_summary.csv`
- `rep50_case_best_full_vs_one_shot.csv`
- `rep50_family_success_summary.csv`
- `grok_blocked_ocd24_failures.csv`
- `grok_blocked_rep50_full_failures.csv`
- `grok_blocked_rep50_mechanism_failures.csv`
