# Figure 2 Ablation Plotting Inputs

This folder is the reproducible plotting handoff for the paper Figure 2 ablation panels.

## Contents

- `data/plot_cmu20_delta_points.csv`: CMU20 success-only energy-delta points.
- `data/plot_ocd24_delta_points.csv`: OCD24 success-only energy-delta points.
- `data/plot_rep50_delta_points.csv`: OCD-GMAE rep50 Full-versus-1-Shot success-only paired energy-delta points.
- `data/failure_audit.csv`: natural and external failure rows for success-rate annotations.
- `figure_caption_notes.md`: caption, axis, and failure-encoding guidance for the figure.
- `scripts/plot_figure2_ablation.py`: lightweight reproducibility script that renders draft PNG/PDF panels from the CSV inputs.
- `output/`: generated draft figures.

## Data Convention

For CMU20 and OCD24:

`Delta E = E_variant - E_full`.

Positive values mean the ablated variant or 1-Shot found a higher, less stable adsorption energy than the same-backend Full run.

For rep50:

`Delta E = E_1shot - E_full`.

Positive values mean iterative Full found a lower-energy configuration.

All delta distributions are success-only. Natural failures are not imputed as zero-energy differences; they are counted separately through `failure_audit.csv`.

## Regeneration

From the repository root:

```bash
python research/results/plotting/figure2_ablation/scripts/plot_figure2_ablation.py
```

The script writes draft figures to `research/results/plotting/figure2_ablation/output/`.
These are not intended to override the final designed figure; they make the plotting inputs and conventions reproducible.

The OCD24 and rep50 panels contain a small number of large positive outliers
(up to approximately 4.67 eV). The draft script keeps the linear scale so no
point is silently hidden; the final designed figure should consider an inset,
axis break, or explicit outlier annotation if the main distribution near zero
needs to remain visually legible.
