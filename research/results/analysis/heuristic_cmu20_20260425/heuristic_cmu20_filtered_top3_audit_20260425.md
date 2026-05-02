# CMU20 Heuristic Connectivity-Filtered Top-3 Audit - 2026-04-25

## Summary
- Saved heuristic top structures audited: 56 top-3 structures across 20 cases.
- Connectivity-valid saved top structures: 41; invalid/dissociated: 15.
- Cases with no valid saved top-3 structure: ['04', '08', '16', '19', '20'].
- Filtered vs AdsMind best-of-four Full: {'tie': 11, 'no_valid_saved_top3': 5, 'heuristic_lower': 3, 'adsmind_lower': 1}.
- Filtered mean delta vs AdsMind best-of-four: -0.024 eV; median -0.003 eV.

## Filtered Case Table
| case | surface | adsorbate | raw heuristic | filtered top3 | selected | delta vs AdsMind | outcome | note |
|---|---|---|---:|---:|---|---:|---|---|
| 01 | Mo3Pd(111) | [H] | -3.637 | -3.637 | 1:hollow_014_conf0 | -0.006 | tie | single_atom |
| 02 | Mo3Pd(111) | [N]=[NH] | -4.777 | -4.777 | 1:hollow_066_conf0 | -0.008 | tie | NN_min=1.294A; NH_min=1.025A |
| 03 | CuPd3(111) | [H] | -3.350 | -3.350 | 1:bridge_018_conf0 | 0.002 | tie | single_atom |
| 04 | CuPd3(111) | [N]=[NH] | -3.470 | NA | NA: | NA | no_valid_saved_top3 | all_saved_top3_invalid_or_dissociated |
| 05 | Cu3Ag(111) | [H] | -2.967 | -2.967 | 1:bridge_055_conf0 | -0.005 | tie | single_atom |
| 06 | Cu3Ag(111) | [N]=[NH] | -2.168 | -2.168 | 1:bridge_020_conf0 | -0.003 | tie | NN_min=1.283A; NH_min=1.040A |
| 07 | Ru3Mo(111) | [H] | -7.051 | -7.051 | 1:bridge_041_conf0 | -0.000 | tie | single_atom |
| 08 | Ru3Mo(111) | [N]=[NH] | -9.209 | NA | NA: | NA | no_valid_saved_top3 | all_saved_top3_invalid_or_dissociated |
| 09 | Pt(111) | [OH] | -1.993 | -1.993 | 1:bridge_008_conf0 | -0.002 | tie | OH_min=0.981A |
| 10 | Pt(100) | [OH] | -2.721 | -2.721 | 1:bridge_011_conf0 | -0.003 | tie | OH_min=0.983A |
| 11 | Pd(111) | [OH] | -2.636 | -2.636 | 1:bridge_022_conf0 | -0.218 | heuristic_lower | OH_min=0.975A |
| 12 | Au(111) | [OH] | -2.361 | -2.361 | 1:bridge_010_conf0 | -0.009 | tie | OH_min=0.979A |
| 13 | Ag(100) | [OH] | -2.828 | -2.828 | 1:hollow_027_conf0 | -0.003 | tie | OH_min=0.978A |
| 14 | CoPt(111) | [OH] | -3.613 | -3.613 | 1:bridge_066_conf0 | 0.003 | tie | OH_min=0.976A |
| 15 | Cu6Ga2(100) | [CH2]CO | -3.226 | -3.226 | 1:bridge_003_conf0 | 0.032 | adsmind_lower | components=1 |
| 16 | Au2Hf(102) | [CH2]CO | -5.376 | NA | NA: | NA | no_valid_saved_top3 | all_saved_top3_invalid_or_dissociated |
| 17 | Rh2Ti2(111) | CC=O | -3.265 | -3.265 | 2:bridge_025_conf0 | -0.024 | heuristic_lower | components=1 |
| 18 | Al3Zr(101) | CC=O | -3.241 | -3.241 | 1:bridge_015_conf0 | -0.112 | heuristic_lower | components=1 |
| 19 | Hf2Zn6(110) | CC=O | -4.696 | NA | NA: | NA | no_valid_saved_top3 | all_saved_top3_invalid_or_dissociated |
| 20 | Bi2Ti6(211) | CN(C)N=O | -11.756 | NA | NA: | NA | no_valid_saved_top3 | all_saved_top3_invalid_or_dissociated |

## Interpretation
This filtered-top3 audit is stricter than the raw heuristic summary but still incomplete: it can reject obvious fragmented adsorbates among saved top structures, but it cannot recover a valid lower-energy structure if it was ranked below top3 and not saved. Therefore, cases with no valid saved top3 should be treated as unresolved rather than as heuristic failures.
The largest raw case-08 heuristic advantage disappears under this connectivity check because all saved low-energy NNH structures are fragmented. The remaining filtered picture still shows heuristic enumeration as a strong depth baseline, but the evidence is less extreme and more consistent with the paper narrative: broader enumeration can find deeper basins at much higher MACE cost, while AdsMind emphasizes reliable closed-loop recovery and lower compute.
