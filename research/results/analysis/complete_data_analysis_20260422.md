# Complete Data Analysis — 2026-04-22

This report is an internal, data-first analysis of the complete data already pulled from the EPFL LIAC workstation on 2026-04-22. It deliberately excludes still-running queues and does not update Overleaf manuscript files.

## Executive Summary

The newly complete data are enough to support a defensible near-term story, but not enough to replace the full ablation matrix. The cleanest completed result is the CMU20 AdsMind Full matrix: 20 cases × 4 LLM backends = 80 successful Full runs. This establishes search reliability for the Full agent on the full CMU20 scope.

The strongest new caution is that broader sampling remains energetically competitive. After adding the five missing random-baseline cases, random N=20 beats AdsMind best-of-four on 6/20 CMU cases, AdsMind beats random on 4/20, and 10/20 are tied within 0.01 eV under the repository's current random-baseline protocol. This should be framed as a reliability/compute-efficiency trade-off, not as AdsMind energy dominance.

The MACE-large data support a force-field sensitivity claim rather than DFT-like validation. CMU20 MACE-large has 20/20 summary successes but large absolute shifts, with mean absolute shift 1.255 eV relative to GPT-5.4 MACE-small. Case 20 is an anomaly/sensitivity case, not a clean success.

Adsorb-Agent single-config control is useful as SI defense: it produces exactly one configuration on 14/20 cases, and on the 12 cases where derived adsorption energies are comparable to the original multi-config Adsorb-Agent run, single-config loses to multi-config on all 12. This supports the interpretation that Adsorb-Agent's deeper energies are primarily due to breadth/multi-configuration enumeration.

## Newly Complete Data Inventory

| Data directory | Scope | Complete use now? | Notes |
|---|---:|---:|---|
| `cmu_extra5_*_ablation_v1/full/` | 5 missing CMU cases × 4 backends × Full | yes | fills CMU20 Full only; non-Full variants still running remotely |
| `random_baseline_cmu_extra5_n20/` | 5 missing CMU cases × 20 random poses | yes | completes CMU20 random when joined with `random_baseline_n20/` |
| `mace_large_gpt54_cmu20_full_v1/` | CMU20 × GPT-5.4 Full × MACE-large | yes | force-field sensitivity, not primary benchmark |
| `mace_large_gpt54_ocd_rep10_full_v1/` | 10 representative OCD-rep50 cases × GPT-5.4 Full × MACE-large | yes | 9/10 success; case 043 natural failure |
| `adsorbagent_single_config_gpt54_cmu20/` | CMU20 single-config CatalystAIgent control | self-contained | 14/20 results; 6 no-selected-config cases |

Generated analysis artifacts:

- `research/results/analysis/cmu20_full_backend_matrix_20260422.csv`
- `research/results/analysis/cmu20_full_backend_stats_20260422.csv`
- `research/results/analysis/cmu_extra5_full_detail_20260422.csv`
- `research/results/analysis/random_vs_adsmind_cmu20_20260422.csv`
- `research/results/analysis/mace_large_cmu20_sensitivity_20260422.csv`
- `research/results/analysis/mace_large_ocd_rep10_sensitivity_20260422.csv`
- `research/results/analysis/adsorbagent_single_config_analysis_20260422.csv`

Legacy `research/results/mace_large_gpt54/ablation_summary.csv` exists with 5 rows. It is the old 5-case sensitivity table and should not be mixed with the new CMU20 directory except as historical context.

## Data Boundaries and Definitions

- `best_energy` / `best_energy_eV` in AdsMind ablation summaries is adsorption energy in eV; lower is better.
- CMU20 Full combines the existing locked CMU15 Full rows with the newly pulled extra5 Full result JSONs. It is not the completed CMU20 5-variant ablation matrix.
- Random-baseline success means MACE relaxation/energy calculation success. The current random summary does not explicitly apply the same anomaly filtering used in AdsMind/Adsorb-Agent summaries.
- MACE-large comparisons are same planner/backend family but different force-field protocol. They quantify sensitivity, not absolute truth.
- Adsorb-Agent single-config `result.txt` stores raw total energy. Derived adsorption energies in this report use the original multi-config Adsorb-Agent reference offset `best_total_energy - best_adsorption_energy_eV` when that offset is available.

