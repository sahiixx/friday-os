"""Tests for plan generation."""

import json
from unittest.mock import MagicMock

from friday.core.llm.base import LLMResponse
from friday.core.planner import Plan, PlanStep, Planner, StepStatus


class TestPlannerLLM:
    def test_parses_valid_json_response(self):
        mock_llm = MagicMock()
        mock_llm.is_available.return_value = True
        mock_llm.chat.return_value = LLMResponse(
            text=json.dumps({
                "intent": "RESEARCH",
                "complexity": "medium",
                "steps": [{"id": 1, "action": "find info",
                           "tool": "search_web", "input_template": "test query",
                           "depends_on": []}],
            }),
            model="m", provider="p",
        )

        plan = Planner(llm=mock_llm).create_plan("research test topic")

        assert plan.intent == "RESEARCH"
        assert len(plan.steps) == 1
        assert plan.steps[0].tool == "search_web"

    def test_falls_back_to_heuristic_on_malformed_json(self):
        mock_llm = MagicMock()
        mock_llm.is_available.return_value = True
        mock_llm.chat.return_value = LLMResponse(
            text="not valid json", model="m", provider="p",
        )

        plan = Planner(llm=mock_llm).create_plan("do something")

        assert isinstance(plan, Plan)
        assert len(plan.steps) == 1  # heuristic fallback


class TestPlanStep:
    def test_lifecycle_transitions(self):
        step = PlanStep(id=1, action="test", tool=None)
        assert step.status == StepStatus.PENDING

        step.start()
        assert step.status == StepStatus.RUNNING
        assert step.attempts == 1

        step.complete("ok")
        assert step.status == StepStatus.COMPLETED
        assert step.result == "ok"


class TestPlanOrdering:
    def test_next_step_respects_depends_on(self):
        s1 = PlanStep(id=1, action="first", tool=None)
        s2 = PlanStep(id=2, action="second", tool=None, depends_on=[1])
        plan = Plan(intent="t", complexity="low", steps=[s1, s2])

        assert plan.next_step().id == 1
        s1.complete("done")
        assert plan.next_step().id == 2
