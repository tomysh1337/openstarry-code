"""Tool boundary re-export for callers that import through openstarry_code.tools."""

from __future__ import annotations

from openstarry_code.tool_boundary import AgentToolHandler, ToolCall, ToolResult

__all__ = ["AgentToolHandler", "ToolCall", "ToolResult"]
