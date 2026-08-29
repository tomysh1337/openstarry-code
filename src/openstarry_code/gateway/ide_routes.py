"""IDE panel HTTP routes: project source tree, file reading, handoff docs.

These endpoints power the Web UI's right-hand "code interpreter" panel
(document + code tabs) and the desktop shell that renders the same bundle.
They expose files from the *project root* only — the directory the gateway
was started from (or ``OPENSTARRY_CODE_PROJECT_ROOT`` when set). Path
traversal outside that root is rejected.

Read endpoints return tree/file listings; the mutating endpoints
(create / rename / delete) accept a JSON body, validate names and resolve
every path against the project root before touching the filesystem.

Auth is inherited from :class:`~openstarry_code.gateway.middleware.AuthMiddleware`
(the same token/loopback rules that guard every other ``/api/*`` route).
"""

from __future__ import annotations

import difflib
import os
import shutil
import threading
import time
from pathlib import Path
from typing import Any

from starlette.requests import Request
from starlette.responses import JSONResponse

# ---------------------------------------------------------------------------
# Project root
# ---------------------------------------------------------------------------

_DEFAULT_SKIP_DIRS = frozenset(
    {
        ".git",
        ".hg",
        ".svn",
        ".idea",
        ".vscode",
        ".vs",
        ".trae",
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
        ".nox",
        ".eggs",
        ".next",
        ".turbo",
        ".cache",
        "coverage",
        ".coverage",
    }
)

# Files that are never useful in a source explorer and may be huge.
_DEFAULT_SKIP_FILES = frozenset(
    {
        ".DS_Store",
        "Thumbs.db",
        "desktop.ini",
        "npm-debug.log",
        "yarn-error.log",
        "package-lock.json",
    }
)

# Extension -> highlight.js language id (used by the Web UI's code viewer).
_LANGUAGE_BY_EXT: dict[str, str] = {
    "py": "python",
    "pyi": "python",
    "js": "javascript",
    "jsx": "javascript",
    "mjs": "javascript",
    "cjs": "javascript",
    "ts": "typescript",
    "tsx": "typescript",
    "mts": "typescript",
    "cts": "typescript",
    "vue": "vue",
    "html": "xml",
    "htm": "xml",
    "xml": "xml",
    "svg": "xml",
    "css": "css",
    "scss": "scss",
    "sass": "scss",
    "less": "less",
    "json": "json",
    "md": "markdown",
    "markdown": "markdown",
    "yaml": "yaml",
    "yml": "yaml",
    "toml": "ini",
    "ini": "ini",
    "cfg": "ini",
    "conf": "ini",
    "sh": "bash",
    "bash": "bash",
    "zsh": "bash",
    "ps1": "powershell",
    "psm1": "powershell",
    "sql": "sql",
    "go": "go",
    "rs": "rust",
    "java": "java",
    "kt": "kotlin",
    "kts": "kotlin",
    "c": "c",
    "h": "c",
    "cpp": "cpp",
    "cc": "cpp",
    "cxx": "cpp",
    "hpp": "cpp",
    "cs": "csharp",
    "php": "php",
    "rb": "ruby",
    "swift": "swift",
    "lua": "lua",
    "r": "r",
    "dart": "dart",
    "dockerfile": "dockerfile",
    "lock": "ini",
    "tf": "hcl",
    "txt": "plaintext",
    "rst": "markdown",
    "graphql": "graphql",
    "gql": "graphql",
}

# Largest file we are willing to return over the wire.
_MAX_FILE_BYTES = 512 * 1024

_BINARY_EXT = frozenset(
    {
        "png",
        "jpg",
        "jpeg",
        "gif",
        "webp",
        "ico",
        "bmp",
        "pdf",
        "zip",
        "gz",
        "tar",
        "7z",
        "rar",
        "exe",
        "dll",
        "so",
        "dylib",
        "bin",
        "wasm",
        "woff",
        "woff2",
        "ttf",
        "otf",
        "eot",
        "pyc",
        "whl",
        "jar",
        "class",
        "o",
        "a",
        "lib",
        "pyd",
        "node",
    }
)


