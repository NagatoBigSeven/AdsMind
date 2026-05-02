# Figure Caption Notes for Ablation Plots

## Required Definition

Use this y-axis definition consistently:

`Error = E_variant - E_full (eV)`

Positive values mean the ablated variant or 1-Shot found a higher, less stable adsorption energy than the same-backend Full run. The zero line is a **Full reference**, not DFT ground truth.

## Failure Encoding

Energy-delta points are success-only. Natural failures must be shown separately, because they do not have reliable `Delta E` values.

Recommended options:

1. Add a small success-rate panel next to the delta plot.
2. Add red N.A. markers or rug/count annotations above each variant group.
3. Put exact failure counts in the caption if space is limited.

Do not encode natural failures as `Delta E = 0` or as missing without annotation.

## Caption Skeleton

CMU20/OCD24 ablation example:

> Ablation energy deltas across LLM backends. Error is defined as `E_variant - E_full` for the same case and backend; positive values indicate a higher, less stable adsorption energy than Full. Points show successful runs only. Natural failures are counted separately in the success-rate annotation/table. Dashed and dotted reference lines indicate 0 eV and +/-0.05 eV tolerance, respectively.

rep50 example:

> Full-versus-1-Shot comparison on the OCD-GMAE rep50 slice. Error is `E_1shot - E_full`; positive values indicate that iterative Full found a lower-energy configuration. Points show backend-case pairs where both variants produced valid relaxed adsorption energies; natural failures are counted separately.

## Counts to Annotate

- CMU20: 400 attempts, 393 successful, 7 natural failures.
- OCD24: 480 attempts, 465 successful, 15 natural failures.
- OCD-GMAE rep50 Full vs 1-Shot: 400 attempts, 375 successful, 25 natural failures.
