# Canonical Raw Result Directories

This directory contains same-protocol split runs merged into canonical raw
result directories.  It is a storage cleanup layer: paper-facing analysis
tables remain under `research/results/analysis/`.

Merged sources are recorded in each directory's `MERGED_SOURCES.json`, and
global coverage checks are recorded in `MERGE_QC.csv`. Rebuild the QC manifest
with:

```bash
python3 research/agent_eval/rebuild_canonical_raw_qc.py
```

The merge intentionally preserves source summaries under `source_summaries/`
and rebuilds canonical root summaries from per-case rows or `result.json`.
Per-case JSON payloads are path-rewritten so artifact references point to this
canonical directory rather than the deleted split-run directories.  Summary-row
counts, not `result.json` counts, define ablation completion because natural
failed runs may have summary rows without a per-case result payload.

Active controls live under `controls/`, including AA single-config, MACE-large,
and multi-seed sensitivity runs. `auxiliary_raw/` is reserved for active
auxiliary evidence such as historical comparison JSON or figure-audit cases.
Superseded and incomplete sources are retained only for provenance under
`superseded_raw_sources/`; do not use those directories for paper statistics.
