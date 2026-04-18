from __future__ import annotations

import json
import urllib.request

from friday.core.a2a.schema import A2ARequest, A2AResponse

_TIMEOUT = 20


class A2AClient:
    """Call another A2A agent. Uses stdlib urllib to avoid a hard httpx dep."""

    def __init__(self, base_url: str, from_agent: str = "friday-os") -> None:
        self.base_url = base_url.rstrip("/")
        self.from_agent = from_agent

    def descriptor(self) -> dict:
        req = urllib.request.Request(f"{self.base_url}/.well-known/agent.json")
        with urllib.request.urlopen(req, timeout=_TIMEOUT) as r:
            return json.loads(r.read().decode("utf-8"))

    def invoke(self, skill: str, input_text: str, **context) -> A2AResponse:
        body = A2ARequest(
            skill=skill, input=input_text, from_agent=self.from_agent, context=context,
        )
        req = urllib.request.Request(
            f"{self.base_url}/a2a/invoke",
            data=json.dumps(body.__dict__).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=_TIMEOUT) as r:
            data = json.loads(r.read().decode("utf-8"))
        return A2AResponse(
            ok=bool(data.get("ok")), output=str(data.get("output", "")),
            intent=str(data.get("intent", "UNKNOWN")),
            tool_calls=list(data.get("tool_calls") or []),
            elapsed_ms=float(data.get("elapsed_ms") or 0.0),
            error=data.get("error"),
        )
