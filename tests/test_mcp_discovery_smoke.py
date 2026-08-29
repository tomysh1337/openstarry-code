"""Smoke test: engine-side MCP tool discovery with a mocked server client.

Verifies that ``discover_and_register`` connects (mocked), lists the enabled
MCP server's tools, and registers them into the ToolRegistry under the
``mcp__<server>__<tool>`` names — including handler execution routing back to
``client.call_tool``.
"""

from __future__ import annotations

import asyncio
from typing import Any

import pytest

from openstarry_code.mcp import discovery
from openstarry_code.mcp.types import MCPToolDef, MCPToolResult
from openstarry_code.tools.registry import ToolRegistry


class _FakeClient:
    """Stands in for MCPStdioClient — no subprocess, canned tools/results."""

    def __init__(self, config: Any) -> None:
        self.config = config
        self.connected = False
        self.calls: list[tuple[str, dict[str, Any]]] = []

    async def connect(self) -> None:
        self.connected = True

    async def close(self) -> None:
        self.connected = False

    async def list_tools(self) -> list[MCPToolDef]:
        return [
            MCPToolDef(
                name="screenshot",
                description="Take a screenshot",
                input_schema={"type": "object", "properties": {}},
            ),
            MCPToolDef(
                name="click",
                description="Click at coordinates",
                input_schema={
                    "type": "object",
                    "properties": {"x": {"type": "number"}, "y": {"type": "number"}},
                    "required": ["x", "y"],
                },
            ),
        ]

    async def call_tool(self, name: str, arguments: dict[str, Any]) -> MCPToolResult:
        self.calls.append((name, arguments))
        return MCPToolResult(content=f"ok:{name}", is_error=False)


def test_mcp_tool_name_sanitizes_server_and_tool() -> None:
    assert (
        discovery.mcp_tool_name("openstarry-computer-use", "screenshot")
        == "mcp__openstarry-computer-use__screenshot"
    )
    # Unsafe characters (spaces, dots, slashes) fold to underscores.
    assert discovery.mcp_tool_name("My Server/1.0", "do thing") == "mcp__My_Server_1_0__do_thing"
    # Empty names fall back to placeholders.
    assert discovery.mcp_tool_name("", "") == "mcp__server__tool"


def test_discover_and_register_lists_and_routes_mocked_tools() -> None:
    async def scenario() -> None:
        config = discovery.MCPServerConfig(
            name="openstarry-computer-use",
            transport="stdio",
            command="python",
            args=["-m", "fake"],
        )
        fake = _FakeClient(config)

        original_create_client = discovery.create_client
        discovery.create_client = lambda cfg: fake  # type: ignore[assignment]
        try:
            registry = ToolRegistry()
            registered = await discovery.discover_and_register(config, registry)
        finally:
            discovery.create_client = original_create_client  # type: ignore[assignment]
            await discovery.close_active_clients()

        assert fake.connected is False  # closed by close_active_clients
        assert registered == [
            "mcp__openstarry-computer-use__screenshot",
            "mcp__openstarry-computer-use__click",
        ]
        assert set(registry.list_names()) == set(registered)

        click = registry.get("mcp__openstarry-computer-use__click")
        assert click is not None
        result = await click.handler(x=10, y=20)
        assert result == "ok:click"
        assert fake.calls == [("click", {"x": 10, "y": 20})]

    asyncio.run(scenario())


def test_discover_and_register_failure_does_not_poison_registry() -> None:
    async def scenario() -> None:
        class _BoomClient(_FakeClient):
            async def connect(self) -> None:
                raise RuntimeError("connection refused")

        config = discovery.MCPServerConfig(
            name="broken", transport="stdio", command="missing", args=[]
        )
        registry = ToolRegistry()

        original_create_client = discovery.create_client
        discovery.create_client = lambda cfg: _BoomClient(cfg)  # type: ignore[assignment]
        try:
            with pytest.raises(RuntimeError):
                await discovery.discover_and_register(config, registry)
        finally:
            discovery.create_client = original_create_client  # type: ignore[assignment]

        # Failed connections register nothing and leave no lingering clients.
        assert registry.list_names() == []
        assert discovery.active_clients_snapshot() == ()

    asyncio.run(scenario())
