# research/results Data Layout

The active result tree is organized by experiment type first.

```text
research/results/
  basic_experiments/
    cmu20/
      gpt|claude|gemini|grok/
        one_shot|full|no_slip|no_termination|no_forbid/
          summary.csv
          <case_id>/result.json
      baselines/
      summaries/
    ocd62/
      gpt|claude|gemini|grok/
        one_shot|full|no_slip|no_termination|no_forbid/
          summary.csv
          <case_id>/result.json
      baselines/
      summaries/
    summaries/
  advanced_experiments/
```

## Basic Experiments

Basic experiments are the matched CMU20 and OCD62 evaluation matrix:

- datasets: `cmu20`, `ocd62`
- LLM backends: `gpt`, `claude`, `gemini`, `grok`
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

Baselines live under each dataset's `baselines/` directory. CMU20 also includes
the matched Adsorb-Agent MACE-MP-0 small control at
`basic_experiments/cmu20/baselines/adsorbagent_mace_mp0_small_gpt54/`.

Note: CMU20 `one_shot` summary tables contain all 20 cases. Some failed or
historically missing one-shot runs have no artifact directory; use
`summary.csv` for the complete case accounting.

## Advanced Experiments

Advanced experiments contain smaller or deeper studies that are not the main
matched CMU20/OCD62 matrix:

- `ocd62_overlap12_reproducibility/`: repeated runs on the 12 overlapping OCD62 cases.
- `mace_force_field_sensitivity/`: MACE-MP-0 large sensitivity checks.
- `adsorbagent_single_config_stress/`: Adsorb-Agent single-config stress test.
- `gpt54_multiseed_cmu20/`: GPT-5.4 full-run seed sensitivity.

RUN3 reproducibility outputs are expected under
`advanced_experiments/ocd62_overlap12_reproducibility/run3/` after the remote
jobs finish. Then refresh with:

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
