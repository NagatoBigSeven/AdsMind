# Phase 0 Report

## Scope

Phase 0 covered the prerequisites defined in
[`research/EXPERIMENT_PLAN.md`](/Users/nagato/workspace/AdsMind/research/EXPERIMENT_PLAN.md):

- resolve SMILES for all 20 CMU benchmark cases
- build the CMU manifest
- freeze the first benchmark configuration

## What Was Done

1. Reconstructed the actual previous AdsMind inputs from local artifacts in
   [`results/`](/Users/nagato/workspace/AdsMind/results).
2. Recovered the original manual command lines for cases 3-19 from
   [`logs/`](/Users/nagato/workspace/AdsMind/logs) and promoted them to the
   authoritative source for those cases.
3. Traced Adsorb-Agent's local configuration structure in
   [`CatalystAIgent/`](/Users/nagato/workspace/AdsMind/CatalystAIgent) and
   confirmed that complex examples rely on an external metadata pickle that is
   not present in this workspace.
4. Verified the local filename sanitization logic in
   [`src/tools/common.py`](/Users/nagato/workspace/AdsMind/src/tools/common.py),
   which explains:
   - `CC_O` <- `CC=O`
   - `CN(C)N_O` <- `CN(C)N=O`
5. Opened prior trajectory artifacts with ASE and checked the recovered
   `adsorbate_formula` values:
   - case 15 / 16 -> `C2H5O`
   - case 17 / 18 / 19 -> `C2H4O`
   - case 20 reconstructed artifacts -> `C2H6N2O`
6. Updated the following Phase 0 assets:
   - [`research/agent_eval/reports/SMILES_RESOLUTION.md`](/Users/nagato/workspace/AdsMind/research/agent_eval/reports/SMILES_RESOLUTION.md)
   - [`research/agent_eval/manifests/cmu_manifest.csv`](/Users/nagato/workspace/AdsMind/research/agent_eval/manifests/cmu_manifest.csv)
   - [`research/agent_eval/configs/frozen_config.json`](/Users/nagato/workspace/AdsMind/research/agent_eval/configs/frozen_config.json)

## Key Findings

- Cases 15-16 are not ambiguous anymore for AdsMind reproducibility purposes:
  the previous local runs used `[CH2]CO`, and the trajectory metadata confirms a
  `C2H5O` adsorbate.
- Cases 17-19 are best reconstructed as `CC=O` from local evidence.
- Case 20 is best reconstructed as `CN(C)N=O` from local evidence.
- The benchmark config is now locked to `gemini-3.1-pro-preview` plus the
  least-pressure macOS MACE setting: `cpu + small + float32 + no dispersion`.
- [`results/20`](/Users/nagato/workspace/AdsMind/results/20) is empty, but the
  case 20 artifacts were previously written at the top level of
  [`results/`](/Users/nagato/workspace/AdsMind/results). This is an archival
  problem we must account for in the new batch runner.

## Problems Encountered

1. The authoritative Adsorb-Agent metadata source is missing locally:
   `updated_sid_to_details.pkl` is referenced by the clone but not present.
2. Cases 15-20 therefore cannot yet be certified as the original
   Adsorb-Agent-side metadata values; they are the best local reconstruction of
   the previous AdsMind inputs.
3. The experimental plan says case 20 was failed and empty; in practice, partial
   outputs exist but were stored outside the expected subdirectory.

## Information Still Needed From You

These do not block Phase 1 implementation, but they matter for final paper-grade
reproducibility:

1. If you have any record of the exact SMILES used in the previous manual runs
   for cases 17-20, that would supersede the current reconstruction.
2. If you have the Adsorb-Agent supplementary table or the missing metadata
   pickle, I can upgrade cases 17-20 from "best local reconstruction" to
   "authoritative mapping".
3. If you want a different default ablation subset than `01, 02, 09, 14, 19`,
   tell me before Phase 5.

## Phase Status

Phase 0 is complete enough to proceed to Phase 1.
