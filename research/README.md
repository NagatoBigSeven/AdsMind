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

- `paper_plots/scripts/regenerate_current_main_figures.py`: regenerates the
  current main manuscript figure panels from curated result inputs.
- `analysis/build_method_comparison_table.py`: rebuilds paper-facing method
  comparison CSV/Markdown/LaTeX tables.
- `analysis/build_ocd62_summary.py`: refreshes OCD-GMAE62 reproducibility
  summary tables from curated result directories.
- `datasets/cmu20/download_cmu20_dataset.py`: legacy helper that re-derives the
  AA20 benchmark slabs from FAIR-Chem/OCP. The fetched slabs are already
  committed at `datasets/cmu20/`, so this is only needed for provenance audits.

## Dependencies

- Plotting and table scripts use the optional `research` extra from
  `pyproject.toml`.
- Re-deriving AA20 slabs requires an installed FAIR-Chem/OCP client exposing
  `fairchem.demo.ocpapi`.

## Outputs

- Generated figure panels are written under `research/paper_plots/`.
- Re-derived AA20 slabs should be written directly under `datasets/cmu20/`.

## Public-Release Policy

Internal execution plans, local status reports, private runbooks, and
machine-specific recovery notes are intentionally excluded from the public
repository. Keep reproducibility metadata in manifests, frozen configs, scripts,
and `research/results/README.md`.

The GitHub repository should keep only curated paper-facing CSV/JSON/TEX files
under `research/results/`. Raw per-run payloads, complete logs, generated
trajectories, and bulky generated structures should be staged into
`adsmind-paper-artifacts-v0.1.0.zip` using the layout in
`paper-artifacts/MANIFEST.md` and attached to the matching GitHub release.
