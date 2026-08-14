"""openstarry_code.tools — Tool Registry + built-in tools."""

from openstarry_code.tools import builtin as _builtin  # noqa: F401 — side-effect: register tools
from openstarry_code.tools.registry import ToolRegistry, get_default_registry, tool
from openstarry_code.tools.types import (
    CallerKind,
    PlanAccess,
    RegisteredTool,
    ToolContext,
    ToolError,
    ToolSpec,
)

__all__ = [
    "ToolRegistry",
    "get_default_registry",
    "tool",
    "CallerKind",
    "PlanAccess",
    "ToolContext",
    "ToolSpec",
    "RegisteredTool",
    "ToolError",
]
