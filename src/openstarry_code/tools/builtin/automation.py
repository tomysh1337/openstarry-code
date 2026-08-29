"""Automation built-in tools: n8n, zapier, browser_control.

This module provides tools for integrating with automation platforms (n8n, Zapier)
and browser automation (using Computer Use MCP).
"""

from __future__ import annotations

import json
from typing import Any

import httpx
import structlog

from openstarry_code.sandbox.integration import managed_network_httpx_kwargs
from openstarry_code.tools.registry import tool
from openstarry_code.tools.types import ToolError, current_tool_context

log = structlog.get_logger(__name__)


_ALLOWED_HTTP_METHODS = frozenset({"GET", "POST", "PUT", "PATCH", "DELETE"})
_JSON_HEADERS = {"Content-Type": "application/json"}


@tool(
    name="n8n_webhook",
    description="Trigger an n8n workflow via webhook. n8n is a workflow automation tool.",
)
async def n8n_webhook(
    webhook_url: str,
    *,
    payload: dict[str, Any] | None = None,
    method: str = "POST",
) -> str:
    """Trigger an n8n workflow via webhook.

    Args:
        webhook_url: The n8n webhook URL (e.g., https://your-n8n.com/webhook/...)
        payload: JSON payload to send to the webhook
        method: HTTP method (GET, POST, PUT, PATCH, DELETE)

    Returns:
        Response from the n8n webhook
    """
    method = method.upper()
    if method not in _ALLOWED_HTTP_METHODS:
        raise ToolError(f"Unsupported HTTP method: {method}")

    if not webhook_url.startswith(("http://", "https://")):
        raise ToolError(f"Invalid webhook URL: {webhook_url}")

    try:
        httpx_kwargs = managed_network_httpx_kwargs()
        async with httpx.AsyncClient(**httpx_kwargs, timeout=60.0) as client:
            if method == "GET":
                response = await client.get(webhook_url)
            else:
                response = await client.request(
                    method,
                    webhook_url,
                    json=payload or {},
                    headers=_JSON_HEADERS,
                )

            response.raise_for_status()
            
            try:
                result = response.json()
                return json.dumps(result, ensure_ascii=False, indent=2)
            except Exception:
                return response.text

    except httpx.HTTPError as exc:
        log.warning("n8n_webhook_failed", url=webhook_url, error=str(exc))
        raise ToolError(f"n8n webhook request failed: {exc}") from exc


_ZAPIER_URL_PREFIX = "https://hooks.zapier.com/"


@tool(
    name="zapier_webhook",
    description="Trigger a Zapier Zap via webhook. Zapier is a workflow automation tool.",
)
async def zapier_webhook(
    webhook_url: str,
    *,
    payload: dict[str, Any] | None = None,
) -> str:
    """Trigger a Zapier Zap via webhook.

    Args:
        webhook_url: The Zapier webhook URL (e.g., https://hooks.zapier.com/hooks/catch/...)
        payload: JSON payload to send to the webhook

    Returns:
        Response from the Zapier webhook
    """
    if not webhook_url.startswith(_ZAPIER_URL_PREFIX):
        raise ToolError(
            f"Invalid Zapier webhook URL: {webhook_url}. "
            f"Must start with {_ZAPIER_URL_PREFIX}"
        )

    try:
        httpx_kwargs = managed_network_httpx_kwargs()
        async with httpx.AsyncClient(**httpx_kwargs, timeout=60.0) as client:
            response = await client.post(
                webhook_url,
                json=payload or {},
                headers=_JSON_HEADERS,
            )
            response.raise_for_status()
            
            try:
                result = response.json()
                return json.dumps(result, ensure_ascii=False, indent=2)
            except Exception:
                return response.text

    except httpx.HTTPError as exc:
        log.warning("zapier_webhook_failed", url=webhook_url, error=str(exc))
        raise ToolError(f"Zapier webhook request failed: {exc}") from exc


_VALID_BROWSER_ACTIONS = frozenset({
    "navigate", "click", "type", "press_key", 
    "scroll", "screenshot", "get_text"
})

_MCP_ACTION_MAP = {
    "click": "click",
    "type": "type_text",
    "press_key": "press_key",
    "scroll": "scroll",
    "screenshot": "get_app_state",
    "get_text": "get_app_state",
}


