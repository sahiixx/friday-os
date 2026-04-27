"""Titans-memory integration for FRIDAY OS.

Wraps the standalone titans-memory package so the orchestrator can do
surprise-weighted recall without knowing the internal ledger format.
"""

from __future__ import annotations

import os
from typing import Any


def _load_memory() -> Any:
    from titans_memory import TitansMemory

    ledger_path = os.getenv("FRIDAY_TITANS_LEDGER", "memory/titans_ledger.json")
    return TitansMemory.load(ledger_path)


def recall(query: str, top_k: int = 5) -> list[dict[str, Any]]:
    """Return ranked memory entries relevant to *query*."""
    memory = _load_memory()
    return memory.recall(query, top_k=top_k)


def remember(
    mission: str,
    verdict: str = "GO",
    reason: str = "",
    delta: float = 0.0,
    metadata: dict[str, Any] | None = None,
) -> None:
    """Store a mission outcome in the Titans ledger."""
    memory = _load_memory()
    memory.remember(
        mission=mission,
        verdict=verdict,
        reason=reason,
        delta=delta,
        metadata=metadata or {},
    )
