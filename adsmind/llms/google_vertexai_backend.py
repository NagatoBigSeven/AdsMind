"""
Google Vertex AI backend implementation.

This backend routes Gemini calls through Vertex AI instead of the Gemini
Developer API or an OpenRouter-compatible proxy. Authentication is handled by
Google ADC / gcloud on the host running AdsMind.
"""

import importlib.util
import os
from typing import Optional

from langchain_core.language_models.chat_models import BaseChatModel

from adsmind.llms.base import BaseLLMBackend, LLMConfig
from adsmind.utils.logger import get_logger

logger = get_logger(__name__)

DEFAULT_MODEL = "gemini-2.5-pro"
DEFAULT_LOCATION = "us-central1"


class GoogleVertexAIBackend(BaseLLMBackend):
    """Google Vertex AI Gemini backend using LangChain's ChatVertexAI."""

    @property
    def name(self) -> str:
        return "google_vertexai"

    @property
    def requires_api_key(self) -> bool:
        return False

    @property
    def is_available(self) -> bool:
        """Check if langchain-google-vertexai is installed."""
        return importlib.util.find_spec("langchain_google_vertexai") is not None

    def get_chat_model(self, config: LLMConfig) -> BaseChatModel:
        """
        Return a ChatVertexAI instance.

        Vertex AI uses Google Application Default Credentials. The optional
        ``project`` and ``location`` values can be supplied through
        ``config.extra_options`` or the standard Google environment variables.
        """
        from langchain_google_vertexai import ChatVertexAI

        project = config.extra_options.get("project") or os.environ.get(
            "GOOGLE_CLOUD_PROJECT"
        ) or os.environ.get("GCLOUD_PROJECT")
        location = (
            config.extra_options.get("location")
            or os.environ.get("GOOGLE_CLOUD_LOCATION")
            or os.environ.get("VERTEXAI_LOCATION")
            or DEFAULT_LOCATION
        )

        logger.info(
            f"Initializing Google Vertex AI backend (model: {config.model}, "
            f"project: {project}, location: {location}, "
            f"temperature: {config.temperature})"
        )

        kwargs = {
            "model": config.model,
            "location": location,
            "temperature": config.temperature,
            "max_tokens": config.max_tokens,
        }
        if project:
            kwargs["project"] = project

        return ChatVertexAI(**kwargs)

    def get_default_config(self, api_key: Optional[str] = None) -> LLMConfig:
        """Return default configuration for Vertex AI Gemini."""
        return LLMConfig(
            backend=self.name,
            api_key=None,
            model=DEFAULT_MODEL,
            temperature=0.0,
            max_tokens=4096,
            timeout=120,
        )
