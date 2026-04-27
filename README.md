# FRIDAY OS — Voice-First AI Operating System

> **A voice-first, memory-persistent, MCP-powered personal AI OS.**  
> PERCEIVE → ROUTE → PLAN → EXECUTE → SYNTHESIZE — with your voice.

[![Voice-First](https://img.shields.io/badge/voice--first-LiveKit-red)](https://livekit.io)
[![Local-First](https://img.shields.io/badge/local--first-ollama-green)](https://ollama.com)
[![Tests](https://img.shields.io/badge/tests-pytest-blue)](tests/)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

---

## The Pitch

**Siri** answers weather. **Alexa** sets timers. **FRIDAY** builds your startup.

FRIDAY OS is a voice-first AI operating system that:
- 🎙️ **Listens** — LiveKit real-time voice pipeline (STT → Brain → TTS)
- 🧠 **Thinks** — PERCEIVE → ROUTE → PLAN → EXECUTE → SYNTHESIZE
- 💾 **Remembers** — Persistent memory across sessions (integrates with `titans-memory`)
- 🔧 **Acts** — Tool registry with web search, code execution, shell, file I/O
- 🏗️ **Delegates** — Multi-step planning with dependency resolution
- 🎭 **Adapts** — Loads your persona from `~/.openjarvis/{SOUL,USER,MEMORY}.md`

All local. All private. No cloud required.

---

## One-Command Start

```bash
# Clone and install
git clone https://github.com/sahiixx/friday-os.git
cd friday-os
pip install -e ".[voice]"

# Start FRIDAY (console mode — no voice deps needed)
python -m friday.cli

# Or start voice agent (requires LiveKit + Ollama)
python -m friday.voice.agent_friday console
```

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  🎙️ Voice Layer (LiveKit Agents SDK)                        │
│   ├── Silero VAD (voice activity detection)                 │
│   ├── OpenAI Whisper STT (or local equivalent)              │
│   └── OpenAI TTS (or local equivalent)                     │
├─────────────────────────────────────────────────────────────┤
│  🧠 FRIDAY Brain                                             │
│   ├── Router — intent classification (heuristic + LLM)      │
│   ├── Planner — multi-step plan with dependency resolution  │
│   ├── Orchestrator — PERCEIVE→ROUTE→PLAN→EXECUTE→SYNTHESIZE│
│   └── Memory — persona + episodic + titans-memory           │
├─────────────────────────────────────────────────────────────┤
│  🔧 Tool Registry                                            │
│   ├── search_web — DuckDuckGo                               │
│   ├── run_code — Python sandbox                             │
│   ├── shell_exec — gated shell access                       │
│   ├── memory_save / memory_recall — persistent storage      │
│   └── file_read / file_write — file I/O                     │
├─────────────────────────────────────────────────────────────┤
│  🦙 LLM Provider (pluggable)                                 │
│   ├── Claude (API)                                          │
│   ├── OpenAI (API)                                          │
│   └── Ollama (local) — qwen2.5-coder, llama3.1, etc.       │
└─────────────────────────────────────────────────────────────┘
```

---

## How It Works

### 1. Router — What do you want?

```python
# Heuristic classification (zero-cost fast path)
"Search for latest AI news"        → RESEARCH
"Calculate 2^128"                 → ANALYTICAL
"Write a poem about recursion"    → CREATIVE
"Build a Chrome extension"        → AGENTIC (requires planning)
"Hello"                           → CONVERSATIONAL
```

If confidence < 0.6, the LLM reclassifies.

### 2. Planner — How do we do it?

```json
{
  "intent": "Build a Chrome extension",
  "complexity": "high",
  "steps": [
    {"id": 1, "action": "Create manifest.json", "tool": "file_write"},
    {"id": 2, "action": "Write content script", "tool": "file_write", "depends_on": [1]},
    {"id": 3, "action": "Test extension", "tool": "shell_exec", "depends_on": [2]}
  ]
}
```

### 3. Executor — Do it.

Each step runs in order, respecting dependencies. Failed steps are logged but don't crash the system.

### 4. Synthesizer — Explain it.

FRIDAY gives you a direct, actionable final answer — not a raw dump of tool outputs.

---

## Memory

FRIDAY has three memory layers:

| Layer | Source | Persistence |
|-------|--------|-------------|
| **Persona** | `~/.openjarvis/{SOUL,USER,MEMORY}.md` | Cross-session |
| **Episodic** | `memory/episodes/*.jsonl` | Cross-session |
| **Titans** | `titans-memory` integration | Surprise-weighted, ranked |

```python
# Use titans-memory for ranked recall
from friday.core.memory import titans

context = titans.recall("auth module refactor")
# Returns weighted memories sorted by surprise + recency
```

---

## Voice Modes

| Mode | Command | What It Does |
|------|---------|-------------|
| **Console** | `python -m friday.cli` | Text-based chat |
| **Local Voice** | `python -m friday.voice.agent_friday console` | Mic + speaker, no LiveKit |
| **LiveKit Room** | `python -m friday.voice.agent_friday dev` | Join a LiveKit room |
| **Web UI** | `python -m friday.server` | Browser-based chat (planned) |

---

## Safety

| Mode | Behavior |
|------|----------|
| `trusted_local` *(default)* | All tools enabled |
| `read_only` | No file writes, no shell |
| `paranoid` | Every action requires confirmation |

Set via `FRIDAY_SAFETY_MODE` env var.

---

## Ecosystem

| Repo | Role |
|------|------|
| [`goose-aios`](https://github.com/sahiixx/goose-aios) | Local LLM backend — Ollama + FastAPI |
| [`titans-memory`](https://github.com/sahiixx/titans-memory) | Surprise-weighted persistent memory |
| [`claude-skills`](https://github.com/sahiixx/claude-skills) | 12 Claude Code skills for specialized tasks |
| [`agent-design.md`](https://github.com/sahiixx/sahiixx-agent-design.md) | Visual identity spec |
| [`hermesclaw`](https://github.com/AaronWong1999/hermesclaw) | WeChat bridge for mobile access |

---

## Tests

```bash
pytest tests/ -v
```

---

## License

MIT — see [LICENSE](LICENSE).

> *"The future of AI isn't a chatbot. It's an operating system that listens, thinks, and acts — and never forgets."*
