# research/results/ Data Manifest

This directory contains curated, paper-facing outputs for AdsMind experiments.
The active paper datasets are:

- `CMU20`
- `OCD62`

OCD62 is the 62-case OCD benchmark. The 12 repeated cases are kept only as `overlap12` reproducibility repeats.

## Paper-Facing Entry Points

Use these directories first:

- `basic_tests/`: Full vs 1-Shot, backend range, random/heuristic cost, and brute-force vs iterative method tables.
- `advanced_tests/`: OCD62 four-backend five-variant ablation matrix, overlap reproducibility audit, and documented outlier treatment.

The `analysis/` directory contains rebuild outputs and intermediate analysis
files. Prefer `basic_tests/` and `advanced_tests/` for writing and plotting.

## Basic Tests

| Target | Source |
|---|---|
| Full vs 1-Shot summary | `basic_tests/full_vs_1shot_summary.csv` |
| Method comparison summary | `basic_tests/method_comparison_summary.csv` |
| CMU20 method-comparison detail | `basic_tests/cmu20_method_comparison.csv` |
| OCD62 method-comparison detail | `basic_tests/ocd62_method_comparison.csv` |
| Human-facing method table | `basic_tests/method_comparison_table.md`, `basic_tests/method_comparison_table.tex` |

## Advanced Tests

| Target | Source |
|---|---|
| OCD62 four-backend five-variant matrix | `advanced_tests/ocd62_ablation_4backend.csv` |
| OCD62 overlap12 N=2 reproducibility table | `advanced_tests/ocd62_overlap12_reproducibility_n2.csv` |
| OCD62 overlap12 N=2 report | `advanced_tests/ocd62_overlap12_reproducibility_n2.md` |
| Grok-4 OCD16 outlier diagnosis | `advanced_tests/grok4_ocd16_outlier_diagnosis.md` |

RUN3 overlap outputs are not present yet. When they land, rerun:

```bash
.venv/bin/python research/analysis/build_ocd62_summary.py --write-n3
```

## Raw Results

Active raw sources live under `canonical_raw/`.

- CMU20 raw results live under `canonical_raw/cmu20/`.
- OCD62 raw results live under `canonical_raw/ocd62/`.
- OCD62 overlap12 reproducibility repeats live under
  `canonical_raw/ocd62_overlap12/` with run directories `run1/`, `run2/`,
  and `run3/`.

After moving or adding raw directories, rebuild the machine-readable registries:

```bash
.venv/bin/python research/agent_eval/rebuild_canonical_raw_qc.py
.venv/bin/python research/agent_eval/rebuild_result_registries.py
```

## Variant Names

Use `single_shot` for the one-step ablation variant inside ablation CSVs. Do not
filter ablation tables with `one_shot`.

Core variants:

- `full`
- `no_slip`
- `no_forbid`
- `no_termination`
- `single_shot`