## CMU Extra5 Full Runs

All five previously missing CMU cases now have Full-variant results for all four LLM backends. These data fill the reliability gap in the Full agent but do not yet fill mechanism ablations.

| case | surface | ads | Gemini | Grok | GPT-5.4 | Claude | range | best/tie |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 03 | CuPd3(111) | [H] | -3.352 | -3.352 | -3.352 | -3.352 | 0.000 | Gemini 2.5 Pro;Grok-4;GPT-5.4;Claude Sonnet 4.6 |
| 06 | Cu3Ag(111) | [N]=[NH] | -2.165 | -1.875 | -2.165 | -1.875 | 0.290 | Gemini 2.5 Pro;GPT-5.4 |
| 07 | Ru3Mo(111) | [H] | -7.051 | -7.051 | -7.031 | -7.051 | 0.020 | Gemini 2.5 Pro;Grok-4;Claude Sonnet 4.6 |
| 08 | Ru3Mo(111) | [N]=[NH] | -6.414 | -6.414 | -7.191 | -6.869 | 0.776 | GPT-5.4 |
| 11 | Pd(111) | [OH] | -2.389 | -2.418 | -2.381 | -2.418 | 0.037 | Grok-4;Claude Sonnet 4.6 |

Observations:

- All 20 new extra5 Full rows are successful.
- Case 03 is perfectly backend-convergent at the reported precision.
- Case 08 is the major extra5 backend-disagreement case: GPT-5.4 finds -7.191 eV, Claude finds -6.869 eV, and Gemini/Grok-4 remain at -6.414 eV.
- Case 06 also has a meaningful backend split: Gemini/GPT-5.4 find about -2.165 eV, whereas Grok-4/Claude find about -1.875 eV.

## CMU20 AdsMind Full Across Four Backends

Completeness:

| Metric | Value |
|---|---:|
| Full runs expected | 80 |
| Full runs available | 80 |
| Successful Full runs | 80 |
| Failed Full runs | 0 |
| Backend success rate | 100% |

Backend aggregate statistics:

| backend | mean E | median E | mean iters | mean slip | diss cases | mean tokens | unique best | tied best |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Gemini 2.5 Pro | -3.885 | -3.240 | 4.45 | 3.20 | 7 | 36666 | 0 | 13 |
| Grok-4 | -3.891 | -3.193 | 4.35 | 2.95 | 5 | 33997 | 2 | 13 |
| GPT-5.4 | -3.905 | -3.249 | 3.80 | 2.55 | 3 | 25070 | 1 | 11 |
| Claude Sonnet 4.6 | -3.911 | -3.249 | 4.10 | 2.70 | 5 | 35685 | 1 | 14 |

Cross-backend range statistics:

| Metric | Value |
|---|---:|
| Mean range | 0.153 eV |
| Median range | 0.0287 eV |
| Maximum range | 0.776 eV |
| Max-range case | 08 |
| Cases within 0.01 eV | 8/20 |
| Cases within 0.05 eV | 12/20 |
| Cases within 0.10 eV | 12/20 |

Largest backend-disagreement cases:

| case | surface | ads | range eV | best backend(s) | energy vector Gemini/Grok/GPT/Claude |
| --- | --- | --- | --- | --- | --- |
| 08 | Ru3Mo(111) | [N]=[NH] | 0.776 | GPT-5.4 | -6.414/-6.414/-7.191/-6.869 |
| 18 | Al3Zr(101) | CC=O | 0.405 | Grok-4 | -2.779/-3.129/-2.724/-2.724 |
| 16 | Au2Hf(102) | [CH2]CO | 0.391 | Gemini 2.5 Pro;Grok-4;Claude Sonnet 4.6 | -4.663/-4.663/-4.272/-4.663 |
| 17 | Rh2Ti2(111) | CC=O | 0.375 | GPT-5.4;Claude Sonnet 4.6 | -3.222/-2.866/-3.241/-3.241 |
| 06 | Cu3Ag(111) | [N]=[NH] | 0.290 | Gemini 2.5 Pro;GPT-5.4 | -2.165/-1.875/-2.165/-1.875 |
| 12 | Au(111) | [OH] | 0.270 | Gemini 2.5 Pro;Grok-4;Claude Sonnet 4.6 | -2.351/-2.351/-2.081/-2.351 |
| 04 | CuPd3(111) | [N]=[NH] | 0.225 | Claude Sonnet 4.6 | -2.060/-2.255/-2.255/-2.285 |
| 19 | Hf2Zn6(110) | CC=O | 0.203 | Grok-4 | -3.841/-4.045/-4.013/-4.013 |

