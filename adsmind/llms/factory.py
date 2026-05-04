"""
LLM backend factory.

This module provides the factory function to get LLM backends by name,
following the same pattern as adsmind/calculators/factory.py.
"""

from typing import Dict, List, Type

from adsmind.llms.base import BaseLLMBackend


def _get_llm_registry() -> Dict[str, Type[BaseLLMBackend]]:
    """
    Lazily build the LLM backend registry.

    Using lazy imports to avoid loading heavy dependencies (like HuggingFace)
    until actually needed.
    """
    from adsmind.llms.anthropic_backend import AnthropicBackend
    from adsmind.llms.openai_backend import OpenAIBackend
    from adsmind.llms.openrouter_backend import OpenRouterBackend
    from adsmind.llms.ollama_backend import OllamaBackend
    from adsmind.llms.huggingface_backend import HuggingFaceBackend

    return {
        "openai": OpenAIBackend,
        "anthropic": AnthropicBackend,
        "openrouter": OpenRouterBackend,
        "ollama": OllamaBackend,
        "huggingface": HuggingFaceBackend,
    }


def get_llm_backend(name: str) -> BaseLLMBackend:
    """
    Get an LLM backend by name.

    Args:
        name: Backend name ("openai", "anthropic", "openrouter", "ollama",
            "huggingface")

    Returns:
        An instance of the requested backend

    Raises:
        ValueError: If the backend name is unknown

    Example:
        >>> backend = get_llm_backend("openrouter")
        >>> config = backend.get_default_config(api_key="your-openrouter-api-key")
        >>> llm = backend.get_chat_model(config)
    """
    registry = _get_llm_registry()

    if name not in registry:
        available = list(registry.keys())
        raise ValueError(
            f"Unknown LLM backend: '{name}'. "
            f"Available backends: {available}"
        )

    backend_class = registry[name]
    return backend_class()


def get_available_llm_backends() -> List[str]:
    """
    Get a list of all available LLM backend names.

    Returns:
        List of backend names that are installed and available
    """
    registry = _get_llm_registry()
    available = []

    for name, backend_class in registry.items():
        try:
            backend = backend_class()
            if backend.is_available:
                available.append(name)
        except Exception:
            pass

    return available
