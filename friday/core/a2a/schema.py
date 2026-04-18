from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class A2ARequest:
    """Agent-to-agent invocation envelope. Draft-compatible with Google's A2A."""
    skill: str
    input: str
    session_id: str | None = None
    from_agent: str | None = None
    context: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "A2ARequest":
        return cls(
            skill=str(data.get("skill", "")),
            input=str(data.get("input", "")),
            session_id=data.get("session_id"),
            from_agent=data.get("from_agent"),
            context=dict(data.get("context") or {}),
        )


@dataclass
class A2AResponse:
    ok: bool
    output: str
    intent: str = "UNKNOWN"
    tool_calls: list[dict[str, Any]] = field(default_factory=list)
    elapsed_ms: float = 0.0
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok, "output": self.output, "intent": self.intent,
            "tool_calls": self.tool_calls, "elapsed_ms": self.elapsed_ms,
            "error": self.error,
        }


def descriptor(name: str = "FRIDAY OS", version: str = "0.0.1",
               base_url: str = "http://localhost:8001") -> dict[str, Any]:
    """The /.well-known/agent.json payload."""
    return {
        "name": name,
        "version": version,
        "description": "Voice-first, memory-persistent personal AI OS.",
        "url": base_url,
        "protocol": "a2a/draft-1",
        "capabilities": {"skills": ["chat", "plan", "research", "recall"]},
        "endpoints": {"invoke": f"{base_url}/a2a/invoke"},
    }
