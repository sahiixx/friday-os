# CLAUDE.md — friday-os

## What this is

FRIDAY OS — the consolidation target for the six parallel Jarvis/AIOS projects in this workspace. Roadmap lives at `~/.claude/plans/i-want-you-go-crystalline-lemur.md`.

## Ground rules when editing this repo

- **Read from `~/.openjarvis/` — don't duplicate state.** SOUL.md, USER.md, MEMORY.md, and the five SQLite DBs are live. FRIDAY OS is a consumer, not a second source of truth.
- **Port, don't re-invent.** Canonical sources:
  - Orchestrator / planner / router → `~/Documents/Claude/Projects/SUPER AGI/super_agi/core/`
  - Registry pattern → `~/OpenJarvis/src/openjarvis/`
  - `.claude/` templates + RPI workflow → `~/claude-code-best-practice/.claude/`
  - Subagent personas → `~/Projects/aios-local/.external/agency-agents/.cursor/rules/`
- **OBLITERATUS is out of scope.** It's interpretability research. Link, don't merge.

## Code standards (inherited from workspace)

- Max 30 lines/function, 300 lines/file.
- Type hints on every public signature.
- `f"..."` strings, list comprehensions, `obj?.x ?? default` equivalents (`getattr(obj, "x", default)`).
- WHY comments only.
- Never swallow errors.

## Entry points

```bash
python -c "from friday.core import Orchestrator; print(Orchestrator().run('hello'))"
python -c "from friday.core.memory import persona; print(persona.load()[:200])"
```

## Roadmap phases

See the two plan files. PR 1 Part A = scaffold (done). PR 1 Part B = real planner/router + Anthropic memory tool. PR 2 = tool surface + A2A + computer-use. PR 3 = Claude Code plugin + Tauri shell + widgets.
