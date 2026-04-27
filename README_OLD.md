# FRIDAY OS

A voice-first, memory-persistent, MCP-powered personal AI OS.

Consolidates patterns from OpenJarvis, SUPER AGI, AIOS-Local, agency-agents, and claude-code-best-practice into one shippable surface: CLI + LiveKit voice + Tauri desktop + Claude Code plugin.

## Status

**PR 1 — Part A (scaffold).** Import graph and persona loader only. No voice, no tools, no A2A yet.

Roadmap: `~/.claude/plans/i-want-you-go-crystalline-lemur.md` + `~/.claude/plans/improving-with-your-latest-lexical-nova.md`.

## Smoke test

```bash
python -c "from friday.core import Orchestrator; print(Orchestrator().run('hello'))"
python -c "from friday.core.memory import persona; print(persona.load()[:200])"
```

The persona loader reads the **live** runtime at `~/.openjarvis/{SOUL,USER,MEMORY}.md`, so FRIDAY OS inherits your existing persona on first boot.

## Layout

```
friday/
├── __init__.py
└── core/
    ├── __init__.py         # re-exports Orchestrator
    ├── orchestrator.py     # PERCEIVE→DECIDE→ACT→LEARN (stub)
    ├── planner.py          # task decomposition (stub)
    ├── router.py           # intent classification (stub)
    └── memory/
        ├── __init__.py
        └── persona.py      # reads ~/.openjarvis/{SOUL,USER,MEMORY}.md
```

## Next

PR 1 Part B — port real planner/router from `Documents/Claude/Projects/SUPER AGI/super_agi/core/` and add Anthropic `memory` tool integration.
