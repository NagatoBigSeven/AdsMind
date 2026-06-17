# Force-Field Sensitivity

This directory contains controlled reruns that change the MACE-MP-0 force-field
size while keeping the LLM/backend protocol explicit in the result path and
summary columns.

- `mace_mp0_large_vs_mace_mp0_small/`: GPT-5.4 Full reruns with MACE-MP-0 large,
  compared against the primary MACE-MP-0 small benchmark protocol.

The current committed result set is CMU20 only. No OCD62 subset is defined in
this force-field sensitivity directory.
