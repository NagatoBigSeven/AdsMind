# OCD62 data layout

Date: 2026-05-04

## Definition

OCD62 is the paper-facing OCD-GMAE benchmark with 62 cases.
The `overlap12` inputs are used only for run-to-run reproducibility analysis.
RUN3 is the third replicate for those 12 cases, not a separate benchmark.

## Manifests

Main benchmark manifest:

`datasets/ocd62/ocd62_manifest.csv`

Reproducibility-repeat manifest:

`datasets/ocd62_overlap12/overlap12_manifest.csv`

## Basic Tests

Paper-facing outputs:

- `research/results/basic_tests/full_vs_1shot_summary.csv`
- `research/results/basic_tests/cmu20_method_comparison.csv`
- `research/results/basic_tests/ocd62_method_comparison.csv`
- `research/results/basic_tests/method_comparison_summary.csv`

## Advanced Tests

Unified OCD62 ablation table:

`research/results/advanced_tests/ocd62_ablation_4backend.csv`

Shape:

`62 cases x 4 backends x 5 variants = 1240 data rows`

Current reproducibility table:

`research/results/advanced_tests/ocd62_overlap12_reproducibility_n2.csv`

Shape:

`12 repeated cases x 4 backends x 5 variants = 240 paired comparisons`

RUN3 will add the N=3 reproducibility table after the remote run lands.

## Raw Result Layout

- OCD62 main results: `research/results/canonical_raw/ocd62/`
- OCD62 overlap12 reproducibility repeats:
  `research/results/canonical_raw/ocd62_overlap12/run1/`,
  `research/results/canonical_raw/ocd62_overlap12/run2/`, and
  `research/results/canonical_raw/ocd62_overlap12/run3/`

Rebuild commands:

```bash
.venv/bin/python research/analysis/build_ocd62_summary.py
.venv/bin/python research/analysis/build_method_comparison_table.py
.venv/bin/python research/agent_eval/rebuild_canonical_raw_qc.py
.venv/bin/python research/agent_eval/rebuild_result_registries.py
```