Interpretation:

- The Full agent is reliable across LLM backends on CMU20, but backend convergence is uneven.
- Aggregate backend means are close, which supports a robustness narrative at the distribution level.
- Per-case backend spread remains material for complex or ambiguous systems, so claims should avoid implying backend invariance case-by-case.

## CMU20 Random Baseline After Adding Extra5

The added random-baseline data close the five-case hole in CMU20 random comparison. For the five new cases alone:

| case | random | AdsMind best-of-4 | delta | outcome |
| --- | --- | --- | --- | --- |
| 03 | -3.323 | -3.352 | 0.029 | adsmind_lower |
| 06 | -2.679 | -2.165 | -0.514 | random_lower |
| 07 | -7.042 | -7.051 | 0.010 | tie |
| 08 | -7.188 | -7.191 | 0.002 | tie |
| 11 | -2.440 | -2.418 | -0.021 | random_lower |

Combined CMU20 outcomes versus AdsMind best-of-four Full, using a 0.01 eV tie threshold:

| Outcome | Count |
|---|---:|
| Random lower than AdsMind | 6/20 |
| AdsMind lower than random | 4/20 |
| Tie | 10/20 |
| Mean random-minus-AdsMind-best delta | -0.232 eV |
| Median random-minus-AdsMind-best delta | -0.000005 eV |
| Largest random advantage | case 16 (-2.074 eV) |
| Largest AdsMind advantage | case 19 (+0.477 eV) |

Versus GPT-5.4 Full alone:

| Outcome | Count |
|---|---:|
| Random lower than GPT-5.4 AdsMind | 9/20 |
| GPT-5.4 AdsMind lower than random | 4/20 |
| Tie | 7/20 |

Interpretation:

- The random baseline is not a straw baseline. Breadth finds deeper basins in several cases, especially case 16.
- The publishable claim should be that AdsMind obtains a reliable, interpretable, low-relaxation-budget solution, not that it dominates random in energy.
- Before turning random wins into a chemical statement, the random top structures must be passed through the same anomaly detector used for AdsMind/Adsorb-Agent. Otherwise the comparison is protocol-valid but chemically under-filtered.

## MACE-Large CMU20 Sensitivity

CMU20 MACE-large completed all 20 rows. It should be treated as force-field sensitivity because the physical backend changes from the primary MACE-small CPU protocol to MACE-large.

| Metric | Value |
|---|---:|
| Rows | 20 |
| Summary successes | 20/20 |
| Mean large-minus-small shift | 0.124 eV |
| Median large-minus-small shift | -0.423 eV |
| Mean absolute shift | 1.255 eV |
| Median absolute shift | 0.714 eV |
| Mean absolute shift excluding case 20 | 0.834 eV |
| Median absolute shift excluding case 20 | 0.606 eV |
| More stable under MACE-large | 15/20 (01,02,03,04,05,09,10,11,12,13,15,16,17,18,19) |
| Less stable under MACE-large | 5/20 (06,07,08,14,20) |
| Tie within 0.01 eV | 0/20 |
| Cases with dissociation_count > 0 | 06,16,17,20 |

Largest force-field shifts:

| case | surface | ads | small GPT | large GPT | shift | diss | flag |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 20 | Bi2Ti6(211) | CN(C)N=O | -11.652 | -2.402 | 9.251 | 4 | high_dissociation_or_extreme_shift |
| 07 | Ru3Mo(111) | [H] | -7.031 | -4.818 | 2.213 | 0 | high_dissociation_or_extreme_shift |
| 19 | Hf2Zn6(110) | CC=O | -4.013 | -6.131 | -2.119 | 0 | high_dissociation_or_extreme_shift |
| 08 | Ru3Mo(111) | [N]=[NH] | -7.191 | -5.385 | 1.806 | 0 | high_dissociation_or_extreme_shift |
| 16 | Au2Hf(102) | [CH2]CO | -4.272 | -5.734 | -1.462 | 1 | high_dissociation_or_extreme_shift |

