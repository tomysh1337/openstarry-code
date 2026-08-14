"""MCP client package — connect to external MCP servers and register their tools."""

from __future__ import annotations

from openstarry_code.mcp.client import MCPClient
from openstarry_code.mcp.discovery import (
    ActiveMCPClient,
    active_clients_snapshot,
    close_active_clients,
    discover_and_register,
)
from openstarry_code.mcp.types import MCPServerConfig, MCPToolDef, MCPToolResult

__all__ = [
    "ActiveMCPClient",
    "MCPClient",
    "MCPServerConfig",
    "MCPToolDef",
    "MCPToolResult",
    "active_clients_snapshot",
    "close_active_clients",
    "discover_and_register",
]
