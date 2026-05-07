# OCD62 Summaries

Dataset-level summary tables for OCD62. Run directories live under sibling
LLM/force-field folders such as
`gpt54_mace_mp0_small`, and non-LLM baselines live under
`baselines/`.

- `method_comparison.csv`: per-case comparison of AdsMind 1-Shot, AdsMind Full,
  random N=20, heuristic enumeration, and the matched Adsorb-Agent 5-config
  control.
- `ablation_4backend.csv`: unified 62-case x 4-backend x 5-variant ablation
  matrix.

Regenerate with:

```bash
.venv/bin/python research/analysis/build_method_comparison_table.py
.venv/bin/python research/analysis/build_ocd62_summary.py
```