Interpretation:

- Absolute adsorption energies are highly force-field sensitive.
- The sign and magnitude of the shift are case-dependent: MACE-large often stabilizes adsorption relative to MACE-small, but not always.
- Case 20 is the most important caveat. The summary row is `success=True` because a retained non-dissociated best result exists at -2.402 eV, but the run also contains four dissociated attempts, and the last dissociated analysis reaches -11.197 eV but is not retained as a valid best adsorption state. This is an anomaly/sensitivity case, not a clean validation point.
- These results defend the manuscript's locked-physics design: primary comparisons should remain within MACE-small, while MACE-large is used to show sensitivity boundaries.

## MACE-Large OCD-GMAE rep10 Sensitivity

The OCD representative run provides a stress-test view on chemistry outside CMU. It is complete as a 10-row dataset, but not a clean positive-only result.

| case | surface | family | ads | energy | success | iters | slip | diss | bucket |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 003 | Na12Pb36 | intermetallic | [H] | -3.126 | True | 5 | 5 | 0 | cmu_exact |
| 006 | Ca16Pb16Pd16 | intermetallic | [OH] | -6.534 | True | 5 | 3 | 0 | cmu_exact |
| 012 | Sb20Ta60 | intermetallic | [N]=N | -10.620 | True | 5 | 5 | 4 | small_n_species |
| 020 | Pb24Y8 | intermetallic | [N]=O | -2.286 | True | 5 | 5 | 1 | small_n_species |
| 024 | Cd24Pd24 | intermetallic | NO | -3.123 | True | 5 | 3 | 0 | small_n_species |
| 027 | Cr36N48 | compound | [CH]=O | -7.819 | True | 4 | 2 | 0 | small_organic |
| 035 | Se48Sn48 | compound | CO | -3.387 | True | 5 | 1 | 1 | small_organic |
| 039 | As40Ti40 | compound | C[O] | -8.640 | True | 5 | 4 | 0 | small_organic |
| 043 | K20 | monometallic | C([CH2])O |  | False | 1 | 1 | 1 | small_organic |
| 050 | Ni38Se40 | compound | [CH2]C | -9.525 | True | 5 | 4 | 0 | small_organic |

| Metric | Value |
|---|---:|
| Rows | 10 |
| Successful rows | 9/10 |
| Failed rows | 1/10 |
| Failed case | 043 |
| Dissociation cases | 012,020,035,043 |
| Successful-energy mean | -6.118 eV |
| Successful-energy median | -6.534 eV |

Interpretation:

- Case 043 fails naturally: result JSON reports `status=failed`, `error=None`, `calc_failure_count=0`, `chemical_slip_count=1`, and `dissociation_count=1`.
- This is not an API/network failure and should not be silently replaced by rerunning the same frozen protocol.
- If a retry is scientifically useful, it should be labeled as a separate relaxed/retry protocol, not merged into this frozen sensitivity set.

## Adsorb-Agent Single-Config Control

The single-config control directly tests whether Adsorb-Agent's energy depth survives when the breadth of initial configurations is removed. It does not produce a clean 20/20 table, but it is useful as a mechanistic control.

