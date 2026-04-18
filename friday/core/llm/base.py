from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class LLMResponse:
    text: str
    model: str
    provider: str
    elapsed_ms: float = 0.0


class LLMProvider(ABC):
    @abstractmethod
    def chat(self, messages: list[dict], system: str = "", max_tokens: int = 2048) -> LLMResponse: ...

    @property
    @abstractmethod
    def name(self) -> str: ...

    @abstractmethod
    def is_available(self) -> bool: ...
