"""FRIDAY-OS Agency Connector — Bridges FRIDAY's A2A server to the SAHIIXX ecosystem.

When FRIDAY receives a request it can't handle locally (unknown skill, complex
task, or domain-specific request), this connector:
1. Checks the A2A router for capable agents
2. Dispatches the request to agency-agents, goose-aios, or Fixfizx
3. Returns the result through FRIDAY's A2A response format

Usage in FRIDAY-OS:
    from connectors.agency_connector import AgencyConnector
    connector = AgencyConnector()
    result = await connector.dispatch("Analyze Dubai real estate trends")
"""
import asyncio
import json
import logging
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

# Add paths
sys.path.insert(0, "/mnt/c/Users/Sahil Khan/Downloads")
sys.path.insert(0, "/home/sahiix/sahiixx-bus")

from sahiixx_bus.a2a_router import A2ARouter
from sahiixx_bus.bridge import AgencyBridge, FridayBridge, GooseBridge, FixfizxBridge, MoltBridge

logger = logging.getLogger("friday.agency_connector")


class AgencyConnector:
    """Connects FRIDAY-OS to the SAHIIXX ecosystem via the A2A router.

    FRIDAY uses this connector when:
    - A request matches a skill not in its 21 MCP connectors
    - A complex mission requires multi-agent orchestration
    - The user explicitly requests agency, goose, or Fixfizx
    - Voice commands map to domain-specific tasks (Dubai, security, etc.)
    """

    def __init__(self):
        self.router = A2ARouter()
        self._setup_bridges()

    def _setup_bridges(self):
        """Register all ecosystem service bridges."""
        self.router.register("agency", AgencyBridge(), priority=10)
        self.router.register("friday", FridayBridge(), priority=5)
        self.router.register("goose", GooseBridge(), priority=3)
        self.router.register("fixfizx", FixfizxBridge(), priority=7)
        self.router.register("molt", MoltBridge(), priority=1)

    async def discover(self) -> List[Dict]:
        """Discover all available agents across the ecosystem."""
        agents = await self.router.discover()
        return [
            {"agent_id": a.agent_id, "service": a.service_name, "skills": a.skills}
            for a in agents
        ]

    async def dispatch(self, task: str, skills: Optional[List[str]] = None,
                       preferred_service: Optional[str] = None) -> Dict:
        """Dispatch a task to the best available agent.

        Args:
            task: The task description (natural language)
            skills: Required capabilities (e.g., ["search", "dubai", "lead"])
            preferred_service: Prefer a specific service ("agency", "goose", etc.)

        Returns:
            Dict with agent_id, service, and result
        """
        results = await self.router.route(task, skills=skills, preferred_service=preferred_service)
        if not results:
            return {"error": "no_agents_available", "task": task}
        return results[0]  # Return best result

    async def dispatch_all(self, task: str, skills: Optional[List[str]] = None) -> List[Dict]:
        """Dispatch to all matching agents and collect results."""
        return await self.router.route(task, skills=skills)

    async def health(self) -> Dict:
        """Check health of all ecosystem services."""
        return await self.router.health_check()

    def match_skill(self, query: str) -> Optional[str]:
        """Map a FRIDAY intent to an ecosystem service.

        Returns the preferred service name, or None for local handling.
        """
        query_lower = query.lower()

        # Dubai / real estate → Fixfizx
        dubai_kw = ["dubai", "property", "real estate", "aed", "villa", "lead qualification"]
        if any(kw in query_lower for kw in dubai_kw):
            return "fixfizx"

        # Security / audit → agency-agents
        security_kw = ["security audit", "vulnerability", "penetration test", "threat model"]
        if any(kw in query_lower for kw in security_kw):
            return "agency"

        # Code / engineering → agency-agents
        code_kw = ["build", "implement", "deploy", "code review", "api"]
        if any(kw in query_lower for kw in code_kw):
            return "agency"

        # Local / private → goose-aios
        local_kw = ["offline", "local", "private", "confidential"]
        if any(kw in query_lower for kw in local_kw):
            return "goose"

        return None  # Handle locally


# Global connector
_connector: Optional[AgencyConnector] = None


def get_connector() -> AgencyConnector:
    """Get the global AgencyConnector singleton."""
    global _connector
    if _connector is None:
        _connector = AgencyConnector()
    return _connector