| case | single status | single Eads derived | multi Eads | single-multi | single-AdsMind GPT | multi configs |
| --- | --- | --- | --- | --- | --- | --- |
| 01 | no_selected_config |  | -3.879 |  |  | 29 |
| 02 | no_selected_config |  | -5.097 |  |  | 2 |
| 03 | success |  |  |  |  |  |
| 04 | success | -1.687 | -2.915 | 1.228 | 0.568 | 34 |
| 05 | no_selected_config |  |  |  |  |  |
| 06 | success | -1.871 | -2.243 | 0.372 | 0.294 | 23 |
| 07 | no_selected_config |  | -6.726 |  |  | 17 |
| 08 | success | -4.768 | -7.142 | 2.374 | 2.422 | 24 |
| 09 | success | -1.805 | -1.997 | 0.192 | 0.186 | 25 |
| 10 | success | -2.369 | -2.741 | 0.373 | 0.341 | 22 |
| 11 | success | -1.730 | -2.577 | 0.847 | 0.651 | 19 |
| 12 | success | -1.491 | -2.245 | 0.754 | 0.590 | 23 |
| 13 | success | -1.691 | -2.857 | 1.166 | 1.134 | 25 |
| 14 | success | -3.998 | -4.125 | 0.127 | -0.407 | 8 |
| 15 | no_selected_config |  |  |  |  |  |
| 16 | no_selected_config |  | -5.700 |  |  | 20 |
| 17 | success | -4.003 | -4.476 | 0.473 | -0.762 | 31 |
| 18 | success |  |  |  |  |  |
| 19 | success | -3.521 | -4.707 | 1.186 | 0.491 | 18 |
| 20 | success | -8.071 | -12.285 | 4.214 | 3.581 | 16 |

Summary:

| Metric | Value |
|---|---:|
| Case directories | 20 |
| Single-config successful outputs | 14/20 |
| No-selected-config or missing cases | 6/20 (01,02,05,07,15,16) |
| Successful config counts | 1 |
| Mean tokens on successful single-config cases | 4499 |
| Median tokens on successful single-config cases | 4555 |
| Comparable single-vs-multi cases | 12 |
| Single-config lower than multi-config | 0/12 |
| Multi-config lower than single-config | 12/12 |
| Tie within 0.01 eV | 0/12 |
| Mean single-minus-multi adsorption energy | 1.109 eV |
| Median single-minus-multi adsorption energy | 0.800 eV |

Interpretation:

- On all 12 comparable cases, multi-config Adsorb-Agent is lower in energy than single-config Adsorb-Agent.
- The control supports the mechanism that Adsorb-Agent's energy advantage comes from broad enumeration of many initial configurations.
- The control also shows a reliability cost: single-config produces no selected configuration on 6/20 cases.
- Because the adsorption energies are derived from reference offsets rather than emitted directly by CatalystAIgent, this table should be used as SI/control evidence, not as the main headline plot.

## What This Data Can Support Today

Strong claims currently supported:

1. CMU20 Full AdsMind reliability: 80/80 successful Full runs across four backends.
2. Backend aggregate robustness with nontrivial per-case exceptions.
3. Random/breadth baselines are energetically competitive, so AdsMind should be framed around reliability, interpretability, and compute-efficiency, not energy dominance.
4. MACE-large sensitivity is substantial; locked-physics comparisons are scientifically necessary.
5. Adsorb-Agent multi-config breadth is central to its lower-energy performance.

Claims not yet supported by the newly complete data:

1. CMU20 5-variant ablation statistics. Only Full is complete for CMU20; non-Full variants are still running remotely.
2. OCD24 or OCD rep50 full ablation conclusions. The new full/mechanism queues have not completed.
3. A main-text claim that random wins are chemically valid without anomaly filtering.
4. A clean 20/20 AA single-config control.

## Recommended Manuscript Use

Near-term figure/table usage:

- Use CMU20 Full success and backend range for a robustness/reliability panel.
- Use random CMU20 as a compute-depth baseline, but label it as current-protocol random until anomaly filtering is applied.
- Use MACE-large CMU20/OCD rep10 as a force-field sensitivity panel or SI table.
- Use AA single-config as SI defense that breadth matters.
- Keep mechanism ablation claims based on the existing locked CMU15/OCD10 matrices until CMU20 5-variant runs complete.

Do not update `overleaf/sections/2_Method.tex`; Lou/Yuyang is editing it.

## Immediate Follow-Ups

1. Run anomaly detection on the top random baseline structures, especially cases where random is lower than AdsMind.
2. After P1 finishes, rebuild CMU20 ablation summaries and rerun pairwise statistics.
3. Resume paused P6/P5 only after P1 completes or after deciding they are no longer needed for the current paper version.
4. Keep OCD24/OCD rep50 full ablation as a background expansion, not as a blocking dependency for today's manuscript work.
