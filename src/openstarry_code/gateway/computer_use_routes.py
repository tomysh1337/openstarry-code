"""Computer-use session state endpoint for the WebUI preview panel.

Reads the atomically-written snapshot persisted by the computer-use MCP
server (``%USERPROFILE%\\.openstarry\\computer_use\\state.json``, see
:mod:`openstarry_code.computer_use.session`) so the Web UI can poll what the
AI is doing on screen — current theme, cursor position, last action and the
most recent screenshot (base64 PNG).

The file may legitimately not exist yet (no computer-use session ever ran on
this machine); the endpoint answers ``{"active": false}`` in that case, and
also when the file is momentarily unreadable (it is replaced atomically via
``os.replace``, so torn reads should not happen, but a partially-provisioned
home directory should not turn into a 500).

Auth is inherited from :class:`~openstarry_code.gateway.middleware.AuthMiddleware`
(the same token/loopback rules that guard every other ``/api/*`` route).
"""

from __future__ import annotations

import json
from typing import Any

import structlog
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Route

from openstarry_code.computer_use.session import default_state_path

log = structlog.get_logger(__name__)


async def api_computer_use_state(request: Request) -> JSONResponse:
    """Return the last persisted computer-use session state."""
    del request
    path = default_state_path()
    if not path.exists():
        return JSONResponse({"active": False})
    try:
        payload: Any = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        log.warning("gateway.computer_use_state_unreadable", path=str(path))
        return JSONResponse({"active": False})
    if not isinstance(payload, dict):
        return JSONResponse({"active": False})
    return JSONResponse(payload)


def computer_use_routes() -> list[Route]:
    """Build the ``/api/computer-use`` routes.

    The returned routes are spliced into the gateway's declarative route
    table by :mod:`openstarry_code.gateway.app`; auth is inherited from the
    shared ``/api/*`` middleware stack.
    """
    return [
        Route("/api/computer-use/state", api_computer_use_state, methods=["GET"]),
    ]
