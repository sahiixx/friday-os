import os
import shlex
import subprocess

from friday.tools.base import Tool, ToolResult

_DEFAULT_BLOCKED = ("rm", "mkfs", "dd", "shutdown", "reboot", "format",
                    "del", "rmdir", ":(){:|:&};:", "sudo", "chmod", "chown")
_TIMEOUT = 15


def _is_enabled() -> bool:
    return os.getenv("SHELL_EXEC_ENABLED", "false").lower() in ("1", "true", "yes")


def _blocked_commands() -> tuple[str, ...]:
    raw = os.getenv("SHELL_BLOCKED_COMMANDS", "")
    return tuple(c.strip() for c in raw.split(",") if c.strip()) or _DEFAULT_BLOCKED


class ShellExecTool(Tool):
    name = "shell_exec"
    description = "Execute a safe shell command. Disabled unless SHELL_EXEC_ENABLED=true."

    def run(self, input_text: str) -> ToolResult:
        cmd = input_text.strip()
        if not cmd:
            return ToolResult(False, "empty command")
        if not _is_enabled():
            return ToolResult(False, "shell_exec disabled (set SHELL_EXEC_ENABLED=true)")
        first = shlex.split(cmd)[0] if cmd else ""
        if any(first.startswith(b) or b in cmd for b in _blocked_commands()):
            return ToolResult(False, f"blocked command: {first}")
        try:
            r = subprocess.run(cmd, shell=True, capture_output=True,
                               text=True, timeout=_TIMEOUT)
            out = (r.stdout + r.stderr).strip()[:2000]
            return ToolResult(r.returncode == 0, out or "(no output)",
                              meta={"returncode": r.returncode})
        except subprocess.TimeoutExpired:
            return ToolResult(False, f"timeout after {_TIMEOUT}s")
        except Exception as exc:
            return ToolResult(False, f"shell error: {exc}")
