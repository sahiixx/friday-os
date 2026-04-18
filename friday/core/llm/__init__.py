import os

from friday.core.llm.anthropic_provider import AnthropicProvider
from friday.core.llm.base import LLMProvider, LLMResponse
from friday.core.llm.ollama_provider import OllamaProvider


def get_provider(preference: str | None = None) -> LLMProvider:
    """Return an LLMProvider by env preference.

    FRIDAY_LLM=ollama    -> local Ollama only
    FRIDAY_LLM=anthropic -> Anthropic only
    FRIDAY_LLM=auto|<unset> -> prefer Ollama if running, fall back to Anthropic,
                              else return a disabled Anthropic (heuristic paths engage).
    """
    pref = (preference or os.getenv("FRIDAY_LLM", "auto")).lower()
    if pref == "ollama":
        return OllamaProvider()
    if pref == "anthropic":
        return AnthropicProvider()
    # auto: local-first, then cloud
    ollama = OllamaProvider()
    if ollama.is_available():
        return ollama
    return AnthropicProvider()


__all__ = ["LLMProvider", "LLMResponse", "AnthropicProvider",
           "OllamaProvider", "get_provider"]