def resolve_project_root() -> Path:
    """Return the project root the IDE panel browses.

    ``OPENSTARRY_CODE_PROJECT_ROOT`` wins when set (desktop shells and tests
    use it); otherwise the gateway's working directory is the project root.
    """
    env_root = os.environ.get("OPENSTARRY_CODE_PROJECT_ROOT", "").strip()
    if env_root:
        candidate = Path(env_root).expanduser()
        if candidate.is_dir():
            return candidate.resolve()
    return Path.cwd().resolve()


def _safe_resolve(root: Path, rel_path: str) -> Path | None:
    """Resolve ``rel_path`` inside ``root``; None when it escapes the root."""
    if not rel_path:
        return root
    candidate = (root / rel_path).resolve()
    try:
        candidate.relative_to(root)
    except ValueError:
        return None
    return candidate


def _language_for(path: Path) -> str | None:
    if path.name.lower() in {"dockerfile"}:
        return "dockerfile"
    return _LANGUAGE_BY_EXT.get(path.suffix.lstrip(".").lower())


def _is_binary_name(path: Path) -> bool:
    return path.suffix.lstrip(".").lower() in _BINARY_EXT


def _decode_text(raw: bytes) -> str:
    for encoding in ("utf-8", "gb18030", "latin-1"):
        try:
            return raw.decode(encoding)
        except (UnicodeDecodeError, LookupError):
            continue
    return raw.decode("utf-8", errors="replace")


# ---------------------------------------------------------------------------
# Handlers
# ---------------------------------------------------------------------------


async def api_ide_root(request: Request) -> JSONResponse:
    """Report the browsable project root (display name + absolute path)."""
    root = resolve_project_root()
    return JSONResponse(
        {
            "name": root.name or str(root),
            "path": str(root),
            "platform": os.name,  # "nt" | "posix"
        }
    )


async def api_ide_tree(request: Request) -> JSONResponse:
    """List immediate children of a project directory (lazy tree).

    Query param ``path`` is a relative directory; omitted means the root.
    Directories are listed first, then files, each sorted by name.
    """
    root = resolve_project_root()
    rel = (request.query_params.get("path") or "").strip()
    target = _safe_resolve(root, rel)
    if target is None:
        return JSONResponse({"error": "Path escapes the project root"}, status_code=400)
    if not target.is_dir():
        return JSONResponse({"error": "Not a directory"}, status_code=400)
    if not target.exists():
        return JSONResponse({"error": "No such directory"}, status_code=404)

    entries: list[dict[str, Any]] = []
    try:
        children = sorted(
            target.iterdir(),
            key=lambda p: (not p.is_dir(), p.name.lower()),
        )
    except OSError:
        return JSONResponse({"error": "Cannot read directory"}, status_code=500)

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
            entries.append({"name": name, "path": str(child.relative_to(root)), "type": "dir"})
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
                    "path": str(child.relative_to(root)),
                    "type": "file",
                    "size": size,
                    "language": _language_for(child),
                }
            )

    return JSONResponse({"path": rel or "", "entries": entries})


async def api_ide_file(request: Request) -> JSONResponse:
    """Return a single text file from the project root.

    Query param ``path`` is a relative file path. Binary files and files
    larger than :data:`_MAX_FILE_BYTES` are truncated/rejected with a flag so
    the UI can degrade gracefully.
    """
    root = resolve_project_root()
    rel = (request.query_params.get("path") or "").strip()
    if not rel:
        return JSONResponse({"error": "Missing path"}, status_code=400)
    target = _safe_resolve(root, rel)
    if target is None:
        return JSONResponse({"error": "Path escapes the project root"}, status_code=400)
    if not target.is_file():
        return JSONResponse({"error": "Not a file"}, status_code=404)

    try:
        raw = target.read_bytes()
    except OSError:
        return JSONResponse({"error": "Cannot read file"}, status_code=500)

    truncated = False
    if len(raw) > _MAX_FILE_BYTES:
        raw = raw[: _MAX_FILE_BYTES]
        truncated = True

    if _is_binary_name(target) or b"\x00" in raw[:4096]:
        return JSONResponse(
            {
                "path": rel,
                "name": target.name,
                "binary": True,
                "size": len(raw),
                "truncated": truncated,
            }
        )

    return JSONResponse(
        {
            "path": rel,
            "name": target.name,
            "content": _decode_text(raw),
            "language": _language_for(target),
            "size": len(raw),
            "truncated": truncated,
            "binary": False,
        }
    )


