from pathlib import Path

from friday.tools.base import Tool, ToolResult

_MAX_BYTES = 32_000


class FileReadTool(Tool):
    name = "file_read"
    description = "Read a UTF-8 text file. Input: absolute or ~-relative path."

    def run(self, input_text: str) -> ToolResult:
        p = Path(input_text.strip()).expanduser()
        if not p.exists():
            return ToolResult(False, f"not found: {p}")
        if not p.is_file():
            return ToolResult(False, f"not a file: {p}")
        try:
            data = p.read_bytes()[:_MAX_BYTES]
            text = data.decode("utf-8", errors="replace")
            truncated = p.stat().st_size > _MAX_BYTES
            suffix = "\n\n[truncated]" if truncated else ""
            return ToolResult(True, text + suffix,
                              meta={"path": str(p), "size": p.stat().st_size})
        except Exception as exc:
            return ToolResult(False, f"read error: {exc}")
