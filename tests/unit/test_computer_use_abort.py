"""Unit tests for the computer-use Esc-abort code paths.

These tests never touch the real tkinter overlay (a no-op stand-in is
injected) and never emit real input: with the abort event pre-set, every
controller action must raise :class:`ComputerUseAbortedError` *before* its
first pyautogui call. The global keyboard hook is exercised only for its
install/uninstall lifecycle, not for synthetic key events (which the task
notes cannot be automated reliably).
"""

from __future__ import annotations

import base64
import json
import sys
import threading
import time

import pytest

from openstarry_code.computer_use.controller import ComputerUseController
from openstarry_code.computer_use.cursor_overlay import _CURSORS_DIR, _load_cur_rgba
from openstarry_code.computer_use.session import (
    ComputerUseAbortedError,
    ComputerUseSession,
    EscapeAbortHook,
)


class _FakeOverlay:
    """Records overlay calls; never touches tkinter."""

    def __init__(self) -> None:
        self.calls: list[tuple] = []

    def show(self, x, y, state="idle"):  # noqa: ANN001
        self.calls.append(("show", x, y, state))

    def move(self, x, y):  # noqa: ANN001
        self.calls.append(("move", x, y))

    def hide(self) -> None:
        self.calls.append(("hide",))

    def set_busy(self, busy) -> None:  # noqa: ANN001
        self.calls.append(("set_busy", busy))

    def session_start(self, theme="dark", accent=None) -> None:  # noqa: ANN001
        self.calls.append(("session_start", theme, accent))

    def session_end(self) -> None:
        self.calls.append(("session_end",))

    def close(self) -> None:
        self.calls.append(("close",))

    def is_available(self) -> bool:
        return True


def _make_controller(tmp_path, aborted: bool):
    session = ComputerUseSession(state_dir=tmp_path)
    session.start(theme="light")
    if aborted:
        session.abort_event.set()
    controller = ComputerUseController(overlay=_FakeOverlay(), session=session)
    return controller, session


def _foreground_window_or_skip() -> None:
    """Virtual/physical typing needs a foreground window to target."""
    if sys.platform != "win32":
        pytest.skip("typing paths are Windows-only")
    import ctypes

    if not ctypes.windll.user32.GetForegroundWindow():
        pytest.skip("no foreground window available")


# ---------------------------------------------------------------------------
# Abort inside every step loop (abort_event pre-set → raise before any input)
# ---------------------------------------------------------------------------


def test_move_aborts_before_any_motion(tmp_path) -> None:
    controller, _ = _make_controller(tmp_path, aborted=True)
    with pytest.raises(ComputerUseAbortedError):
        controller.move(400, 300)


def test_left_click_aborts_before_press(tmp_path) -> None:
    controller, _ = _make_controller(tmp_path, aborted=True)
    with pytest.raises(ComputerUseAbortedError):
        controller.left_click(400, 300)


def test_drag_aborts_before_mouse_down(tmp_path) -> None:
    controller, _ = _make_controller(tmp_path, aborted=True)
    with pytest.raises(ComputerUseAbortedError):
        controller.drag(100, 100, 500, 500)


def test_type_text_virtual_aborts_before_first_char(tmp_path) -> None:
    _foreground_window_or_skip()
    controller, _ = _make_controller(tmp_path, aborted=True)
    with pytest.raises(ComputerUseAbortedError):
        controller.type_text("hello", virtual=True)


def test_type_text_physical_aborts_before_first_char(tmp_path) -> None:
    _foreground_window_or_skip()
    controller, _ = _make_controller(tmp_path, aborted=True)
    with pytest.raises(ComputerUseAbortedError):
        controller.type_text("hello")


def test_press_key_aborts(tmp_path) -> None:
    controller, _ = _make_controller(tmp_path, aborted=True)
    with pytest.raises(ComputerUseAbortedError):
        controller.press_key("enter")


def test_scroll_aborts(tmp_path) -> None:
    controller, _ = _make_controller(tmp_path, aborted=True)
    with pytest.raises(ComputerUseAbortedError):
        controller.scroll(5)


def test_screenshot_aborts_before_capture(tmp_path) -> None:
    controller, _ = _make_controller(tmp_path, aborted=True)
    with pytest.raises(ComputerUseAbortedError):
        controller.screenshot()


