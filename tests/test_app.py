"""Tests for the server entry point and packaging metadata."""

import json
import pathlib
import tomllib

import pytest

import rentcast_mcp_server
from rentcast_mcp_server import app as app_module
from rentcast_mcp_server.app import mcp

ROOT = pathlib.Path(__file__).resolve().parent.parent


def test_main_exits_without_api_key(monkeypatch):
    monkeypatch.delenv("RENTCAST_API_KEY", raising=False)
    monkeypatch.setattr(app_module.mcp, "run", lambda *a, **k: pytest.fail("server started"))

    with pytest.raises(SystemExit) as exc:
        app_module.main([])
    assert exc.value.code == 1


def test_main_runs_stdio_by_default(monkeypatch):
    monkeypatch.setenv("RENTCAST_API_KEY", "k")
    calls = []
    monkeypatch.setattr(app_module.mcp, "run", lambda *a, **k: calls.append(k))

    app_module.main([])

    assert calls == [{}]


def test_main_http_transport_keeps_host_validation(monkeypatch):
    monkeypatch.setenv("RENTCAST_API_KEY", "k")
    calls = []
    monkeypatch.setattr(app_module.mcp, "run", lambda *a, **k: calls.append(k))

    app_module.main(
        ["--transport", "http", "--host", "0.0.0.0", "--allowed-host", "mcp.example.com"]
    )

    assert calls == [{"transport": "streamable-http"}]
    security = mcp.settings.transport_security
    assert "mcp.example.com" in security.allowed_hosts
    assert "localhost" in security.allowed_hosts


def test_main_rejects_bad_port():
    with pytest.raises(SystemExit):
        app_module.main(["--port", "70000"])


async def test_manifest_matches_registered_tools_and_prompts():
    manifest = json.loads((ROOT / "manifest.json").read_text())

    tools = {t.name for t in await mcp.list_tools()}
    prompts = {p.name for p in await mcp.list_prompts()}

    assert {t["name"] for t in manifest["tools"]} == tools
    assert {p["name"] for p in manifest["prompts"]} == prompts


def test_versions_agree():
    manifest = json.loads((ROOT / "manifest.json").read_text())
    pyproject = tomllib.loads((ROOT / "pyproject.toml").read_text())

    assert manifest["version"] == pyproject["project"]["version"]
    assert rentcast_mcp_server.__version__ == pyproject["project"]["version"]
