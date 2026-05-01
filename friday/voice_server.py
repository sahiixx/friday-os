"""
friday/voice_server.py — Twilio voice call-in server.

Accepts incoming Twilio calls, transcribes speech using faster-whisper,
processes through FRIDAY pipeline, speaks response back using Edge TTS.

Run:
    friday --voice-server --port 8080

Requires:
    pip install twilio fastapi uvicorn faster-whisper edge-tts
"""
from __future__ import annotations

import asyncio
import json
import logging
import os
import tempfile
from pathlib import Path
from typing import Optional

import httpx

logger = logging.getLogger("friday-voice")

BUS_URL = os.getenv("SAHIIXX_BUS_URL", "http://localhost:9000")
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID", "")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN", "")
TWILIO_PHONE = os.getenv("TWILIO_PHONE_NUMBER", "")

WHISPER_MODEL = None


def get_whisper():
    """Lazy-load WhisperModel."""
    global WHISPER_MODEL
    if WHISPER_MODEL is None:
        from faster_whisper import WhisperModel
        WHISPER_MODEL = WhisperModel("base", device="cpu", compute_type="int8")
    return WHISPER_MODEL


async def transcribe(audio_path: str) -> str:
    """Transcribe audio file to text."""
    model = get_whisper()
    segments, info = model.transcribe(audio_path)
    return " ".join(s.text for s in segments)


async def process_query(text: str) -> str:
    """Send text through the FRIDAY A2A pipeline."""
    try:
        async with httpx.AsyncClient(timeout=60) as client:
            # Try local A2A invoke endpoint (self-call for internal routing)
            r = await client.post(
                "http://127.0.0.1:8080/a2a/invoke",
                json={"skill": "chat", "input": text},
            )
            if r.status_code == 200:
                data = r.json()
                if isinstance(data, dict) and data.get("ok"):
                    return data.get("output", str(data))
                return str(data)

            # Try GET /speak?text=... (browser fallback)
            r = await client.get(
                "http://127.0.0.1:8000/speak",
                params={"text": text},
            )
            if r.status_code == 200:
                data = r.json()
                if isinstance(data, dict):
                    return data.get("response", data.get("output", data.get("spoken", str(data))))
                return str(data)

    except Exception:
        pass

    # Fallback: Ollama directly
    try:
        async with httpx.AsyncClient(timeout=60) as client:
            r = await client.post(
                "http://127.0.0.1:11434/v1/chat/completions",
                json={
                    "model": "llama3.1",
                    "messages": [{"role": "user", "content": text}],
                    "max_tokens": 512,
                },
            )
            if r.status_code == 200:
                return r.json()["choices"][0]["message"]["content"]
    except Exception as e:
        logger.error("Process failed: %s", e)

    return "I'm sorry, I couldn't process that request. Please try again."


async def speak(text: str) -> Optional[str]:
    """Convert text to speech using Edge TTS, return file path."""
    try:
        from edge_tts import Communicate
        tts_dir = Path(tempfile.gettempdir()) / "friday_tts"
        tts_dir.mkdir(exist_ok=True)
        out_path = str(tts_dir / f"response_{hash(text)}.mp3")

        communicate = Communicate(text, voice="en-US-AriaNeural")
        await communicate.save(out_path)
        return out_path
    except ImportError:
        logger.warning("edge-tts not installed")
        return None
    except Exception as e:
        logger.error("TTS failed: %s", e)
        return None


# ---------------------------------------------------------------------------
# Twilio Voice XML builders
# ---------------------------------------------------------------------------

def welcome_twiml() -> str:
    """TwiML for the welcome message + gather speech input."""
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="Google.en-US-Neural2-F">{os.getenv("TWILIO_WELCOME_MSG",
        "You are connected to the SAHIIXX ecosystem voice assistant. How can I help you today?")}</Say>
    <Gather input="speech" speechTimeout="auto" speechModel="phone_call"
            action="/twilio/process" method="POST" enhanced="true">
        <Say>Please speak after the beep.</Say>
    </Gather>
    <Redirect method="POST">/twilio/fallback</Redirect>
