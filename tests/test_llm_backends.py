"""
Unit tests for LLM backend factory.

Tests the multi-backend LLM support including factory pattern,
configuration, and backend availability checks.
"""

import os
import sys
import types
import unittest
from unittest.mock import patch


class TestLLMFactory(unittest.TestCase):
    """Test the LLM backend factory."""
    
    def test_factory_import(self):
        """Test that factory can be imported."""
        from src.llms import get_llm_backend, get_available_llm_backends
        self.assertTrue(callable(get_llm_backend))
        self.assertTrue(callable(get_available_llm_backends))
    
    def test_get_google_backend(self):
        """Test getting Google backend."""
        from src.llms import get_llm_backend
        backend = get_llm_backend("google")
        self.assertEqual(backend.name, "google")
        self.assertTrue(backend.requires_api_key)
    
    def test_get_openrouter_backend(self):
        """Test getting OpenRouter backend."""
        from src.llms import get_llm_backend
        backend = get_llm_backend("openrouter")
        self.assertEqual(backend.name, "openrouter")
        self.assertTrue(backend.requires_api_key)

    def test_get_anthropic_backend(self):
        """Test getting Anthropic backend."""
        from src.llms import get_llm_backend
        backend = get_llm_backend("anthropic")
        self.assertEqual(backend.name, "anthropic")
        self.assertTrue(backend.requires_api_key)

    def test_get_xai_backend(self):
        """Test getting xAI backend."""
        from src.llms import get_llm_backend
        backend = get_llm_backend("xai")
        self.assertEqual(backend.name, "xai")
        self.assertTrue(backend.requires_api_key)
    
    def test_get_ollama_backend(self):
        """Test getting Ollama backend."""
        from src.llms import get_llm_backend
        backend = get_llm_backend("ollama")
        self.assertEqual(backend.name, "ollama")
        self.assertFalse(backend.requires_api_key)
    
    def test_get_huggingface_backend(self):
        """Test getting HuggingFace backend."""
        from src.llms import get_llm_backend
        backend = get_llm_backend("huggingface")
        self.assertEqual(backend.name, "huggingface")
        self.assertFalse(backend.requires_api_key)
    
    def test_unknown_backend_raises_error(self):
        """Test that unknown backend raises ValueError."""
        from src.llms import get_llm_backend
        with self.assertRaises(ValueError) as exc_info:
            get_llm_backend("unknown_backend")
        self.assertIn("Unknown LLM backend", str(exc_info.exception))
    
    def test_available_backends(self):
        """Test listing available backends without relying on host installs."""
        from src.llms import get_available_llm_backends

        class AvailableBackend:
            def __init__(self):
                self.is_available = True

        class UnavailableBackend:
            def __init__(self):
                self.is_available = False

        with patch("src.llms.factory._get_llm_registry", return_value={
            "available": AvailableBackend,
            "unavailable": UnavailableBackend,
        }):
            available = get_available_llm_backends()

        self.assertEqual(available, ["available"])


class TestLLMConfig(unittest.TestCase):
    """Test LLM configuration dataclass."""
    
    def test_config_creation(self):
        """Test creating LLMConfig."""
        from src.llms.base import LLMConfig
        config = LLMConfig(
            backend="google",
            api_key="test-key",
            model="gemini-2.5-pro"
        )
        self.assertEqual(config.backend, "google")
        self.assertEqual(config.api_key, "test-key")
        self.assertEqual(config.model, "gemini-2.5-pro")
        self.assertEqual(config.temperature, 0.0)
    
    def test_config_defaults(self):
        """Test LLMConfig default values."""
        from src.llms.base import LLMConfig
        config = LLMConfig(backend="test")
        self.assertEqual(config.temperature, 0.0)
        self.assertEqual(config.max_tokens, 4096)
        self.assertEqual(config.timeout, 120)
        self.assertEqual(config.extra_options, {})


