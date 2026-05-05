# OCD62 overlap12 RUN3

Date: 2026-05-03

This launcher runs only the third reproducibility repeat for the 12 overlapping
OCD62 cases. It is not a 62-case rerun.

## Scope

- cases: 12 overlap cases from `datasets/ocd62_overlap12/ocd62_overlap12_manifest.csv`
- backend keys accepted by the launcher: `gpt`, `claude`, `gemini`, `grok`
- result directories encode the LLM backend/version and force field
- variants: `full`, `no_slip`, `no_forbid`, `no_termination`, `one_shot`
- total jobs: 240

The runner writes to:

```text
research/results/advanced_experiments/reproducibility/ocd62_overlap12_rerun/run3/
  gpt54_mace_mp0_small/
  claude_sonnet46_mace_mp0_small/
  gemini25pro_mace_mp0_small/
  grok4_mace_mp0_small/
    full|no_slip|no_forbid|no_termination|one_shot/
```

## Configs

Backend config snapshots stay under `research/agent_eval/configs/`:

- GPT: `ocd62_overlap12_run3/frozen_config_ocd62_overlap12_run3_gpt54_mace_mp0_small.json`
- Claude: `ocd62_overlap12_run3/frozen_config_ocd62_overlap12_run3_claude_sonnet46_mace_mp0_small.json`
- Gemini: `ocd62_overlap12_run3/frozen_config_ocd62_overlap12_run3_gemini25pro_mace_mp0_small.json`
- Grok: `ocd62_overlap12_run3/frozen_config_ocd62_overlap12_run3_grok4_mace_mp0_small.json`

The CLI accepts short backend keys; public result folders use only the
backend/model identity.

## Run

```bash
research/agent_eval/run_configs/ocd62_overlap12_run3/run_ocd62_overlap12_run3_failover.sh
```

To run one backend:

```bash
research/agent_eval/run_configs/ocd62_overlap12_run3/run_ocd62_overlap12_run3_failover.sh --backends grok
```

The launcher uses the API transport settings frozen in the config JSON files:

- GPT with `OPENAI_API_KEY`.
- Claude with `ANTHROPIC_API_KEY`.
- Gemini and Grok with `OPENROUTER_API_KEY_PRIMARY`; on auth, quota, payment, or
  rate-limit failure, the launcher retries with `OPENROUTER_API_KEY_SECONDARY`.

All keys can also be supplied through the corresponding `*_FILE` variants. Keys
are not stored in the repository or logs.

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

- `research/results/advanced_experiments/reproducibility/ocd62_overlap12_rerun/summaries/reproducibility_n3.csv`
- `research/results/advanced_experiments/reproducibility/ocd62_overlap12_rerun/summaries/reproducibility_n3.md`
