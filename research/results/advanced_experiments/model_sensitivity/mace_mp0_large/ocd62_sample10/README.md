# OCD62 Sample10 MACE-MP-0 Large Check

This directory is a force-field sensitivity check on a 10-case subset of OCD62,
not a separate dataset. The selected cases are listed in `manifest.csv`.

- Dataset source: `datasets/ocd62/ocd62_manifest.csv`.
- Case IDs: `003`, `011`, `017`, `020`, `026`, `031`, `040`, `051`, `053`,
  `054`.
- Basic-experiment coverage: all 10 cases are present in the OCD62 basic matrix
  across 4 LLM backends x 5 variants under MACE-MP-0 small.
- Sensitivity run here: OpenAI GPT-5.4 full variant with MACE-MP-0 large.

The purpose is to compare the force-field size on already baselined OCD62
systems, so these rows should be interpreted as model sensitivity, not as new
unbaselined evaluation cases.
