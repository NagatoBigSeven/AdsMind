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

CMU20/OCD62 ablation example:

> Ablation energy deltas across LLM backends. Error is defined as `E_variant - E_full` for the same case and backend; positive values indicate a higher, less stable adsorption energy than Full. Points show successful runs only. Natural failures are counted separately in the success-rate annotation/table. Dashed and dotted reference lines indicate 0 eV and +/-0.05 eV tolerance, respectively.

## Counts to Annotate

- CMU20: see `data/failure_audit.csv` for failed run counts and `data/plot_cmu20_delta_points.csv` for success-only deltas.
- OCD62: see `data/failure_audit.csv` for failed run counts and `data/plot_ocd62_delta_points.csv` for success-only deltas.

## Outlier Display

OCD62 contains large positive errors.
If these panels are drawn on a linear scale, the main mass near zero becomes visually compressed.
For the final figure, prefer an inset, axis break, or labelled outlier marker rather than clipping or silently dropping those points.
