# Figure: per-agent ablation (no_executor / no_validator)

Diagnostic figures generated for the per-agent ablation run on 2026-05-22.
These diagnostics are retained as supplementary research artifacts for auditing
the ablation analysis.

- `figure_A_6dft_cases.png` — grouped bar chart on the six DFT-anchored CMU20
  cases comparing DFT (VASP/PBE), MACE Full, and each backend's LLM-predicted
  energy under `no_executor`. Annotated with per-backend MAE vs DFT.
- `figure_B_llm_vs_mace_scatter.png` — per-backend scatter of LLM-predicted
  (`no_executor`) energy against MACE Full energy (`no_validator`) across all
  20 CMU20 cases. Diamonds mark the six DFT-anchored cases; circles mark the
  remaining 14.

Regenerate with `research/analysis/plot_per_agent_ablation_dashboard.py`.
