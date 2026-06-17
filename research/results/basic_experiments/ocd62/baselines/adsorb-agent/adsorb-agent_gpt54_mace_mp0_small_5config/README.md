# Adsorb-Agent GPT-5.4 MACE-MP-0 Small 5-Config Control

This directory contains the paper-facing Adsorb-Agent control for OCD62.

Protocol:

- Baseline method: modified CatalystAIgent/Adsorb-Agent default planner
- LLM: GPT-5.4 (`gpt-5.4-2026-03-05`)
- Force field: MACE-MP-0 small
- Candidate budget: up to 5 generated initial configurations per case
- Internal Adsorb-Agent sampling: `random_ratio=0.2`
- Relaxation: MACE-MP-0 small CPU float32, `fmax=0.10`

Files:

- `summary.csv`: one row per OCD62 case, including status, anomaly-filtered
  adsorption energy, number of generated configurations, and protocol metadata.
- `comparison.csv`: paired AdsMind Full vs Adsorb-Agent comparison.
- `comparison_stats.json`: Wilcoxon, McNemar, rank-biserial, bootstrap, and
  Benjamini-Hochberg statistics derived from `comparison.csv`.
- `config/`: frozen CatalystAIgent/Adsorb-Agent YAML inputs used for the rerun.
- `results/`: raw Adsorb-Agent outputs, including `progress.csv`, per-case
  `result.txt`, `result.pkl`, copied YAML, and relaxation trajectories.
- `catalyst_tools/`: local parser/anomaly helper used to summarize the raw
  CatalystAIgent outputs.

Outcome in this rerun: 62 cases total, 49 successful Adsorb-Agent cases, 10
cases with no selected/generated configurations, and 3 cases rejected by
trajectory anomaly filters.
