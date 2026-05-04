# LLM Backend System

AdsMind exposes one clean provider route per paper-facing model family:
GPT through OpenAI's official endpoint, Claude through Anthropic's official
endpoint, and Gemini/Grok through OpenRouter. Local Ollama and HuggingFace
backends remain available for non-paper interactive use.

## Quick Start

The default hosted backend is **OpenRouter**. Set your key and run:

```bash
export OPENROUTER_API_KEY="your-openrouter-api-key"
adsmind-ui
```

## Supported Backends

| Backend | Type | API Key Required | Best For |
|---------|------|------------------|----------|
| **OpenAI** | Cloud | Yes (`OPENAI_API_KEY`) | GPT models through OpenAI's official endpoint |
| **Anthropic** | Cloud | Yes (`ANTHROPIC_API_KEY`) | Claude models through Anthropic's official endpoint |
| **OpenRouter** | Cloud | Yes (`OPENROUTER_API_KEY`) | Gemini and Grok models used in the paper benchmark |
| **Ollama** | Local | No | Privacy, offline use |
| **HuggingFace** | Local | No | Full customization |

## Backend Selection

### Via UI

1. Open the Streamlit app.
2. In the sidebar, select your backend from the "LLM Backend" dropdown.
3. Enter an API key if using a hosted backend.
4. Select your preferred model.

### Via Environment Variable

```bash
# Gemini or Grok through OpenRouter
export ADSMIND_LLM_BACKEND=openrouter
export OPENROUTER_API_KEY="your-openrouter-api-key"

# GPT through OpenAI official endpoint
export ADSMIND_LLM_BACKEND=openai
export OPENAI_API_KEY="your-openai-api-key"

# Claude through Anthropic official endpoint
export ADSMIND_LLM_BACKEND=anthropic
export ANTHROPIC_API_KEY="your-anthropic-api-key"

# Ollama (local)
export ADSMIND_LLM_BACKEND=ollama

# HuggingFace (local)
export ADSMIND_LLM_BACKEND=huggingface
export HF_QUANTIZE=4bit  # Optional: reduce memory usage
```

Legacy `ADSKRK_LLM_BACKEND` is still accepted as a fallback.

## Cloud Backends

### OpenRouter

OpenRouter is the only hosted route used for Gemini and Grok in the
paper-facing benchmark data.

**Setup:**

1. Get API key from [OpenRouter](https://openrouter.ai).
2. Set `OPENROUTER_API_KEY` or enter it in the app.

Paper-facing OpenRouter model ids:

- `google/gemini-2.5-pro`
- `x-ai/grok-4`

### OpenAI

OpenAI is the official route for GPT paper-facing runs.

```bash
export ADSMIND_LLM_BACKEND=openai
export OPENAI_API_KEY="your-openai-api-key"
```

Paper-facing model id:

- `gpt-5.4-2026-03-05`

### Anthropic

Anthropic is the official route for Claude paper-facing runs.

```bash
export ADSMIND_LLM_BACKEND=anthropic
export ANTHROPIC_API_KEY="your-anthropic-api-key"
```

Paper-facing model id:

- `claude-sonnet-4-6`

Pin a specific model id in reproducibility configs; do not rely on a moving
"latest" alias.

## Local Backends

### Ollama

```bash
curl -fsSL https://ollama.com/install.sh | sh
ollama pull qwen3:8b
ollama serve
```

### HuggingFace Transformers

```bash
python -m pip install adsmind
uv pip install -e ".[dev]"
pip install bitsandbytes  # optional, for quantization
```

## Programmatic Usage

```python
from adsmind.llms import get_llm_backend

backend = get_llm_backend("openrouter")
config = backend.get_default_config(api_key="your-api-key")
config.model = "google/gemini-2.5-pro"
llm = backend.get_chat_model(config)
```