async def api_ide_doc(request: Request) -> JSONResponse:
    """Return a Markdown document from the project root (raw text).

    A superset of :func:`api_ide_file` restricted to ``.md``/``.markdown``
    files, used by the right panel's "document" tab.
    """
    root = resolve_project_root()
    rel = (request.query_params.get("path") or "").strip()
    if not rel:
        return JSONResponse({"error": "Missing path"}, status_code=400)
    target = _safe_resolve(root, rel)
    if target is None:
        return JSONResponse({"error": "Path escapes the project root"}, status_code=400)
    if not target.is_file():
        return JSONResponse({"error": "Not a file"}, status_code=404)
    if target.suffix.lower() not in {".md", ".markdown", ".rst", ".txt"}:
        return JSONResponse({"error": "Not a document"}, status_code=400)

    try:
        raw = target.read_bytes()
    except OSError:
        return JSONResponse({"error": "Cannot read file"}, status_code=500)

    truncated = False
    if len(raw) > _MAX_FILE_BYTES:
        raw = raw[: _MAX_FILE_BYTES]
        truncated = True

    return JSONResponse(
        {
            "path": rel,
            "name": target.name,
            "content": _decode_text(raw),
            "size": len(raw),
            "truncated": truncated,
        }
    )


async def api_ide_handoff(request: Request) -> JSONResponse:
    """Return the newest ``handoff/*.md`` document (the IDE's current handoff).

    The handoff filename embeds a date (``handoff-YYYY-MM-DD.md``), so instead
    of hard-coding a name the UI asks for the newest one.
    """
    root = resolve_project_root()
    handoff_dir = root / "handoff"
    if not handoff_dir.is_dir():
        return JSONResponse({"error": "No handoff directory"}, status_code=404)

    candidates: list[Path] = []
    try:
        for candidate in handoff_dir.glob("*.md"):
            if not candidate.is_file():
                continue
            candidates.append(candidate)
    except OSError:
        return JSONResponse({"error": "Cannot read handoff directory"}, status_code=500)
    if not candidates:
        return JSONResponse({"error": "No handoff document found"}, status_code=404)

    newest = max(candidates, key=lambda p: (p.stat().st_mtime, p.name))
    try:
        raw = newest.read_bytes()
    except OSError:
        return JSONResponse({"error": "Cannot read handoff document"}, status_code=500)

    return JSONResponse(
        {
            "path": str(newest.relative_to(root)),
            "name": newest.name,
            "content": _decode_text(raw),
        }
    )


# ---------------------------------------------------------------------------
# Recent changes (files modified after a unix timestamp)
# ---------------------------------------------------------------------------

# Polling clients hit this endpoint every few seconds; caching the walk for a
# short window keeps repeated requests from rescanning the whole project tree.
_CHANGES_CACHE_TTL = 2.0  # seconds
_CHANGES_LIMIT = 100

_changes_cache_lock = threading.Lock()
# (cached_at_wall_clock, root_path_string, scanned_entries)
_changes_cache: tuple[float, str, list[dict[str, Any]]] | None = None


