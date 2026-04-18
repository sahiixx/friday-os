# SKILL — friday-tool-author

Add a new MCP tool to FRIDAY OS in 3 steps.

## Steps

1. **Choose domain**: `friday/tools/{web,shell,files,memory,desktop,NEW}.py`
2. **Implement**: Subclass `Tool`, define `name`, `description`, `run(input) -> ToolResult`
3. **Register**: Add to `default_registry()` in `friday/tools/__init__.py`

## Template

```python
from friday.tools.base import Tool, ToolResult

class MyTool(Tool):
    name = "my_tool"
    description = "One-line LLM-visible description."
    def run(self, input_text: str) -> ToolResult:
        return ToolResult(ok=True, output=f"got: {input_text}")
```

## Rules

- Return `ToolResult(ok=False, output="...")` on any failure; never raise
- Gate dangerous ops behind env flags (e.g., `SHELL_EXEC_ENABLED`)
- Keep run() ≤30 lines
- Test with: `python -c "from friday.tools import default_registry; r=default_registry(); print(r.call('my_tool', 'test'))"`
