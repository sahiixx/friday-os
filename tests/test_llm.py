"""Tests for LLM provider selection."""

import os
from unittest.mock import patch

from friday.core.llm import (AnthropicProvider, OllamaProvider,
                             get_provider)


class TestOllamaProvider:
    def test_defaults_from_env(self):
        with patch.dict(os.environ, {"OLLAMA_MODEL": "mistral",
                                      "OLLAMA_HOST": "http://x:11434"}):
            p = OllamaProvider()
        assert p.model == "mistral"
        assert p.host == "http://x:11434"

    def test_strips_trailing_slash_from_host(self):
        p = OllamaProvider(host="http://localhost:11434/")
        assert p.host == "http://localhost:11434"

    def test_normalizes_schemeless_host(self):
        # Users set OLLAMA_HOST=127.0.0.1:11434 without a scheme; urllib needs one.
        assert OllamaProvider(host="127.0.0.1:11434").host == "http://127.0.0.1:11434"
        assert OllamaProvider(host="localhost:11434/").host == "http://localhost:11434"

    def test_name(self):
        assert OllamaProvider().name == "ollama"

    def test_unavailable_when_host_unreachable(self):
        # Port 1 is virtually never listening; ping must fail fast.
        p = OllamaProvider(host="http://127.0.0.1:1")
        assert p.is_available() is False


class TestProviderFactory:
    def test_explicit_anthropic(self):
        with patch.dict(os.environ, {"FRIDAY_LLM": "anthropic"}):
            assert isinstance(get_provider(), AnthropicProvider)

    def test_explicit_ollama(self):
        with patch.dict(os.environ, {"FRIDAY_LLM": "ollama"}):
            assert isinstance(get_provider(), OllamaProvider)

    def test_auto_falls_back_to_anthropic_when_ollama_down(self):
        # No Ollama on port 1, no ANTHROPIC_API_KEY → still returns Anthropic
        # instance (disabled); orchestrator will use heuristic path.
        with patch.dict(os.environ, {"FRIDAY_LLM": "auto",
                                      "OLLAMA_HOST": "http://127.0.0.1:1"}):
            provider = get_provider()
        assert isinstance(provider, AnthropicProvider)

    def test_preference_argument_overrides_env(self):
        with patch.dict(os.environ, {"FRIDAY_LLM": "anthropic"}):
            assert isinstance(get_provider("ollama"), OllamaProvider)