class TestGoogleBackend(unittest.TestCase):
    """Test Google AI backend."""
    
    def test_default_config(self):
        """Test default configuration."""
        from src.llms import get_llm_backend
        backend = get_llm_backend("google")
        config = backend.get_default_config(api_key="test-key")
        
        self.assertEqual(config.backend, "google")
        self.assertEqual(config.api_key, "test-key")
        self.assertEqual(config.model, "gemini-2.5-pro")
        self.assertEqual(config.temperature, 0.0)
    
    def test_is_available(self):
        """Test availability check."""
        from src.llms import get_llm_backend
        backend = get_llm_backend("google")
        # Should be True if langchain_google_genai is installed
        self.assertIsInstance(backend.is_available, bool)


class TestOpenRouterBackend(unittest.TestCase):
    """Test OpenRouter backend."""
    
    def test_default_config(self):
        """Test default configuration."""
        from src.llms import get_llm_backend
        backend = get_llm_backend("openrouter")
        config = backend.get_default_config(api_key="test-key")
        
        self.assertEqual(config.backend, "openrouter")
        self.assertEqual(config.api_key, "test-key")
        self.assertEqual(config.model, "google/gemini-2.5-pro")

    def test_chat_model_respects_custom_base_url(self):
        """Custom transport options should be forwarded to ChatOpenAI."""
        from src.llms import get_llm_backend

        captured = {}

        class FakeChatOpenAI:
            def __init__(self, **kwargs):
                captured.update(kwargs)

        fake_module = types.SimpleNamespace(ChatOpenAI=FakeChatOpenAI)

        with patch.dict(sys.modules, {"langchain_openai": fake_module}):
            backend = get_llm_backend("openrouter")
            config = backend.get_default_config(api_key="test-key")
            config.model = "gemini-3.1-pro-preview"
            config.extra_options = {
                "base_url": "https://aihubmix.com/v1",
                "default_headers": {"X-Test": "1"},
                "seed": 7,
            }
            backend.get_chat_model(config)

        self.assertEqual(captured["openai_api_base"], "https://aihubmix.com/v1")
        self.assertEqual(captured["default_headers"], {"X-Test": "1"})
        self.assertEqual(captured["seed"], 7)


class TestAnthropicBackend(unittest.TestCase):
    """Test Anthropic backend."""

    def test_default_config(self):
        """Test default Anthropic configuration."""
        from src.llms import get_llm_backend
        backend = get_llm_backend("anthropic")
        config = backend.get_default_config(api_key="test-key")

        self.assertEqual(config.backend, "anthropic")
        self.assertEqual(config.api_key, "test-key")
        self.assertEqual(config.model, "claude-sonnet-4-6")

    def test_chat_model_uses_official_anthropic_base_url(self):
        """Anthropic backend should call the official compatibility endpoint."""
        from src.llms import get_llm_backend

        captured = {}

        class FakeChatOpenAI:
            def __init__(self, **kwargs):
                captured.update(kwargs)

        fake_module = types.SimpleNamespace(ChatOpenAI=FakeChatOpenAI)

        with patch.dict(sys.modules, {"langchain_openai": fake_module}):
            backend = get_llm_backend("anthropic")
            config = backend.get_default_config(api_key="test-key")
            backend.get_chat_model(config)

        self.assertEqual(captured["openai_api_base"], "https://api.anthropic.com/v1/")
        self.assertEqual(captured["openai_api_key"], "test-key")
        self.assertEqual(captured["model"], "claude-sonnet-4-6")

    def test_chat_model_allows_custom_headers(self):
        """Anthropic backend should forward custom headers when configured."""
        from src.llms import get_llm_backend

        captured = {}

        class FakeChatOpenAI:
            def __init__(self, **kwargs):
                captured.update(kwargs)

        fake_module = types.SimpleNamespace(ChatOpenAI=FakeChatOpenAI)

        with patch.dict(sys.modules, {"langchain_openai": fake_module}):
            backend = get_llm_backend("anthropic")
            config = backend.get_default_config(api_key="test-key")
            config.extra_options = {"default_headers": {"X-Test": "1"}}
            backend.get_chat_model(config)

        self.assertEqual(captured["default_headers"], {"X-Test": "1"})


