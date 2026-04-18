# FRIDAY Conventions

## Architecture

- Two processes: `server.py` (MCP), `agent_friday.py` (voice)
- Tools in `friday/tools/*.py`, each exports `def register(mcp)`
- Core primitives in `friday/core/` — tools may import core, core never imports tools

## Python style

- Max **30 lines/function**, **300 lines/file**
- Type hints on public functions
- F-strings, list comprehensions, walrus where clear
- `async def` for IO; don't mix sync/async
- Errors: never `except: pass`. Log or raise.

## Security gates

- Shell: `SHELL_EXEC_ENABLED` + `SHELL_BLOCKED_COMMANDS`
- Desktop: `DESKTOP_CONTROL_ENABLED`
- Files: sandboxed to `FRIDAY_HOME`

## Git

- Commit per logical unit, imperative messages
- Small PRs (~118 lines), squash merge