</Response>"""


def response_twiml(response_text: str) -> str:
    """TwiML speaking back the response and gathering next input."""
    import xml.sax.saxutils as saxutils
    safe = saxutils.escape(response_text[:1000])
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="Google.en-US-Neural2-F">{safe}</Say>
    <Gather input="speech" speechTimeout="auto" speechModel="phone_call"
            action="/twilio/process" method="POST" enhanced="true">
        <Say>What else can I help with?</Say>
    </Gather>
    <Redirect method="POST">/twilio/fallback</Redirect>
</Response>"""


def fallback_twiml() -> str:
    """TwiML for when speech isn't detected."""
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="Google.en-US-Neural2-F">{os.getenv("TWILIO_FALLBACK_MSG",
        "I did not catch that. Please try again.")}</Say>
    <Redirect method="POST">/twilio/voice</Redirect>
</Response>"""


def goodbye_twiml() -> str:
    return """<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="Google.en-US-Neural2-F">Goodbye. Have a great day.</Say>
    <Hangup/>
</Response>"""


# ---------------------------------------------------------------------------
# FastAPI app
# ---------------------------------------------------------------------------


def make_voice_app():
    """Create a Starlette ASGI app for Twilio voice endpoints."""
    from starlette.applications import Starlette
    from starlette.requests import Request
    from starlette.responses import Response
    from starlette.routing import Route

    async def voice_endpoint(request: Request):
        """Entry point for incoming Twilio calls."""
        try:
            _ = await request.form()
        except Exception:
            pass
        return Response(content=welcome_twiml(), media_type="application/xml")

    async def process_endpoint(request: Request):
        """Process speech from the caller."""
        try:
            form = await request.form()
        except Exception:
            form = {}
        speech_result = form.get("SpeechResult", "")

        if not speech_result.strip():
            return Response(content=fallback_twiml(), media_type="application/xml")

        if speech_result.lower().strip() in ("goodbye", "bye", "hang up", "stop", "quit", "exit", "end call"):
            return Response(content=goodbye_twiml(), media_type="application/xml")

        # Return immediate TwiML with Twilio's built-in TTS (Google Neural2)
        # to stay under the 15-second Twilio timeout. Use <Say> not <Play>.
        response_text = await process_query(speech_result)

        import xml.sax.saxutils as saxutils
        safe = saxutils.escape(response_text[:1500])
        twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="Google.en-US-Neural2-F">{safe}</Say>
    <Gather input="speech" speechTimeout="auto" speechModel="phone_call"
            action="/twilio/process" method="POST" enhanced="true">
        <Say>What else can I help with?</Say>
    </Gather>
    <Redirect method="POST">/twilio/fallback</Redirect>
</Response>"""
        return Response(content=twiml, media_type="application/xml")

    async def fallback_endpoint(request: Request):
        """Fallback when no speech detected."""
        try:
            _ = await request.form()
        except Exception:
            pass
        return Response(content=fallback_twiml(), media_type="application/xml")

    async def health_endpoint(request: Request):
        import json
        return Response(
            content=json.dumps({"status": "ok", "service": "friday-voice-server", "twilio_configured": bool(TWILIO_ACCOUNT_SID)}),
            media_type="application/json"
        )

    async def agent_card_endpoint(request: Request):
        import json
        agent_card = json.load(open(str(Path(__file__).parent.parent / "agent-card.json")))
        return Response(content=json.dumps(agent_card), media_type="application/json")

    async def a2a_invoke_endpoint(request: Request):
        """
        A2A invoke endpoint.
        Accepts {"skill": "chat", "input": "query"} and routes through:
          1. agency-agents capability discovery + Ollama chat
          2. falls back to direct Ollama call (deepseek-v4-flash:cloud)
        Returns {"ok": true, "output": "..."} or {"ok": false, "error": "..."}
        """
        import json
        try:
            body = await request.json()
        except Exception:
            return Response(
                content=json.dumps({"ok": False, "error": "invalid JSON body"}),
                media_type="application/json",
                status_code=400,
            )

        skill = body.get("skill", "chat")
        user_input = body.get("input", "")
        if not user_input.strip():
            return Response(
                content=json.dumps({"ok": False, "error": "empty input"}),
                media_type="application/json",
                status_code=400,
            )

        # Step 1: Try agency-agents at localhost:8766
        try:
            async with httpx.AsyncClient(timeout=120) as client:
                # Discover capabilities
                r = await client.get("http://localhost:8766/.well-known/agent.json")
                if r.status_code == 200:
                    agent_meta = r.json()
                    logger.info("agency-agents discovered: %s", agent_meta.get("name", "unknown"))

                    # Try agency-agents Ollama chat completion
                    r2 = await client.post(
                        "http://localhost:8766/a2a/chat",
                        json={
                            "skill": skill,
                            "input": user_input,
                            "max_tokens": 1024,
                        },
                        timeout=30,
                    )
                    if r2.status_code == 200:
                        data = r2.json()
                        output = data.get("output", data.get("response", str(data)))
                        return Response(
                            content=json.dumps({"ok": True, "output": output, "source": "agency-agents"}),
                            media_type="application/json",
                        )
                    logger.warning("agency-agents chat returned %d, falling back", r2.status_code)
        except Exception as e:
            logger.warning("agency-agents unavailable: %s", e)

        # Step 2: Fallback — direct Ollama call
        try:
            async with httpx.AsyncClient(timeout=60) as client:
                r = await client.post(
                    "http://127.0.0.1:11434/api/chat",
                    json={
                        "model": "deepseek-v4-flash:cloud",
                        "messages": [{"role": "user", "content": user_input}],
                        "stream": False,
                        "options": {"num_predict": 1024},
                    },
                )
                if r.status_code == 200:
                    data = r.json()
                    output = data.get("message", {}).get("content", str(data))
                    return Response(
                        content=json.dumps({"ok": True, "output": output, "source": "ollama"}),
                        media_type="application/json",
                    )
                return Response(
                    content=json.dumps({"ok": False, "error": f"Ollama returned {r.status_code}"}),
                    media_type="application/json",
                    status_code=502,
                )
        except Exception as e:
            logger.error("A2A invoke failed: %s", e)
            return Response(
                content=json.dumps({"ok": False, "error": str(e)}),
                media_type="application/json",
                status_code=500,
            )

    app = Starlette(routes=[
        Route("/twilio/voice", endpoint=voice_endpoint, methods=["GET", "POST"]),
        Route("/twilio/process", endpoint=process_endpoint, methods=["GET", "POST"]),
        Route("/twilio/fallback", endpoint=fallback_endpoint, methods=["GET", "POST"]),
        Route("/health", endpoint=health_endpoint, methods=["GET"]),
        Route("/.well-known/agent.json", endpoint=agent_card_endpoint, methods=["GET"]),
        Route("/a2a/invoke", endpoint=a2a_invoke_endpoint, methods=["POST"]),
    ])

    return app


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

async def voice_server_main(port: int = 8080):
    """Start the voice server."""
    from uvicorn import Config, Server

    logger.info("Starting FRIDAY Voice Server on port %d", port)

    app = make_voice_app()
    config = Config(app=app, host="127.0.0.1", port=port, log_level="info")
    server = Server(config)

    # Verify whisper
    try:
        get_whisper()
        logger.info("faster-whisper loaded (base model)")
    except Exception as e:
        logger.warning("faster-whisper not available: %s", e)

    await server.serve()


if __name__ == "__main__":
    import sys
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8080
    asyncio.run(voice_server_main(port=port))