class TestXAIBackend(unittest.TestCase):
    """Test xAI backend."""

    def test_default_config(self):
        """Test default xAI configuration."""
        from src.llms import get_llm_backend
        backend = get_llm_backend("xai")
        config = backend.get_default_config(api_key="test-key")

        self.assertEqual(config.backend, "xai")
        self.assertEqual(config.api_key, "test-key")
        self.assertEqual(config.model, "grok-4-0709")

    def test_chat_model_uses_official_xai_base_url(self):
        """xAI backend should call the official API endpoint."""
        from src.llms import get_llm_backend

        captured = {}

        class FakeChatOpenAI:
            def __init__(self, **kwargs):
                captured.update(kwargs)

        fake_module = types.SimpleNamespace(ChatOpenAI=FakeChatOpenAI)

        with patch.dict(sys.modules, {"langchain_openai": fake_module}):
            backend = get_llm_backend("xai")
            config = backend.get_default_config(api_key="test-key")
            backend.get_chat_model(config)

        self.assertEqual(captured["openai_api_base"], "https://api.x.ai/v1")
        self.assertEqual(captured["openai_api_key"], "test-key")
        self.assertEqual(captured["model"], "grok-4-0709")
        self.assertEqual(captured["seed"], 42)


class TestOllamaBackend(unittest.TestCase):
    """Test Ollama backend."""
    
    def test_default_config(self):
        """Test default configuration."""
        from src.llms import get_llm_backend
        backend = get_llm_backend("ollama")
        config = backend.get_default_config()
        
        self.assertEqual(config.backend, "ollama")
        self.assertIsNone(config.api_key)
        self.assertEqual(config.model, "qwen3:8b")
        self.assertIn("host", config.extra_options)
    
    def test_custom_host_from_env(self):
        """Test custom host from environment variable."""
        from src.llms import get_llm_backend
        with patch.dict(os.environ, {"OLLAMA_HOST": "http://custom:11434"}):
            backend = get_llm_backend("ollama")
            config = backend.get_default_config()
            self.assertEqual(config.extra_options["host"], "http://custom:11434")


class TestHuggingFaceBackend(unittest.TestCase):
    """Test HuggingFace backend."""
    
    def test_default_config(self):
        """Test default configuration."""
        from src.llms import get_llm_backend
        backend = get_llm_backend("huggingface")
        config = backend.get_default_config()
        
        self.assertEqual(config.backend, "huggingface")
        self.assertIsNone(config.api_key)
        self.assertEqual(config.model, "Qwen/Qwen3-8B")
        self.assertIn("device", config.extra_options)
        self.assertIn("quantize", config.extra_options)

    def test_cache_key_distinguishes_device_and_quantization(self):
        """Cached pipelines should be keyed by model, device, and quantization."""
        from src.llms import get_llm_backend
        from src.llms.huggingface_backend import HuggingFaceBackend

        fake_module = types.SimpleNamespace(
            ChatHuggingFace=lambda llm, model_id: {"llm": llm, "model_id": model_id},
            HuggingFacePipeline=object,
        )

        with patch.dict(sys.modules, {"langchain_huggingface": fake_module}):
            backend = get_llm_backend("huggingface")
            self.assertIsInstance(backend, HuggingFaceBackend)
            backend.clear_cache()

            with patch.object(backend, "_create_pipeline", side_effect=["pipe-a", "pipe-b"]) as create_pipeline:
                config = backend.get_default_config()
                config.model = "Qwen/Qwen3-8B"
                config.extra_options = {"device": "cpu", "quantize": "none"}
                backend.get_chat_model(config)

                cached_config = backend.get_default_config()
                cached_config.model = "Qwen/Qwen3-8B"
                cached_config.extra_options = {"device": "cpu", "quantize": "none"}
                backend.get_chat_model(cached_config)

                changed_config = backend.get_default_config()
                changed_config.model = "Qwen/Qwen3-8B"
                changed_config.extra_options = {"device": "cpu", "quantize": "4bit"}
                backend.get_chat_model(changed_config)

            self.assertEqual(create_pipeline.call_count, 2)
            backend.clear_cache()


