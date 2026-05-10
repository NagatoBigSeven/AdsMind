# Basic Experiment Summaries

Single entry point for paper-facing summaries from the matched CMU20 and OCD62
basic experiment matrix. Dataset-level files use an explicit dataset prefix so
remote readers do not need to browse separate `cmu20/summaries` and
`ocd62/summaries` folders.

- `cmu20_method_comparison.csv`: CMU20 per-case comparison of AdsMind 1-Shot,
  AdsMind Full, random N=20, heuristic enumeration, and matched Adsorb-Agent.
- `cmu20_ablation_4backend.csv`: CMU20 four-backend x five-variant ablation
  matrix.
- `ocd62_method_comparison.csv`: OCD62 per-case comparison of the same method
  families.
- `ocd62_ablation_4backend.csv`: OCD62 four-backend x five-variant ablation
  matrix.
- `full_vs_one_shot_summary.csv`: dataset-level Full vs 1-Shot success, energy,
  backend-spread, and baseline-cost summary.
- `method_comparison_summary.csv`: method-level search-depth and outcome
  summary across CMU20 and OCD62. Adsorb-Agent rows use the matched GPT-5.4,
  MACE-MP-0 small, up-to-5-config control for both datasets.
- `method_comparison_table.md`: human-readable brute-force vs iterative table.
- `method_comparison_table.tex`: manuscript table draft generated from the same
  source data.

Regenerate with:

```bash
.venv/bin/python research/analysis/build_method_comparison_table.py
```
