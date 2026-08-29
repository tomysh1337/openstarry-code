"""SSH host configuration HTTP routes for the Web UI settings panel.

These endpoints manage the *configuration* of SSH hosts persisted in the
gateway config TOML (``[[ssh.hosts]]`` entries). Like the MCP counterpart
(:mod:`openstarry_code.gateway.mcp_routes`) this phase deliberately stops at
configuration management — create / update / delete / enable — and does NOT
open SSH connections: sessions are later carried by the system ``ssh`` client
inside a builtin-terminal WebSocket (``/ws/builtin/terminal?ssh_host=<id>``),
never by a protocol library here.

Validation contract (mirrored by the settings panel):
  * ``name`` — non-empty after trimming.
  * ``host`` — non-empty after trimming.
  * ``port`` — integer in 1..65535 (default 22).
  * ``username`` — optional; empty lets ssh pick the current user.
  * ``id`` — uuid4 hex, assigned server-side on create.

Auth is inherited from :class:`~openstarry_code.gateway.middleware.AuthMiddleware`
(the same token/loopback rules that guard every other ``/api/*`` route).
"""

from __future__ import annotations

import uuid
from typing import Any

import structlog
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Route

from openstarry_code.gateway.config import GatewayConfig, SSHHostEntry
from openstarry_code.paths import default_opensquilla_home

log = structlog.get_logger(__name__)

_PORT_MIN = 1
_PORT_MAX = 65535
_DEFAULT_PORT = 22


# ---------------------------------------------------------------------------
# Persistence
# ---------------------------------------------------------------------------


def _persist_config(config: GatewayConfig) -> None:
    """Persist ``config.ssh`` changes through the shared sparse TOML persister.

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
            "gateway.ssh_config_persist_failed",
            path=path,
            error=type(exc).__name__,
        )
        raise
    log.info(
        "gateway.ssh_config_persisted",
        path=str(result.path),
        backup=str(result.backup_path) if result.backup_path else None,
    )


# ---------------------------------------------------------------------------
# Serialization / validation
# ---------------------------------------------------------------------------


def _serialize(entry: SSHHostEntry) -> dict[str, Any]:
    """Return the wire shape of one configured SSH host."""
    return {
        "id": entry.id,
        "name": entry.name,
        "host": entry.host,
        "port": entry.port,
        "username": entry.username,
        "enabled": entry.enabled,
    }


def find_ssh_host(config: GatewayConfig, key: str) -> SSHHostEntry | None:
    """Locate an entry by its id, falling back to the name.

    Shared with :mod:`openstarry_code.gateway.terminal_ws`, which resolves the
    ``ssh_host`` WebSocket query parameter against the same config entries.
    The name fallback keeps hand-authored TOML entries (which predate the
    ``id`` field) addressable without a migration.
    """
    for entry in config.ssh.hosts:
        if entry.id and entry.id == key:
            return entry
    for entry in config.ssh.hosts:
        if entry.name and entry.name == key:
            return entry
    return None


def _parse_port(raw: Any) -> tuple[int | None, str | None]:
    """Coerce the wire port value; returns ``(port, None)`` or ``(None, error)``."""
    if raw is None or raw == "":
        return _DEFAULT_PORT, None
    if isinstance(raw, bool):
        return None, "Port must be an integer between 1 and 65535"
    try:
        port = int(raw)
    except (TypeError, ValueError):
        return None, "Port must be an integer between 1 and 65535"
    if not (_PORT_MIN <= port <= _PORT_MAX):
        return None, "Port must be an integer between 1 and 65535"
    return port, None


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

    host = str(body.get("host") or "").strip()
    if not host:
        return None, "Host is required"

    port, error = _parse_port(body.get("port"))
    if error is not None:
        return None, error

    username = str(body.get("username") or "").strip()

    enabled = body.get("enabled", True)
    if not isinstance(enabled, bool):
        return None, "Enabled must be a boolean"

    return (
        {
            "name": name,
            "host": host,
            "port": port,
            "username": username,
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


def _apply_fields(entry: SSHHostEntry, fields: dict[str, Any]) -> None:
    """Copy validated fields onto a config entry in place."""
    entry.name = fields["name"]
    entry.host = fields["host"]
    entry.port = fields["port"]
    entry.username = fields["username"]
    entry.enabled = fields["enabled"]


# ---------------------------------------------------------------------------
# Handlers (closures over the live GatewayConfig instance)
# ---------------------------------------------------------------------------


def ssh_host_routes(config: GatewayConfig) -> list[Route]:
    """Build the ``/api/ssh/hosts`` CRUD routes bound to ``config``.

    The returned routes are spliced into the gateway's declarative route table
    by :mod:`openstarry_code.gateway.app`; auth is inherited from the shared
    ``/api/*`` middleware stack.
    """

    async def handle_list(request: Request) -> JSONResponse:
        """List every configured SSH host (enabled and disabled)."""
        del request
        return JSONResponse({"hosts": [_serialize(e) for e in config.ssh.hosts]})

    async def handle_create(request: Request) -> JSONResponse:
        """Add a configured SSH host (JSON body; ``id`` assigned here)."""
        body = await _json_object(request)
        if body is None:
            return JSONResponse({"error": "Invalid JSON body"}, status_code=400)
        fields, error = _validate_payload(body)
        if fields is None or error is not None:
            return JSONResponse({"error": error or "Invalid payload"}, status_code=400)

        entry = SSHHostEntry(id=uuid.uuid4().hex)
        _apply_fields(entry, fields)
        config.ssh.hosts = [*config.ssh.hosts, entry]
        try:
            _persist_config(config)
        except Exception:
            return JSONResponse({"error": "Cannot persist configuration"}, status_code=500)
        log.info(
            "gateway.ssh_host_created",
            name=fields["name"],
            host=fields["host"],
            port=fields["port"],
        )
        return JSONResponse(_serialize(entry), status_code=201)

    async def handle_update(request: Request) -> JSONResponse:
        """Replace the editable fields of one configured SSH host."""
        key = str(request.path_params.get("host_id") or "")
        entry = find_ssh_host(config, key) if key else None
        if entry is None:
            return JSONResponse({"error": "No such SSH host"}, status_code=404)

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
            "gateway.ssh_host_updated",
            name=fields["name"],
            host=fields["host"],
            port=fields["port"],
        )
        return JSONResponse(_serialize(entry))

    async def handle_delete(request: Request) -> JSONResponse:
        """Remove one configured SSH host from the config."""
        key = str(request.path_params.get("host_id") or "")
        entry = find_ssh_host(config, key) if key else None
        if entry is None:
            return JSONResponse({"error": "No such SSH host"}, status_code=404)

        config.ssh.hosts = [e for e in config.ssh.hosts if e is not entry]
        try:
            _persist_config(config)
        except Exception:
            return JSONResponse({"error": "Cannot persist configuration"}, status_code=500)
        log.info("gateway.ssh_host_deleted", name=entry.name)
        return JSONResponse({"id": entry.id or entry.name, "deleted": True})

    return [
        Route("/api/ssh/hosts", handle_list, methods=["GET"]),
        Route("/api/ssh/hosts", handle_create, methods=["POST"]),
        Route("/api/ssh/hosts/{host_id}", handle_update, methods=["PUT"]),
        Route("/api/ssh/hosts/{host_id}", handle_delete, methods=["DELETE"]),
    ]


def register_ssh_routes(app: Starlette, config: GatewayConfig) -> None:
    """Append the SSH configuration routes to an already-built app."""
    app.router.routes.extend(ssh_host_routes(config))
