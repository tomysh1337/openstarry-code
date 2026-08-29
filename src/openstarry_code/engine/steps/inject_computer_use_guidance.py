"""Inject computer-use workflow guidance when MCP exposes those tools.

When a computer-use MCP server (e.g. the bundled ``openstarry-computer-use``)
has its tools registered into the model tool table, the model needs a short
protocol reminder: start a session first, look before it clicks, and prefer
the virtual cursor so the operator can follow along. Mirrors the
``inject_platform_hint`` step shape: append one block to the uncached suffix
slot of ``ctx.system_prompt`` so the cached base stays stable.
"""

from __future__ import annotations

import re

from openstarry_code.engine.pipeline import TurnContext

# Leaf tool names (after the mcp__<server>__ / legacy mcp_ prefix) that mark a
# computer-use server. session_start/session_end are the session-lifecycle
# pair; the rest are the action surface.
_COMPUTER_USE_TOOL_LEAVES = frozenset(
    {
        "session_start",
        "session_end",
        "screenshot",
        "move",
        "left_click",
        "right_click",
        "double_click",
        "drag",
        "type_text",
        "press_key",
        "scroll",
        "abort",
    }
)

_MCP_LEGACY_PREFIX = re.compile(r"^mcp_")


def _tool_leaf(name: str) -> str:
    """Return the bare tool name behind an MCP-prefixed registry name.

    Server names may contain underscores, so ``mcp__my_pc__screenshot`` is
    resolved from the trailing ``__`` segment rather than a leading regex.
    Legacy flat registrations (``mcp_screenshot``) just drop the prefix.
    """
    if "__" in name:
        return name.rsplit("__", 1)[-1]
    return _MCP_LEGACY_PREFIX.sub("", name)


def _computer_use_tools(tool_defs: list) -> list[str]:
    """Return registered computer-use tool names, preserving model order."""
    return [
        td.name
        for td in tool_defs
        if _tool_leaf(getattr(td, "name", "")) in _COMPUTER_USE_TOOL_LEAVES
    ]


def _build_block(session_start_name: str, theme: str) -> str:
    return (
        "## Computer Use\n\n"
        "Computer-use tools are available for driving the local screen.\n"
        f"1. Before the first pointer/keyboard action of a task, call "
        f"`{session_start_name}` with theme=\"{theme}\" to arm the on-screen "
        "cursor; call the matching session_end tool when the task finishes.\n"
        "2. Always take a screenshot first and read it before acting: choose "
        "coordinates from what you can see, never guess.\n"
        "3. Re-screenshot after each action to verify the effect before the "
        "next step.\n"
        "4. Prefer virtual=true on pointer actions so every move is rendered "
        "on-screen."
    )


async def inject_computer_use_guidance(ctx: TurnContext) -> TurnContext:
    """Append computer-use guidance when its MCP tools are registered."""
    try:
        computer_tools = _computer_use_tools(list(ctx.tool_defs or []))
    except Exception:  # noqa: BLE001 - guidance must never break a turn
        computer_tools = []
    if not computer_tools:
        ctx.metadata["inject_computer_use_guidance__applied"] = False
        return ctx

    session_start_name = next(
        (name for name in computer_tools if _tool_leaf(name) == "session_start"),
        "",
    )
    if not session_start_name:
        # Without the session lifecycle pair there is no protocol to teach.
        ctx.metadata["inject_computer_use_guidance__applied"] = False
        return ctx

    theme = str(getattr(ctx.config, "ui_theme", "") or "dark")

    if isinstance(ctx.system_prompt, str):
        base, suffix = ctx.system_prompt, ""
    else:
        base, suffix = ctx.system_prompt

    block = _build_block(session_start_name, theme)
    ctx.system_prompt = (base, f"{suffix}\n\n{block}" if suffix else block)
    ctx.metadata["computer_use_guidance_theme"] = theme
    return ctx
