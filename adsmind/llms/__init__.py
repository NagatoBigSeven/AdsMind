"""
LLM Backend Module for AdsMind.

This module provides a factory pattern for LLM backends, allowing easy switching
between different LLM providers (cloud and local).

Supported backends:
- openai: OpenAI GPT API - Direct access via official endpoint
- anthropic: Anthropic Claude API - Direct access via official compatibility endpoint
- openrouter: OpenRouter API - Gemini and Grok model access for paper runs
- ollama: Ollama local service - Privacy-focused, no API cost
- huggingface: HuggingFace Transformers - Offline, customizable

Usage:
    from adsmind.llms import get_llm_backend, get_available_llm_backends

    # Get a specific backend
    backend = get_llm_backend("openrouter")
    config = backend.get_default_config(api_key="your-openrouter-api-key")
    llm = backend.get_chat_model(config)

    # List available backends
    available = get_available_llm_backends()
"""

from adsmind.llms.factory import get_llm_backend, get_available_llm_backends

__all__ = ["get_llm_backend", "get_available_llm_backends"]
