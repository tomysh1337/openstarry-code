"""WebUI theme HTTP routes for the gateway config.

The settings/appearance surface writes the operator's chosen UI theme here so
the engine can mirror it into computer-use sessions (``session_start(theme=...)``)
and into MCP server subprocesses (``OSC_THEME``). One scalar on the gateway
config (``ui_theme``), persisted through the shared sparse TOML persister —
the same diff-merge + backup + re-validation contract as the MCP/SSH settings
routes (:mod:`openstarry_code.gateway.mcp_routes`).

Validation contract:
  * ``theme`` — non-empty string after trimming (any theme id; the engine and
    the computer-use server treat unknown values tolerantly, defaulting dark).

Auth is inherited from :class:`~openstarry_code.gateway.middleware.AuthMiddleware`
(the same token/loopback rules that guard every other ``/api/*`` route).
"""

from __future__ import annotations

import structlog
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Route

from openstarry_code.gateway.config import GatewayConfig
from openstarry_code.paths import default_opensquilla_home

log = structlog.get_logger(__name__)

_DEFAULT_THEME = "dark"
_MAX_THEME_LENGTH = 64


# ---------------------------------------------------------------------------
# Persistence
# ---------------------------------------------------------------------------


def _persist_config(config: GatewayConfig) -> None:
    """Persist ``config.ui_theme`` through the shared sparse TOML persister.

    Mirrors :func:`openstarry_code.gateway.mcp_routes._persist_config` so every
    gateway write path keeps one persistence contract: diff-merge onto the
    on-disk TOML, timestamped backup, re-validation, fsync-before-rename.
    """
    if not config.config_path:
        config.config_path = str(default_opensquilla_home() / "config.toml")

    from openstarry_code.onboarding.config_store import persist_config

    path = str(config.config_path)
    try:
        result = persist_config(config, path=path)
    except Exception as exc:
        # Exception type only: a pydantic ValidationError repr can embed
        # rejected field values.
        log.error(
            "gateway.ui_config_persist_failed",
            path=path,
            error=type(exc).__name__,
        )
        raise
    log.info(
        "gateway.ui_config_persisted",
        path=str(result.path),
        backup=str(result.backup_path) if result.backup_path else None,
    )


# ---------------------------------------------------------------------------
# Handlers (closures over the live GatewayConfig instance)
# ---------------------------------------------------------------------------


def ui_theme_routes(config: GatewayConfig) -> list[Route]:
    """Build the ``/api/ui/theme`` route bound to ``config``.

    The returned route is spliced into the gateway's declarative route table
    by :mod:`openstarry_code.gateway.app`; auth is inherited from the shared
    ``/api/*`` middleware stack.
    """

    async def handle_put_theme(request: Request) -> JSONResponse:
        """Record the WebUI theme on the gateway config and persist it."""
        try:
            body = await request.json()
        except Exception:
            return JSONResponse({"error": "Invalid JSON body"}, status_code=400)
        if not isinstance(body, dict):
            return JSONResponse({"error": "Invalid JSON body"}, status_code=400)

        theme = str(body.get("theme") or "").strip()
        if not theme:
            return JSONResponse({"error": "Theme is required"}, status_code=400)
        if len(theme) > _MAX_THEME_LENGTH:
            return JSONResponse({"error": "Theme is too long"}, status_code=400)

        previous = config.ui_theme
        config.ui_theme = theme
        try:
            # Explicit operator write: must land even when it equals the
            # model default (e.g. switching back to "dark").
            if hasattr(config, "mark_force_persist_segments"):
                config.mark_force_persist_segments(("ui_theme",))
            _persist_config(config)
        except Exception:
            config.ui_theme = previous
            return JSONResponse({"error": "Cannot persist configuration"}, status_code=500)

        log.info("gateway.ui_theme_updated", theme=theme, previous=previous)
        return JSONResponse({"theme": config.ui_theme})

    return [
        Route("/api/ui/theme", handle_put_theme, methods=["PUT"]),
    ]


def register_ui_routes(app: Starlette, config: GatewayConfig) -> None:
    """Append the WebUI theme routes to an already-built app."""
    app.router.routes.extend(ui_theme_routes(config))
