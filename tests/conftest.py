"""Shared test fixtures for RentCast MCP Server tests."""

import json
from typing import Any, Callable, Dict, List, Union
from urllib.parse import parse_qsl

import httpx
import pytest

from rentcast_mcp_server import client as client_module

Handler = Union[httpx.Response, Callable[[httpx.Request], httpx.Response]]


class FakeRentCast:
    """Stands in for api.rentcast.io and records every request made to it."""

    def __init__(self) -> None:
        self.routes: Dict[str, List[Handler]] = {}
        self.requests: List[httpx.Request] = []

    def add(self, path: str, *responses: Handler) -> None:
        """Queue responses for a path. The last one repeats once the queue runs out."""
        self.routes[f"/v1{path}"] = list(responses)

    def json(self, path: str, body: Any, status: int = 200, **headers: str) -> None:
        self.add(path, httpx.Response(status, json=body, headers=headers))

    def error(self, path: str, status: int, message: str) -> None:
        self.json(path, {"status": status, "error": "test/error", "message": message}, status)

    def handle(self, request: httpx.Request) -> httpx.Response:
        self.requests.append(request)
        queue = self.routes.get(request.url.path)
        if not queue:
            return httpx.Response(404, json={"message": f"no fake route for {request.url.path}"})
        handler = queue.pop(0) if len(queue) > 1 else queue[0]
        return handler(request) if callable(handler) else handler

    @property
    def last(self) -> httpx.Request:
        return self.requests[-1]

    @property
    def last_params(self) -> Dict[str, str]:
        return dict(parse_qsl(self.last.url.query.decode()))


@pytest.fixture
def rentcast(monkeypatch) -> FakeRentCast:
    """Route the shared HTTP client to a fake RentCast API."""
    fake = FakeRentCast()
    monkeypatch.setenv("RENTCAST_API_KEY", "test-key")
    monkeypatch.delenv("RENTCAST_SURROGATE_KEY", raising=False)
    monkeypatch.delenv("RENTCAST_SUPPRESS_LOGGING", raising=False)

    async def no_sleep(_: float) -> None:
        return None

    monkeypatch.setattr(client_module.asyncio, "sleep", no_sleep)
    monkeypatch.setattr(
        client_module,
        "_client",
        httpx.AsyncClient(
            base_url=client_module.BASE_URL,
            headers={"X-Api-Key": "test-key"},
            transport=httpx.MockTransport(fake.handle),
        ),
    )
    return fake


async def call_tool(name: str, arguments: Dict[str, Any]) -> Any:
    """Call a tool through the MCP server and return its decoded JSON result."""
    from rentcast_mcp_server.app import mcp

    result = await mcp.call_tool(name, arguments)
    content = result[0] if isinstance(result, tuple) else result
    return json.loads(content[0].text)
