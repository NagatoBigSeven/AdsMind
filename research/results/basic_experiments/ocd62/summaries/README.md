# OCD62 Summaries

Dataset-level summary tables for OCD62. Run directories live under the sibling
backend folders (`gpt`, `claude`, `gemini`, `grok`), and non-LLM baselines live
under `baselines/`.

- `method_comparison.csv`: per-case comparison of AdsMind 1-Shot, AdsMind Full,
  random N=20, and heuristic enumeration.
- `ablation_4backend.csv`: unified 62-case x 4-backend x 5-variant ablation
  matrix.

Regenerate with:

```bash
.venv/bin/python research/analysis/build_method_comparison_table.py
.venv/bin/python research/analysis/build_ocd62_summary.py
```
