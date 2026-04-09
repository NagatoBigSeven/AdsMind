# Research Assets

This directory contains scripts and artifacts used for benchmarks, figure
generation, and manuscript work. These files are not required to run the main
AdsMind application.

## Scripts

- `generate_figures.py`: generates paper figures under `research/images/`
- `generate_slabs.py`: fetches benchmark slabs for the research dataset

## Dependencies

- `generate_figures.py` uses the optional `research` extra from `pyproject.toml`
- `generate_slabs.py` also requires an installed FAIR-Chem/OCP client exposing
  `fairchem.demo.ocpapi`

## Outputs

- Generated figures are written to `research/images/`
- Benchmark slabs are written to `benchmark_slabs/`
