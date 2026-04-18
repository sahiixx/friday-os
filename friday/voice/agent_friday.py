"""FRIDAY voice agent — LiveKit Agents SDK, wraps Orchestrator.run().

Runs a realtime voice pipeline: STT -> Orchestrator -> TTS. Designed to stay
dormant until you install the `voice` extra (`pip install friday-os[voice]`).

Entry point:
    python -m friday.voice.agent_friday console   # local mic/speaker
    python -m friday.voice.agent_friday dev       # LiveKit room
"""

from __future__ import annotations

import os
import sys

from friday.core import Orchestrator, OrchestratorConfig


def _require_livekit():
    try:
        from livekit.agents import Agent, AgentSession, JobContext, WorkerOptions, cli
        from livekit.plugins import openai, silero
        return Agent, AgentSession, JobContext, WorkerOptions, cli, openai, silero
    except ImportError as exc:
        raise RuntimeError(
            "livekit not installed — `pip install friday-os[voice]` "
            "or `pip install livekit-agents livekit-plugins-openai livekit-plugins-silero`"
        ) from exc


class FridayVoiceAgent:
    """Thin wrapper: LiveKit provides the audio loop; Orchestrator provides the brain."""

    def __init__(self, orchestrator: Orchestrator | None = None) -> None:
        self.orchestrator = orchestrator or Orchestrator(
            config=OrchestratorConfig(verbose=os.getenv("FRIDAY_VERBOSE") == "1"),
        )

    async def on_user_turn(self, transcript: str) -> str:
        # Runs the full PERCEIVE -> ROUTE -> PLAN -> EXECUTE -> SYNTHESIZE loop.
        response = self.orchestrator.run(transcript)
        return response.output or "(no response)"


async def entrypoint(ctx) -> None:
    """LiveKit entrypoint — called per room join."""
    Agent, AgentSession, _, _, _, openai, silero = _require_livekit()
    friday = FridayVoiceAgent()

    session = AgentSession(
        vad=silero.VAD.load(),
        stt=openai.STT(),
        tts=openai.TTS(voice=os.getenv("FRIDAY_VOICE", "nova")),
    )
    agent = Agent(instructions=friday.orchestrator.persona_prompt)

    async def on_transcript(text: str) -> None:
        reply = await friday.on_user_turn(text)
        await session.say(reply)

    session.on("user_transcript", on_transcript)
    await session.start(agent=agent, room=ctx.room)


def main() -> None:
    _, _, _, WorkerOptions, cli, _, _ = _require_livekit()
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))


if __name__ == "__main__":
    main()