def _scan_recent_files(root: Path) -> list[dict[str, Any]]:
    """Walk the project root and collect every tracked file's stat info.

    Uses the same skip lists as the tree endpoint so hidden / dependency
    directories never reach the wire. Entries are returned unsorted; callers
    sort by mtime after filtering.
    """
    found: list[dict[str, Any]] = []
    root_str = str(root)
    for dirpath, dirnames, filenames in os.walk(root_str):
        # Prune in-place so os.walk never descends into skipped directories.
        dirnames[:] = [d for d in dirnames if d not in _DEFAULT_SKIP_DIRS]
        for name in filenames:
            if name in _DEFAULT_SKIP_FILES:
                continue
            full = Path(dirpath) / name
            try:
                stat = full.stat()
            except OSError:
                continue
            found.append(
                {
                    "path": str(full.relative_to(root)),
                    "mtime": stat.st_mtime,
                    "size": stat.st_size,
                }
            )
    return found


def _recent_files_cached(root: Path) -> list[dict[str, Any]]:
    """Return the scanned file list for ``root``, cached for a short TTL."""
    global _changes_cache
    now = time.time()
    root_str = str(root)
    with _changes_cache_lock:
        if _changes_cache is not None:
            cached_at, cached_root, entries = _changes_cache
            if cached_root == root_str and now - cached_at < _CHANGES_CACHE_TTL:
                return entries
    entries = _scan_recent_files(root)
    with _changes_cache_lock:
        _changes_cache = (now, root_str, entries)
    return entries


async def api_ide_changes(request: Request) -> JSONResponse:
    """List project files modified after ``since`` (unix seconds).

    Query param ``since`` is a unix timestamp (omitted means "everything").
    Files whose mtime is greater are returned newest-first, capped at
    :data:`_CHANGES_LIMIT` entries. ``serverTime`` (the gateway's current
    unix time) lets clients use it as the next ``since`` and stay immune to
    client/server clock skew.
    """
    root = resolve_project_root()
    raw_since = (request.query_params.get("since") or "").strip()
    try:
        since = float(raw_since) if raw_since else 0.0
    except ValueError:
        return JSONResponse({"error": "since must be a unix timestamp"}, status_code=400)

    scanned = _recent_files_cached(root)
    changed = [entry for entry in scanned if entry["mtime"] > since]
    changed.sort(key=lambda entry: entry["mtime"], reverse=True)
    return JSONResponse(
        {"files": changed[:_CHANGES_LIMIT], "serverTime": time.time()}
    )


# ---------------------------------------------------------------------------
# File diff (AI-change marks) — project-wide snapshot baseline
# ---------------------------------------------------------------------------

# There is no git dependency here, so "what the AI changed" is computed against
# a one-time in-memory snapshot of every text file in the project. The snapshot
# is taken lazily the first time /api/ide/diff is called (after the gateway
# starts); files edited after that moment show up as green (new) / red
# (modified) lines in the code-interpreter viewer. Files created after the
# snapshot are treated as entirely new.
_DIFF_SNAPSHOT_MAX_FILES = 4000

_diff_lock = threading.Lock()
# (root_path_string, snapshot_taken_at, path -> baseline lines); None until use.
_diff_snapshot: tuple[str, float, dict[str, list[str]]] | None = None


def _ensure_diff_snapshot(root: Path) -> None:
    """Take a one-time content snapshot of the project as the diff baseline."""
    global _diff_snapshot
    root_str = str(root)
    with _diff_lock:
        if _diff_snapshot is not None and _diff_snapshot[0] == root_str:
            return

    taken_at = time.time()
    baselines: dict[str, list[str]] = {}
    count = 0
    for dirpath, dirnames, filenames in os.walk(root_str):
        dirnames[:] = [d for d in dirnames if d not in _DEFAULT_SKIP_DIRS]
        for name in filenames:
            if name in _DEFAULT_SKIP_FILES:
                continue
            full = Path(dirpath) / name
            try:
                if full.stat().st_size > _MAX_FILE_BYTES:
                    continue
            except OSError:
                continue
            if _is_binary_name(full):
                continue
            try:
                raw = full.read_bytes()
            except OSError:
                continue
            if b"\x00" in raw[:4096]:
                continue
            baselines[str(full.relative_to(root))] = _decode_text(raw).splitlines()
            count += 1
            if count >= _DIFF_SNAPSHOT_MAX_FILES:
                break
        if count >= _DIFF_SNAPSHOT_MAX_FILES:
            break

    with _diff_lock:
        _diff_snapshot = (root_str, taken_at, baselines)


