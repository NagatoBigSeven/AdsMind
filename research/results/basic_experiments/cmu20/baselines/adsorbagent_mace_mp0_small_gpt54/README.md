# Adsorb-Agent MACE-MP-0 Small GPT-5.4 Control

This directory is a CMU20 control source for the matched-physics Adsorb-Agent
comparison. It is not a separate dataset and should not be cited as a root-level
result family.

- `summary.csv`: all 20 CMU20 Adsorb-Agent cases summarized under the matched
  MACE-MP-0 small CPU float32 protocol.
- `comparison.csv`: 15 paired CMU20 cases used for the AdsMind vs Adsorb-Agent
  comparison table.
- `comparison_stats.json`: statistics derived from `comparison.csv`.

Protocol: Adsorb-Agent with GPT-5.4, MACE-MP-0 small, CPU, float32, dispersion
disabled, `fmax=0.10`.
