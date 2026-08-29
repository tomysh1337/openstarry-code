"""Session state, Esc-abort plumbing and global keyboard hook.

Three concerns shared by the controller and the MCP server live here:

* :class:`ComputerUseAbortedError` — raised by the controller the moment the
  user presses Esc, so ``tools/call`` answers with ``isError``;
* :class:`ComputerUseSession` — the abort :class:`threading.Event` plus the
  atomically-written ``%USERPROFILE%\\.openstarry\\computer_use\\state.json``
  snapshot the WebUI preview panel polls;
* :class:`EscapeAbortHook` — a ``WH_KEYBOARD_LL`` global low-level keyboard
  hook on a dedicated message-pump thread that trips the abort event the
  instant Esc goes down, no matter which window has focus.

The hook is Windows-only; on other platforms it is a no-op and the abort
event can still be set programmatically (which is what the unit tests do).
"""

from __future__ import annotations

import base64
import json
import os
import sys
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import structlog

log = structlog.get_logger(__name__)


class ComputerUseAbortedError(RuntimeError):
    """Raised when the user pressed Esc to abort the running actions."""


def default_state_dir() -> Path:
    """``%USERPROFILE%\\.openstarry\\computer_use`` — state.json lives here."""
    return Path.home() / ".openstarry" / "computer_use"


def default_state_path() -> Path:
    return default_state_dir() / "state.json"


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class ComputerUseSession:
    """Abort flag + persisted session snapshot shared across threads.

    In-action cursor updates only touch memory (the humanized move loop
    emits a step every ~10 ms); the state file is rewritten by
    :meth:`flush`, which the controller calls once per completed action and
    the MCP server calls on session lifecycle changes.
    """

    def __init__(self, state_dir: str | Path | None = None) -> None:
        self._dir = Path(state_dir) if state_dir is not None else default_state_dir()
        self._path = self._dir / "state.json"
        self._lock = threading.Lock()
        self.abort_event = threading.Event()
        self._active = False
        self._aborted = False
        self._theme = "dark"
        self._accent: str | None = None
        self._cursor: dict[str, Any] = {"x": 0, "y": 0, "state": "idle"}
        self._last_action: dict[str, Any] | None = None
        self._last_screenshot: str | None = None

    # -- lifecycle -----------------------------------------------------------

    def start(self, theme: str = "dark", accent: str | None = None) -> None:
        """Begin a session: fresh state, cleared abort, persisted immediately."""
        with self._lock:
            self._active = True
            self._aborted = False
            self._theme = theme
            self._accent = accent
            self._last_screenshot = None
        self.abort_event.clear()
        self.flush()

    def end(self) -> None:
        with self._lock:
            self._active = False
        self.flush()

    def mark_aborted(self) -> None:
        """Persist that Esc was pressed; the session counts as finished."""
        with self._lock:
            self._active = False
            self._aborted = True
        self.flush()

    # -- in-action recording (memory only) ------------------------------------

    def record_cursor(self, x: float, y: float, state: str) -> None:
        with self._lock:
            self._cursor = {"x": int(x), "y": int(y), "state": str(state)}

    def record_action(self, name: str, **details: Any) -> None:
        with self._lock:
            self._last_action = {"name": name, **details, "at": _utcnow()}
        self.flush()

    def record_screenshot(self, png: bytes) -> None:
        """Keep the most recent screenshot (base64 PNG) for the WebUI panel."""
        encoded = base64.b64encode(png).decode("ascii")
        with self._lock:
            self._last_screenshot = encoded
        self.flush()

    # -- persistence -----------------------------------------------------------

    def flush(self) -> None:
        """Atomically rewrite ``state.json`` (tmp file + ``os.replace``)."""
        with self._lock:
            payload = {
                "active": self._active,
                "theme": self._theme,
                "accent": self._accent,
                "cursor": dict(self._cursor),
                "last_action": dict(self._last_action) if self._last_action else None,
                "last_screenshot": self._last_screenshot,
                "aborted": self._aborted,
                "updated_at": _utcnow(),
            }
        try:
            self._dir.mkdir(parents=True, exist_ok=True)
            tmp = self._path.with_suffix(".json.tmp")
            tmp.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
            os.replace(tmp, self._path)
        except OSError as exc:
            log.warning("computer_use.state_write_failed", error=str(exc))

    @property
    def state_path(self) -> Path:
        return self._path


# ---------------------------------------------------------------------------
# Global Esc hook (Windows-only)
# ---------------------------------------------------------------------------

if sys.platform == "win32":
    import ctypes
    from ctypes import wintypes

    _WH_KEYBOARD_LL = 13
    _WM_KEYDOWN = 0x0100
    _WM_SYSKEYDOWN = 0x0104
    _VK_ESCAPE = 0x1B
    _WM_QUIT = 0x0012

    _LRESULT = ctypes.c_ssize_t
    _HOOKPROC = ctypes.WINFUNCTYPE(_LRESULT, ctypes.c_int, wintypes.WPARAM, wintypes.LPARAM)

    class _KBDLLHOOKSTRUCT(ctypes.Structure):
        _fields_ = [
            ("vkCode", wintypes.DWORD),
            ("scanCode", wintypes.DWORD),
            ("flags", wintypes.DWORD),
            ("time", wintypes.DWORD),
            ("dwExtraInfo", ctypes.POINTER(wintypes.ULONG)),
        ]


