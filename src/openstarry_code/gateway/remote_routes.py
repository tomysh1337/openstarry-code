"""Remote file browsing routes for the Web UI's "code interpreter" panel.

Read-only endpoints that let the right-hand IDE panel browse files on remote
servers alongside the local project tree. Four transport families:

  * ``ssh`` — ``[[ssh.hosts]]`` entries, carried by the system ``sftp``/``ssh``
    clients (no protocol library; matches the builtin-terminal semantics).
  * ``ftp`` — ``[[ftp.hosts]]`` entries, stdlib ``ftplib`` (optionally TLS).
  * ``wsl`` — Windows Subsystem for Linux distros, auto-detected via
    ``wsl.exe`` (the source list is empty on non-Windows hosts).
  * ``mcp`` — ``[[mcp.servers]]`` entries, browsed through the server's
    filesystem tool family (``list_directory`` / ``read_text_file`` …).
  * ``git`` — repositories cloned into the agent workspace (``git clone``
    via ``exec_command``), browsed as a read-only working tree on the
    gateway host.

Wire contract (mirrors the local IDE endpoints in :mod:`ide_routes`)::

    GET /api/remote/sources
        -> {"ssh":[...], "ftp":[...], "wsl":[...], "mcp":[...], "git":[...]}
    GET /api/remote/tree?type=<ssh|ftp|wsl|mcp|git>&id=<id>&path=<dir>
        -> {"path": "...", "entries": [{name,path,type,size?,language?}]}
    GET /api/remote/file?type=<...>&id=<...>&path=<file>
        -> {path,name,content?,language?,size?,truncated?,binary?}

Auth is inherited from the shared ``/api/*`` middleware stack like every other
panel route.
"""

from __future__ import annotations

import asyncio
import json
import os
import shlex
import shutil
import subprocess
from pathlib import Path
from typing import Any

import structlog
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Route

from openstarry_code.gateway.config import GatewayConfig
from openstarry_code.gateway.ide_routes import (
    _BINARY_EXT,
    _DEFAULT_SKIP_DIRS,
    _DEFAULT_SKIP_FILES,
    _LANGUAGE_BY_EXT,
    _MAX_FILE_BYTES,
    _decode_text,
)

log = structlog.get_logger(__name__)

# Hard bounds so a misconfigured host can never stall a panel request forever.
_CONNECT_TIMEOUT = 5.0
_COMMAND_TIMEOUT = 30.0
_WSL_TIMEOUT = 20.0
_FTP_TIMEOUT = 10.0

_ALLOWED_TYPES = frozenset({"ssh", "ftp", "wsl", "mcp", "git"})

# Tools a filesystem-style MCP server typically exposes; the panel looks these
# up by name so any server following the conventional filesystem surface works.
_MCP_DIR_TOOLS = ("list_directory", "directory_tree")
_MCP_READ_TOOLS = ("read_text_file", "read_file")


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------


def _language_for_name(name: str) -> str | None:
    if name.lower() == "dockerfile":
        return "dockerfile"
    return _LANGUAGE_BY_EXT.get(Path(name).suffix.lstrip(".").lower())


def _is_binary_name(name: str) -> bool:
    return Path(name).suffix.lstrip(".").lower() in _BINARY_EXT


def _to_int(raw: Any) -> int | None:
    try:
        return int(raw)
    except (TypeError, ValueError):
        return None


def _join_path(parent: str, name: str) -> str:
    if not parent or parent == "/":
        return f"/{name}"
    return f"{parent.rstrip('/')}/{name}"


def _stderr_tail(err: bytes) -> str:
    text = err.decode("utf-8", errors="replace").strip()
    if not text:
        return ""
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    return lines[-1] if lines else text


def _parse_long_listing(line: str) -> dict[str, Any] | None:
    """Parse one POSIX-style ``ls -l`` / FTP ``LIST`` line into an entry.

    Token shape: ``<perm> <nlinks> <owner> <group> <size> <month> <day>
    <time|year> <name...>`` — the name is everything after the first eight
    fields, so names containing spaces survive. Returns None for banners
    (``total N``), stray output and non-listing lines.
    """
    tokens = line.split()
    if len(tokens) < 9:
        return None
    perm = tokens[0]
    if not perm or perm[0] not in "dl-":
        return None
    name = " ".join(tokens[8:]).strip()
    if not name or name in {".", ".."}:
        return None
    return {
        "name": name,
        "type": "dir" if perm[0] == "d" else "file",
        "size": _to_int(tokens[4]),
    }


