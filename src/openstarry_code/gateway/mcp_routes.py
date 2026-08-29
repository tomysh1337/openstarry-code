"""MCP server configuration HTTP routes for the Web UI settings panel.

These endpoints manage the *configuration* of MCP servers persisted in the
gateway config TOML (``[[mcp.servers]]`` entries). This phase deliberately
stops at configuration management — create / update / delete / enable — and
does NOT open MCP protocol connections: no handshake, tool listing, or
connectivity probe happens here. Runtime discovery
(:mod:`openstarry_code.mcp.discovery`) reads the same config entries at boot
and honors the ``enabled`` flag.

Validation contract (mirrored by the settings panel):
  * ``name`` — non-empty after trimming.
  * ``transport`` — ``"stdio"`` or ``"http"``.
  * ``stdio`` servers must carry a non-empty ``command`` (``args`` optional).
  * ``http`` servers must carry a URL with an ``http``/``https`` scheme and a
    host.
  * ``id`` — uuid4 hex, assigned server-side on create.
  * ``env`` — a flat string→string mapping (one ``KEY=VALUE`` per editor line
    in the UI).

Auth is inherited from :class:`~openstarry_code.gateway.middleware.AuthMiddleware`
(the same token/loopback rules that guard every other ``/api/*`` route).
"""

from __future__ import annotations

import uuid
from typing import Any
from urllib.parse import urlparse

import structlog
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Route

from openstarry_code.gateway.config import GatewayConfig, MCPServerEntry
from openstarry_code.paths import default_opensquilla_home

log = structlog.get_logger(__name__)

_ALLOWED_TRANSPORTS = frozenset({"stdio", "http"})

# Only http(s) URLs are accepted for the http transport; the runtime transport
# layer decides the protocol dialect once connections land in a later phase.
_ALLOWED_URL_SCHEMES = frozenset({"http", "https"})


# ---------------------------------------------------------------------------
# Persistence
# ---------------------------------------------------------------------------