async def api_ide_diff(request: Request) -> JSONResponse:
    """Return per-line diff marks for a file vs the project's baseline.

    Query param ``path`` is a relative file path. The response carries the
    current file's lines classified as ``context`` / ``add`` (green) /
    ``mod`` (red), plus a summary counting added / modified / removed lines.
    """
    root = resolve_project_root()
    rel = (request.query_params.get("path") or "").strip()
    if not rel:
        return JSONResponse({"error": "Missing path"}, status_code=400)
    target = _safe_resolve(root, rel)
    if target is None:
        return JSONResponse({"error": "Path escapes the project root"}, status_code=400)
    if not target.is_file():
        return JSONResponse({"error": "Not a file"}, status_code=404)

    try:
        raw = target.read_bytes()
    except OSError:
        return JSONResponse({"error": "Cannot read file"}, status_code=500)
    current = _decode_text(raw).splitlines()

    _ensure_diff_snapshot(root)
    with _diff_lock:
        _taken_at, baselines = _diff_snapshot[1], _diff_snapshot[2]
        baseline = baselines.get(rel)

    if baseline is None:
        try:
            mtime = target.stat().st_mtime
        except OSError:
            mtime = 0.0
        if mtime < _taken_at:
            # The file already existed when the snapshot ran but was not
            # captured (over the per-file size cap or beyond the file-count
            # limit). Baseline it on first access instead of flagging every
            # line as new.
            baseline = current
            with _diff_lock:
                baselines.setdefault(rel, current)
        else:
            # Created after the snapshot: treat every line as added.
            baseline = []

    added = modified = removed = 0
    entries: list[dict[str, Any]] = []
    matcher = difflib.SequenceMatcher(None, baseline or [], current, autojunk=False)
    for tag, _i1, _i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            for line in current[j1:j2]:
                entries.append({"type": "context", "line": line})
        elif tag == "replace":
            modified += j2 - j1
            for line in current[j1:j2]:
                entries.append({"type": "mod", "line": line})
        elif tag == "insert":
            added += j2 - j1
            for line in current[j1:j2]:
                entries.append({"type": "add", "line": line})
        elif tag == "delete":
            removed += _i2 - _i1

    return JSONResponse(
        {
            "path": rel,
            "has_changes": added > 0 or modified > 0 or removed > 0,
            "entries": entries,
            "summary": {"added": added, "modified": modified, "removed": removed},
        }
    )


# ---------------------------------------------------------------------------
# Mutating handlers (create / rename / delete)
# ---------------------------------------------------------------------------

# A single entry name (never a path): separators and Windows drive prefixes
# are rejected so ``name`` can never smuggle a traversal or an absolute path.
_INVALID_NAME_CHARS = frozenset({"/", "\\", "\x00"})


def _validate_entry_name(name: str) -> str | None:
    """Return an error message for an invalid entry name, else None."""
    if not name or name in {".", ".."}:
        return "Invalid entry name"
    if any(ch in _INVALID_NAME_CHARS for ch in name):
        return "Name must not contain path separators"
    if os.path.isabs(name) or Path(name).drive:
        return "Name must not be an absolute path"
    return None


async def _ide_json_body(request: Request) -> dict[str, Any] | None:
    """Parse the request's JSON body; None when it is not a JSON object."""
    try:
        body = await request.json()
    except Exception:
        return None
    return body if isinstance(body, dict) else None


def _resolve_inside(root: Path, parent: Path, name: str) -> Path | None:
    """Join ``parent`` / ``name`` and return it only when inside ``root``."""
    candidate = (parent / name).resolve()
    try:
        candidate.relative_to(root)
    except ValueError:
        return None
    return candidate


