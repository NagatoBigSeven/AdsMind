# LLM Backend System

AdsMind supports multiple LLM backends for the agentic workflow. Choose between cloud APIs (for best performance) or local models (for privacy and no API costs).

## Quick Start

The default backend is **Google AI (Gemini 2.5 Pro)**. Set your API key and run:

```bash
export GOOGLE_API_KEY="your-google-api-key"
adsmind-ui
```

## Supported Backends

| Backend | Type | API Key Required | Best For |
|---------|------|------------------|----------|
| **Google AI** | Cloud | Yes (`GOOGLE_API_KEY`) | Production, low latency |
| **Vertex AI** | Cloud | No API key; uses Google ADC | Enterprise Gemini deployments |
| **Anthropic** | Cloud | Yes (`ANTHROPIC_API_KEY`) | Claude models |
| **xAI** | Cloud | Yes (`XAI_API_KEY`) | Grok models |
| **OpenRouter** | Cloud | Yes (`OPENROUTER_API_KEY`) | Access to multiple models |
| **Ollama** | Local | No | Privacy, offline use |
| **HuggingFace** | Local | No | Full customization |

## Backend Selection

### Via UI

1. Open the Streamlit app
2. In the sidebar, select your backend from the "🤖 LLM Backend" dropdown
3. Enter API key if using a cloud backend
4. Select your preferred model

### Via Environment Variable

```bash
# Use Google AI (default)
export ADSMIND_LLM_BACKEND=google
export GOOGLE_API_KEY="your-google-api-key"

# Use Vertex AI
export ADSMIND_LLM_BACKEND=google_vertexai
export GOOGLE_CLOUD_PROJECT="your-gcp-project"
export GOOGLE_CLOUD_LOCATION="us-central1"

# Use Anthropic
export ADSMIND_LLM_BACKEND=anthropic
export ANTHROPIC_API_KEY="your-anthropic-api-key"

# Use xAI
export ADSMIND_LLM_BACKEND=xai
export XAI_API_KEY="your-xai-api-key"

# Use OpenRouter
export ADSMIND_LLM_BACKEND=openrouter
export OPENROUTER_API_KEY="your-openrouter-api-key"

# Use Ollama (local)
export ADSMIND_LLM_BACKEND=ollama
# Make sure Ollama is running: ollama serve

# Use HuggingFace (local)
export ADSMIND_LLM_BACKEND=huggingface
export HF_QUANTIZE=4bit  # Optional: reduce memory usage
```

Legacy `ADSKRK_LLM_BACKEND` is still accepted as a fallback.

## Cloud Backends

### Google AI (Gemini)

Direct access to Google's Gemini models. Recommended for production use.

**Setup:**

1. Get API key from [Google AI Studio](https://aistudio.google.com/apikey)
2. Set `GOOGLE_API_KEY` or enter in the app

**Available Models:**

- `gemini-2.5-pro` (default) - Best reasoning
- `gemini-2.5-flash` - Fast responses
- `gemini-2.5-flash-lite` - Fastest, lightweight

### Vertex AI (Gemini)

Gemini through Google Cloud Vertex AI. This backend uses Google Application
Default Credentials rather than an API key.

**Setup:**

```bash
gcloud auth application-default login
export GOOGLE_CLOUD_PROJECT="your-gcp-project"
export GOOGLE_CLOUD_LOCATION="us-central1"
export ADSMIND_LLM_BACKEND=google_vertexai
```

### Anthropic

Direct Claude access through Anthropic's OpenAI-compatible endpoint.

**Setup:**

```bash
export ADSMIND_LLM_BACKEND=anthropic
export ANTHROPIC_API_KEY="your-anthropic-api-key"
```

### xAI

Direct Grok access through xAI's OpenAI-compatible endpoint.

**Setup:**

```bash
export ADSMIND_LLM_BACKEND=xai
export XAI_API_KEY="your-xai-api-key"
```

### OpenRouter

Access multiple AI providers through a unified API.

**Setup:**

1. Get API key from [OpenRouter](https://openrouter.ai)
2. Set `OPENROUTER_API_KEY` or enter in the app

**Available Models:** any model from [OpenRouter's catalog](https://openrouter.ai/models). For reference, the frozen experiment configs in
`research/agent_eval/configs/` route to:

- `google/gemini-2.5-pro`
- `x-ai/grok-4`
- `anthropic/claude-sonnet-4.6`
- (GPT-5.4 is reached through OpenAI's official endpoint, not OpenRouter)

Pin a specific model id in your config; do not rely on a moving "latest" alias.

## Local Backends

### Ollama

Run models locally using Ollama. Free and private.

**Setup:**

```bash
# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Pull a model
ollama pull qwen3:8b

# Start the service
ollama serve
```

**Configuration:**

- `OLLAMA_HOST`: Server URL (default: `http://localhost:11434`)
- `OLLAMA_MODEL`: Model Name (default: `qwen3:8b`)

### HuggingFace Transformers

Load models directly from HuggingFace Hub for full offline capability.

**Setup:**

```bash
# Install core project deps
python -m pip install adsmind

# Optional for source checkouts: install development tooling
uv pip install -e ".[dev]"

# Optional: For quantization
pip install bitsandbytes
```

**Configuration:**

- `HF_MODEL`: Model ID (default: `Qwen/Qwen3-8B`)
- `HF_DEVICE`: Device (`auto`, `cuda`, `cpu`)
- `HF_QUANTIZE`: Quantization mode (`4bit`, `8bit`, `none`)

## Advanced Settings

The app provides advanced settings for fine-tuning LLM behavior:

| Setting | Range | Default | Description |
|---------|-------|---------|-------------|
| Temperature | 0.0 - 1.0 | 0.0 | Higher = more creative |
| Max Tokens | 256 - 16384 | 4096 | Maximum response length |

## Programmatic Usage

```python
from adsmind.llms import get_llm_backend

# Get a backend
backend = get_llm_backend("google")

# Get default configuration
config = backend.get_default_config(api_key="your-api-key")

# Customize
config.model = "gemini-2.5-flash"
config.temperature = 0.3

# Get LangChain-compatible chat model
llm = backend.get_chat_model(config)
```

## Troubleshooting

### Ollama Connection Failed

```
❌ Ollama not running
```

**Solution:** Start Ollama with `ollama serve`

### HuggingFace Out of Memory

**Solution:** Enable quantization in the UI (select 4bit or 8bit in the Quantization dropdown) or via environment variable:

```bash
export HF_QUANTIZE=4bit
```

### API Key Not Found

**Solution:** Check environment variable or enter in the app sidebar.
