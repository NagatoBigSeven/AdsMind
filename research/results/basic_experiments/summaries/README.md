# Basic Experiment Summaries

Cross-dataset summary tables for the matched CMU20 and OCD62 basic experiment
matrix.

- `full_vs_one_shot_summary.csv`: dataset-level Full vs 1-Shot success, energy,
  backend-spread, and baseline-cost summary.
- `method_comparison_summary.csv`: method-level search-depth and outcome
  summary across CMU20 and OCD62.
- `method_comparison_table.md`: human-readable brute-force vs iterative table.
- `method_comparison_table.tex`: manuscript table draft generated from the same
  source data.

Regenerate with:

```bash
.venv/bin/python research/analysis/build_method_comparison_table.py
```