async def api_ide_create(request: Request) -> JSONResponse:
    """Create an empty file or a directory inside the project root.

    JSON body: ``{"path": "<relative parent dir>", "name": "<entry name>",
    "type": "file" | "dir"}``. ``path`` omitted or empty means the project
    root. The parent must already exist; the entry itself must not.
    """
    root = resolve_project_root()
    body = await _ide_json_body(request)
    if body is None:
        return JSONResponse({"error": "Invalid JSON body"}, status_code=400)
    parent_rel = str(body.get("path") or "").strip()
    name = str(body.get("name") or "").strip()
    kind = str(body.get("type") or "").strip()
    if kind not in {"file", "dir"}:
        return JSONResponse({"error": "type must be 'file' or 'dir'"}, status_code=400)
    name_error = _validate_entry_name(name)
    if name_error:
        return JSONResponse({"error": name_error}, status_code=400)
    parent = _safe_resolve(root, parent_rel)
    if parent is None:
        return JSONResponse({"error": "Path escapes the project root"}, status_code=400)
    if not parent.is_dir():
        return JSONResponse({"error": "Not a directory"}, status_code=400)
    target = _resolve_inside(root, parent, name)
    if target is None:
        return JSONResponse({"error": "Path escapes the project root"}, status_code=400)
    if target.exists():
        return JSONResponse({"error": "Already exists"}, status_code=409)
    try:
        if kind == "dir":
            target.mkdir()
        else:
            with target.open("x"):
                pass
    except OSError:
        return JSONResponse({"error": "Cannot create entry"}, status_code=500)
    return JSONResponse(
        {"path": str(target.relative_to(root)), "name": target.name, "type": kind}
    )


async def api_ide_rename(request: Request) -> JSONResponse:
    """Rename a file or directory (within its parent, inside the root).

    JSON body: ``{"path": "<relative entry path>", "name": "<new name>"}``.
    """
    root = resolve_project_root()
    body = await _ide_json_body(request)
    if body is None:
        return JSONResponse({"error": "Invalid JSON body"}, status_code=400)
    rel = str(body.get("path") or "").strip()
    name = str(body.get("name") or "").strip()
    if not rel:
        return JSONResponse({"error": "Missing path"}, status_code=400)
    name_error = _validate_entry_name(name)
    if name_error:
        return JSONResponse({"error": name_error}, status_code=400)
    target = _safe_resolve(root, rel)
    if target is None:
        return JSONResponse({"error": "Path escapes the project root"}, status_code=400)
    if target == root:
        return JSONResponse({"error": "Cannot rename the project root"}, status_code=400)
    if not target.exists():
        return JSONResponse({"error": "No such entry"}, status_code=404)
    renamed = _resolve_inside(root, target.parent, name)
    if renamed is None:
        return JSONResponse({"error": "Path escapes the project root"}, status_code=400)
    if renamed != target and renamed.exists():
        return JSONResponse({"error": "Already exists"}, status_code=409)
    try:
        target.rename(renamed)
    except OSError:
        return JSONResponse({"error": "Cannot rename entry"}, status_code=500)
    return JSONResponse(
        {
            "path": str(renamed.relative_to(root)),
            "name": renamed.name,
            "previousPath": rel,
        }
    )


async def api_ide_delete(request: Request) -> JSONResponse:
    """Delete a file, or a directory tree, inside the project root.

    JSON body: ``{"path": "<relative entry path>"}``. The project root itself
    can never be deleted.
    """
    root = resolve_project_root()
    body = await _ide_json_body(request)
    if body is None:
        return JSONResponse({"error": "Invalid JSON body"}, status_code=400)
    rel = str(body.get("path") or "").strip()
    if not rel:
        return JSONResponse({"error": "Missing path"}, status_code=400)
    target = _safe_resolve(root, rel)
    if target is None:
        return JSONResponse({"error": "Path escapes the project root"}, status_code=400)
    if target == root:
        return JSONResponse({"error": "Cannot delete the project root"}, status_code=400)
    if not target.exists():
        return JSONResponse({"error": "No such entry"}, status_code=404)
    try:
        if target.is_dir():
            shutil.rmtree(target)
        else:
            target.unlink()
    except OSError:
        return JSONResponse({"error": "Cannot delete entry"}, status_code=500)
    return JSONResponse({"path": rel, "deleted": True})
