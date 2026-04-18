import json
import os
import time
import urllib.error
import urllib.request

from friday.core.llm.base import LLMProvider, LLMResponse


class OllamaProvider(LLMProvider):
    """Local LLM via Ollama's HTTP API. Zero-dep: stdlib urllib only.

    Default host is http://localhost:11434; model is llama3.1 unless overridden.
    `is_available()` pings /api/tags so orchestrator can fall back silently.
    """

    def __init__(self, model: str | None = None, host: str | None = None) -> None:
        self.model = model or os.getenv("OLLAMA_MODEL", "llama3.1")
        raw = host or os.getenv("OLLAMA_HOST", "http://localhost:11434")
        self.host = _normalize_host(raw)
        self._available: bool | None = None

    @property
    def name(self) -> str:
        return "ollama"

    def is_available(self) -> bool:
        if self._available is not None:
            return self._available
        try:
            req = urllib.request.Request(f"{self.host}/api/tags")
            with urllib.request.urlopen(req, timeout=2) as r:
                r.read()
            self._available = True
        except Exception:
            self._available = False
        return self._available

    def chat(self, messages: list[dict], system: str = "",
             max_tokens: int = 2048) -> LLMResponse:
        if not self.is_available():
            raise RuntimeError(f"OllamaProvider unavailable at {self.host}")
        payload = {
            "model": self.model,
            "messages": _with_system(messages, system),
            "stream": False,
            "options": {"num_predict": max_tokens},
        }
        t0 = time.time()
        text = _post_chat(f"{self.host}/api/chat", payload)
        return LLMResponse(text=text, model=self.model, provider=self.name,
                           elapsed_ms=(time.time() - t0) * 1000)


def _normalize_host(raw: str) -> str:
    # Ollama's default OLLAMA_HOST often omits the scheme; urllib needs one.
    raw = raw.strip().rstrip("/")
    if not raw.startswith(("http://", "https://")):
        raw = f"http://{raw}"
    return raw


def _with_system(messages: list[dict], system: str) -> list[dict]:
    if not system:
        return messages
    return [{"role": "system", "content": system}, *messages]


def _post_chat(url: str, payload: dict) -> str:
    req = urllib.request.Request(
        url, data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"}, method="POST",
    )
    with urllib.request.urlopen(req, timeout=60) as r:
        data = json.loads(r.read().decode("utf-8"))
    return (data.get("message") or {}).get("content", "").strip()
