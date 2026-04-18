import os

from friday.tools.base import Tool, ToolResult


def _is_enabled() -> bool:
    return os.getenv("DESKTOP_CONTROL_ENABLED", "false").lower() in ("1", "true", "yes")


class DesktopControlTool(Tool):
    """Wraps the computer-use MCP. In-process runs return an instruction record
    that the embedding layer (LiveKit/CLI/plugin) routes to the MCP server.
    """

    name = "desktop_control"
    description = "Describe a desktop action for the computer-use MCP. Gated by DESKTOP_CONTROL_ENABLED."

    def run(self, input_text: str) -> ToolResult:
        task = input_text.strip()
        if not task:
            return ToolResult(False, "empty desktop task")
        if not _is_enabled():
            return ToolResult(False, "desktop_control disabled (set DESKTOP_CONTROL_ENABLED=true)")
        envelope = {"tool": "computer-use", "task": task, "requires_mcp": True}
        return ToolResult(True, f"[desktop] queued: {task}", meta=envelope)


class CodeRunnerTool(Tool):
    name = "run_code"
    description = "Evaluate a safe arithmetic or Python literal expression."

    def run(self, input_text: str) -> ToolResult:
        expr = input_text.strip()
        try:
            import ast
            tree = ast.parse(expr, mode="eval")
            value = _safe_eval(tree.body)
            return ToolResult(True, str(value))
        except Exception as exc:
            return ToolResult(False, f"eval error: {exc}")


def _safe_eval(node):
    import ast
    import operator as op
    ops = {ast.Add: op.add, ast.Sub: op.sub, ast.Mult: op.mul,
           ast.Div: op.truediv, ast.Mod: op.mod, ast.Pow: op.pow,
           ast.USub: op.neg, ast.UAdd: op.pos, ast.FloorDiv: op.floordiv}
    if isinstance(node, ast.Constant):
        return node.value
    if isinstance(node, ast.BinOp):
        return ops[type(node.op)](_safe_eval(node.left), _safe_eval(node.right))
    if isinstance(node, ast.UnaryOp):
        return ops[type(node.op)](_safe_eval(node.operand))
    raise ValueError(f"unsupported node: {type(node).__name__}")
