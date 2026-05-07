# CMU20 Summaries

Dataset-level summary tables for CMU20. Run directories live under sibling
LLM/force-field folders such as
`gpt54_mace_mp0_small`, and non-LLM baselines live under
`baselines/`.

- `method_comparison.csv`: per-case comparison of AdsMind 1-Shot, AdsMind Full,
  random N=20, heuristic enumeration, and the matched Adsorb-Agent 5-config
  control.

Regenerate with:

```bash
.venv/bin/python research/analysis/build_method_comparison_table.py
```
