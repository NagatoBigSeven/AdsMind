# CMU20 Heuristic Baseline Analysis - 2026-04-25

## Scope
This report analyzes the newly pulled `heuristic_baseline_cmu_extra5` results and joins them with the existing locked-15 heuristic baseline to form a CMU20 heuristic enumeration comparison.
All energy differences use `delta = E_heuristic - E_reference`; negative values mean heuristic enumeration found a lower-energy relaxed structure.

## Data Integrity
- Extra5 case summaries: 5/5 case-level successes.
- Extra5 site evaluations: 315 successful / 14 failed across 329 attempted sites.
- No extra5 case has a top-level API/network/calculator error in `result.json`; failed site records are local candidate-level failures inside otherwise successful exhaustive enumeration runs.
- `wall_clock_sec` is not used for performance claims because the remote job was paused/resumed; use attempted site count as the compute proxy.

## Extra5 Case-Level Comparison
| case | surface | adsorbate | heuristic | AdsMind best-of-4 Full | delta vs AdsMind | random N=20 | delta vs random | sites ok/fail |
|---|---|---|---:|---:|---:|---:|---:|---:|
| 03 | CuPd3(111) | [H] | -3.350 | -3.352 | 0.002 | -3.323 | -0.026 | 56/0 |
| 06 | Cu3Ag(111) | [N]=[NH] | -2.168 | -2.165 | -0.003 | -2.679 | 0.511 | 59/0 |
| 07 | Ru3Mo(111) | [H] | -7.051 | -7.051 | -0.000 | -7.042 | -0.010 | 81/3 |
| 08 | Ru3Mo(111) | [N]=[NH] | -9.209 | -7.191 | -2.019 | -7.188 | -2.021 | 73/11 |
| 11 | Pd(111) | [OH] | -2.636 | -2.418 | -0.218 | -2.440 | -0.196 | 46/0 |

Interpretation of extra5: heuristic enumeration ties AdsMind best-of-four on cases 03 and 07, is slightly worse on 06, and is substantially lower on 08 and 11. The raw case 08 gap is large (-2.019 eV relative to AdsMind best-of-four), but the saved top structures fail a simple adsorbate-connectivity check; treat this case as anomaly-flagged, not as a valid heuristic win.

## CMU20 Aggregate
- CMU20 heuristic case success: 20/20.
- Attempted high-symmetry site evaluations: 1137 total, median 56 sites/case, range 25-98.
- Site-level failures: 41/1137; case-level result still succeeds because at least one valid relaxed structure exists.
- Raw versus AdsMind best-of-four Full at 0.01 eV tolerance: {'tie': 11, 'heuristic_lower': 8, 'adsmind_lower': 1}.
- Raw mean delta vs AdsMind best-of-four Full: -0.251 eV; median -0.007 eV.
- After saved-top-3 connectivity filtering, the conservative outcome is {'tie': 11, 'no_valid_saved_top3': 5, 'heuristic_lower': 3, 'adsmind_lower': 1}.
- Filtered mean delta vs AdsMind best-of-four Full over the 15 cases with a valid saved heuristic top-3 structure: -0.024 eV; median -0.003 eV.
- Versus GPT-5.4 Full at 0.01 eV tolerance: {'tie': 7, 'heuristic_lower': 12, 'adsmind_lower': 1}; mean delta -0.313 eV.
- Versus random N=20 at 0.01 eV tolerance: {'tie': 8, 'heuristic_lower': 9, 'random_lower': 3}; mean delta -0.020 eV.

## Largest Raw Gaps vs AdsMind Best-of-Four Full
| direction | case | surface | adsorbate | heuristic | AdsMind | delta | sites |
|---|---|---|---|---:|---:|---:|---:|
| heuristic lower | 08 | Ru3Mo(111) | [N]=[NH] | -9.209 | -7.191 | -2.019 | 84 |
| heuristic lower | 04 | CuPd3(111) | [N]=[NH] | -3.470 | -2.285 | -1.185 | 56 |
| heuristic lower | 16 | Au2Hf(102) | [CH2]CO | -5.376 | -4.663 | -0.713 | 56 |
| heuristic lower | 19 | Hf2Zn6(110) | CC=O | -4.696 | -4.045 | -0.652 | 42 |
| heuristic lower | 11 | Pd(111) | [OH] | -2.636 | -2.418 | -0.218 | 46 |
| AdsMind lower | 15 | Cu6Ga2(100) | [CH2]CO | -3.226 | -3.258 | 0.032 | 34 |
| AdsMind lower | 14 | CoPt(111) | [OH] | -3.613 | -3.617 | 0.003 | 79 |
| AdsMind lower | 03 | CuPd3(111) | [H] | -3.350 | -3.352 | 0.002 | 56 |
| AdsMind lower | 07 | Ru3Mo(111) | [H] | -7.051 | -7.051 | -0.000 | 84 |
| AdsMind lower | 09 | Pt(111) | [OH] | -1.993 | -1.991 | -0.002 | 46 |

