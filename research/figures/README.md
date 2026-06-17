# Paper Figure Assets

This directory is the canonical home for paper figure inputs, plotting scripts,
and selected reproducible draft outputs.

## Layout

- `panel_a_pipeline/`: pipeline figure image used by the manuscript. The
  editable PPT source is not currently tracked in this repository.
- `panel_b_blender/`: CatDT-style Blender structure-rendering workspace used to
  define the default AdsMind summarizer visualization style.
- `panel_b_ovito/`: OVITO rendering workspace for optional native OVITO
  structure snapshots.
- `figure2_ablation/`: reproducible Figure 2 ablation plotting package,
  including CSV inputs, plotting script, caption notes, and draft outputs.

## Conventions

- Keep paper-facing plotting inputs and scripts here, not under
  `research/results/plotting/` or root-level `plots/`.
- Keep benchmark result tables and machine-readable summaries under
  `research/results/`.
- Bulky generated render batches can stay local unless they are explicitly
  selected as manuscript assets.
- The runtime AdsMind summarizer visualizer mirrors the same Panel-B color,
  radius, camera, and lighting conventions from this directory's established
  Blender/OVITO configuration.
