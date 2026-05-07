# research/results Data Layout

The active result tree is organized by experiment type first.

```text
research/results/
  basic_experiments/
    cmu20/
      gpt54_mace_mp0_small/
      claude_sonnet46_mace_mp0_small/
      gemini25pro_mace_mp0_small/
      grok4_mace_mp0_small/
        one_shot|full|no_slip|no_termination|no_forbid/
          summary.csv
          <case_id>/result.json
      baselines/
      summaries/
    ocd62/
      gpt54_mace_mp0_small/
      claude_sonnet46_mace_mp0_small/
      gemini25pro_mace_mp0_small/
      grok4_mace_mp0_small/
        one_shot|full|no_slip|no_termination|no_forbid/
          summary.csv
          <case_id>/result.json
      baselines/
      summaries/
    summaries/
  advanced_experiments/
    ablation_and_chemical_slip_diagnostics/
    reproducibility/
    force_field_sensitivity/
    case_studies/
```

## Basic Experiments

Basic experiments are the matched CMU20 and OCD62 evaluation matrix:

- datasets: `cmu20`, `ocd62`
- LLM/force-field directories:
  `gpt54_mace_mp0_small`,
  `claude_sonnet46_mace_mp0_small`,
  `gemini25pro_mace_mp0_small`,
  `grok4_mace_mp0_small`
- variants: `one_shot`, `full`, `no_slip`, `no_termination`, `no_forbid`

Each backend has `all_variants_summary.csv` for the full backend table. Each
variant directory also has its own `summary.csv` beside the case result
directories.

Dataset-level summaries:

- `basic_experiments/cmu20/summaries/method_comparison.csv`
- `basic_experiments/ocd62/summaries/method_comparison.csv`
- `basic_experiments/ocd62/summaries/ablation_4backend.csv`
- `basic_experiments/summaries/full_vs_one_shot_summary.csv`
- `basic_experiments/summaries/method_comparison_summary.csv`
- `basic_experiments/summaries/method_comparison_table.md`
- `basic_experiments/summaries/method_comparison_table.tex`

Baselines live under each dataset's `baselines/` directory. The paper-facing
Adsorb-Agent control uses GPT-5.4, MACE-MP-0 small, and up to five generated
candidate configurations per case:

- `basic_experiments/cmu20/baselines/adsorb-agent/adsorb-agent_gpt54_mace_mp0_small_5config/`
- `basic_experiments/ocd62/baselines/adsorb-agent/adsorb-agent_gpt54_mace_mp0_small_5config/`

The older unbounded-candidate CMU20 Adsorb-Agent rerun has been removed from
the curated result tree; generated method-comparison tables require the
matched-budget 5-config directories above.

## Advanced Experiments

Advanced experiments are organized by research question rather than by the
main dataset/backend/variant matrix:

- `ablation_and_chemical_slip_diagnostics/ablation_effects/`: Full-vs-ablation
  statistics, backend agreement, and reach-Full tables.
- `ablation_and_chemical_slip_diagnostics/chemical_slip_interpretability/`:
  chemical-slip interpretation tables and trajectories.
- `reproducibility/ocd62_overlap12_rerun/`: repeated runs on the 12 overlapping OCD62
  cases, including complete run1/run2/run3/run4 directories, a partial audited
  run5, and N=2/N=3/N=4 summaries.
- `reproducibility/cmu20_gpt54_mace_mp0_small_multiseed/`:
  GPT-5.4 CMU20 full-run seed sensitivity under MACE-MP-0 small.
- `force_field_sensitivity/mace_mp0_large_vs_mace_mp0_small/`: MACE-MP-0 large vs
  MACE-MP-0 small force-field sensitivity. CMU20 is complete; no OCD62 subset is
  defined in this experiment.
- `case_studies/dft_iteration_alignment/`: CMU20 case-level trajectory exports
  for DFT alignment.
- `case_studies/iteration_convergence/`: per-iteration running-best energy
  curves.

Reproducibility summaries can be refreshed from the run directories with:

```bash
.venv/bin/python research/analysis/build_ocd62_summary.py --write-n3
```

## Refresh Commands

```bash
.venv/bin/python research/analysis/build_method_comparison_table.py
.venv/bin/python research/analysis/build_ocd62_summary.py
```

Large local artifacts such as `.xyz`, `.traj`, logs, and per-run configs may be
present in this tree, but they are ignored by Git by default.