These are raw energy gaps. The saved-top-3 connectivity audit invalidates or leaves unresolved four of the five largest raw heuristic wins (04, 08, 16, 19) and also leaves case 20 unresolved because no saved top structure is available.

## Geometry Audit of Extra5 Top Structures
A simple adsorbate-connectivity check was applied to saved top-3 structures for the new extra5 cases. For `[H]`, no internal connectivity check is needed; for `[OH]`, the O-H distance must remain <=1.3 A; for `[N]=[NH]`, the N-N distance must remain <=1.6 A and at least one N-H distance must remain <=1.3 A. This is not a full AdsMind post-relaxation anomaly detector, but it is enough to flag obvious dissociation.

| case | rank | label | E (eV) | verdict | reason |
|---|---:|---|---:|---|---|
| 06 | 1 | bridge_020_conf0 | -2.168 | valid | NN_min=1.283 A; NH_min=1.040 A |
| 06 | 2 | bridge_037_conf0 | -2.057 | invalid_or_dissociated | NN_min=1.150 A; NH_min=3.352 A |
| 06 | 3 | bridge_005_conf0 | -2.054 | invalid_or_dissociated | NN_min=1.151 A; NH_min=3.350 A |
| 08 | 1 | hollow_038_conf0 | -9.209 | invalid_or_dissociated | NN_min=4.914 A; NH_min=1.035 A |
| 08 | 2 | hollow_003_conf0 | -8.782 | invalid_or_dissociated | NN_min=2.898 A; NH_min=1.035 A |
| 08 | 3 | ontop_004_conf0 | -8.058 | invalid_or_dissociated | NN_min=1.209 A; NH_min=2.329 A |
| 11 | 1 | bridge_022_conf0 | -2.636 | valid | OH_min=0.975 A |
| 11 | 2 | ontop_026_conf0 | -2.442 | valid | OH_min=0.988 A |
| 11 | 3 | bridge_015_conf0 | -2.441 | valid | OH_min=0.988 A |

The key extra5 result is case 08: all three saved low-energy heuristic structures are flagged as invalid/dissociated by this simple connectivity check. Therefore the raw case-08 heuristic energy (-9.209 eV) should not be used as a valid NNH adsorption result unless a full anomaly audit identifies a lower valid structure among non-saved candidates.

## Full CMU20 Saved-Top-3 Connectivity Audit
A follow-up audit was applied to all saved heuristic top-3 structures across CMU20. This audit checked 56 saved top-3 structures; 41 passed and 15 were flagged as fragmented or otherwise invalid. Five cases have no valid saved top-3 structure: 04, 08, 16, 19, and 20. These rows are unresolved rather than heuristic failures, because the current artifacts cannot recover a potentially valid non-saved candidate ranked below top3.

The filtered CMU20 heuristic-vs-AdsMind best-of-four outcome is {'tie': 11, 'no_valid_saved_top3': 5, 'heuristic_lower': 3, 'adsmind_lower': 1}. The three validated heuristic-lower cases are 11, 17, and 18; AdsMind is lower on case 15. The largest raw wins in cases 04, 08, 16, and 19 should not be used as chemical winner claims.

## Scientific Interpretation
The completed CMU20 heuristic baseline strengthens, rather than weakens, the current narrative: exhaustive canonical-site enumeration is a strong depth baseline, especially on selected complex systems, while AdsMind is a lower-compute, closed-loop, interpretable approximation rather than a universal deepest-basin solver. However, the largest raw heuristic advantages are anomaly-sensitive. Case 08 is fragmented, cases 04/16/19 have no valid saved top-3 structure, and case 20 lacks a saved top structure for audit.
The new extra5 data add one validated moderate heuristic win (case 11) and show several cases where AdsMind matches heuristic despite using far fewer relaxations (cases 03, 06, and 07). The apparent major extra5 win on case 08 is not chemically validated under the connectivity screen.
The safest manuscript wording is protocol-level: heuristic enumeration can expose lower MACE-small minima on selected cases, but raw lows must be filtered before chemical winner claims.

## Manuscript Impact
- Any statement saying heuristic was only available on 15 locked cases is now stale.
- Replace locked-15 raw heuristic aggregate with the CMU20 saved-top-3 filtered aggregate when discussing completed baselines.
- Update approximate compute range if using CMU20: heuristic now spans 25-98 sites/case with median 56 sites/case; AdsMind Full remains roughly 4 attempts per single-backend Full run.
- Do not cite raw heuristic case 19 or case 08 as validated wins; both are unresolved/invalidated by the saved-top-3 audit.
- Do not use `wall_clock_sec` from the extra5 heuristic run as runtime evidence.
