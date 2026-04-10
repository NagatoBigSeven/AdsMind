"""
Anthropic backend implementation.

This backend talks to Anthropic's official OpenAI-compatible Chat Completions
endpoint. It keeps AdsMind's LangChain integration small while avoiding
OpenRouter or other third-party routing for Claude experiments.
"""

import importlib.util
from typing import Optional

from langchain_core.language_models.chat_models import BaseChatModel

from src.llms.base import BaseLLMBackend, LLMConfig
from src.utils.logger import get_logger

logger = get_logger(__name__)

ANTHROPIC_BASE_URL = "https://api.anthropic.com/v1/"
DEFAULT_MODEL = "claude-sonnet-4-6"


class AnthropicBackend(BaseLLMBackend):
    """Direct Anthropic Claude backend via the official compatibility endpoint."""

    @property
    def name(self) -> str:
        return "anthropic"

    @property
    def requires_api_key(self) -> bool:
        return True

    @property
    def is_available(self) -> bool:
        """Check if langchain-openai is installed for OpenAI-compatible transport."""
        return importlib.util.find_spec("langchain_openai") is not None

    def get_chat_model(self, config: LLMConfig) -> BaseChatModel:
        """Return a ChatOpenAI instance pointed at Anthropic's official endpoint."""
        from langchain_openai import ChatOpenAI

        if not config.api_key:
            raise ValueError(
                "Anthropic API key is required. Set ANTHROPIC_API_KEY environment "
                "variable or provide it in the configuration."
            )

        base_url = config.extra_options.get("base_url", ANTHROPIC_BASE_URL)
        default_headers = config.extra_options.get("default_headers") or {}

        logger.info(
            f"Initializing Anthropic backend (base_url: {base_url}, "
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
            default_headers=default_headers,
        )

    def get_default_config(self, api_key: Optional[str] = None) -> LLMConfig:
        """Return default configuration for Anthropic Claude."""
        return LLMConfig(
            backend=self.name,
            api_key=api_key,
            model=DEFAULT_MODEL,
            temperature=0.0,
            max_tokens=4096,
            timeout=120,
        )
