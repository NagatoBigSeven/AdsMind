# Advanced Experiments

These experiments are smaller or deeper studies outside the main CMU20/OCD62
evaluation matrix. They are grouped by the question they answer:

- `ablation_and_chemical_slip_diagnostics/`: Full-vs-ablation statistics and
  chemical-slip interpretability diagnostics.
- `reproducibility/`: how stable repeated runs are.
- `force_field_sensitivity/`: how results change when the underlying force-field
  model changes.
- `case_studies/`: case-level exports for figures, trajectory inspection, or
  DFT handoff.

Current contents:

- `ablation_and_chemical_slip_diagnostics/ablation_effects/`: Full-vs-ablation
  summary tables across CMU20 and OCD62.
- `ablation_and_chemical_slip_diagnostics/chemical_slip_interpretability/cmu20/`:
  CMU20 chemical-slip tables and case-19 trajectory records.
- `reproducibility/ocd62_overlap12_rerun/`: repeated runs for the 12 duplicated OCD62
  cases. Run directories are `run1/`, `run2/`, and `run3/`; N=2/N=3 summaries live in
  `summaries/`.
- `reproducibility/cmu20_gpt54_mace_mp0_small_multiseed/seed43|seed44|seed45|seed46|seed47/full/`:
  CMU20 GPT-5.4 full-run seed sensitivity under MACE-MP-0 small.
- `force_field_sensitivity/mace_mp0_large_vs_mace_mp0_small/cmu20/gpt54_mace_mp0_large/full/`:
  CMU20 GPT full-run check with MACE-MP-0 large.
- `case_studies/dft_iteration_alignment/cmu20/case01/`: per-iteration
  trajectory export for DFT comparison.
- `case_studies/iteration_convergence/cmu20/all_backends/full/`: running-best
  energy curves for CMU20 full runs across backends.

Reproducibility refresh:

```bash
.venv/bin/python research/analysis/build_ocd62_summary.py --write-n3
```