class TestConfigModule(unittest.TestCase):
    """Test config module LLM functions."""
    
    def test_get_llm_backend_name_default(self):
        """Test default backend name."""
        from src.utils.config import get_llm_backend_name, DEFAULT_LLM_BACKEND
        # Clear any environment override
        with patch.dict(os.environ, {}, clear=True):
            backend = get_llm_backend_name()
            self.assertEqual(backend, DEFAULT_LLM_BACKEND)
    
    def test_is_cloud_backend(self):
        """Test cloud backend detection."""
        from src.utils.config import is_cloud_backend
        self.assertTrue(is_cloud_backend("google"))
        self.assertTrue(is_cloud_backend("anthropic"))
        self.assertTrue(is_cloud_backend("xai"))
        self.assertTrue(is_cloud_backend("openrouter"))
        self.assertFalse(is_cloud_backend("ollama"))
        self.assertFalse(is_cloud_backend("huggingface"))

    def test_provider_api_key_mappings(self):
        """Provider-specific cloud backends should use their own API key vars."""
        from src.utils.config import get_api_key_for_backend

        with patch.dict(
            os.environ,
            {
                "ANTHROPIC_API_KEY": "anthropic-key",
                "XAI_API_KEY": "xai-key",
            },
            clear=True,
        ):
            self.assertEqual(get_api_key_for_backend("anthropic"), ("anthropic-key", "env"))
            self.assertEqual(get_api_key_for_backend("xai"), ("xai-key", "env"))


class TestAgentIntegration(unittest.TestCase):
    """Test agent.py integration with LLM backends."""
    
    def test_get_llm_function_signature(self):
        """Test get_llm function signature."""
        from src.agent.agent import get_llm
        import inspect
        sig = inspect.signature(get_llm)
        params = list(sig.parameters.keys())
        self.assertIn("api_key", params)
        self.assertIn("backend_name", params)
        self.assertIn("llm_config", params)
    
    def test_agent_state_has_llm_fields(self):
        """Test AgentState has LLM configuration fields."""
        from src.agent.agent import AgentState
        # TypedDict annotations
        annotations = AgentState.__annotations__
        self.assertIn("llm_backend", annotations)
        self.assertIn("llm_config", annotations)
    
    def test_prepare_initial_state_signature(self):
        """Test _prepare_initial_state function signature."""
        from src.agent.agent import _prepare_initial_state
        import inspect
        sig = inspect.signature(_prepare_initial_state)
        params = list(sig.parameters.keys())
        self.assertIn("llm_backend", params)
        self.assertIn("llm_config", params)

    def test_get_llm_merges_extra_options(self):
        """Unknown llm_config keys should flow into backend extra_options."""
        from src.agent.agent import get_llm
        from src.llms.base import LLMConfig

        class FakeBackend:
            requires_api_key = False
            saved_config = None

            def get_default_config(self, api_key=None):
                return LLMConfig(backend="openrouter", api_key=api_key, model="placeholder")

            def get_chat_model(self, config):
                self.saved_config = config
                return {"model": config.model, "extra_options": dict(config.extra_options)}

        backend = FakeBackend()
        with patch("src.agent.agent.get_llm_backend", return_value=backend):
            model = get_llm(
                api_key="",
                backend_name="openrouter",
                llm_config={
                    "model": "gemini-3.1-pro-preview",
                    "extra_options": {"base_url": "https://aihubmix.com/v1"},
                    "default_headers": {"X-Test": "1"},
                },
            )

        self.assertEqual(model["model"], "gemini-3.1-pro-preview")
        self.assertEqual(
            backend.saved_config.extra_options["base_url"],
            "https://aihubmix.com/v1",
        )
        self.assertEqual(
            backend.saved_config.extra_options["default_headers"],
            {"X-Test": "1"},
        )
