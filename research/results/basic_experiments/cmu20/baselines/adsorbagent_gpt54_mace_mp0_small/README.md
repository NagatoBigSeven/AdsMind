# Adsorb-Agent MACE-MP-0 Small GPT-5.4 Control

This directory is a CMU20 control source for the matched-physics Adsorb-Agent
comparison. It is not a separate dataset and should not be cited as a root-level
result family.

- `summary.csv`: all 20 CMU20 Adsorb-Agent cases summarized under the matched
  MACE-MP-0 small CPU float32 protocol.
- `comparison.csv`: all 20 CMU20 cases in the AdsMind vs Adsorb-Agent
  comparison table. Adsorb-Agent cases `03`, `05`, `15`, and `18` have no valid
  trajectory and are included as failures.
- `comparison_stats.json`: statistics derived from `comparison.csv`; energy
  paired statistics use the 16 rows with valid energies.

Protocol: Adsorb-Agent with GPT-5.4, MACE-MP-0 small, CPU, float32, dispersion
disabled, `fmax=0.10`.
