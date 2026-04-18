"""Pytest configuration and shared fixtures."""

import os

import pytest
from unittest.mock import MagicMock


@pytest.fixture(autouse=True)
def _isolate_llm_env(monkeypatch):
    # Tests must be deterministic regardless of whether the dev machine has
    # Ollama running or an ANTHROPIC_API_KEY set. Pin to "anthropic" with no
    # key -> provider reports unavailable -> heuristic paths engage.
    monkeypatch.setenv("FRIDAY_LLM", "anthropic")
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)


@pytest.fixture
def mock_llm():
    """Returns a mock LLM that returns valid JSON."""
    llm = MagicMock()
    llm.complete.return_value = '{"intent": "CONVERSATIONAL", "steps": []}'
    return llm


@pytest.fixture
def mock_registry():
    """Returns a mock tool registry."""
    reg = MagicMock()
    reg.call.return_value = {"ok": True, "output": "mocked"}
    reg.list_tools.return_value = ["mock_tool"]
    return reg
