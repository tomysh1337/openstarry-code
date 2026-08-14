from __future__ import annotations

from typing import Any

import pytest
import pytest_asyncio

from openstarry_code.mcp.client import MCPClient
from openstarry_code.mcp.types import MCPServerConfig, MCPToolDef, MCPToolResult
from openstarry_code.tools.registry import ToolRegistry


class FakeMCPClient(MCPClient):
    def __init__(
        self,
        config: MCPServerConfig,
        tools: list[MCPToolDef] | None = None,
        *,
        fail_list: bool = False,
        call_result: MCPToolResult | None = None,
    ) -> None:
        super().__init__(config)
        self.tools = tools or []
        self.fail_list = fail_list
        self.call_result = call_result
        self.connected = False
        self.closed = False

    async def connect(self) -> None:
        self.connected = True

    async def close(self) -> None:
        self.closed = True

    async def list_tools(self) -> list[MCPToolDef]:
        if self.fail_list:
            raise RuntimeError("list failed")
        return self.tools

    async def call_tool(self, name: str, arguments: dict[str, Any]) -> MCPToolResult:
        if self.call_result is not None:
            return self.call_result
        return MCPToolResult(content=f"{name}:{arguments}")


@pytest_asyncio.fixture(autouse=True)
async def _close_mcp_clients():
    from openstarry_code.mcp.discovery import close_active_clients

    await close_active_clients()
    yield
    await close_active_clients()


@pytest.mark.asyncio
async def test_discovered_mcp_clients_have_owner_and_close_lifecycle(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from openstarry_code.mcp import discovery

    config = MCPServerConfig(name="docs", transport="stdio", command="mock-mcp")
    client = FakeMCPClient(
        config,
        tools=[
            MCPToolDef(
                name="lookup",
                description="Lookup docs",
                input_schema={"properties": {"q": {"type": "string"}}, "required": ["q"]},
            )
        ],
    )
    monkeypatch.setattr(discovery, "create_client", lambda _config: client)

    names = await discovery.discover_and_register(config, ToolRegistry(), owner="gateway")
    snapshot = discovery.active_clients_snapshot()

    assert names == ["mcp_lookup"]
    assert len(snapshot) == 1
    assert snapshot[0].owner == "gateway"
    assert snapshot[0].server_name == "docs"
    assert snapshot[0].transport == "stdio"
    assert snapshot[0].client is client
    assert await discovery.close_active_clients(owner="docs") == 1
    assert client.closed is True
    assert discovery.active_clients_snapshot() == ()


@pytest.mark.asyncio
async def test_failed_mcp_discovery_closes_client_without_leaking(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from openstarry_code.mcp import discovery

    config = MCPServerConfig(name="broken", transport="stdio", command="mock-mcp")
    client = FakeMCPClient(config, fail_list=True)
    monkeypatch.setattr(discovery, "create_client", lambda _config: client)

    with pytest.raises(RuntimeError, match="list failed"):
        await discovery.discover_and_register(config, ToolRegistry())

    assert client.closed is True
    assert discovery.active_clients_snapshot() == ()


@pytest.mark.asyncio
async def test_registered_handler_surfaces_client_error_flag(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from openstarry_code.mcp import discovery
    from openstarry_code.tool_boundary import ToolCall
    from openstarry_code.tools.dispatch import build_tool_handler

    config = MCPServerConfig(name="docs", transport="stdio", command="mock-mcp")
    client = FakeMCPClient(
        config,
        tools=[MCPToolDef(name="lookup", description="Lookup docs", input_schema={})],
        call_result=MCPToolResult(content="invalid params", is_error=True),
    )
    monkeypatch.setattr(discovery, "create_client", lambda _config: client)

    registry = ToolRegistry()
    await discovery.discover_and_register(config, registry)
    handler = build_tool_handler(registry)
    result = await handler(ToolCall(tool_use_id="tu1", tool_name="mcp_lookup", arguments={}))

    assert result.is_error is True
    assert "invalid params" in result.content
