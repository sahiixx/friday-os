from pathlib import Path

from friday.core.a2a.schema import A2ARequest, A2AResponse, descriptor
from friday.core.orchestrator import Orchestrator

try:  # keep fastapi optional — CLI must run without it
    from fastapi import FastAPI, Request
    from fastapi.responses import HTMLResponse, StreamingResponse
    _FASTAPI_OK = True
except ImportError:
    _FASTAPI_OK = False

# WHY: ship a zero-install see+hear surface. Chrome/Edge speechSynthesis + STT
# means the user opens one URL and can talk to FRIDAY — no Tauri build needed.
_STATIC_DIR = Path(__file__).parent / "static"


def build_app(orchestrator: Orchestrator | None = None,
              base_url: str = "http://localhost:8001"):
    """Return a FastAPI app exposing A2A + discovery."""
    if not _FASTAPI_OK:
        raise RuntimeError("fastapi not installed — `pip install friday-os[a2a]`")

    app = FastAPI(title="FRIDAY OS A2A")
    orch = orchestrator or Orchestrator()

    @app.get("/", response_class=HTMLResponse)
    async def index() -> HTMLResponse:
        # WHY: tell the browser never to cache the shell — during iteration a
        # stale index.html causes "no response" bugs that look like the server.
        body = (_STATIC_DIR / "index.html").read_text(encoding="utf-8")
        return HTMLResponse(body, headers={"Cache-Control": "no-store"})

    @app.get("/.well-known/agent.json")
    async def agent_descriptor() -> dict:
        return descriptor(base_url=base_url)

    @app.get("/health")
    async def health() -> dict:
        return {"ok": True, "tools": orch.tools.names()}

    @app.get("/connectors")
    async def connectors() -> dict:
        from friday.connectors import load_connectors
        return {"connectors": load_connectors()}

    @app.post("/chat/stream")
    async def chat_stream(req: Request):
        # WHY: SSE of Ollama tokens → perceived latency drops to ~200ms.
        payload = await req.json()
        text = (payload or {}).get("input", "").strip()
        if not text:
            return {"error": "input required"}

        def gen():
            try:
                for piece in orch.llm.stream(
                        [{"role": "user", "content": text}],
                        system=orch.persona_prompt):
                    yield f"data: {piece}\n\n"
            except Exception as exc:
                yield f"event: error\ndata: {exc}\n\n"
            yield "event: done\ndata: [done]\n\n"
        return StreamingResponse(gen(), media_type="text/event-stream")

    @app.get("/speak")
    async def speak(text: str):
        # WHY: Windows SAPI fallback when the browser has zero TTS voices.
        import subprocess
        safe = text.replace("'", "").replace('"', "")[:400]
        script = (f"Add-Type -AssemblyName System.Speech; "
                  f"(New-Object System.Speech.Synthesis.SpeechSynthesizer).Speak('{safe}')")
        subprocess.Popen(["powershell", "-NoProfile", "-Command", script])
        return {"ok": True, "spoken": safe}

    @app.post("/tool/{name}")
    async def call_tool(name: str, req: Request) -> dict:
        # WHY: lets the UI run a tool in ~10ms without waiting on the 15-45s
        # LLM planner. Proves tool execution works in isolation.
        if not orch.tools.has(name):
            return {"ok": False, "tool": name, "output": "", "error": "unknown tool"}
        payload = await req.json()
        text = (payload or {}).get("input", "")
        result = orch.tools.call(name, text)
        return {"ok": True, "tool": name, "output": str(result)}

    @app.post("/a2a/invoke")
    async def invoke(req: Request) -> dict:
        payload = await req.json()
        a2a = A2ARequest.from_dict(payload)
        if not a2a.input.strip():
            return A2AResponse(ok=False, output="", error="input required").to_dict()
        resp = orch.run(a2a.input)
        return A2AResponse(
            ok=resp.success, output=resp.output, intent=resp.intent,
            tool_calls=resp.tool_calls, elapsed_ms=resp.elapsed_ms, error=resp.error,
        ).to_dict()

    return app


def serve(host: str = "0.0.0.0", port: int = 8001) -> None:
    try:
        import uvicorn
    except ImportError as exc:
        raise RuntimeError("uvicorn not installed — `pip install friday-os[a2a]`") from exc
    uvicorn.run(build_app(base_url=f"http://{host}:{port}"), host=host, port=port)


if __name__ == "__main__":
    serve()