class EscapeAbortHook:
    """Global low-level keyboard hook that trips ``abort_event`` on Esc.

    ``WH_KEYBOARD_LL`` callbacks must be serviced by a thread that pumps
    messages, so :meth:`start` spawns a dedicated daemon thread that installs
    the hook, runs a ``GetMessageW`` loop and unhooks itself on ``WM_QUIT``.
    The callback does nothing but set the event — real work happens on the
    abort watcher thread, never inside the hook.
    """

    def __init__(self, abort_event: threading.Event) -> None:
        self._abort_event = abort_event
        self._thread: threading.Thread | None = None
        self._ready = threading.Event()
        self._thread_id = 0
        self._hook_handle = 0
        # Keep a reference so the native callback is never garbage collected
        # while the hook is installed.
        self._proc = _HOOKPROC(self._on_key) if sys.platform == "win32" else None

    @property
    def running(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    def start(self) -> None:
        """Install the hook on a fresh pump thread (no-op off Windows)."""
        if sys.platform != "win32" or self.running:
            return
        self._ready.clear()
        self._thread = threading.Thread(
            target=self._run, name="openstarry-esc-abort-hook", daemon=True
        )
        self._thread.start()
        if not self._ready.wait(timeout=2.0):
            log.warning("computer_use.esc_hook_start_timeout")

    def stop(self) -> None:
        """Post ``WM_QUIT`` to the pump thread; the hook unhooks itself."""
        thread = self._thread
        if thread is None:
            return
        if sys.platform == "win32" and self._thread_id:
            try:
                ctypes.windll.user32.PostThreadMessageW(self._thread_id, _WM_QUIT, 0, 0)
            except Exception:  # pragma: no cover - thread already gone
                pass
        thread.join(timeout=2.0)
        self._thread = None
        self._thread_id = 0

    # -- pump thread -----------------------------------------------------------

    def _run(self) -> None:
        import ctypes

        user32 = ctypes.windll.user32
        kernel32 = ctypes.windll.kernel32
        self._thread_id = kernel32.GetCurrentThreadId()
        # hMod=None is the standard (and required-in-practice) form for
        # low-level hooks; passing GetModuleHandleW(None) fails with
        # ERROR_MOD_NOT_FOUND under some launchers. Explicit argtypes keep
        # the HANDLE values intact on 64-bit Python.
        user32.SetWindowsHookExW.restype = ctypes.c_void_p
        user32.SetWindowsHookExW.argtypes = [
            ctypes.c_int,
            _HOOKPROC,
            ctypes.c_void_p,
            wintypes.DWORD,
        ]
        user32.UnhookWindowsHookEx.restype = wintypes.BOOL
        user32.UnhookWindowsHookEx.argtypes = [ctypes.c_void_p]
        # Without explicit types ctypes marshals the 64-bit LPARAM as c_int
        # inside the hook callback's CallNextHookEx call and raises
        # OverflowError, silently breaking the hook chain for other apps.
        user32.CallNextHookEx.restype = _LRESULT
        user32.CallNextHookEx.argtypes = [
            ctypes.c_void_p,
            ctypes.c_int,
            wintypes.WPARAM,
            wintypes.LPARAM,
        ]
        hook = user32.SetWindowsHookExW(_WH_KEYBOARD_LL, self._proc, None, 0)
        self._hook_handle = hook
        self._ready.set()
        if not hook:
            log.warning("computer_use.esc_hook_install_failed")
            return
        msg = wintypes.MSG()
        try:
            while user32.GetMessageW(ctypes.byref(msg), None, 0, 0) > 0:
                user32.TranslateMessage(ctypes.byref(msg))
                user32.DispatchMessageW(ctypes.byref(msg))
        finally:
            self._unhook()

    def _unhook(self) -> None:
        if self._hook_handle:
            try:
                ctypes.windll.user32.UnhookWindowsHookEx(ctypes.c_void_p(self._hook_handle))
            except Exception:  # pragma: no cover
                pass
            self._hook_handle = 0

    def _on_key(self, n_code: int, w_param: int, l_param: int) -> int:
        import ctypes

        try:
            if n_code == 0 and w_param in (_WM_KEYDOWN, _WM_SYSKEYDOWN):
                info = ctypes.cast(
                    l_param, ctypes.POINTER(_KBDLLHOOKSTRUCT)
                ).contents
                if info.vkCode == _VK_ESCAPE:
                    self._abort_event.set()
        except Exception:  # never raise inside a keyboard hook
            pass
        return ctypes.windll.user32.CallNextHookEx(None, n_code, w_param, l_param)
