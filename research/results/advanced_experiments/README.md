# Advanced Experiments

These experiments are smaller or deeper studies outside the main CMU20/OCD62
evaluation matrix. They are grouped by the question they answer:

- `mechanism/`: why the system behaves the way it does.
- `reproducibility/`: how stable repeated runs are.
- `model_sensitivity/`: how results change when the underlying force-field
  model changes.
- `case_studies/`: case-level exports for figures, trajectory inspection, or
  DFT handoff.

Current contents:

- `mechanism/ablation_effects/`: summary tables for Full vs no-slip,
  no-forbid, and no-termination comparisons across CMU20 and OCD62.
- `mechanism/chemical_slip_interpretability/cmu20/`: chemical-slip tables and
  case 19 trajectory records.
- `reproducibility/ocd62_overlap12/`: repeated runs for the 12 duplicated OCD62
  cases. RUN3 results land in `run3/`; summaries live in `summaries/`.
- `reproducibility/cmu20_openai_gpt54_mace_mp0_small_multiseed/seed43|seed44|seed45|seed46|seed47/full/`:
  CMU20 GPT-5.4 full-run seed sensitivity under MACE-MP-0 small.
- `model_sensitivity/mace_mp0_large/cmu20/openai_gpt54_mace_mp0_large/full/`:
  CMU20 GPT full-run check with MACE-MP-0 large.
- `model_sensitivity/mace_mp0_large/ocd62_sample10/openai_gpt54_mace_mp0_large/full/`:
  OCD62 10-case subset GPT full-run check with MACE-MP-0 large. The subset is
  listed in `model_sensitivity/mace_mp0_large/ocd62_sample10/manifest.csv`, and
  all 10 cases are already covered by the OCD62 basic-experiment matrix.
- `case_studies/dft_iteration_alignment/cmu20/case01/`: per-iteration
  trajectory export for DFT comparison.
- `case_studies/iteration_convergence/cmu20/all_backends/full/`: running-best
  energy curves for CMU20 full runs across backends.

RUN3 reproducibility refresh:

```bash
.venv/bin/python research/analysis/build_ocd62_summary.py --write-n3
```
