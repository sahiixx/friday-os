import logging
import time
from dataclasses import dataclass, field
from typing import Any

from friday.core.llm import LLMProvider, get_provider
from friday.core.memory import persona
from friday.core.planner import Plan, PlanStep, Planner
from friday.core.router import Router, RouterDecision
from friday.tools import ToolRegistry, default_registry

logger = logging.getLogger(__name__)


@dataclass
class OrchestratorConfig:
    planner_model: str = "claude-opus-4-7"
    executor_model: str = "claude-haiku-4-5-20251001"
    max_plan_steps: int = 8
    max_step_retries: int = 1
    verbose: bool = False


@dataclass
class OrchestratorResponse:
    query: str
    intent: str
    plan: Plan | None
    output: str
    tool_calls: list[dict[str, Any]] = field(default_factory=list)
    elapsed_ms: float = 0.0
    success: bool = True
    error: str | None = None


class Orchestrator:
    """PERCEIVE → ROUTE → PLAN → EXECUTE → SYNTHESIZE loop.

    Ported and slimmed from SUPER AGI. Works without an API key via heuristic
    planner/router + stub tool results. Picks up persona from ~/.openjarvis/.
    """

    def __init__(self, config: OrchestratorConfig | None = None,
                 registry: ToolRegistry | None = None,
                 llm: LLMProvider | None = None) -> None:
        self.config = config or OrchestratorConfig()
        self.persona_prompt = persona.load()
        # LLM is pluggable: pass one in, or let the factory pick by FRIDAY_LLM env.
        self.llm = llm or get_provider()
        self.router = Router(llm=self.llm)
        self.planner = Planner(llm=self.llm)
        self.tools = registry or default_registry()

    def run(self, query: str) -> OrchestratorResponse:
        t0 = time.time()
        try:
            decision = self.router.classify(query)
            self._log("ROUTE", f"{decision.intent_class} conf={decision.confidence}")
            # WHY: chat queries don't need plan→execute→synthesize. One direct
            # LLM call cuts llama3.1:8b latency from ~60s (3-4 calls) to ~15s.
            if not decision.requires_planning:
                return self._fast_chat(query, decision, t0)
            plan = self.planner.create_plan(
                query, suggested_tools=decision.suggested_tools,
                allowed_tools=self.tools.names(),
            )
            self._log("PLAN", plan.summary())
            tool_calls = self._execute_plan(plan, query)
            output = self._synthesize(query, plan)
            self._remember(query, output)
            return OrchestratorResponse(
                query=query, intent=decision.intent_class, plan=plan, output=output,
                tool_calls=tool_calls, elapsed_ms=(time.time() - t0) * 1000,
            )
        except Exception as exc:
            logger.exception("orchestrator fatal")
            return OrchestratorResponse(
                query=query, intent="UNKNOWN", plan=None,
                output=f"Error: {exc}", elapsed_ms=(time.time() - t0) * 1000,
                success=False, error=str(exc),
            )

    def _fast_chat(self, query: str, decision: RouterDecision,
                   t0: float) -> OrchestratorResponse:
        memories = self._recall(query)
        system = self.persona_prompt
        if memories:
            context = "\n\n".join(
                f"[Memory {i+1}] {m.get('mission', '')}: {m.get('reason', '')}"
                for i, m in enumerate(memories)
            )
            system = f"{system}\n\nRelevant past memories:\n{context}"
        if not self.llm.is_available():
            output = f"[conversational fallback] {query}"
        else:
            resp = self.llm.chat([{"role": "user", "content": query}],
                                 system=system, max_tokens=1024)
            output = resp.text
        self._remember(query, output)
        return OrchestratorResponse(
            query=query, intent=decision.intent_class, plan=None, output=output,
            tool_calls=[{"step": 1, "tool": None, "success": True}],
            elapsed_ms=(time.time() - t0) * 1000,
        )

    def _remember(self, query: str, output: str) -> None:
        # WHY: persistent session memory. Both sides of the turn go to the
        # same jsonl so recall can cite who said what. Fails silent — memory
        # loss must never break a response.
        try:
            if self.tools.has("memory_save"):
                self.tools.call("memory_save", f"user: {query[:300]}")
                self.tools.call("memory_save", f"friday: {output[:600]}")
            # Titans surprise-weighted memory
            from friday.core.memory import titans
            titans.remember(
                mission=query[:200],
                verdict="GO" if "error" not in output.lower() else "NO-GO",
                reason=output[:300],
                delta=0.0,
                metadata={"agent": "friday", "query": query[:200]},
            )
        except Exception as exc:
            logger.debug("memory_save skipped: %s", exc)

    def _recall(self, query: str) -> list[dict[str, Any]]:
        """Return surprise-weighted memories for query context."""
        try:
            from friday.core.memory import titans
            return titans.recall(query, top_k=3)
        except Exception as exc:
            logger.debug("titans recall skipped: %s", exc)
            return []

    def _execute_plan(self, plan: Plan, query: str) -> list[dict[str, Any]]:
        calls: list[dict[str, Any]] = []
        limit = self.config.max_plan_steps * 2
        for _ in range(limit):
            step = plan.next_step()
            if step is None or plan.is_complete or plan.has_failed:
                break
            self._execute_one(step, query, calls)
        return calls

    def _execute_one(self, step: PlanStep, query: str, calls: list[dict[str, Any]]) -> None:
        step.start()
        try:
            result = self._dispatch(step, query)
            step.complete(result)
            calls.append({"step": step.id, "tool": step.tool, "success": True})
            self._log("STEP_OK", f"[{step.id}] {str(result)[:160]}")
        except Exception as exc:
            step.fail(str(exc))
            calls.append({"step": step.id, "tool": step.tool, "success": False, "error": str(exc)})
            self._log("STEP_FAIL", f"[{step.id}] {exc}")

    def _dispatch(self, step: PlanStep, query: str) -> str:
        if not step.tool:
            return self._reason(step.action, query)
        # WHY: the planner should have stripped invalid tools already. If one
        # survives to here it's a real bug — fail loudly so audit logs are honest.
        if not self.tools.has(step.tool):
            raise ValueError(f"unknown tool: {step.tool!r}")
        tool_input = step.input_template or query
        return self.tools.call(step.tool, tool_input)

    def _reason(self, action: str, query: str) -> str:
        if not self.llm.is_available():
            return f"[reasoning] {action}"
        prompt = f"Original request: {query}\n\nStep to complete: {action}\n\nBe concise."
        return self.llm.chat([{"role": "user", "content": prompt}], max_tokens=512).text

    def _synthesize(self, query: str, plan: Plan) -> str:
        results = [s.result for s in plan.steps if s.result]
        if not self.llm.is_available():
            return "\n".join(results) if results else f"[no output] {query}"
        gathered = "\n\n".join(f"[Step {s.id}] {s.result[:600]}" for s in plan.steps if s.result)
        prompt = f"User: {query}\n\nWork:\n{gathered}\n\nGive a direct, actionable final answer."
        resp = self.llm.chat([{"role": "user", "content": prompt}],
                             system=self.persona_prompt, max_tokens=2048)
        return resp.text

    def _log(self, tag: str, msg: str) -> None:
        if self.config.verbose:
            print(f"[friday:{tag}] {msg}")
        logger.debug("[%s] %s", tag, msg)