def _persist_config(config: GatewayConfig) -> None:
    """Persist ``config.mcp`` changes through the shared sparse TOML persister.

    Mirrors :func:`openstarry_code.gateway.rpc_config._persist_config` so every
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
        # rejected field values, and env dicts may carry secrets.
        log.error(
            "gateway.mcp_config_persist_failed",
            path=path,
            error=type(exc).__name__,
        )
        raise
    log.info(
        "gateway.mcp_config_persisted",
        path=str(result.path),
        backup=str(result.backup_path) if result.backup_path else None,
    )


# ---------------------------------------------------------------------------
# Serialization / validation
# ---------------------------------------------------------------------------


def _serialize(entry: MCPServerEntry) -> dict[str, Any]:
    """Return the wire shape of one configured MCP server."""
    return {
        "id": entry.id,
        "name": entry.name,
        "transport": entry.transport,
        "command": entry.command,
        "args": list(entry.args),
        "env": dict(entry.env),
        "url": entry.url,
        "enabled": entry.enabled,
    }


def _find_entry(config: GatewayConfig, key: str) -> MCPServerEntry | None:
    """Locate an entry by its id, falling back to the name.

    The name fallback keeps hand-authored TOML entries (which predate the
    ``id`` field) addressable from the settings UI without a migration.
    """
    for entry in config.mcp.servers:
        if entry.id and entry.id == key:
            return entry
    for entry in config.mcp.servers:
        if entry.name and entry.name == key:
            return entry
    return None


def _validate_payload(
    body: dict[str, Any],
) -> tuple[dict[str, Any] | None, str | None]:
    """Normalize a create/update payload.

    Returns ``(fields, None)`` on success or ``(None, error_message)`` with a
    client-presentable message.
    """
    name = str(body.get("name") or "").strip()
    if not name:
        return None, "Name is required"

    transport = str(body.get("transport") or "stdio").strip().lower()
    if transport not in _ALLOWED_TRANSPORTS:
        return None, "Transport must be 'stdio' or 'http'"

    raw_args = body.get("args") or []
    if not isinstance(raw_args, list):
        return None, "Args must be a list of strings"
    args = [str(arg) for arg in raw_args]

    raw_env = body.get("env") or {}
    if not isinstance(raw_env, dict):
        return None, "Env must be an object of KEY=VALUE strings"
    env = {str(key): str(value) for key, value in raw_env.items()}

    command: str | None = None
    url: str | None = None
    if transport == "stdio":
        command = str(body.get("command") or "").strip()
        if not command:
            return None, "Command is required for stdio servers"
    else:
        url = str(body.get("url") or "").strip()
        parsed = urlparse(url)
        if parsed.scheme not in _ALLOWED_URL_SCHEMES or not parsed.netloc:
            return None, "A valid http(s) URL is required for http servers"

    enabled = body.get("enabled", True)
    if not isinstance(enabled, bool):
        return None, "Enabled must be a boolean"

    return (
        {
            "name": name,
            "transport": transport,
            "command": command,
            "args": args,
            "env": env,
            "url": url,
            "enabled": enabled,
        },
        None,
    )


async def _json_object(request: Request) -> dict[str, Any] | None:
    """Parse the request body; None when it is not a JSON object."""
    try:
        body = await request.json()
    except Exception:
        return None
    return body if isinstance(body, dict) else None


def _apply_fields(entry: MCPServerEntry, fields: dict[str, Any]) -> None:
    """Copy validated fields onto a config entry in place."""
    entry.name = fields["name"]
    entry.transport = fields["transport"]
    entry.command = fields["command"]
    entry.args = fields["args"]
    entry.env = fields["env"]
    entry.url = fields["url"]
    entry.enabled = fields["enabled"]


# ---------------------------------------------------------------------------
# Handlers (closures over the live GatewayConfig instance)
# ---------------------------------------------------------------------------


def mcp_server_routes(config: GatewayConfig) -> list[Route]:
    """Build the ``/api/mcp/servers`` CRUD routes bound to ``config``.

    The returned routes are spliced into the gateway's declarative route table
    by :mod:`openstarry_code.gateway.app`; auth is inherited from the shared
    ``/api/*`` middleware stack.
    """

    async def handle_list(request: Request) -> JSONResponse:
        """List every configured MCP server (enabled and disabled)."""
        del request
        return JSONResponse({"servers": [_serialize(e) for e in config.mcp.servers]})

    async def handle_create(request: Request) -> JSONResponse:
        """Add a configured MCP server (JSON body; ``id`` assigned here)."""
        body = await _json_object(request)
        if body is None:
            return JSONResponse({"error": "Invalid JSON body"}, status_code=400)
        fields, error = _validate_payload(body)
        if fields is None or error is not None:
            return JSONResponse({"error": error or "Invalid payload"}, status_code=400)

        entry = MCPServerEntry(id=uuid.uuid4().hex)
        _apply_fields(entry, fields)
        config.mcp.servers = [*config.mcp.servers, entry]
        try:
            _persist_config(config)
        except Exception:
            return JSONResponse({"error": "Cannot persist configuration"}, status_code=500)
        log.info(
            "gateway.mcp_server_created",
            name=fields["name"],
            transport=fields["transport"],
        )
        return JSONResponse(_serialize(entry), status_code=201)

    async def handle_update(request: Request) -> JSONResponse:
        """Replace the editable fields of one configured MCP server."""
        key = str(request.path_params.get("server_id") or "")
        entry = _find_entry(config, key) if key else None
        if entry is None:
            return JSONResponse({"error": "No such MCP server"}, status_code=404)

        body = await _json_object(request)
        if body is None:
            return JSONResponse({"error": "Invalid JSON body"}, status_code=400)
        fields, error = _validate_payload(body)
        if fields is None or error is not None:
            return JSONResponse({"error": error or "Invalid payload"}, status_code=400)

        _apply_fields(entry, fields)
        if not entry.id:
            # Legacy hand-authored entry reached through the name fallback:
            # assign a stable id so later edits address it deterministically.
            entry.id = uuid.uuid4().hex
        try:
            _persist_config(config)
        except Exception:
            return JSONResponse({"error": "Cannot persist configuration"}, status_code=500)
        log.info(
            "gateway.mcp_server_updated",
            name=fields["name"],
            transport=fields["transport"],
        )
        return JSONResponse(_serialize(entry))

    async def handle_delete(request: Request) -> JSONResponse:
        """Remove one configured MCP server from the config."""
        key = str(request.path_params.get("server_id") or "")
        entry = _find_entry(config, key) if key else None
        if entry is None:
            return JSONResponse({"error": "No such MCP server"}, status_code=404)

        config.mcp.servers = [e for e in config.mcp.servers if e is not entry]
        try:
            _persist_config(config)
        except Exception:
            return JSONResponse({"error": "Cannot persist configuration"}, status_code=500)
        log.info("gateway.mcp_server_deleted", name=entry.name)
        return JSONResponse({"id": entry.id or entry.name, "deleted": True})

    return [
        Route("/api/mcp/servers", handle_list, methods=["GET"]),
        Route("/api/mcp/servers", handle_create, methods=["POST"]),
        Route("/api/mcp/servers/{server_id}", handle_update, methods=["PUT"]),
        Route("/api/mcp/servers/{server_id}", handle_delete, methods=["DELETE"]),
    ]


def register_mcp_routes(app: Starlette, config: GatewayConfig) -> None:
    """Append the MCP configuration routes to an already-built app."""
    app.router.routes.extend(mcp_server_routes(config))
