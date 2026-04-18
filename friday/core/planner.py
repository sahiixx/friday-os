import json
import re
import time
from dataclasses import dataclass, field
from enum import Enum, auto

from friday.core.llm.base import LLMProvider

PLANNER_PROMPT = """You are the Planner for FRIDAY OS. Decompose the user's request into 1-6 ordered steps.
Return ONLY JSON with this shape:
{"intent": "<one-line>", "complexity": "low|medium|high",
 "steps": [{"id": 1, "action": "...", "tool": "tool_name_or_null", "input_template": "...", "depends_on": []}],
 "success_criteria": "...", "risks": []}"""


class StepStatus(Enum):
    PENDING = auto()
    RUNNING = auto()
    COMPLETED = auto()
    FAILED = auto()


@dataclass
class PlanStep:
    id: int
    action: str
    tool: str | None
    input_template: str = ""
    depends_on: list[int] = field(default_factory=list)
    status: StepStatus = StepStatus.PENDING
    result: str | None = None
    error: str | None = None
    attempts: int = 0

    def start(self) -> None:
        self.status = StepStatus.RUNNING
        self.attempts += 1

    def complete(self, result: str) -> None:
        self.status = StepStatus.COMPLETED
        self.result = result

    def fail(self, error: str) -> None:
        self.status = StepStatus.FAILED
        self.error = error

    def summary(self) -> str:
        icon = {StepStatus.PENDING: "?", StepStatus.RUNNING: "~",
                StepStatus.COMPLETED: "+", StepStatus.FAILED: "x"}[self.status]
        return f"  [{self.id}] {icon} {self.action} (tool={self.tool})"


@dataclass
class Plan:
    intent: str
    complexity: str
    steps: list[PlanStep]
    success_criteria: str = ""
    risks: list[str] = field(default_factory=list)

    @property
    def is_complete(self) -> bool:
        return all(s.status == StepStatus.COMPLETED for s in self.steps)

    @property
    def has_failed(self) -> bool:
        return any(s.status == StepStatus.FAILED for s in self.steps)

    def next_step(self) -> PlanStep | None:
        done = {s.id for s in self.steps if s.status == StepStatus.COMPLETED}
        pending = (s for s in self.steps if s.status == StepStatus.PENDING)
        return next((s for s in pending if all(d in done for d in s.depends_on)), None)

    def summary(self) -> str:
        header = f"PLAN: {self.intent} (complexity={self.complexity}, steps={len(self.steps)})"
        return "\n".join([header, *[s.summary() for s in self.steps]])


class Planner:
    def __init__(self, llm: LLMProvider | None = None) -> None:
        self.llm = llm

    def create_plan(self, request: str, suggested_tools: list[str] | None = None) -> Plan:
        if self.llm and self.llm.is_available():
            try:
                return self._llm_plan(request, suggested_tools or [])
            except Exception:
                pass
        return self._heuristic_plan(request, suggested_tools)

    def _llm_plan(self, request: str, suggested_tools: list[str]) -> Plan:
        hint = f"\nAvailable tools: {', '.join(suggested_tools)}" if suggested_tools else ""
        prompt = f"{PLANNER_PROMPT}{hint}\n\nUser request:\n{request}"
        resp = self.llm.chat([{"role": "user", "content": prompt}], max_tokens=1024)
        match = re.search(r"\{.*\}", resp.text, re.DOTALL)
        if not match:
            raise ValueError(f"planner: no JSON in {resp.text[:120]!r}")
        data = json.loads(match.group())
        steps = [PlanStep(id=s["id"], action=s.get("action", ""), tool=s.get("tool"),
                          input_template=s.get("input_template", ""),
                          depends_on=s.get("depends_on", [])) for s in data.get("steps", [])]
        return Plan(intent=data.get("intent", request), complexity=data.get("complexity", "medium"),
                    steps=steps, success_criteria=data.get("success_criteria", ""),
                    risks=data.get("risks", []))

    def _heuristic_plan(self, request: str, suggested_tools: list[str] | None) -> Plan:
        tool = suggested_tools[0] if suggested_tools else None
        return Plan(intent=request, complexity="low",
                    steps=[PlanStep(id=1, action=f"Respond to: {request}", tool=tool,
                                    input_template=request)],
                    success_criteria="Return a direct answer.",
                    risks=["No LLM planner; single-step fallback."])
