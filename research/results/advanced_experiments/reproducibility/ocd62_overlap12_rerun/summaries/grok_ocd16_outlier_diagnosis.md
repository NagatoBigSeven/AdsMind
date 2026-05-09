# Grok OCD16 outlier diagnosis

Date: 2026-05-03; updated 2026-05-09

## Scope

This diagnosis covers OCD16 (`Hf18Sc18Si36` + `NO`) in the Grok OCD62 reproducibility run:

- `research/results/advanced_experiments/reproducibility/ocd62_overlap12_rerun/run2/grok4_mace_mp0_small/full/001/result.json`
- `research/results/advanced_experiments/reproducibility/ocd62_overlap12_rerun/run2/grok4_mace_mp0_small/no_forbid/001/result.json`
- related variants for the same case in `research/results/advanced_experiments/reproducibility/ocd62_overlap12_rerun/run2/grok4_mace_mp0_small/`
- matching main OCD62 run `research/results/basic_experiments/ocd62/grok4_mace_mp0_small/full/002/`

## Findings

The corrupted values are not CSV serialization artifacts. In the original run
outputs, they were present in `result.json`, in `agent_log.txt`, and in the
saved `BEST_*.xyz` files:

- run2/full attempt 2: `E_total = -1124687744.0000 eV`, reported adsorption energy `-1124687200.7337 eV`
- run2/no_slip attempt 5: reported adsorption energy below `-2.0e9 eV`; the
  top-level best energy stayed on the healthy attempt, but `last_analysis`
  pointed at the collapsed candidate
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

For the Grok OCD62 overlap12 run2 OCD16 records, the paper-facing `result.json`
files now use the healthy molecular attempt for top-level result fields. The
original unedited payloads are preserved next to them as
`result.raw_mace_collapse.json` for auditability. Structure artifacts are not
rewritten; the official `result.json` artifact pointers now refer to the
healthy copied artifacts.

The patch policy is:

- exclude any molecular candidate with physically impossible energy below `-10000 eV`
- recompute the case-level molecular best from healthy molecular attempts,
  preserving the existing AdsMind semantics that `best_result` tracks molecular
  states while dissociated states are reported separately
- patch paper-facing `best_energy_eV`, `best_result`, `last_analysis`,
  `final_site_type`, and artifact pointers for affected records
- keep the original attempt history and the raw backup so the numerical
  collapse remains auditable
- recompute `delta_vs_full` for the five case rows

Patch CSV:

`research/results/advanced_experiments/reproducibility/ocd62_overlap12_rerun/summaries/grok_ocd16_outlier_patch.csv`

Patched `reproducibility/ocd62_overlap12_rerun/run2/grok/all_variants_summary.csv` rows for case `001`:

| variant | patched best energy (eV) | patched delta vs full (eV) |
|---|---:|---:|
| full | -4.3469638824 | 0.0000000000 |
| no_slip | -4.3469638824 | 0.0000000000 |
| no_forbid | -4.3469638824 | 0.0000000000 |
| no_termination | -4.3469619751 | 0.0000019073 |
| one_shot | -4.3469638824 | 0.0000000000 |

`all_variants_stats.json` was rebuilt from the patched summary and includes a
`patch_note` entry. The affected official JSON files also include a
`patch_provenance` block.

## Reproducibility Table Treatment

The paired comparisons affected by the original top-level numerical collapse
are marked as `outlier_excluded` in:

`research/results/advanced_experiments/reproducibility/ocd62_overlap12_rerun/summaries/reproducibility_n2.csv`

Rows:

- Grok / sid=16 / Full
- Grok / sid=16 / -Forbid

The other three sid=16 Grok variants keep their healthy paired-comparison
classification, but their deltas had depended on the corrupted Full baseline
before the patch; those deltas are now recomputed.
