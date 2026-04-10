# Phase 5 Report: Grok-4 Ablation Matrix Completed

## Status

Phase 5 is complete for the locked Grok-4 representative set:

- cases: `01`, `02`, `09`, `14`, `19`
- variants: `full`, `no_slip`, `no_forbid`, `no_termination`
- single-shot baseline: loaded from `research/results/cmu_v1_xai_progressive_one_shot`

Primary outputs:

- `research/results/xai_ablation_v2/ablation_summary.csv`
- `research/results/xai_ablation_v2/ablation_stats.json`

## Work Completed

1. Finished `no_forbid` for all five Grok-4 ablation cases.
2. Finished `no_termination` for all five Grok-4 ablation cases.
3. Rebuilt the full Grok-4 ablation matrix from disk to avoid the partial-summary overwrite behavior of `run_ablation.py`.
4. Verified that every new case directory contains a successful `result.json`.

## Final Matrix

| Case | full | no_slip | no_forbid | no_termination | single_shot |
|------|------|---------|-----------|----------------|-------------|
| 01 | -3.6317 | -3.6317 | -3.6317 | -3.6317 | -3.6312 |
| 02 | -4.7660 | -4.7660 | -4.7600 | -4.7660 | -4.1505 |
| 09 | -1.9739 | -1.9739 | -1.9739 | -1.9739 | -1.9739 |
| 14 | -3.6166 | -3.6166 | -3.6166 | -3.6166 | -3.2451 |
| 19 | -4.0447 | -3.5939 | -3.5939 | -4.0272 | -3.5939 |

## Main Findings

1. `single_shot` is the clearest weak baseline.
   - relative to `full`, it is worse by about `+0.615 eV` on case `02`
   - worse by about `+0.372 eV` on case `14`
   - worse by about `+0.451 eV` on case `19`

2. `no_slip` and `no_forbid` are nearly indistinguishable from `full` on easy and medium cases, but both fail on the hard case `19`.
   - `no_slip/19`: `+0.4508 eV` vs `full`
   - `no_forbid/19`: `+0.4508 eV` vs `full`
   - `no_forbid/02` is only slightly worse than `full` by `+0.0060 eV`

3. `no_termination` behaves like a cost ablation more than an accuracy ablation.
   - it matches `full` on `01`, `02`, `09`, and `14`
   - it is only `+0.0175 eV` worse on `19`
   - token use rises materially on some cases, especially `09`

4. Case `19` remains the dominant stress test.
   - it is the only case where removing slip-oriented guidance clearly hurts Grok-4
   - during `no_termination/19`, one attempt found a more stable dissociated structure at `-4.3786 eV`
   - the final locked best remained the best non-dissociated state at `-4.0272 eV`, so the runtime is not silently switching objectives

## Statistics

From `research/results/xai_ablation_v2/ablation_stats.json`:

- Friedman test across the five variants: `p = 0.0185`
- pairwise Wilcoxon vs `full`:
  - `no_slip`: `p = 1.0`
  - `no_forbid`: `p = 0.5`
  - `no_termination`: `p = 1.0`
  - `single_shot`: `p = 0.125`
- Benjamini-Hochberg corrected pairwise values remain non-significant on this five-case set

Interpretation:

- the matrix shows a real variant effect at the whole-table level
- the pairwise sample size is too small to support a strong significance claim variant-by-variant
- the safe claim is pattern-level and effect-size based, not “statistically proven per switch”

## Runtime Notes

- `no_termination/09` exhausted validation retries after repeated duplicate or invalid plans and still preserved the earlier best energy. This is expected behavior after the validator-budget fix.
- `no_termination` substantially increases token burn without meaningful energy gain on four of the five cases.
- The ablation outputs are now complete enough to support paper tables and cross-LLM narrative updates.

## What I Need From You

Nothing for this phase.

If you want the next step, the best options are:

1. update paper-facing tables and prose from the completed Grok-4 matrix
2. build a combined Gemini-vs-Grok ablation comparison table
3. package the current benchmark and ablation artifacts for handoff
