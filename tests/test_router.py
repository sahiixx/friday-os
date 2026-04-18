"""Tests for intent router."""

from unittest.mock import MagicMock

from friday.core.router import INTENT_CLASSES, Router, heuristic_classify


class TestRouterHeuristics:
    def test_conversational_short_greeting(self):
        d = heuristic_classify("hello there")
        assert d.intent_class == "CONVERSATIONAL"

    def test_research_search_trigger(self):
        d = heuristic_classify("search for python tutorials latest")
        assert d.intent_class == "RESEARCH"

    def test_analytical_calculation_trigger(self):
        d = heuristic_classify("calculate 15% of 230 and compute median")
        assert d.intent_class == "ANALYTICAL"

    def test_agentic_action_trigger(self):
        d = heuristic_classify("plan and implement a pipeline to automate this workflow")
        assert d.intent_class == "AGENTIC"

    def test_long_unknown_defaults_to_agentic(self):
        # Short unknown → CONVERSATIONAL; long unknown with no keyword → AGENTIC.
        long_unknown = "xyz " * 20 + "completely unknown query with no trigger tokens"
        d = heuristic_classify(long_unknown)
        assert d.intent_class == "AGENTIC"


class TestRouterLLMFallback:
    def test_skips_llm_when_heuristic_confident(self):
        mock_llm = MagicMock()
        mock_llm.is_available.return_value = True

        Router(llm=mock_llm).classify("search the latest news today")

        mock_llm.chat.assert_not_called()

    def test_classify_returns_valid_intent_class(self):
        d = Router(llm=None).classify("hello")
        assert d.intent_class in INTENT_CLASSES
