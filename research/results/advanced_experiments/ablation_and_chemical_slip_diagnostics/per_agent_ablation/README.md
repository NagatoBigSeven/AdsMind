# Per-agent ablation diagnostics

Diagnostics for the `no_executor` and `no_validator` variants added on
2026-05-22 to CMU20. The raw per-case `result.json` files are alongside the
other variants under `research/results/basic_experiments/cmu20/adsmind/`.

Files in this directory:

- `mae_by_variant.csv` — per `(backend, variant)` rollup with `n_success`,
  `mean_E_eV`, `validator_rejections`, MAE vs DFT (6 reference cases) and
  MAE vs `full` (20-case paired difference). Includes the five paper-level
  variants for context.

Headline numbers (CMU20, 4 backends, 20 cases each):

- `no_validator` success rate is 100% — identical to `full`.
- `validator_rejections == 0` for every (backend, variant) combination.
  Combined with the OCD62 corpus (1240 additional runs) the validator has
  never fired in this paper's experiments; on these benchmarks it is
  architectural insurance rather than active machinery.
- `no_executor` MAE vs `full` is 1.5–2.4 eV (10–100× larger than removing
  any single mechanism); skipping MACE relaxation breaks the agent.

Regenerate with `research/analysis/plot_per_agent_ablation_dashboard.py`.
