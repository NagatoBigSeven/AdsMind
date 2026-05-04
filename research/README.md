# Research Assets

This directory contains scripts and artifacts used for benchmarks, figure
generation, and manuscript work. These files are not required to run the main
AdsMind application.

Do not store API keys, workstation credentials, copied external repositories,
downloaded PDFs, or private meeting notes here. Keep public research outputs in
`research/results/` and document which CSV/JSON files are paper-facing.

## Layout

- `agent_eval/`: reproducible benchmark runners, locked manifests, and frozen
  experiment configs.
- `figures/`: canonical paper figure inputs, plotting scripts, selected draft
  outputs, and structure-rendering style references.
- `results/`: curated paper-facing summaries, joined analysis tables, and
  LaTeX table exports. Start from `results/README.md` before plotting.
- `images/`: legacy generated paper figures, if present locally.

## Scripts

- `generate_figures.py`: generates paper figures under `research/images/`
- `figures/figure2_ablation/scripts/plot_figure2_ablation.py`: regenerates the
  current ablation draft figure from curated CSV inputs.
- `generate_slabs.py`: legacy script that fetches the CMU-20 benchmark slabs
  from FAIR-Chem/OCP. The fetched slabs are now committed at
  `datasets/cmu20/`, so this script is only needed if you want to
  re-derive them from source.

## Dependencies

- `generate_figures.py` uses the optional `research` extra from `pyproject.toml`
- `generate_slabs.py` also requires an installed FAIR-Chem/OCP client exposing
  `fairchem.demo.ocpapi`

## Outputs

- Generated figures are written to `research/images/`
- Re-derived CMU20 slabs should be written directly under `datasets/cmu20/`.

## Public-Release Policy

Internal execution plans, local status reports, private runbooks, and
machine-specific recovery notes are intentionally excluded from the public
repository. Keep reproducibility metadata in manifests, frozen configs, scripts,
and `research/results/README.md`.

The GitHub repository should keep only curated paper-facing CSV/JSON/TEX files
under `research/results/`. Raw per-run payloads, complete logs, generated
trajectories, and bulky generated structures should be staged into
`adsmind-paper-artifacts-v0.1.0.zip` using the layout in
`paper-artifacts/MANIFEST.md`, attached to the matching GitHub release, and
archived as the same zip on Zenodo for a DOI.
