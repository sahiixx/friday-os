from friday.tools.base import Tool, ToolResult
from friday.tools.desktop import CodeRunnerTool, DesktopControlTool
from friday.tools.files import FileReadTool
from friday.tools.memory_tool import MemoryRecallTool, MemorySaveTool
from friday.tools.shell import ShellExecTool
from friday.tools.web import WebSearchTool


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, Tool] = {}

    def register(self, tool: Tool) -> None:
        if not tool.name:
            raise ValueError("tool must have a name")
        self._tools[tool.name] = tool

    def has(self, name: str) -> bool:
        return name in self._tools

    def get(self, name: str) -> Tool:
        if name not in self._tools:
            raise KeyError(f"tool not registered: {name}")
        return self._tools[name]

    def names(self) -> list[str]:
        return sorted(self._tools)

    def call(self, name: str, input_text: str) -> str:
        result = self.get(name).run(input_text)
        if not result.ok:
            raise RuntimeError(result.output)
        return result.output


def default_registry() -> ToolRegistry:
    reg = ToolRegistry()
    for tool in (WebSearchTool(), ShellExecTool(), FileReadTool(),
                 MemorySaveTool(), MemoryRecallTool(),
                 CodeRunnerTool(), DesktopControlTool()):
        reg.register(tool)
    return reg


__all__ = ["Tool", "ToolResult", "ToolRegistry", "default_registry"]
