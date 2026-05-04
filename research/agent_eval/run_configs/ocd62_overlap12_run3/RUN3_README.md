# OCD62 overlap12 RUN3

Date: 2026-05-03

This launcher runs only the third reproducibility repeat for the 12 overlapping
OCD62 cases. It is not a 62-case rerun.

## Scope

- cases: 12 overlap cases from `datasets/ocd62_overlap12/overlap12_manifest.csv`
- backends: `gpt`, `claude`, `gemini`, `grok`
- variants: `full`, `no_slip`, `no_forbid`, `no_termination`, `one_shot`
- total jobs: 240

The runner writes to:

```text
research/results/advanced_experiments/ocd62_overlap12_reproducibility/run3/
  gpt|claude|gemini|grok/
    full|no_slip|no_forbid|no_termination|one_shot/
```

## Configs

Backend config snapshots stay under `research/agent_eval/configs/`:

- native GPT: `ocd62_overlap12_run3_native/frozen_config_ocd62_overlap12_run3_native_openai_gpt54.json`
- native Claude: `ocd62_overlap12_run3_native/frozen_config_ocd62_overlap12_run3_native_anthropic_sonnet46.json`
- OpenRouter Gemini: `ocd62_overlap12_run3_openrouter/frozen_config_ocd62_overlap12_run3_openrouter_gemini.json`
- OpenRouter Grok: `ocd62_overlap12_run3_openrouter/frozen_config_ocd62_overlap12_run3_openrouter_grok4.json`

The public result folders use short backend names. The launcher maps those names
to the frozen config filenames internally.

## Run

```bash
research/agent_eval/run_configs/ocd62_overlap12_run3/run_ocd62_overlap12_run3_failover.sh
```

To run one backend:

```bash
research/agent_eval/run_configs/ocd62_overlap12_run3/run_ocd62_overlap12_run3_failover.sh --backends grok
```

The script reads `OPENROUTER_API_KEY_PRIMARY`,
`OPENROUTER_API_KEY_SECONDARY`, `OPENAI_API_KEY`, and `ANTHROPIC_API_KEY`, or
their `*_FILE` variants. Keys are not stored in the repository or logs.

## Check

```bash
.venv/bin/python research/agent_eval/run_configs/ocd62_overlap12_run3/check_ocd62_overlap12_run3.py
```

This rewrites:

`research/agent_eval/run_configs/ocd62_overlap12_run3/RUN3_DASHBOARD.md`

## After RUN3

```bash
.venv/bin/python research/analysis/build_ocd62_summary.py --write-n3
```

Expected summary outputs:

- `research/results/advanced_experiments/ocd62_overlap12_reproducibility/summaries/reproducibility_n3.csv`
- `research/results/advanced_experiments/ocd62_overlap12_reproducibility/summaries/reproducibility_n3.md`
