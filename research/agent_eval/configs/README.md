# Frozen Experiment Configs

These JSON files pin the runtime settings used for AdsMind benchmark and
ablation runs. They intentionally store model names, physics settings, and
provider routes, but never API keys.

## Recommended Public Routes

- `frozen_config_openai_gpt54*.json`: GPT-5.4 through OpenAI's official
  endpoint.
- `frozen_config_anthropic_sonnet46*.json`: Claude Sonnet 4.6 through
  Anthropic's official OpenAI-compatible endpoint.
- `frozen_config_gemini25pro_openrouter*.json`: Gemini 2.5 Pro through
  OpenRouter.
- `frozen_config_grok4_openrouter*.json`: Grok-4 through OpenRouter.

## Route Policy

The paper-facing benchmark uses one public route per model family: OpenAI for
GPT, Anthropic for Claude, and OpenRouter for Gemini and Grok. Historical
alternate-provider recovery configs are intentionally not retained here because
they make the public experiment identity ambiguous.

## Local Overrides

Use environment variables for credentials and machine-specific settings:

- Cloud API credentials: `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, or
  `OPENROUTER_API_KEY`.
- OCD-GMAE LMDB path: `OCD_GMAE_LMDB_PATH` or the `--lmdb-path` CLI flag.

Do not commit local output directories, per-run `config.json`, trajectories,
logs, or provider credentials.
