# friday-os

![Python](https://img.shields.io/badge/python-3.11+-blue) ![Docker](https://img.shields.io/badge/docker-ready-blue) ![Agentic](https://img.shields.io/badge/agentic-harness-purple)

**Siri** answers weather. **Alexa** sets timers. **FRIDAY** builds your startup.

## Table of Contents

- [Overview](#overview)
- [Quick Start](#quick-start)
- [Agentic Architecture](#agentic-architecture)
- [Model Routing](#model-routing)
- [Project Layout](#project-layout)
- [Development](#development)
- [Related Repositories](#related-repositories)

## Overview

**Siri** answers weather. **Alexa** sets timers. **FRIDAY** builds your startup.

| | |
|---|---|
| **Stack** | python |
| **Frameworks** | anthropic, docker, fastapi, openai, pydantic |
| **Tests** | yes |
| **Commits** | 2 |
| **Last activity** | 2026-08-10 |
| **Visibility** | public |

## Quick Start

### Install

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt   # or: pip install -e .
```

### Run

```bash
# Entry point not auto-detected; inspect the layout below.
```

## Agentic Architecture

This repository participates in the [sahiixx agentic harness](https://github.com/sahiixx/agentic-harness) — a shared
contract for how agents plan, act, verify, and recover across all repos in this account.

**Signal strength:** agentic density score `164` (references to agent,
tool-call, LLM, RAG and orchestration primitives across the source tree).

### Patterns in play

| Pattern | Role here |
|---|---|
| **Prompt Chaining** | Deterministic multi-step pipelines where subtasks are known upfront |
| **Routing** | Classify input, dispatch to the specialist path (cheap model for easy work) |
| **Parallelization** | Independent subtasks fan out; results aggregated programmatically |
| **Orchestrator–Workers** | Central planner decomposes dynamically when subtasks can't be predicted |
| **Evaluator–Optimizer** | Generator/judge split with explicit rubric; bounded retry |
| **ReAct** | Interleaved reason → act → observe for adaptive tool use |
| **Reflection** | Self-critique before emitting a final answer |

> Escalation rule: start with the simplest pattern that solves the problem. Add
> Reflection only when verification fails, Planning only when dependencies emerge,
> Multi-Agent only when work exceeds a single role or context window.

### Reliability envelope

- **Bounded execution** — every loop has a max-iteration and wall-clock ceiling.
- **Tool sandboxing** — filesystem/network side effects are isolated and reversible.
- **Guardrail layering** — validate at input, mid-loop, and output.
- **Context engineering** — select, compress, isolate; never let raw history grow unbounded.
- **Self-verification** — check intermediate output against constraints before continuing.

## Model Routing

Agent work in this repo routes through Azure AI Foundry. See [`AGENTS.md`](./AGENTS.md)
for the full contract.

| Purpose | Deployment | Endpoint |
|---|---|---|
| Default / general | `gpt-5.6-sol` | `/openai/v1/chat/completions` |
| Deep reasoning | `claude-opus-5` | `/openai/v1/responses` **only** |
| Embeddings | `text-embedding-3-small` | `/openai/v1/embeddings` |

```bash
export AZURE_FOUNDRY_API_KEY=...        # never commit this
export AZURE_FOUNDRY_BASE_URL=https://<resource>.openai.azure.com/openai/v1
```

> **Gotcha:** Claude deployments on Azure return `404 api_not_supported` on
> `/chat/completions`. They answer **only** via the Responses API.

## Project Layout

```
AGENTS.md
CLAUDE.md
Dockerfile
LICENSE
README.md
README_OLD.md
agent-card.json
desktop/
friday/
pyproject.toml
tests/
```

## Development

```bash
# lint / format before committing
ruff check . && ruff format .

# run the CI check locally
gh workflow run hermes-azure-check.yml
```

Secrets live in environment variables and CI secrets — never in tracked files.

## Related Repositories

Part of a 84-repository workspace sharing one agentic contract:

- **[agentic-harness](https://github.com/sahiixx/agentic-harness)** — patterns, contracts, and reference implementations
- `AGENTS.md` in every repo pins identical model routing

---

<sub>README maintained by the agentic harness · last regenerated 2026-08-10</sub>
