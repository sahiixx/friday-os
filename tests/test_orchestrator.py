"""Tests for orchestrator integration."""

from friday.core.orchestrator import Orchestrator, OrchestratorConfig


class TestOrchestratorRun:
    def test_conversational_short_query(self):
        orch = Orchestrator(config=OrchestratorConfig(verbose=False))
        r = orch.run("hello")
        assert r.success is True
        assert r.intent == "CONVERSATIONAL"
        assert r.plan is not None
        assert len(r.plan.steps) >= 1

    def test_agentic_routes_through_tools(self):
        orch = Orchestrator()
        r = orch.run("plan and automate a simple workflow end-to-end")
        assert r.intent in {"AGENTIC", "CREATIVE"}
        assert r.plan is not None

    def test_response_has_elapsed_ms(self):
        orch = Orchestrator()
        r = orch.run("hello")
        assert r.elapsed_ms >= 0.0

    def test_handles_empty_query_gracefully(self):
        orch = Orchestrator()
        r = orch.run("")
        # Heuristic classifier defaults to AGENTIC/CONVERSATIONAL; must not crash.
        assert isinstance(r.output, str)
