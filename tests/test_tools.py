"""Tests for tool registry and individual tools."""

import os
from unittest.mock import patch

import pytest

from friday.tools import ToolRegistry, default_registry
from friday.tools.base import Tool, ToolResult
from friday.tools.desktop import DesktopControlTool
from friday.tools.shell import ShellExecTool


class _FakeTool(Tool):
    name = "mock_tool"
    description = "fake"

    def run(self, input_text: str) -> ToolResult:
        return ToolResult(ok=True, output="mocked")


class TestToolRegistry:
    def test_registers_and_calls_tool(self):
        reg = ToolRegistry()
        reg.register(_FakeTool())
        assert reg.call("mock_tool", "input") == "mocked"

    def test_unknown_tool_raises(self):
        with pytest.raises(KeyError):
            ToolRegistry().get("nonexistent")

    def test_default_registry_has_all_tools(self):
        expected = {"shell_exec", "search_web", "file_read", "memory_save",
                    "memory_recall", "run_code", "desktop_control"}
        assert expected.issubset(set(default_registry().names()))


class TestShellTool:
    def test_blocked_when_disabled(self):
        with patch.dict(os.environ, {"SHELL_EXEC_ENABLED": "false"}):
            r = ShellExecTool().run("echo hello")
        assert r.ok is False
        assert "disabled" in r.output.lower()

    def test_blocked_command_rejected(self):
        with patch.dict(os.environ, {"SHELL_EXEC_ENABLED": "true"}):
            r = ShellExecTool().run("rm -rf /")
        assert r.ok is False
        assert "blocked" in r.output.lower()


class TestDesktopTool:
    def test_blocked_when_disabled(self):
        with patch.dict(os.environ, {"DESKTOP_CONTROL_ENABLED": ""}):
            r = DesktopControlTool().run("click 100 200")
        assert r.ok is False
        assert "disabled" in r.output.lower()


class TestMemoryRoundtrip:
    def test_save_and_recall(self, tmp_path):
        with patch.dict(os.environ, {"FRIDAY_HOME": str(tmp_path)}):
            reg = default_registry()
            assert reg.call("memory_save", "marker=roundtrip-xyz")
            out = reg.call("memory_recall", "roundtrip-xyz")
            assert "roundtrip-xyz" in out
