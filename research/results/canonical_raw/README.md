# Canonical Raw Result Directories

This directory contains canonical raw result directories for the paper-facing
`CMU20` and `OCD62` benchmarks. Paper-facing analysis tables are under
`research/results/basic_tests/` and `research/results/advanced_tests/`.

Global coverage checks are recorded in `MERGE_QC.csv`. Rebuild the QC manifest
with:

```bash
python3 research/agent_eval/rebuild_canonical_raw_qc.py
```

Summary-row counts, not `result.json` counts, define ablation completion
because natural failed runs may have summary rows without a per-case result
payload.

Control experiments live under the corresponding dataset, e.g.
`cmu20/controls/` or `ocd62/controls/`, so they remain visibly attached to the
benchmark they audit. Historical comparison numbers should be kept as analysis
outputs rather than as active canonical raw directories.
