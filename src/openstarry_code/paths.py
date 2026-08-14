"""OpenStarry Code state-root resolution.

Single source of truth for the on-disk state root. Most users keep the
legacy single-instance home, while operators can opt into explicit
multi-profile homes for side-by-side agents.

Precedence:
1. ``OPENSTARRY_CODE_STATE_DIR`` environment variable (expanded for ``~``/``$HOME``)
2. ``OPENSTARRY_CODE_HOME`` + ``OPENSTARRY_CODE_PROFILE`` profile mode
3. ``$HOME/.openstarry-code``
"""

from __future__ import annotations

import os
import re
from pathlib import Path

_STATE_DIR_ENV = "OPENSTARRY_CODE_STATE_DIR"
_PROFILES_ROOT_ENV = "OPENSTARRY_CODE_HOME"
_PROFILE_ENV = "OPENSTARRY_CODE_PROFILE"
_DEFAULT_PROFILE = "default"
_PROFILE_RE = re.compile(r"^[a-z0-9][a-z0-9_-]{0,63}$")


def _home_dir() -> Path:
    home = os.environ.get("HOME", "").strip()
    if home:
        return Path(home).expanduser()
    return Path.home()


def _expand_user(path: str) -> Path:
    if path == "~":
        return _home_dir()
    if path.startswith("~/") or path.startswith("~\\"):
        return _home_dir() / path[2:]
    return Path(path).expanduser()


def native_io_path(path: str | Path) -> Path:
    """Return an internal path spelling that bypasses Windows ``MAX_PATH``.

    Callers must keep their public/configured path logical and use this value
    only at the filesystem or SQLite boundary.
    """

    logical = Path(path).expanduser()
    if os.name != "nt":
        return logical
    absolute = os.path.abspath(os.fspath(logical))
    if absolute.startswith("\\\\?\\"):
        return Path(absolute)
    if absolute.startswith("\\\\"):
        return Path(f"\\\\?\\UNC\\{absolute[2:]}")
    return Path(f"\\\\?\\{absolute}")


def is_valid_profile_name(name: str) -> bool:
    """Return True when ``name`` is safe to use as one profile path segment."""
    return bool(_PROFILE_RE.fullmatch(name))


def default_profile_name() -> str:
    """Return the selected profile name, defaulting to ``default``."""
    profile = os.environ.get(_PROFILE_ENV, "").strip()
    return profile or _DEFAULT_PROFILE


def default_profiles_root() -> Path:
    """Return the root directory that contains explicit profile homes."""
    root = os.environ.get(_PROFILES_ROOT_ENV, "").strip()
    if root:
        return _expand_user(root)
    return _home_dir() / ".openstarry-code" / "profiles"


def profile_home(profile: str | None = None, *, root: Path | None = None) -> Path:
    """Return the home directory for ``profile`` under the profiles root."""
    name = (profile or default_profile_name()).strip()
    if not is_valid_profile_name(name):
        raise ValueError(
            "Invalid OpenStarry Code profile name. Use lowercase letters, digits, "
            "hyphens, or underscores; start with a letter or digit; max length 64."
        )
    return (root or default_profiles_root()) / name


def _profile_mode_requested() -> bool:
    return bool(
        os.environ.get(_PROFILES_ROOT_ENV, "").strip()
        or os.environ.get(_PROFILE_ENV, "").strip()
    )


def default_opensquilla_home() -> Path:
    """Return the OpenStarry Code state root as an absolute :class:`~pathlib.Path`.

    Honors ``OPENSTARRY_CODE_STATE_DIR`` (trimmed, ``~`` expanded). Explicit profile
    mode uses ``OPENSTARRY_CODE_HOME/<profile>``; the default remains the legacy
    ``$HOME/.openstarry-code`` when no profile env vars are set.
    """
    override = os.environ.get(_STATE_DIR_ENV, "").strip()
    if override:
        return _expand_user(override)
    if _profile_mode_requested():
        return profile_home()
    return _home_dir() / ".openstarry-code"


def state_dir(*parts: str) -> Path:
    """Return a path under OpenStarry Code's state directory.

    ``default_opensquilla_home()`` is the user-visible OpenStarry Code home. Runtime state
    lives in the ``state`` subdirectory below it, matching the gateway config
    default and keeping prompt history out of the config/env root.
    """
    return default_opensquilla_home() / "state" / Path(*parts)


def media_root_from_config(config: object | None = None) -> Path:
    """Return the stable attachment/artifact media root.

    Explicit ``attachments.media_root`` wins. Otherwise derive from the configured
    OpenStarry Code home instead of process cwd so artifact links keep working when the
    gateway is launched from a long or transient source/worktree path.
    """
    attachments_cfg = getattr(config, "attachments", None)
    media_root = getattr(attachments_cfg, "media_root", None)
    if isinstance(media_root, str) and media_root.strip():
        return _expand_user(media_root.strip())

    state_root = getattr(config, "state_dir", None)
    if isinstance(state_root, str) and state_root.strip():
        state_path = _expand_user(state_root.strip())
        # Only use the sibling `<home>/media` layout when state_dir follows the
        # default `<home>/state` shape. A relocated/custom state dir must keep
        # its media inside it, not escape to the parent (which could land media
        # outside the intended state tree entirely).
        if state_path.name == "state":
            return state_path.parent / "media"
        return state_path / "media"

    config_path = getattr(config, "config_path", None)
    if isinstance(config_path, str) and config_path.strip():
        return _expand_user(config_path.strip()).parent / "media"

    return default_opensquilla_home() / "media"
