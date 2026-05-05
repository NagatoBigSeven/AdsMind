# Frozen Experiment Configs

These JSON files pin the runtime settings used for AdsMind benchmark and
ablation runs. They intentionally store model names, physics settings, and API
transport settings, but never API keys.

## Frozen Configs

- `frozen_config_gpt54_mace_mp0_small*.json`: GPT-5.4 with MACE-MP-0 small.
- `frozen_config_claude_sonnet46_mace_mp0_small*.json`: Claude Sonnet 4.6 with MACE-MP-0 small.
- `frozen_config_gemini25pro_mace_mp0_small*.json`: Gemini 2.5 Pro with MACE-MP-0 small.
- `frozen_config_grok4_mace_mp0_small*.json`: Grok-4 with MACE-MP-0 small.
- `frozen_config_gpt54_mace_mp0_large.json`: GPT-5.4 with MACE-MP-0 large.

## Identity Policy

Paper-facing results identify runs by dataset, LLM backend/version, variant, and
force-field size. API transport settings are retained here only so the runner can
reproduce the execution environment; they are not benchmark identity dimensions.

## Local Overrides

Use environment variables for credentials and machine-specific settings:

- Cloud API credentials: `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, or
  `OPENROUTER_API_KEY`.
- OCD-GMAE LMDB path: `OCD_GMAE_LMDB_PATH` or the `--lmdb-path` CLI flag.

Do not commit local output directories, per-run `config.json`, trajectories,
logs, or provider credentials.
