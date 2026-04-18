from friday.core.a2a.schema import A2ARequest, A2AResponse, descriptor
from friday.core.orchestrator import Orchestrator

try:  # keep fastapi optional — CLI must run without it
    from fastapi import FastAPI, Request
    _FASTAPI_OK = True
except ImportError:
    _FASTAPI_OK = False


def build_app(orchestrator: Orchestrator | None = None,
              base_url: str = "http://localhost:8001"):
    """Return a FastAPI app exposing A2A + discovery."""
    if not _FASTAPI_OK:
        raise RuntimeError("fastapi not installed — `pip install friday-os[a2a]`")

    app = FastAPI(title="FRIDAY OS A2A")
    orch = orchestrator or Orchestrator()

    @app.get("/.well-known/agent.json")
    async def agent_descriptor() -> dict:
        return descriptor(base_url=base_url)

    @app.get("/health")
    async def health() -> dict:
        return {"ok": True, "tools": orch.tools.names()}

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
