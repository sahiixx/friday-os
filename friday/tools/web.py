import json
import os
import urllib.parse
import urllib.request

from friday.tools.base import Tool, ToolResult

_UA = "Mozilla/5.0 (FRIDAY-OS)"
_TIMEOUT = 8


class WebSearchTool(Tool):
    name = "search_web"
    description = "Search the web via DuckDuckGo Instant Answer API. Input: query string."

    def run(self, input_text: str) -> ToolResult:
        q = input_text.strip()
        if not q:
            return ToolResult(False, "empty query")
        try:
            url = "https://api.duckduckgo.com/?" + urllib.parse.urlencode(
                {"q": q, "format": "json", "no_redirect": "1", "no_html": "1"}
            )
            req = urllib.request.Request(url, headers={"User-Agent": _UA})
            with urllib.request.urlopen(req, timeout=_TIMEOUT) as r:
                data = json.loads(r.read().decode("utf-8", errors="replace"))
            return ToolResult(True, _format_ddg(q, data), meta={"source": "duckduckgo"})
        except Exception as exc:
            return ToolResult(False, f"[search_web stub] {q} (error: {exc})")


def _format_ddg(q: str, data: dict) -> str:
    parts = [f"Query: {q}"]
    if abstract := data.get("AbstractText"):
        parts.append(f"Summary: {abstract}")
    if answer := data.get("Answer"):
        parts.append(f"Answer: {answer}")
    related = data.get("RelatedTopics", [])[:5]
    for topic in related:
        if text := topic.get("Text"):
            parts.append(f"- {text}")
    return "\n".join(parts) if len(parts) > 1 else f"No instant answer for: {q}"