async def _run_cmd(
    argv: list[str],
    *,
    input_bytes: bytes | None = None,
    timeout: float = _COMMAND_TIMEOUT,
) -> tuple[int, bytes, bytes]:
    """Run a child process, returning ``(returncode, stdout, stderr)``."""
    proc = await asyncio.create_subprocess_exec(
        *argv,
        stdin=asyncio.subprocess.PIPE if input_bytes is not None else None,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    try:
        out, err = await asyncio.wait_for(proc.communicate(input_bytes), timeout=timeout)
    except asyncio.TimeoutError:
        try:
            proc.kill()
        except ProcessLookupError:
            pass
        await proc.wait()
        raise
    return proc.returncode or 0, out, err


def _build_file_response(rel: str, name: str, raw: bytes) -> dict[str, Any]:
    """Shape a file payload the same way :func:`ide_routes.api_ide_file` does."""
    truncated = False
    if len(raw) > _MAX_FILE_BYTES:
        raw = raw[: _MAX_FILE_BYTES]
        truncated = True
    if _is_binary_name(name) or b"\x00" in raw[:4096]:
        return {
            "path": rel,
            "name": name,
            "binary": True,
            "size": len(raw),
            "truncated": truncated,
        }
    return {
        "path": rel,
        "name": name,
        "content": _decode_text(raw),
        "language": _language_for_name(name),
        "size": len(raw),
        "truncated": truncated,
        "binary": False,
    }


def _sorted_entries(entries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(entries, key=lambda e: (e["type"] != "dir", e["name"].lower()))


# ---------------------------------------------------------------------------
# SSH — system sftp/ssh clients
# ---------------------------------------------------------------------------


def _ssh_target(entry: Any) -> str:
    return f"{entry.username}@{entry.host}" if entry.username else entry.host


def _ssh_base_argv(entry: Any) -> list[str]:
    return [
        "ssh",
        "-oBatchMode=yes",
        "-oConnectTimeout=5",
        "-oStrictHostKeyChecking=accept-new",
        "-p",
        str(entry.port),
        _ssh_target(entry),
    ]


def _sftp_argv(entry: Any) -> list[str]:
    return [
        "sftp",
        "-oBatchMode=yes",
        "-oConnectTimeout=5",
        "-oStrictHostKeyChecking=accept-new",
        "-P",
        str(entry.port),
        _ssh_target(entry),
    ]


def _sftp_quote(path: str) -> str:
    return '"' + path.replace("\\", "\\\\").replace('"', '\\"') + '"'


def _find_ssh_host(config: GatewayConfig, key: str) -> Any | None:
    from openstarry_code.gateway.ssh_routes import find_ssh_host

    return find_ssh_host(config, key)


async def _ssh_list(entry: Any, path: str) -> list[dict[str, Any]] | str:
    if shutil.which("sftp") is None:
        return "sftp binary missing on the gateway host"
    batch = "ls -l\n" if not path else f"ls -l {_sftp_quote(path)}\n"
    try:
        code, out, err = await _run_cmd(_sftp_argv(entry), input_bytes=batch.encode("utf-8"))
    except asyncio.TimeoutError:
        return "SSH listing timed out"
    if code != 0:
        return _stderr_tail(err) or f"sftp exited with code {code}"
    entries: list[dict[str, Any]] = []
    for line in out.decode("utf-8", errors="replace").splitlines():
        parsed = _parse_long_listing(line)
        if parsed is None:
            continue
        entries.append(
            {
                "name": parsed["name"],
                "path": _join_path(path, parsed["name"]),
                "type": parsed["type"],
                "size": parsed.get("size"),
                "language": _language_for_name(parsed["name"]) if parsed["type"] == "file" else None,
            }
        )
    return _sorted_entries(entries)


async def _ssh_read(entry: Any, path: str) -> tuple[bytes | None, str | None]:
    if shutil.which("ssh") is None:
        return None, "ssh binary missing on the gateway host"
    argv = [*_ssh_base_argv(entry), f"cat -- {shlex.quote(path)}"]
    try:
        code, out, err = await _run_cmd(argv)
    except asyncio.TimeoutError:
        return None, "SSH read timed out"
    if code != 0:
        return None, _stderr_tail(err) or f"ssh exited with code {code}"
    return out, None


# ---------------------------------------------------------------------------
# FTP — stdlib ftplib (optionally TLS)
# ---------------------------------------------------------------------------


def _find_ftp_host(config: GatewayConfig, key: str) -> Any | None:
    for entry in config.ftp.hosts:
        if entry.id and entry.id == key:
            return entry
    for entry in config.ftp.hosts:
        if entry.name and entry.name == key:
            return entry
    return None


def _ftp_connect(entry: Any):
    """Open a (TLS-capable) FTP connection and log in; raises on failure."""
    from ftplib import FTP, FTP_TLS

    ftp = FTP_TLS() if entry.tls else FTP()
    ftp.connect(entry.host, entry.port, timeout=_FTP_TIMEOUT)
    if entry.tls:
        ftp.auth()
    ftp.login(entry.username or "anonymous", entry.password)
    if entry.tls:
        ftp.prot_p()
    return ftp


def _ftp_list_fallback(ftp: Any, path: str) -> list[dict[str, Any]]:
    """Type detection for servers without MLSD: nlst names + LIST parse."""
    from ftplib import error_perm

    names: list[str] = []
    try:
        names = list(ftp.nlst(path or "/"))
    except (error_perm, OSError):
        names = []
    types: dict[str, dict[str, Any]] = {}

    def _cb(line: str) -> None:
        parsed = _parse_long_listing(line)
        if parsed is not None:
            types[parsed["name"]] = parsed

    try:
        ftp.retrlines(f"LIST {path or '/'}", _cb)
    except (error_perm, OSError):
        pass

    entries: list[dict[str, Any]] = []
    for name in names:
        if not name or name in {".", ".."}:
            continue
        info = types.get(name)
        is_dir = bool(info and info["type"] == "dir")
        entries.append(
            {
                "name": name,
                "path": _join_path(path, name),
                "type": "dir" if is_dir else "file",
                "size": info.get("size") if info else None,
                "language": _language_for_name(name) if not is_dir else None,
            }
        )
    return _sorted_entries(entries)


def _ftp_list_blocking(entry: Any, path: str) -> list[dict[str, Any]] | str:
    from ftplib import error_perm

    ftp = None
    try:
        ftp = _ftp_connect(entry)
        try:
            items = list(ftp.mlsd(path or "/"))
        except (error_perm, OSError):
            return _ftp_list_fallback(ftp, path)
        entries: list[dict[str, Any]] = []
        for name, facts in items:
            if not name or name in {".", ".."}:
                continue
            kind = str(facts.get("type") or "").lower()
            is_dir = kind in {"dir", "cdir", "pdir"}
            size = _to_int(facts.get("size"))
            entries.append(
                {
                    "name": name,
                    "path": _join_path(path, name),
                    "type": "dir" if is_dir else "file",
                    "size": size,
                    "language": _language_for_name(name) if not is_dir else None,
                }
            )
        return _sorted_entries(entries)
    except Exception as exc:  # noqa: BLE001 — surface any connect/login failure
        return str(exc) or "FTP connection failed"
    finally:
        if ftp is not None:
            try:
                ftp.close()
            except Exception:
                pass


def _ftp_read_blocking(entry: Any, path: str) -> tuple[bytes | None, str | None]:
    ftp = None
    try:
        ftp = _ftp_connect(entry)
        chunks: list[bytes] = []
        ftp.retrbinary(f"RETR {path}", chunks.append)
        return b"".join(chunks), None
    except Exception as exc:  # noqa: BLE001
        return None, str(exc) or "FTP read failed"
    finally:
        if ftp is not None:
            try:
                ftp.close()
            except Exception:
                pass


# ---------------------------------------------------------------------------
# WSL — Windows Subsystem for Linux (Windows only)
# ---------------------------------------------------------------------------


def _wsl_binary() -> str | None:
    if os.name != "nt":
        return None
    return shutil.which("wsl") or shutil.which("wsl.exe")


def _decode_wsl_text(data: bytes) -> str:
    # Some Windows builds emit UTF-16LE from wsl.exe; others UTF-8.
    if b"\x00" in data[:8]:
        try:
            return data.decode("utf-16-le")
        except UnicodeDecodeError:
            pass
    return data.decode("utf-8", errors="replace")


def wsl_distros() -> list[str]:
    """Return the installed WSL distro names (empty when WSL is unavailable)."""
    wsl = _wsl_binary()
    if wsl is None:
        return []
    # Modern WSL accepts --list --quiet; older builds only know -l -q.
    candidates: tuple[list[str], ...] = (
        [wsl, "--list", "--quiet"],
        [wsl, "-l", "-q"],
    )
    for argv in candidates:
        try:
            proc = subprocess.run(argv, capture_output=True, timeout=_CONNECT_TIMEOUT)
        except (OSError, subprocess.SubprocessError):
            return []
        if proc.returncode != 0:
            continue
        distros: list[str] = []
        for line in _decode_wsl_text(proc.stdout).splitlines():
            name = line.strip().lstrip("*").strip()
            if name and name.lower() != "windows":
                distros.append(name)
        return distros
    return []


def _wsl_argv(distro: str, cmd: str, *args: str) -> list[str]:
    return ["wsl.exe", "-d", distro, "--", cmd, *args]


async def _wsl_list(distro: str, path: str) -> list[dict[str, Any]] | str:
    if _wsl_binary() is None:
        return "WSL is only available on Windows"
    argv = _wsl_argv(
        distro,
        "find",
        path or "/",
        "-maxdepth",
        "1",
        "-mindepth",
        "1",
        "-printf",
        "%y\t%f\t%s\n",
    )
    try:
        code, out, err = await _run_cmd(argv, timeout=_WSL_TIMEOUT)
    except asyncio.TimeoutError:
        return "WSL listing timed out"
    if code != 0:
        return _stderr_tail(err) or f"wsl exited with code {code}"
    entries: list[dict[str, Any]] = []
    for line in _decode_wsl_text(out).splitlines():
        parts = line.split("\t")
        if len(parts) < 2:
            continue
        kind, name = parts[0], parts[1]
        if not name or name in {".", ".."}:
            continue
        is_dir = kind == "d"
        size = _to_int(parts[2]) if len(parts) > 2 else None
        entries.append(
            {
                "name": name,
                "path": _join_path(path, name),
                "type": "dir" if is_dir else "file",
                "size": size,
                "language": _language_for_name(name) if not is_dir else None,
            }
        )
    return _sorted_entries(entries)


async def _wsl_read(distro: str, path: str) -> tuple[bytes | None, str | None]:
    if _wsl_binary() is None:
        return None, "WSL is only available on Windows"
    argv = _wsl_argv(distro, "cat", path)
    try:
        code, out, err = await _run_cmd(argv, timeout=_WSL_TIMEOUT)
    except asyncio.TimeoutError:
        return None, "WSL read timed out"
    if code != 0:
        return None, _stderr_tail(err) or f"wsl exited with code {code}"
    return out, None


# ---------------------------------------------------------------------------
# MCP — browse through the server's filesystem tool family
# ---------------------------------------------------------------------------


def _find_mcp_server(config: GatewayConfig, key: str) -> Any | None:
    for entry in config.mcp.servers:
        if entry.id and entry.id == key:
            return entry
    for entry in config.mcp.servers:
        if entry.name and entry.name == key:
            return entry
    return None


def _mcp_tool(tools: list[Any], preferred: tuple[str, ...]) -> Any | None:
    by_name = {tool.name: tool for tool in tools}
    for name in preferred:
        if name in by_name:
            return by_name[name]
    # Fall back to a tool that looks filesystem-ish (name hint + path arg).
    for tool in tools:
        schema = getattr(tool, "input_schema", {}) or {}
        props = schema.get("properties", {}) if isinstance(schema, dict) else {}
        lowered = tool.name.lower()
        if "path" in props and ("director" in lowered or "file" in lowered or "ls" == lowered):
            return tool
    return None


async def _mcp_client(config: GatewayConfig, key: str):
    entry = _find_mcp_server(config, key)
    if entry is None:
        raise LookupError("No such MCP server")
    from openstarry_code.mcp.discovery import create_client
    from openstarry_code.mcp.types import MCPServerConfig

    server_cfg = MCPServerConfig(
        name=entry.name,
        transport=entry.transport,
        command=entry.command,
        args=list(entry.args),
        url=entry.url,
        env=dict(entry.env),
        tool_timeout_seconds=entry.tool_timeout_seconds,
    )
    client = create_client(server_cfg)
    await client.connect()
    return client


def _parse_mcp_dir(content: str) -> list[dict[str, Any]] | str:
    try:
        data = json.loads(content)
    except (ValueError, TypeError):
        return "MCP directory result was not JSON"
    if not isinstance(data, list):
        return "MCP directory result was not a list"
    entries: list[dict[str, Any]] = []
    for item in data:
        if not isinstance(item, dict):
            continue
        name = str(item.get("name") or "")
        if not name or name in {".", ".."}:
            continue
        kind = str(item.get("type") or item.get("kind") or "").lower()
        is_dir = kind in {"dir", "directory", "folder", "cdir", "pdir"} or item.get("is_directory") is True
        if not is_dir and not kind:
            is_dir = bool(item.get("isDirectory"))
        size = _to_int(item.get("size"))
        entries.append(
            {
                "name": name,
                "path": name,
                "type": "dir" if is_dir else "file",
                "size": size,
                "language": _language_for_name(name) if not is_dir else None,
            }
        )
    return _sorted_entries(entries)


async def _mcp_list(config: GatewayConfig, key: str, path: str) -> list[dict[str, Any]] | str:
    client = None
    try:
        client = await _mcp_client(config, key)
        tools = await client.list_tools()
        tool = _mcp_tool(tools, _MCP_DIR_TOOLS)
        if tool is None:
            return "MCP server exposes no filesystem directory tool"
        result = await client.call_tool(tool.name, {"path": path or "/"})
        if result.is_error:
            return result.content or "MCP directory tool failed"
        return _parse_mcp_dir(result.content)
    except asyncio.TimeoutError:
        return "MCP directory call timed out"
    except Exception as exc:  # noqa: BLE001
        return str(exc) or "MCP connection failed"
    finally:
        if client is not None:
            try:
                await client.close()
            except Exception:
                pass


async def _mcp_read(config: GatewayConfig, key: str, path: str) -> tuple[bytes | None, str | None]:
    client = None
    try:
        client = await _mcp_client(config, key)
        tools = await client.list_tools()
        tool = _mcp_tool(tools, _MCP_READ_TOOLS)
        if tool is None:
            return None, "MCP server exposes no filesystem read tool"
        result = await client.call_tool(tool.name, {"path": path})
        if result.is_error:
            return None, result.content or "MCP read tool failed"
        return result.content.encode("utf-8", errors="replace"), None
    except asyncio.TimeoutError:
        return None, "MCP read timed out"
    except Exception as exc:  # noqa: BLE001
        return None, str(exc) or "MCP connection failed"
    finally:
        if client is not None:
            try:
                await client.close()
            except Exception:
                pass


# ---------------------------------------------------------------------------
# Git — locally cloned repositories (browse the working tree of clones)
# ---------------------------------------------------------------------------
#
# The AI clones repositories with ``git clone`` via ``exec_command``; the
# default working directory is the agent workspace (``config.workspace_dir``).
# This transport discovers repositories under that root and lets the panel
# browse each clone's working tree. Everything is read-only and confined to
# the discovered repositories (path traversal outside them is rejected).

# Directories never worth descending into while scanning for clones.
_GIT_SKIP_SCAN_DIRS = frozenset(
    {
        ".git",
        ".hg",
        ".svn",
        ".idea",
        ".vscode",
        ".vs",
        ".venv",
        "venv",
        "env",
        "node_modules",
        "dist",
        "build",
        "out",
        "__pycache__",
        ".mypy_cache",
        ".pytest_cache",
        ".ruff_cache",
        ".tox",
        ".next",
        ".turbo",
        ".cache",
        "coverage",
        ".openstarry-code",
    }
)

# Clones may be nested (e.g. vendored repos), but cap the scan so a huge
# workspace never turns a panel request into a full-tree walk.
_GIT_MAX_SCAN_DEPTH = 4


def _git_scan_roots(config: GatewayConfig) -> list[Path]:
    roots: list[Path] = []
    raw = getattr(config, "workspace_dir", None)
    if isinstance(raw, str) and raw.strip():
        roots.append(Path(raw).expanduser().resolve())
    return [root for root in dict.fromkeys(roots) if root.is_dir()]


def _same_local_path(a: str, b: str) -> bool:
    pa, pb = Path(a).resolve(), Path(b).resolve()
    if os.name == "nt":
        return str(pa).lower() == str(pb).lower()
    return str(pa) == str(pb)


def _discover_git_repos(config: GatewayConfig) -> list[dict[str, str]]:
    """Return cloned repositories under the workspace scan roots.

    A directory counts as a repository when it contains a ``.git`` entry (a
    directory for normal clones, a file for worktrees/submodules). Results are
    de-duplicated across roots (Windows paths compare case-insensitively).
    """
    found: list[dict[str, str]] = []
    seen: set[str] = set()

    def _add(repo: Path) -> None:
        key = str(repo.resolve())
        norm = key.lower() if os.name == "nt" else key
        if norm in seen:
            return
        seen.add(norm)
        found.append(
            {
                "id": str(repo),
                "name": repo.name or str(repo),
                "path": str(repo),
            }
        )

    for root in _git_scan_roots(config):
        for dirpath, dirnames, filenames in os.walk(root):
            if ".git" in dirnames or ".git" in filenames:
                _add(Path(dirpath).resolve())
                # A clone is a leaf: don't descend and re-report inner repos.
                dirnames[:] = []
                continue
            depth = len(Path(dirpath).relative_to(root).parts)
            if depth >= _GIT_MAX_SCAN_DEPTH:
                dirnames[:] = []
                continue
            dirnames[:] = [d for d in dirnames if d not in _GIT_SKIP_SCAN_DIRS]
    return found


def _find_git_repo(config: GatewayConfig, key: str) -> Path | None:
    for repo in _discover_git_repos(config):
        if _same_local_path(repo["id"], key):
            return Path(repo["id"])
    return None


def _safe_resolve_local(root: Path, rel: str) -> Path | None:
    """Resolve ``rel`` inside ``root``; None when it escapes the root."""
    if not rel:
        return root
    candidate = (root / rel).resolve()
    try:
        candidate.relative_to(root)
    except ValueError:
        return None
    return candidate


def _git_list(repo: Path, rel: str) -> list[dict[str, Any]] | str:
    target = _safe_resolve_local(repo, rel)
    if target is None:
        return "Path escapes the repository root"
    if not target.exists():
        return "No such directory"
    if not target.is_dir():
        return "Not a directory"

    entries: list[dict[str, Any]] = []
    try:
        children = sorted(target.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower()))
    except OSError:
        return "Cannot read directory"

    for child in children:
        name = child.name
        try:
            is_dir = child.is_dir()
            is_file = child.is_file()
        except OSError:
            continue
        if is_dir:
            if name in _DEFAULT_SKIP_DIRS:
                continue
            entries.append(
                {
                    "name": name,
                    "path": str(child.relative_to(repo)),
                    "type": "dir",
                }
            )
        elif is_file:
            if name in _DEFAULT_SKIP_FILES:
                continue
            size = 0
            try:
                size = child.stat().st_size
            except OSError:
                pass
            entries.append(
                {
                    "name": name,
                    "path": str(child.relative_to(repo)),
                    "type": "file",
                    "size": size,
                    "language": _language_for_name(name),
                }
            )
    return _sorted_entries(entries)


def _git_read(repo: Path, rel: str) -> tuple[bytes | None, str | None]:
    target = _safe_resolve_local(repo, rel)
    if target is None:
        return None, "Path escapes the repository root"
    if not target.is_file():
        return None, "Not a file"
    try:
        raw = target.read_bytes()
    except OSError:
        return None, "Cannot read file"
    return raw, None


# ---------------------------------------------------------------------------
# Dispatch
# ---------------------------------------------------------------------------


async def _list_for(config: GatewayConfig, kind: str, key: str, path: str) -> list[dict[str, Any]] | str:
    if kind == "ssh":
        entry = _find_ssh_host(config, key)
        if entry is None:
            return "No such SSH host"
        return await _ssh_list(entry, path)
    if kind == "ftp":
        entry = _find_ftp_host(config, key)
        if entry is None:
            return "No such FTP host"
        return await asyncio.to_thread(_ftp_list_blocking, entry, path)
    if kind == "wsl":
        return await _wsl_list(key, path)
    if kind == "mcp":
        return await _mcp_list(config, key, path)
    if kind == "git":
        repo = _find_git_repo(config, key)
        if repo is None:
            return "No such git repository"
        return _git_list(repo, path)
    return "Unsupported remote type"


async def _read_for(config: GatewayConfig, kind: str, key: str, path: str) -> tuple[bytes | None, str | None]:
    if kind == "ssh":
        entry = _find_ssh_host(config, key)
        if entry is None:
            return None, "No such SSH host"
        return await _ssh_read(entry, path)
    if kind == "ftp":
        entry = _find_ftp_host(config, key)
        if entry is None:
            return None, "No such FTP host"
        return await asyncio.to_thread(_ftp_read_blocking, entry, path)
    if kind == "wsl":
        return await _wsl_read(key, path)
    if kind == "mcp":
        return await _mcp_read(config, key, path)
    if kind == "git":
        repo = _find_git_repo(config, key)
        if repo is None:
            return None, "No such git repository"
        return _git_read(repo, path)
    return None, "Unsupported remote type"


# ---------------------------------------------------------------------------
# Handlers (closures over the live GatewayConfig instance)
# ---------------------------------------------------------------------------


def remote_routes(config: GatewayConfig) -> list[Route]:
    """Build the read-only ``/api/remote/*`` routes bound to ``config``."""

    async def handle_sources(request: Request) -> JSONResponse:
        del request
        ssh = [
            {
                "id": e.id or e.name,
                "name": e.name,
                "host": e.host,
                "port": e.port,
                "username": e.username,
            }
            for e in config.ssh.hosts
            if e.enabled
        ]
        ftp = [
            {
                "id": e.id or e.name,
                "name": e.name,
                "host": e.host,
                "port": e.port,
                "username": e.username,
                "tls": e.tls,
            }
            for e in config.ftp.hosts
            if e.enabled
        ]
        wsl = [{"id": name, "name": name} for name in wsl_distros()]
        mcp = [
            {
                "id": e.id or e.name,
                "name": e.name,
                "transport": e.transport,
            }
            for e in config.mcp.servers
            if e.enabled
        ]
        git = _discover_git_repos(config)
        return JSONResponse({"ssh": ssh, "ftp": ftp, "wsl": wsl, "mcp": mcp, "git": git})

    async def handle_tree(request: Request) -> JSONResponse:
        kind = (request.query_params.get("type") or "").strip().lower()
        key = (request.query_params.get("id") or "").strip()
        path = (request.query_params.get("path") or "").strip()
        if kind not in _ALLOWED_TYPES:
            return JSONResponse({"error": "type must be ssh, ftp, wsl, mcp or git"}, status_code=400)
        if not key:
            return JSONResponse({"error": "Missing id"}, status_code=400)
        result = await _list_for(config, kind, key, path)
        if isinstance(result, str):
            return JSONResponse({"error": result}, status_code=502)
        return JSONResponse({"path": path, "entries": result})

    async def handle_file(request: Request) -> JSONResponse:
        kind = (request.query_params.get("type") or "").strip().lower()
        key = (request.query_params.get("id") or "").strip()
        path = (request.query_params.get("path") or "").strip()
        if kind not in _ALLOWED_TYPES:
            return JSONResponse({"error": "type must be ssh, ftp, wsl, mcp or git"}, status_code=400)
        if not key:
            return JSONResponse({"error": "Missing id"}, status_code=400)
        if not path:
            return JSONResponse({"error": "Missing path"}, status_code=400)
        raw, error = await _read_for(config, kind, key, path)
        if error is not None:
            return JSONResponse({"error": error}, status_code=502)
        name = Path(path).name or path
        return JSONResponse(_build_file_response(path, name, raw))

    return [
        Route("/api/remote/sources", handle_sources, methods=["GET"]),
        Route("/api/remote/tree", handle_tree, methods=["GET"]),
        Route("/api/remote/file", handle_file, methods=["GET"]),
    ]


def register_remote_routes(app: Starlette, config: GatewayConfig) -> None:
    """Append the remote browsing routes to an already-built app."""
    app.router.routes.extend(remote_routes(config))
