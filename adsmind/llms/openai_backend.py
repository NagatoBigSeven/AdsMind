"""
OpenAI backend implementation.

This backend talks to OpenAI's official Chat Completions-compatible endpoint.
It exists separately from OpenRouter so experiment configs can name the public
GPT route unambiguously.
"""

import importlib.util
from typing import Optional

from langchain_core.language_models.chat_models import BaseChatModel

from adsmind.llms.base import BaseLLMBackend, LLMConfig
from adsmind.utils.logger import get_logger

logger = get_logger(__name__)

OPENAI_BASE_URL = "https://api.openai.com/v1"
DEFAULT_MODEL = "gpt-5.4-2026-03-05"


class OpenAIBackend(BaseLLMBackend):
    """Direct OpenAI GPT backend via the official endpoint."""

    @property
    def name(self) -> str:
        return "openai"

    @property
    def requires_api_key(self) -> bool:
        return True

    @property
    def is_available(self) -> bool:
        """Check if langchain-openai is installed."""
        return importlib.util.find_spec("langchain_openai") is not None

    def get_chat_model(self, config: LLMConfig) -> BaseChatModel:
        """Return a ChatOpenAI instance pointed at OpenAI's official endpoint."""
        from langchain_openai import ChatOpenAI

        if not config.api_key:
            raise ValueError(
                "OpenAI API key is required. Set OPENAI_API_KEY environment "
                "variable or provide it in the configuration."
            )

        base_url = config.extra_options.get("base_url", OPENAI_BASE_URL)
        default_headers = config.extra_options.get("default_headers") or {}
        seed = config.extra_options.get("seed", 42)

        logger.info(
            f"Initializing OpenAI backend (base_url: {base_url}, "
            f"model: {config.model}, temperature: {config.temperature})"
        )

        return ChatOpenAI(
            openai_api_base=base_url,
            openai_api_key=config.api_key,
            model=config.model,
            streaming=False,
            temperature=config.temperature,
            max_tokens=config.max_tokens,
            timeout=config.timeout,
            seed=seed,
            default_headers=default_headers,
        )

    def get_default_config(self, api_key: Optional[str] = None) -> LLMConfig:
        """Return default configuration for OpenAI GPT."""
        return LLMConfig(
            backend=self.name,
            api_key=api_key,
            model=DEFAULT_MODEL,
            temperature=0.0,
            max_tokens=4096,
            timeout=120,
        )
