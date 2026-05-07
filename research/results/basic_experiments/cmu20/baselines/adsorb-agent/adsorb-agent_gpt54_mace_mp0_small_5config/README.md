# Adsorb-Agent GPT-5.4 MACE-MP-0 Small 5-Config Control

This directory contains the paper-facing Adsorb-Agent control for CMU20.

Protocol:

- Baseline method: modified CatalystAIgent/Adsorb-Agent default planner
- LLM: GPT-5.4 (`gpt-5.4-2026-03-05`)
- Force field: MACE-MP-0 small
- Candidate budget: up to 5 generated initial configurations per case
- Internal Adsorb-Agent sampling: `random_ratio=0.2`
- Relaxation: MACE-MP-0 small CPU float32, `fmax=0.10`

Files:

- `summary.csv`: one row per CMU20 case, including status, anomaly-filtered
  adsorption energy, number of generated configurations, and protocol metadata.
- `comparison.csv`: paired AdsMind Full vs Adsorb-Agent comparison.
- `comparison_stats.json`: Wilcoxon, McNemar, rank-biserial, bootstrap, and
  Benjamini-Hochberg statistics derived from `comparison.csv`.

Outcome in this rerun: 20 cases total, all 20 successful, 38 generated
relaxation trajectories in total, and 1.90 relaxations per case on average.
