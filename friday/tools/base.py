from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class ToolResult:
    ok: bool
    output: str
    meta: dict | None = None


class Tool(ABC):
    name: str = ""
    description: str = ""

    @abstractmethod
    def run(self, input_text: str) -> ToolResult: ...

    def __str__(self) -> str:
        return f"<Tool {self.name}>"
