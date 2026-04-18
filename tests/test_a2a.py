"""Tests for Agent-to-Agent protocol."""

import pytest

from friday.core.a2a.schema import A2ARequest, A2AResponse, descriptor


class TestA2ASchema:
    def test_request_from_dict(self):
        req = A2ARequest.from_dict({
            "skill": "chat", "input": "hello",
            "session_id": "s-1", "from_agent": "agent-a",
        })
        assert req.skill == "chat"
        assert req.input == "hello"
        assert req.from_agent == "agent-a"

    def test_response_to_dict(self):
        resp = A2AResponse(ok=True, output="result", intent="RESEARCH")
        d = resp.to_dict()
        assert d["ok"] is True
        assert d["output"] == "result"
        assert d["intent"] == "RESEARCH"

    def test_descriptor_shape(self):
        d = descriptor()
        assert d["name"] == "FRIDAY OS"
        assert d["protocol"].startswith("a2a/")
        assert "/a2a/invoke" in d["endpoints"]["invoke"]
        assert "chat" in d["capabilities"]["skills"]


class TestA2AServer:
    def test_routes_registered(self):
        fastapi = pytest.importorskip("fastapi")
        from fastapi.testclient import TestClient

        from friday.core.a2a.server import build_app

        client = TestClient(build_app())
        assert client.get("/.well-known/agent.json").status_code == 200
        assert client.get("/health").status_code == 200

    def test_invoke_requires_input(self):
        pytest.importorskip("fastapi")
        from fastapi.testclient import TestClient

        from friday.core.a2a.server import build_app

        client = TestClient(build_app())
        r = client.post("/a2a/invoke", json={"skill": "chat", "input": ""})
        assert r.status_code == 200
        assert r.json()["ok"] is False
        assert "input required" in r.json()["error"]
