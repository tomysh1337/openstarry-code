"""FTP host configuration HTTP routes for the Web UI settings panel.

These endpoints manage the *configuration* of FTP hosts persisted in the
gateway config TOML (``[[ftp.hosts]]`` entries) and mirror the SSH counterpart
(:mod:`openstarry_code.gateway.ssh_routes`). This phase deliberately stops at
configuration management — create / update / delete / enable — and does NOT
open FTP connections: browsing is later carried by stdlib ``ftplib`` inside the
IDE panel's remote tab (:mod:`openstarry_code.gateway.remote_routes`).

Validation contract (mirrored by the settings panel):
  * ``name`` — non-empty after trimming.
  * ``host`` — non-empty after trimming.
  * ``port`` — integer in 1..65535 (default 21).
  * ``username`` / ``password`` — optional; empty username means anonymous.
  * ``tls`` — optional boolean (FTPS via AUTH TLS).
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

from openstarry_code.gateway.config import FTPHostEntry, GatewayConfig
from openstarry_code.paths import default_opensquilla_home

log = structlog.get_logger(__name__)

_PORT_MIN = 1
_PORT_MAX = 65535
_DEFAULT_PORT = 21


# ---------------------------------------------------------------------------
# Persistence
# ---------------------------------------------------------------------------


def _persist_config(config: GatewayConfig) -> None:
    """Persist ``config.ftp`` changes through the shared sparse TOML persister."""
    if not config.config_path:
        config.config_path = str(default_opensquilla_home() / "config.toml")

    from openstarry_code.onboarding.config_store import persist_config

    path = str(config.config_path)
    try:
        result = persist_config(config, path=path)
    except Exception as exc:
        log.error(
            "gateway.ftp_config_persist_failed",
            path=path,
            error=type(exc).__name__,
        )
        raise
    log.info(
        "gateway.ftp_config_persisted",
        path=str(result.path),
        backup=str(result.backup_path) if result.backup_path else None,
    )


# ---------------------------------------------------------------------------
# Serialization / validation
# ---------------------------------------------------------------------------


def _serialize(entry: FTPHostEntry) -> dict[str, Any]:
    """Return the wire shape of one configured FTP host.

    The password is included so the operator's own settings panel can edit an
    existing entry in place; the value rides the same token/loopback-protected
    ``/api/*`` channel as every other settings field.
    """
    return {
        "id": entry.id,
        "name": entry.name,
        "host": entry.host,
        "port": entry.port,
        "username": entry.username,
        "password": entry.password,
        "tls": entry.tls,
        "enabled": entry.enabled,
    }


def find_ftp_host(config: GatewayConfig, key: str) -> FTPHostEntry | None:
    """Locate an entry by its id, falling back to the name."""
    for entry in config.ftp.hosts:
        if entry.id and entry.id == key:
            return entry
    for entry in config.ftp.hosts:
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
    password = str(body.get("password") or "")

    tls = body.get("tls", False)
    if not isinstance(tls, bool):
        return None, "TLS must be a boolean"

    enabled = body.get("enabled", True)
    if not isinstance(enabled, bool):
        return None, "Enabled must be a boolean"

    return (
        {
            "name": name,
            "host": host,
            "port": port,
            "username": username,
            "password": password,
            "tls": tls,
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


def _apply_fields(entry: FTPHostEntry, fields: dict[str, Any]) -> None:
    """Copy validated fields onto a config entry in place."""
    entry.name = fields["name"]
    entry.host = fields["host"]
    entry.port = fields["port"]
    entry.username = fields["username"]
    entry.password = fields["password"]
    entry.tls = fields["tls"]
    entry.enabled = fields["enabled"]


# ---------------------------------------------------------------------------
# Handlers (closures over the live GatewayConfig instance)
# ---------------------------------------------------------------------------


def ftp_host_routes(config: GatewayConfig) -> list[Route]:
    """Build the ``/api/ftp/hosts`` CRUD routes bound to ``config``."""

    async def handle_list(request: Request) -> JSONResponse:
        """List every configured FTP host (enabled and disabled)."""
        del request
        return JSONResponse({"hosts": [_serialize(e) for e in config.ftp.hosts]})

    async def handle_create(request: Request) -> JSONResponse:
        """Add a configured FTP host (JSON body; ``id`` assigned here)."""
        body = await _json_object(request)
        if body is None:
            return JSONResponse({"error": "Invalid JSON body"}, status_code=400)
        fields, error = _validate_payload(body)
        if fields is None or error is not None:
            return JSONResponse({"error": error or "Invalid payload"}, status_code=400)

        entry = FTPHostEntry(id=uuid.uuid4().hex)
        _apply_fields(entry, fields)
        config.ftp.hosts = [*config.ftp.hosts, entry]
        try:
            _persist_config(config)
        except Exception:
            return JSONResponse({"error": "Cannot persist configuration"}, status_code=500)
        log.info(
            "gateway.ftp_host_created",
            name=fields["name"],
            host=fields["host"],
            port=fields["port"],
        )
        return JSONResponse(_serialize(entry), status_code=201)

    async def handle_update(request: Request) -> JSONResponse:
        """Replace the editable fields of one configured FTP host."""
        key = str(request.path_params.get("host_id") or "")
        entry = find_ftp_host(config, key) if key else None
        if entry is None:
            return JSONResponse({"error": "No such FTP host"}, status_code=404)

        body = await _json_object(request)
        if body is None:
            return JSONResponse({"error": "Invalid JSON body"}, status_code=400)
        fields, error = _validate_payload(body)
        if fields is None or error is not None:
            return JSONResponse({"error": error or "Invalid payload"}, status_code=400)

        _apply_fields(entry, fields)
        if not entry.id:
            entry.id = uuid.uuid4().hex
        try:
            _persist_config(config)
        except Exception:
            return JSONResponse({"error": "Cannot persist configuration"}, status_code=500)
        log.info(
            "gateway.ftp_host_updated",
            name=fields["name"],
            host=fields["host"],
            port=fields["port"],
        )
        return JSONResponse(_serialize(entry))

    async def handle_delete(request: Request) -> JSONResponse:
        """Remove one configured FTP host from the config."""
        key = str(request.path_params.get("host_id") or "")
        entry = find_ftp_host(config, key) if key else None
        if entry is None:
            return JSONResponse({"error": "No such FTP host"}, status_code=404)

        config.ftp.hosts = [e for e in config.ftp.hosts if e is not entry]
        try:
            _persist_config(config)
        except Exception:
            return JSONResponse({"error": "Cannot persist configuration"}, status_code=500)
        log.info("gateway.ftp_host_deleted", name=entry.name)
        return JSONResponse({"id": entry.id or entry.name, "deleted": True})

    return [
        Route("/api/ftp/hosts", handle_list, methods=["GET"]),
        Route("/api/ftp/hosts", handle_create, methods=["POST"]),
        Route("/api/ftp/hosts/{host_id}", handle_update, methods=["PUT"]),
        Route("/api/ftp/hosts/{host_id}", handle_delete, methods=["DELETE"]),
    ]


def register_ftp_routes(app: Starlette, config: GatewayConfig) -> None:
    """Append the FTP configuration routes to an already-built app."""
    app.router.routes.extend(ftp_host_routes(config))