def test_abort_tears_visuals_down(tmp_path) -> None:
    """_check_abort must order the overlay session_end before raising."""
    controller, _ = _make_controller(tmp_path, aborted=True)
    overlay = controller._overlay
    with pytest.raises(ComputerUseAbortedError):
        controller.move(400, 300)
    assert ("session_end",) in overlay.calls


# ---------------------------------------------------------------------------
# Session state file
# ---------------------------------------------------------------------------


def test_state_file_lifecycle(tmp_path) -> None:
    session = ComputerUseSession(state_dir=tmp_path)
    session.start(theme="light", accent="#5b8cff")
    payload = json.loads((tmp_path / "state.json").read_text(encoding="utf-8"))
    assert payload["active"] is True
    assert payload["aborted"] is False
    assert payload["theme"] == "light"
    assert payload["accent"] == "#5b8cff"

    session.record_action("move", x=10, y=20)
    session.record_cursor(10, 20, "idle")
    session.record_screenshot(b"\x89PNG-fake")
    payload = json.loads((tmp_path / "state.json").read_text(encoding="utf-8"))
    assert payload["last_action"]["name"] == "move"
    assert payload["last_action"]["x"] == 10
    assert payload["cursor"] == {"x": 10, "y": 20, "state": "idle"}
    assert payload["last_screenshot"] == base64.b64encode(b"\x89PNG-fake").decode("ascii")

    session.mark_aborted()
    payload = json.loads((tmp_path / "state.json").read_text(encoding="utf-8"))
    assert payload["active"] is False
    assert payload["aborted"] is True

    session.end()
    payload = json.loads((tmp_path / "state.json").read_text(encoding="utf-8"))
    assert payload["active"] is False


def test_session_start_clears_abort(tmp_path) -> None:
    session = ComputerUseSession(state_dir=tmp_path)
    session.start()
    session.abort_event.set()
    session.start(theme="dark")
    assert not session.abort_event.is_set()
    payload = json.loads((tmp_path / "state.json").read_text(encoding="utf-8"))
    assert payload["active"] is True and payload["aborted"] is False


# ---------------------------------------------------------------------------
# Global Esc hook lifecycle (no synthetic key events)
# ---------------------------------------------------------------------------


@pytest.mark.skipif(sys.platform != "win32", reason="Windows-only hook")
def test_esc_hook_install_uninstall() -> None:
    hook = EscapeAbortHook(threading.Event())
    hook.start()
    deadline = time.monotonic() + 2.0
    while not hook.running and time.monotonic() < deadline:
        time.sleep(0.02)
    assert hook.running, "hook pump thread should be alive"
    assert hook._hook_handle, "SetWindowsHookExW must succeed (handle != 0)"
    hook.stop()
    assert not hook.running
    assert hook._hook_handle == 0, "hook must be unhooked after stop"


@pytest.mark.skipif(sys.platform != "win32", reason="Windows-only hook")
def test_real_esc_keypress_trips_abort_event() -> None:
    """End-to-end chain: install hook → real Esc keypress → abort event.

    SendInput-injected keys traverse low-level keyboard hooks, so a
    synthetic Esc exercises the full install → callback → event path. The
    keypress goes to whatever window has focus; Esc is benign there.
    """
    import pyautogui

    event = threading.Event()
    hook = EscapeAbortHook(event)
    hook.start()
    try:
        deadline = time.monotonic() + 2.0
        while not hook._hook_handle and time.monotonic() < deadline:
            time.sleep(0.02)
        assert hook._hook_handle, "hook must be installed before pressing Esc"
        pyautogui.press("esc")
        assert event.wait(timeout=3.0), "Esc did not trip the abort event"
    finally:
        hook.stop()


# ---------------------------------------------------------------------------
# Cursor asset parsing (the overlay's .cur decoder)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("theme", ["light", "dark"])
@pytest.mark.parametrize("kind", ["pointer", "link"])
def test_cursor_cur_parses_with_alpha(theme: str, kind: str) -> None:
    image = _load_cur_rgba(_CURSORS_DIR / theme / f"{kind}.cur")
    assert image is not None
    assert image.size == (32, 32)
    assert image.mode == "RGBA"
    low, high = image.getchannel("A").getextrema()
    assert high > 0, "cursor artwork must contain visible pixels"
    assert low < 255, "cursor artwork must contain transparent pixels"
