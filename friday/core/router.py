import re
from dataclasses import dataclass, field

from friday.core.llm.base import LLMProvider

INTENT_CLASSES = frozenset({"CONVERSATIONAL", "RESEARCH", "ANALYTICAL",
                            "CREATIVE", "AGENTIC", "DELEGATION"})


@dataclass
class RouterDecision:
    intent_class: str
    confidence: float
    reasoning: str
    requires_tools: bool
    requires_planning: bool
    suggested_tools: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.intent_class not in INTENT_CLASSES:
            self.intent_class = "AGENTIC"


_RESEARCH = re.compile(r"\b(search|find|look up|latest|news|today|price|weather|what is|who is)\b", re.I)
_CODE = re.compile(r"\b(calculate|compute|run|execute|code|script|sort|parse|benchmark)\b", re.I)
_CREATIVE = re.compile(r"\b(write|draft|compose|generate|design|story|poem|summarize|rewrite)\b", re.I)
_AGENTIC = re.compile(r"\b(plan|build|implement|automate|organize|end-to-end|workflow|pipeline|multi-step)\b", re.I)

_TOOL_MAP = {
    "RESEARCH": ["search_web", "memory_recall"],
    "ANALYTICAL": ["run_code", "memory_recall"],
    "CREATIVE": [],
    "AGENTIC": ["search_web", "run_code", "memory_recall", "memory_save", "shell_exec"],
    "CONVERSATIONAL": [],
    "DELEGATION": [],
}


def heuristic_classify(message: str) -> RouterDecision:
    """Rule-based intent classification. Zero-cost fast path."""
    msg = message.strip()
    scores = {
        "RESEARCH": len(_RESEARCH.findall(msg)),
        "ANALYTICAL": len(_CODE.findall(msg)),
        "CREATIVE": len(_CREATIVE.findall(msg)),
        "AGENTIC": len(_AGENTIC.findall(msg)),
        "CONVERSATIONAL": 0,
    }
    if len(msg) < 60 and max(scores.values()) == 0:
        scores["CONVERSATIONAL"] = 1
    best = max(scores, key=lambda k: scores[k])
    if scores[best] == 0:
        best = "AGENTIC"
    total = sum(scores.values()) or 1
    confidence = round(min(scores[best] / total, 1.0), 2) if scores[best] > 0 else 0.5
    return RouterDecision(
        intent_class=best, confidence=confidence,
        reasoning=f"Heuristic matched {scores[best]} token(s) for {best}.",
        requires_tools=best not in ("CONVERSATIONAL", "CREATIVE"),
        requires_planning=best in ("AGENTIC", "ANALYTICAL", "RESEARCH"),
        suggested_tools=_TOOL_MAP.get(best, []),
    )


class Router:
    def __init__(self, llm: LLMProvider | None = None) -> None:
        self.llm = llm

    def classify(self, message: str) -> RouterDecision:
        decision = heuristic_classify(message)
        if decision.confidence >= 0.6 or not (self.llm and self.llm.is_available()):
            return decision
        try:
            return self._llm_classify(message)
        except Exception:
            return decision

    def _llm_classify(self, message: str) -> RouterDecision:
        prompt = (
            "Classify the message into one of: "
            f"{sorted(INTENT_CLASSES)}. "
            'Return JSON: {"intent_class": "...", "confidence": 0-1, "reasoning": "..."}. '
            f"Message: {message}"
        )
        resp = self.llm.chat([{"role": "user", "content": prompt}], max_tokens=256)
        import json
        match = re.search(r"\{.*?\}", resp.text, re.DOTALL)
        if not match:
            raise ValueError("router: no JSON in LLM response")
        data = json.loads(match.group())
        intent = data.get("intent_class", "AGENTIC").upper()
        return RouterDecision(
            intent_class=intent, confidence=float(data.get("confidence", 0.7)),
            reasoning=data.get("reasoning", "LLM classification"),
            requires_tools=intent not in ("CONVERSATIONAL", "CREATIVE"),
            requires_planning=intent in ("AGENTIC", "ANALYTICAL", "RESEARCH"),
            suggested_tools=_TOOL_MAP.get(intent, []),
        )
