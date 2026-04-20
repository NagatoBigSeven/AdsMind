# Frozen Experiment Configs

These JSON files pin the runtime settings used for AdsMind benchmark and
ablation runs. They intentionally store model names, physics settings, and
provider routes, but never API keys.

## Recommended Public Routes

- `frozen_config_gemini25pro_vertexai*.json`: Gemini 2.5 Pro through Vertex AI
  using Google Application Default Credentials.
- `frozen_config_xai_grok4*.json`: Grok-4 through xAI's official
  OpenAI-compatible endpoint.
- `frozen_config_openai_gpt54*.json`: GPT-5.4 through OpenAI's official
  endpoint.
- `frozen_config_anthropic_sonnet46*.json`: Claude Sonnet 4.6 through
  Anthropic's official OpenAI-compatible endpoint.

## Provenance-Only Routes

Some historical runs used alternate provider transports when direct provider
quota or routing was unavailable. Only public, official-provider route configs
are retained in this repository:

- `frozen_config_gemini25pro_openrouter.json`
- `frozen_config_gemini25pro_openrouter_one_shot.json`

For new public reproductions, prefer the official provider routes above unless
you are deliberately reproducing a historical run.

## Local Overrides

Use environment variables for credentials and machine-specific settings:

- Cloud API credentials: provider-specific environment variables such as
  `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `XAI_API_KEY`, or `OPENROUTER_API_KEY`.
- Vertex AI project: `GOOGLE_CLOUD_PROJECT` or `GCLOUD_PROJECT`.
- OCD-GMAE LMDB path: `OCD_GMAE_LMDB_PATH` or the `--lmdb-path` CLI flag.

Do not commit local output directories, per-run `config.json`, trajectories,
logs, or provider credentials.
