import json
import os
import time
from pathlib import Path

from friday.tools.base import Tool, ToolResult


def _store_path() -> Path:
    root = Path(os.getenv("FRIDAY_HOME", Path.home() / ".openjarvis")).expanduser()
    root.mkdir(parents=True, exist_ok=True)
    return root / "friday_memory.jsonl"


def _load() -> list[dict]:
    p = _store_path()
    if not p.exists():
        return []
    out: list[dict] = []
    for line in p.read_text("utf-8").splitlines():
        line = line.strip()
        if line:
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return out


class MemorySaveTool(Tool):
    name = "memory_save"
    description = "Append a fact to long-term memory. Input: free text."

    def run(self, input_text: str) -> ToolResult:
        text = input_text.strip()
        if not text:
            return ToolResult(False, "empty memory")
        record = {"ts": int(time.time()), "text": text}
        with _store_path().open("a", encoding="utf-8") as f:
            f.write(json.dumps(record) + "\n")
        return ToolResult(True, f"saved ({len(text)} chars)")


class MemoryRecallTool(Tool):
    name = "memory_recall"
    description = "Recall memories matching a keyword. Input: query string."

    def run(self, input_text: str) -> ToolResult:
        q = input_text.strip().lower()
        records = _load()
        hits = [r for r in records if q in r.get("text", "").lower()] if q else records[-5:]
        if not hits:
            return ToolResult(True, f"no memories match: {q}")
        lines = [f"[{r['ts']}] {r['text']}" for r in hits[-10:]]
        return ToolResult(True, "\n".join(lines), meta={"count": len(hits)})
