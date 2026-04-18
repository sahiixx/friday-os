import os
import time

from friday.core.llm.base import LLMProvider, LLMResponse


class AnthropicProvider(LLMProvider):
    """Wraps the `anthropic` SDK. Graceful when the SDK or key is missing."""

    def __init__(self, model: str = "claude-opus-4-7", api_key: str | None = None) -> None:
        self.model = model
        self._api_key = api_key or os.getenv("ANTHROPIC_API_KEY", "")
        self._client = self._make_client()

    def _make_client(self):
        if not self._api_key:
            return None
        try:
            import anthropic
            return anthropic.Anthropic(api_key=self._api_key)
        except ImportError:
            return None

    @property
    def name(self) -> str:
        return "anthropic"

    def is_available(self) -> bool:
        return self._client is not None

    def chat(self, messages: list[dict], system: str = "", max_tokens: int = 2048) -> LLMResponse:
        if not self._client:
            raise RuntimeError("AnthropicProvider unavailable: install `anthropic` and set ANTHROPIC_API_KEY")
        t0 = time.time()
        kwargs = {"model": self.model, "max_tokens": max_tokens, "messages": messages}
        if system:
            kwargs["system"] = system
        resp = self._client.messages.create(**kwargs)
        elapsed_ms = (time.time() - t0) * 1000
        text = resp.content[0].text.strip() if resp.content else ""
        return LLMResponse(text=text, model=self.model, provider=self.name, elapsed_ms=elapsed_ms)
