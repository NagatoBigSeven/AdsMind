# Result Registries

This directory now has two machine-readable registries that make short result
names auditable without renaming paper-facing paths:

- `RUN_REGISTRY.csv` covers canonical raw result directories plus the retained
  root-level `adsorbagent_mace_gpt54/` comparison source.
- `ANALYSIS_REGISTRY.csv` covers first-level artifacts under `analysis/`.

Rebuild both with:

```bash
python3 research/agent_eval/rebuild_result_registries.py
```

## Naming Policy

Directory names may keep compact backend slugs such as `openai_gpt54`,
`anthropic_sonnet46`, `gemini`, and `grok4` for path stability. Treat those
slugs as labels only. For reproducibility, use `RUN_REGISTRY.csv` fields:

- `backend_display`
- `exact_llm_models`
- `llm_backends`
- `transport_variants`
- `frozen_config_refs`
- `embedded_config_count`
- `manifest_paths`
- `calculator_protocols`

Date tokens such as `20260428` in `analysis/` are historical snapshot labels,
not authority or recency signals. Use `ANALYSIS_REGISTRY.csv` fields
`category` and `preferred_status` before citing an analysis artifact.

Opaque labels such as `retry`, `dryrun`, or any future `vN` suffix should not be
used as the only explanation of a dataset. They must be paired with registry
metadata or a short note in `MIGRATION.md`.

## Current Audit Signals

As of Round 4:

- `RUN_REGISTRY.csv` has 42 rows.
- `ANALYSIS_REGISTRY.csv` has 65 rows.
- 4 run rows are flagged with `mixed_model_ids`; these contain multiple
  embedded model identifiers across per-case `config.json` snapshots and should
  be inspected before aggregating by model.
- 17 analysis rows carry a `date_token` naming flag.
- 5 analysis rows still contain host-specific paths in historical JSON/CSV/MD
  content. These are outside canonical raw data and are tracked in
  `ANALYSIS_REGISTRY.csv` via `host_path_match_count`.

## When Adding Data

1. Add raw per-case data under `canonical_raw/` unless a README explicitly
   preserves a root-level paper-facing path.
2. Prefer descriptive role/dataset/backend slugs over `v1`, `new`, `final`, or
   ad hoc date-only names.
3. If a date-stamped analysis export is useful, keep it under `analysis/`, but
   add or regenerate `ANALYSIS_REGISTRY.csv` so it is not mistaken for the
   authoritative source.
4. Rebuild `canonical_raw/MERGE_QC.csv` after moving raw-result directories.
5. Rebuild both registries after moving raw results, changing configs, or adding
   paper-facing analysis outputs.
