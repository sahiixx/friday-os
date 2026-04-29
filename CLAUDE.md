# CLAUDE.md — friday-os

## What this is

FRIDAY OS — voice-first personal AI OS. Part of the sahiix ecosystem with agency-agents, sahiixx-bus, and sovereign-swarm-v2.

## Ground rules when editing this repo

- **Ollama-native**: uses local models via ChatOllama. No Anthropic API dependency.
- **Integration points**: sahiixx-bus (port 9000) for A2A/MCP routing, agency-agents for persona orchestration.
- **Voice**: Twilio pipeline with Whisper STT + local TTS.
- **Type hints** on every public signature.
- **Never swallow errors** — always raise or log.

## Entry points

```bash
python -c "from friday.core import Orchestrator; print(Orchestrator().run('hello'))"
python -c "from friday.core.memory import persona; print(persona.load()[:200])"
# Twilio voice server:
python scripts/voice_server.py
```

## Tech Stack

- Python 3.12+ / Ollama (localhost:11434)
- MCP via sahiixx-bus, A2A protocol for inter-agent routing
- Twilio + Whisper + faster-whisper for voice
- Titans memory system

## Code standards

- Max 30 lines/function, 300 lines/file.
- `f"..."` strings, list comprehensions.
- WHY comments only.

## Roadmap

PR 1 = scaffold (done). PR 2 = tool surface + A2A + computer-use. PR 3 = Claude Code plugin + Tauri shell + widgets.
