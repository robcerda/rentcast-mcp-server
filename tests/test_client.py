"""Tests for the shared RentCast HTTP client."""

import httpx
import pytest
from conftest import call_tool
from mcp.server.fastmcp.exceptions import ToolError

from rentcast_mcp_server import client as client_module


async def test_rate_limit_is_retried(rentcast):
    rentcast.add(
        "/markets",
        httpx.Response(429, json={"message": "slow down"}),
        httpx.Response(200, json={"zipCode": "78704"}),
    )

    result = await call_tool("get_market_statistics", {"zip_code": "78704"})

    assert result == {"zipCode": "78704"}
    assert len(rentcast.requests) == 2


async def test_rate_limit_gives_up_after_retries(rentcast):
    rentcast.error("/markets", 429, "slow down")

    with pytest.raises(ToolError, match="429: slow down .*20 requests per second"):
        await call_tool("get_market_statistics", {"zip_code": "78704"})
    assert len(rentcast.requests) == client_module.MAX_RETRIES + 1


@pytest.mark.parametrize(
    "status, hint",
    [(401, "RENTCAST_API_KEY is valid"), (403, "subscription or billing")],
)
async def test_auth_errors_include_a_hint(rentcast, status, hint):
    rentcast.error("/markets", status, "denied")

    with pytest.raises(ToolError, match=hint):
        await call_tool("get_market_statistics", {"zip_code": "78704"})
    assert len(rentcast.requests) == 1


async def test_non_json_error_body(rentcast):
    rentcast.add("/markets", httpx.Response(502, text="Bad Gateway"))

    with pytest.raises(ToolError, match="502: Bad Gateway"):
        await call_tool("get_market_statistics", {"zip_code": "78704"})


async def test_network_error_is_reported(rentcast):
    def fail(request):
        raise httpx.ConnectError("connection refused", request=request)

    rentcast.add("/markets", fail)

    with pytest.raises(ToolError, match="Could not reach RentCast"):
        await call_tool("get_market_statistics", {"zip_code": "78704"})


async def test_suppress_logging_is_sent_on_every_request(rentcast, monkeypatch):
    monkeypatch.setenv("RENTCAST_SUPPRESS_LOGGING", "true")
    rentcast.json("/markets", {})

    await call_tool("get_market_statistics", {"zip_code": "78704"})

    assert rentcast.last_params["suppressLogging"] == "true"


@pytest.mark.parametrize("value", ["", "false", "0", "no"])
async def test_suppress_logging_off(rentcast, monkeypatch, value):
    monkeypatch.setenv("RENTCAST_SUPPRESS_LOGGING", value)
    rentcast.json("/markets", {})

    await call_tool("get_market_statistics", {"zip_code": "78704"})

    assert "suppressLogging" not in rentcast.last_params


async def test_missing_api_key_is_reported(monkeypatch):
    monkeypatch.delenv("RENTCAST_API_KEY", raising=False)
    monkeypatch.setattr(client_module, "_client", None)

    with pytest.raises(ToolError, match="RENTCAST_API_KEY environment variable is not set"):
        await call_tool("get_market_statistics", {"zip_code": "78704"})


def test_client_sends_api_key_header(monkeypatch):
    monkeypatch.setenv("RENTCAST_API_KEY", "abc123")
    monkeypatch.setattr(client_module, "_client", None)

    client = client_module.get_http_client()

    assert client.headers["X-Api-Key"] == "abc123"
    assert str(client.base_url) == "https://api.rentcast.io/v1/"
    assert client_module.get_http_client() is client
