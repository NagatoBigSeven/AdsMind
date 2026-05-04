# Grok OCD16 outlier diagnosis

Date: 2026-05-03

## Scope

This diagnosis covers OCD16 (`Hf18Sc18Si36` + `NO`) in the Grok OCD62 reproducibility run:

- `research/results/advanced_experiments/reproducibility/ocd62_overlap12/run2/xai_grok4_0709_mace_mp0_small/full/001/result.json`
- `research/results/advanced_experiments/reproducibility/ocd62_overlap12/run2/xai_grok4_0709_mace_mp0_small/no_forbid/001/result.json`
- related variants for the same case in `research/results/advanced_experiments/reproducibility/ocd62_overlap12/run2/xai_grok4_0709_mace_mp0_small/`
- matching main OCD62 run `research/results/basic_experiments/ocd62/xai_grok4_0709_mace_mp0_small/full/002/`

## Findings

The corrupted values are not CSV serialization artifacts. They are present in `result.json`, in `agent_log.txt`, and in the saved `BEST_*.xyz` files:

- run2/full attempt 2: `E_total = -1124687744.0000 eV`, reported adsorption energy `-1124687200.7337 eV`
- run2/no_forbid attempt 2: `E_total = -45282964.0000 eV`, reported adsorption energy `-45282420.7337 eV`
- main/full attempt 2 also produced a numerical-collapse structure (`-37962092.7337 eV`) but the final molecular `best_result` stayed on the healthy first attempt (`-4.3469638824 eV`) because that collapse was classified as dissociated.

ASE inspection shows the copied `relaxation.traj` files for the final healthy attempts have normal energies:

- run2/full `artifacts/relaxation.traj`: 63 frames, min `-551.5184936523 eV`, no frame below `-2000 eV`
- run2/full `artifacts/final.xyz`: `-551.5184936523 eV`
- main/full `artifacts/relaxation.traj`: 79 frames, min `-548.0498046875 eV`, no frame below `-2000 eV`

The abnormal `BEST_NO_ontop_to_hollow_FCC-No-Subsurf_ISO_E-1124687200.734.xyz` file itself contains `energy=-1124687744.0`, very large forces, and very large stress. Thus the root cause is a MACE-MP-0 numerical-collapse relaxation for one candidate structure, followed by the agent accepting that physically impossible molecular attempt as `best_result`.

## Root Cause Classification

Root cause: **(a) MACE-MP-0 numerical collapse during relaxation**, with downstream best-result selection accepting the collapsed candidate.

It is not a JSON serialization bug. It is not caused by byte-level slab differences. It is a real abnormal energy stored in the collapsed `BEST_*.xyz` candidate.

## Patch Policy

For the Grok OCD62 overlap12 run2 OCD16 summary, the raw `result.json` and artifacts are left untouched for auditability. The reproducibility summary is patched at the summary layer:

- exclude any molecular candidate with physically impossible energy below `-10000 eV`
- recompute the case-level molecular best from healthy molecular attempts, preserving the existing AdsMind semantics that `best_result` tracks molecular states while dissociated states are reported separately
- recompute `delta_vs_full` for the five case rows

Patch CSV:

`research/results/advanced_experiments/reproducibility/ocd62_overlap12/summaries/grok_ocd16_outlier_patch.csv`

Patched `reproducibility/ocd62_overlap12/run2/grok/all_variants_summary.csv` rows for case `001`:

| variant | patched best energy (eV) | patched delta vs full (eV) |
|---|---:|---:|
| full | -4.3469638824 | 0.0000000000 |
| no_slip | -4.3469638824 | 0.0000000000 |
| no_forbid | -4.3469638824 | 0.0000000000 |
| no_termination | -4.3469619751 | 0.0000019073 |
| one_shot | -4.3469638824 | 0.0000000000 |

`all_variants_stats.json` was rebuilt from the patched summary and includes a `patch_note` entry.

## Reproducibility Table Treatment

The two corrupted paired comparisons are marked as `outlier_excluded` in:

`research/results/advanced_experiments/reproducibility/ocd62_overlap12/summaries/reproducibility_n2.csv`

Rows:

- Grok / sid=16 / Full
- Grok / sid=16 / -Forbid

The other three sid=16 Grok variants were not outliers, but their deltas had depended on the corrupted Full baseline before the patch; those deltas are now recomputed.
