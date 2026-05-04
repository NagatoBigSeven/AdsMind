# CMU20 Summaries

Dataset-level summary tables for CMU20. Run directories live under the sibling
backend folders (`gpt`, `claude`, `gemini`, `grok`), and non-LLM baselines live
under `baselines/`.

- `method_comparison.csv`: per-case comparison of AdsMind 1-Shot, AdsMind Full,
  random N=20, heuristic enumeration, and Adsorb-Agent where available.

Regenerate with:

```bash
.venv/bin/python research/analysis/build_method_comparison_table.py
```
