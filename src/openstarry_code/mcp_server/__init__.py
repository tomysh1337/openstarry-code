"""Inbound MCP server bridge for OpenStarry Code.

This package exposes OpenStarry Code sessions to external MCP clients. It is
intentionally separate from :mod:`openstarry_code.mcp`, which is the outbound MCP
client integration used to import tools from external MCP servers.
"""

from openstarry_code.mcp_server.bridge import OpenSquillaMCPBridge
from openstarry_code.mcp_server.server import create_mcp_server

__all__ = ["OpenSquillaMCPBridge", "create_mcp_server"]