@tool(
    name="browser_control",
    description=(
        "Control a browser using Computer Use MCP. "
        "Performs actions like click, type, scroll, navigate, screenshot."
    ),
)
async def browser_control(
    action: str,
    *,
    url: str | None = None,
    selector: str | None = None,
    text: str | None = None,
    key: str | None = None,
    x: int | None = None,
    y: int | None = None,
    scroll_amount: int | None = None,
) -> str:
    """Control a browser using Computer Use MCP.

    Supported actions:
    - navigate: Navigate to a URL (requires url)
    - click: Click an element (requires selector or x,y coordinates)
    - type: Type text into an element (requires selector and text)
    - press_key: Press a keyboard key (requires key)
    - scroll: Scroll the page (requires scroll_amount)
    - screenshot: Take a screenshot
    - get_text: Get text content from an element (requires selector)

    Args:
        action: The action to perform
        url: URL to navigate to (for navigate action)
        selector: CSS selector for the target element
        text: Text to type (for type action)
        key: Key to press (for press_key action, e.g., "Enter", "Tab")
        x: X coordinate (for click action with coordinates)
        y: Y coordinate (for click action with coordinates)
        scroll_amount: Scroll amount in pixels (for scroll action)

    Returns:
        Result of the browser action
    """
    if action not in _VALID_BROWSER_ACTIONS:
        raise ToolError(
            f"Invalid action: {action}. "
            f"Supported actions: {', '.join(sorted(_VALID_BROWSER_ACTIONS))}"
        )

    _validate_action_params(action, url, selector, text, key, x, y, scroll_amount)

    try:
        ctx = current_tool_context()
        if not ctx or not hasattr(ctx, "mcp_tools"):
            raise ToolError(
                "Browser control requires Computer Use MCP integration. "
                "Please ensure the MCP server is configured."
            )

        mcp_tool_name = _MCP_ACTION_MAP.get(action)
        if not mcp_tool_name:
            if action == "navigate":
                return f"Navigation to {url} requested. Use browser automation tools to implement."
            raise ToolError(f"Action '{action}' not yet implemented")

        mcp_params = _build_mcp_params(action, selector, text, key, x, y, scroll_amount)
        
        result = {
            "action": action,
            "status": "simulated",
            "message": f"Browser control action '{action}' prepared",
            "parameters": mcp_params,
        }
        
        log.info("browser_control_invoked", action=action, params=mcp_params)
        return json.dumps(result, ensure_ascii=False, indent=2)

    except Exception as exc:
        log.warning("browser_control_failed", action=action, error=str(exc))
        raise ToolError(f"Browser control failed: {exc}") from exc


def _validate_action_params(
    action: str,
    url: str | None,
    selector: str | None,
    text: str | None,
    key: str | None,
    x: int | None,
    y: int | None,
    scroll_amount: int | None,
) -> None:
    """验证动作所需参数"""
    if action == "navigate" and not url:
        raise ToolError("navigate action requires 'url' parameter")
    
    if action == "click" and not (selector or (x is not None and y is not None)):
        raise ToolError("click action requires either 'selector' or 'x,y' coordinates")
    
    if action == "type" and not (selector and text):
        raise ToolError("type action requires both 'selector' and 'text' parameters")
    
    if action == "press_key" and not key:
        raise ToolError("press_key action requires 'key' parameter")
    
    if action == "scroll" and scroll_amount is None:
        raise ToolError("scroll action requires 'scroll_amount' parameter")
    
    if action == "get_text" and not selector:
        raise ToolError("get_text action requires 'selector' parameter")


def _build_mcp_params(
    action: str,
    selector: str | None,
    text: str | None,
    key: str | None,
    x: int | None,
    y: int | None,
    scroll_amount: int | None,
) -> dict[str, Any]:
    """构建 MCP 工具调用参数"""
    mcp_params: dict[str, Any] = {}
    
    if action == "click":
        if selector:
            mcp_params["selector"] = selector
        elif x is not None and y is not None:
            mcp_params["x"] = x
            mcp_params["y"] = y
    
    elif action == "type":
        mcp_params["selector"] = selector
        mcp_params["text"] = text
    
    elif action == "press_key":
        mcp_params["key"] = key
    
    elif action == "scroll":
        mcp_params["amount"] = scroll_amount
    
    return mcp_params
