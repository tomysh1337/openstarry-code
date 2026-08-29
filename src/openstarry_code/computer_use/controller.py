"""Computer-use controller — humanized keyboard/mouse automation.

The AI drives the machine through pyautogui, but raw pyautogui motion is
robotic: instant pointer teleportation, constant-speed drags, keystrokes in
perfect rhythm. Every action here is humanized instead:

* pointer travel follows a randomized quadratic Bézier curve with an
  easeOutQuad tween, split into many small ``moveTo`` steps whose inter-step
  sleeps are jittered ±20% around a human cadence;
* clicks pause a random 80–150 ms after arrival before pressing;
* typing streams ASCII characters with 40–120 ms gaps; text ``typewrite``
  cannot emit (CJK and other non-ASCII) is routed through the clipboard and
  pasted, because ``typewrite`` silently drops such characters.

Every action writes a structlog audit record and refreshes the persisted
session snapshot (``%USERPROFILE%\\.openstarry\\computer_use\\state.json``,
see :mod:`openstarry_code.computer_use.session`). A single re-entrant lock
serializes concurrent tool calls. A tkinter visual overlay (dedicated thread,
see :mod:`openstarry_code.computer_use.cursor_overlay`) mirrors each action
on screen — real cursor artwork, border glow and a glass banner; when
tkinter is unavailable it silently degrades to no-op.

Every step loop also polls the session's abort event: when the user presses
Esc (global low-level keyboard hook, same module) the action in flight
raises :class:`ComputerUseAbortedError` and the whole visual session tears
down immediately.

Windows DPI: this module must be imported *before* the first screen query, so
process-wide DPI awareness is declared at import time (``SetProcessDpiAwareness(2)``,
falling back to the legacy ``SetProcessDPIAware``); otherwise Windows lies to
pyautogui about the screen size and every coordinate is wrong.
"""

from __future__ import annotations

import contextlib
import io
import math
import random
import sys
import threading
import time

import structlog

if sys.platform == "win32":
    try:
        import ctypes

        ctypes.windll.shcore.SetProcessDpiAwareness(2)
    except Exception:  # older Windows or already set
        try:
            import ctypes

            ctypes.windll.user32.SetProcessDPIAware()
        except Exception:
            pass

try:
    import pyautogui

    pyautogui.FAILSAFE = False  # corner fail-safe would abort scripted actions
    pyautogui.PAUSE = 0.0  # inter-action pacing is handled here, with jitter
except Exception as _exc:  # headless or not installed
    pyautogui = None  # type: ignore[assignment]
    _PYAUTOGUI_IMPORT_ERROR: Exception | None = _exc
else:
    _PYAUTOGUI_IMPORT_ERROR = None

from openstarry_code.computer_use.cursor_overlay import (
    STATE_IDLE,
    STATE_PRESSED,
    CursorOverlay,
)
from openstarry_code.computer_use.session import (
    ComputerUseAbortedError,
    ComputerUseSession,
)

log = structlog.get_logger(__name__)

#: Humanization tunables.
_JITTER = 0.2  # ±20% on every delay
_PRE_CLICK_PAUSE_RANGE = (0.08, 0.15)  # seconds between arrival and press
_TYPE_DELAY_RANGE = (0.04, 0.12)  # seconds between keystrokes
_STEP_PIXELS = 12  # target distance covered by one moveTo step
_MIN_STEPS = 8
_MAX_STEPS = 60


class ComputerUseUnavailableError(RuntimeError):
    """Raised when screen/keyboard control is not possible in this process."""


def _jitter(base: float, spread: float = _JITTER) -> float:
    """Scale ``base`` by a random factor in ``[1-spread, 1+spread]``."""
    return max(0.0, base * (1.0 + random.uniform(-spread, spread)))


def _bezier_points(
    x0: float, y0: float, x1: float, y1: float, steps: int
) -> list[tuple[float, float]]:
    """Sample a randomized quadratic Bézier path with easeOutQuad pacing.

    The control point is offset perpendicular to the travel direction by up to
    25% of the distance (capped), so repeated moves to the same target never
    trace the exact same line. The easing is baked into the curve parameter so
    each ``moveTo`` step itself stays instant.
    """
    distance = math.hypot(x1 - x0, y1 - y0)
    if distance < 1e-6:
        return [(x1, y1)]
    offset = min(120.0, distance * 0.25) * random.uniform(-1.0, 1.0)
    mid_x, mid_y = (x0 + x1) / 2.0, (y0 + y1) / 2.0
    control_x = mid_x - (y1 - y0) / distance * offset
    control_y = mid_y + (x1 - x0) / distance * offset
    points: list[tuple[float, float]] = []
    for step in range(1, steps + 1):
        t = step / steps
        eased = 1.0 - (1.0 - t) ** 2  # easeOutQuad
        u = 1.0 - eased
        x = u * u * x0 + 2.0 * u * eased * control_x + eased * eased * x1
        y = u * u * y0 + 2.0 * u * eased * control_y + eased * eased * y1
        points.append((x, y))
    return points


class ComputerUseController:
    """Thread-safe, humanized screen/keyboard/mouse controller."""

    def __init__(
        self,
        overlay: CursorOverlay | None = None,
        session: ComputerUseSession | None = None,
    ) -> None:
        self._lock = threading.RLock()
        self._overlay = overlay if overlay is not None else CursorOverlay()
        self._session = session if session is not None else ComputerUseSession()

    # ------------------------------------------------------------------
    # Guards / helpers
    # ------------------------------------------------------------------

    def _require_pyautogui(self) -> None:
        if pyautogui is None:
            raise ComputerUseUnavailableError(
                f"pyautogui is unavailable in this process: {_PYAUTOGUI_IMPORT_ERROR}"
            )

    def _check_abort(self) -> None:
        """Raise :class:`ComputerUseAbortedError` once the user hit Esc.

        Called inside every step loop (each Bézier move step, each typed
        character, each drag step, each scroll tick) so an abort lands
        within tens of milliseconds of the key press. Tearing the visual
        session down here — not just in the MCP layer — guarantees the
        banner/glow/cursor disappear even if no further tool call arrives.
        """
        if self._session.abort_event.is_set():
            try:
                self._overlay.session_end()
            except Exception:
                pass
            raise ComputerUseAbortedError("用户按 Esc 中止了电脑使用")

    def _record_cursor(self, x: float, y: float, state: str) -> None:
        """Update the session snapshot's cursor position (memory only)."""
        self._session.record_cursor(x, y, state)

    def _screen_size(self) -> tuple[int, int]:
        self._require_pyautogui()
        size = pyautogui.size()  # type: ignore[union-attr]
        return int(size.width), int(size.height)

    def _clamp(self, x: float, y: float) -> tuple[int, int]:
        """Clamp coordinates to the (primary) screen — no exceptions, no OOB."""
        width, height = self._screen_size()
        return (
            min(max(int(round(x)), 0), width - 1),
            min(max(int(round(y)), 0), height - 1),
        )

    def _step_count(self, distance: float) -> int:
        return max(_MIN_STEPS, min(_MAX_STEPS, int(distance / _STEP_PIXELS)))

    def _move_locked(self, x: int, y: int, duration: float) -> None:
        """Move the pointer along the humanized path. Lock must be held."""
        assert pyautogui is not None
        position = pyautogui.position()
        start_x, start_y = float(position.x), float(position.y)
        distance = math.hypot(x - start_x, y - start_y)
        steps = self._step_count(distance)
        points = _bezier_points(start_x, start_y, float(x), float(y), steps)
        step_delay = (duration if duration > 0 else 0.5) / max(1, len(points))
        self._overlay.show(start_x, start_y, STATE_IDLE)
        self._record_cursor(start_x, start_y, STATE_IDLE)
        for point_x, point_y in points:
            self._check_abort()  # Esc lands within one ~10ms step
            # The ease curve is already baked into the Bézier parameter; the
            # tween argument is kept so a non-zero per-step duration would
            # still ease correctly.
            pyautogui.moveTo(point_x, point_y, duration=0, tween=pyautogui.easeOutQuad)
            self._overlay.move(point_x, point_y)
            self._record_cursor(point_x, point_y, STATE_IDLE)
            time.sleep(_jitter(step_delay))
        self._overlay.move(x, y)
        self._record_cursor(x, y, STATE_IDLE)

    def _audit(self, action: str, elapsed_ms: float, **details: object) -> None:
        log.info("computer_use.action", action=action, elapsed_ms=round(elapsed_ms, 1), **details)

    # ------------------------------------------------------------------
    # Virtual ("second cursor") layer.  Synthetic input necessarily moves
    # the single OS pointer, but in virtual mode we snapshot the user's
    # cursor position before the action and snap it back afterwards, so
    # their physical mouse is never visibly hijacked — the AI's hand lives
    # only in the glowing overlay cursor.
    # ------------------------------------------------------------------

    _pinned_pos: tuple[int, int] | None = None

    def _pin_cursor(self, virtual: bool) -> None:
        if virtual and pyautogui is not None:
            position = pyautogui.position()
            self._pinned_pos = (int(position.x), int(position.y))

    def _release_cursor(self) -> None:
        if self._pinned_pos is not None and pyautogui is not None:
            x, y = self._pinned_pos
            self._pinned_pos = None
            pyautogui.moveTo(x, y, duration=0, _pause=False)

    # ------------------------------------------------------------------
    # Public actions (each acquires the lock)
    # ------------------------------------------------------------------

    def screenshot(self) -> bytes:
        """Capture the (primary) screen and return PNG bytes."""
        self._require_pyautogui()
        self._check_abort()
        with self._lock:
            started = time.monotonic()
            image = pyautogui.screenshot()  # type: ignore[union-attr]
            buffer = io.BytesIO()
            image.save(buffer, format="PNG")
            data = buffer.getvalue()
            width, height = image.size
        self._session.record_screenshot(data)  # for the WebUI preview panel
        self._session.record_action("screenshot", width=width, height=height, bytes=len(data))
        self._audit(
            "screenshot",
            (time.monotonic() - started) * 1000.0,
            width=width,
            height=height,
            bytes=len(data),
        )
        return data

    def move(
        self, x: float, y: float, duration: float = 0.5, virtual: bool = False
    ) -> tuple[int, int]:
        """Glide the pointer to ``(x, y)`` along a humanized Bézier path.

        With ``virtual=True`` the user's cursor snaps back to its original
        position after the glide; only the overlay cursor shows the move.
        """
        self._require_pyautogui()
        with self._lock:
            started = time.monotonic()
            target_x, target_y = self._clamp(x, y)
            self._pin_cursor(virtual)
            try:
                self._move_locked(target_x, target_y, duration)
            finally:
                self._release_cursor()
                self._session.flush()
            elapsed_ms = (time.monotonic() - started) * 1000.0
        self._session.record_action("move", x=target_x, y=target_y, virtual=virtual)
        self._audit(
            "move", elapsed_ms, x=target_x, y=target_y, duration=duration, virtual=virtual
        )
        return target_x, target_y

    def _click(
        self,
        action: str,
        x: float | None,
        y: float | None,
        duration: float,
        *,
        button: str,
        clicks: int,
        interval: float = 0.0,
        virtual: bool = False,
    ) -> tuple[int, int]:
        self._require_pyautogui()
        with self._lock:
            assert pyautogui is not None
            started = time.monotonic()
            self._pin_cursor(virtual)
            try:
                if x is not None and y is not None:
                    target_x, target_y = self._clamp(x, y)
                    self._move_locked(target_x, target_y, duration)
                else:
                    position = pyautogui.position()
                    target_x, target_y = int(position.x), int(position.y)
                # Humans do not press the instant the pointer lands.
                time.sleep(random.uniform(*_PRE_CLICK_PAUSE_RANGE))
                self._check_abort()  # cancel the click if Esc lands mid-pause
                self._overlay.show(target_x, target_y, STATE_PRESSED)
                pyautogui.click(clicks=clicks, interval=interval, button=button)
                self._overlay.show(target_x, target_y, STATE_IDLE)
                self._overlay.hide()
            finally:
                self._release_cursor()
                self._session.flush()
            elapsed_ms = (time.monotonic() - started) * 1000.0
        self._session.record_action(
            action, x=target_x, y=target_y, button=button, clicks=clicks, virtual=virtual
        )
        self._audit(
            action,
            elapsed_ms,
            x=target_x,
            y=target_y,
            button=button,
            clicks=clicks,
            virtual=virtual,
        )
        return target_x, target_y

    def left_click(
        self, x: float, y: float, duration: float = 0.5, virtual: bool = False
    ) -> tuple[int, int]:
        """Move to ``(x, y)`` and left-click once."""
        return self._click(
            "left_click", x, y, duration, button="left", clicks=1, interval=0.0,
            virtual=virtual,
        )

    def right_click(
        self, x: float, y: float, duration: float = 0.5, virtual: bool = False
    ) -> tuple[int, int]:
        """Move to ``(x, y)`` and right-click once."""
        return self._click(
            "right_click", x, y, duration, button="right", clicks=1, interval=0.0,
            virtual=virtual,
        )

    def double_click(
        self, x: float, y: float, duration: float = 0.5, virtual: bool = False
    ) -> tuple[int, int]:
        """Move to ``(x, y)`` and double-click (human-paced inter-click gap)."""
        return self._click(
            "double_click",
            x,
            y,
            duration,
            button="left",
            clicks=2,
            interval=random.uniform(0.06, 0.12),
            virtual=virtual,
        )

    def drag(
        self,
        x1: float,
        y1: float,
        x2: float,
        y2: float,
        duration: float = 0.8,
        virtual: bool = False,
    ) -> tuple[int, int]:
        """Press at ``(x1, y1)``, ease-drag to ``(x2, y2)`` and release."""
        self._require_pyautogui()
        with self._lock:
            assert pyautogui is not None
            started = time.monotonic()
            start_x, start_y = self._clamp(x1, y1)
            end_x, end_y = self._clamp(x2, y2)
            self._pin_cursor(virtual)
            try:
                self._move_locked(start_x, start_y, duration * 0.4)
                time.sleep(random.uniform(*_PRE_CLICK_PAUSE_RANGE))
                self._check_abort()  # cancel before the button ever goes down
                self._overlay.show(start_x, start_y, STATE_PRESSED)
                pyautogui.mouseDown(button="left")
                distance = math.hypot(end_x - start_x, end_y - start_y)
                steps = self._step_count(distance)
                step_delay = duration / max(1, steps)
                for point_x, point_y in _bezier_points(
                    float(start_x), float(start_y), float(end_x), float(end_y), steps
                ):
                    self._check_abort()
                    pyautogui.dragTo(
                        point_x, point_y, duration=0, button="left", tween=pyautogui.easeOutQuad
                    )
                    self._overlay.move(point_x, point_y)
                    self._record_cursor(point_x, point_y, STATE_PRESSED)
                    time.sleep(_jitter(step_delay))
                time.sleep(random.uniform(0.05, 0.12))  # humans release slightly late
                pyautogui.mouseUp(button="left")
                self._overlay.show(end_x, end_y, STATE_IDLE)
                self._overlay.hide()
            finally:
                # An abort mid-drag must never leave the physical button held.
                with contextlib.suppress(Exception):
                    pyautogui.mouseUp(button="left")
                self._release_cursor()
                self._session.flush()
            elapsed_ms = (time.monotonic() - started) * 1000.0
        self._session.record_action(
            "drag", x1=start_x, y1=start_y, x2=end_x, y2=end_y, duration=duration, virtual=virtual
        )
        self._audit(
            "drag",
            elapsed_ms,
            x1=start_x,
            y1=start_y,
            x2=end_x,
            y2=end_y,
            duration=duration,
            virtual=virtual,
        )
        return end_x, end_y

    def type_text(self, text: str, virtual: bool = False) -> int:
        """Type ``text`` with human keystroke rhythm.

        Virtual mode posts ``WM_CHAR`` messages straight to the foreground
        window — no focus change, no IME interference, CJK included. The
        physical path types via ``typewrite`` with the focused window
        temporarily switched to the English (US) layout (a Chinese IME
        otherwise swallows spaces and rewrites punctuation); runs of
        ``typewrite``-impossible characters (CJK, emoji, …) go through the
        clipboard and are pasted.
        """
        self._require_pyautogui()
        if not text:
            return 0
        if virtual:
            return self._type_virtual(text)
        typed = 0
        with self._lock, self._english_layout():
            assert pyautogui is not None
            started = time.monotonic()
            self._overlay.set_busy(True)  # typing = the busy cursor wash
            index = 0
            length = len(text)
            try:
                while index < length:
                    self._check_abort()  # between keystrokes
                    character = text[index]
                    if ord(character) < 128:
                        pyautogui.typewrite(character, interval=0)
                        typed += 1
                        index += 1
                        time.sleep(random.uniform(*_TYPE_DELAY_RANGE))
                        continue
                    # Collect the whole run of non-typewrite characters so a
                    # Chinese phrase is pasted once instead of per character.
                    run_start = index
                    while index < length and ord(text[index]) >= 128:
                        index += 1
                    paste_text = text[run_start:index]
                    self._paste_text(paste_text)
                    typed += len(paste_text)
                    time.sleep(random.uniform(*_TYPE_DELAY_RANGE))
            finally:
                self._overlay.set_busy(False)
                self._session.flush()
            elapsed_ms = (time.monotonic() - started) * 1000.0
        self._session.record_action("type_text", characters=typed, virtual=False)
        self._audit("type_text", elapsed_ms, characters=typed, virtual=False)
        return typed

    def _type_virtual(self, text: str) -> int:
        """Post ``WM_CHAR`` per character to the foreground window.

        Bypasses both keyboard focus and the IME, so spaces, punctuation and
        CJK all land verbatim while the user keeps working elsewhere.
        """
        import ctypes

        if sys.platform != "win32":
            raise ComputerUseUnavailableError("virtual typing is Windows-only")
        user32 = ctypes.windll.user32
        hwnd = user32.GetForegroundWindow()
        if not hwnd:
            raise ComputerUseUnavailableError("no foreground window to type into")
        # Modern apps (WinUI notepad, browsers…) ignore WM_CHAR on their
        # frame window; post to the thread's actual focused control instead.
        target = self._focused_control(hwnd)
        typed = 0
        with self._lock:
            started = time.monotonic()
            self._overlay.set_busy(True)  # typing = the busy cursor wash
            try:
                for character in text:
                    self._check_abort()  # between WM_CHAR posts
                    code = 0x0D if character == "\n" else ord(character)  # WM_CHAR CR
                    user32.PostMessageW(target, 0x0102, code, 0)  # WM_CHAR
                    typed += 1
                    time.sleep(random.uniform(*_TYPE_DELAY_RANGE))
            finally:
                self._overlay.set_busy(False)
                self._session.flush()
            elapsed_ms = (time.monotonic() - started) * 1000.0
        self._session.record_action("type_text", characters=typed, virtual=True)
        self._audit("type_text", elapsed_ms, characters=typed, virtual=True)
        return typed

    @staticmethod
    def _focused_control(fallback_hwnd: int) -> int:
        """Return the focused child control of the foreground thread."""
        import ctypes

        user32 = ctypes.windll.user32
        kernel32 = ctypes.windll.kernel32

        class GUITHREADINFO(ctypes.Structure):
            _fields_ = [
                ("cbSize", ctypes.c_ulong),
                ("flags", ctypes.c_ulong),
                ("hwndActive", ctypes.c_void_p),
                ("hwndFocus", ctypes.c_void_p),
                ("hwndCapture", ctypes.c_void_p),
                ("hwndMenuOwner", ctypes.c_void_p),
                ("hwndMoveSize", ctypes.c_void_p),
                ("hwndCaret", ctypes.c_void_p),
                ("rcCaret", ctypes.c_long * 4),
            ]

        hwnd = fallback_hwnd
        tid = user32.GetWindowThreadProcessId(hwnd, None)
        info = GUITHREADINFO()
        info.cbSize = ctypes.sizeof(GUITHREADINFO)
        if tid and user32.GetGUIThreadInfo(tid, ctypes.byref(info)):
            hwnd = info.hwndFocus or info.hwndActive or fallback_hwnd
        return int(hwnd)

    @staticmethod
    @contextlib.contextmanager
    def _english_layout():
        """Temporarily switch the focused window to the English (US) layout.

        A Chinese IME in the target window swallows spaces and rewrites
        punctuation (``!`` → ``！``); requesting the ``en-US`` layout via
        ``WM_INPUTLANGCHANGEREQUEST`` for the duration of physical typing
        keeps the keystrokes verbatim, and the previous layout is restored
        afterwards.
        """
        if sys.platform != "win32":
            yield
            return
        import ctypes

        user32 = ctypes.windll.user32
        hwnd = user32.GetForegroundWindow()
        tid = user32.GetWindowThreadProcessId(hwnd, None) if hwnd else 0
        previous = user32.GetKeyboardLayout(tid) if tid else 0
        if hwnd:
            user32.PostMessageW(hwnd, 0x0050, 0, 0x04090409)
            time.sleep(0.08)
        try:
            yield
        finally:
            if hwnd and previous:
                user32.PostMessageW(hwnd, 0x0050, 0, previous)

    @staticmethod
    def _copy_to_clipboard(text: str) -> None:
        """Put ``text`` on the system clipboard (pyperclip, then Win32)."""
        try:
            import pyperclip

            pyperclip.copy(text)
            return
        except Exception:
            pass
        if sys.platform == "win32":
            ComputerUseController._copy_to_clipboard_windows(text)
            return
        raise ComputerUseUnavailableError(
            "pyperclip is required to type non-ASCII text on this platform"
        )

    @staticmethod
    def _copy_to_clipboard_windows(text: str) -> None:
        """Minimal Win32 clipboard write (CF_UNICODETEXT), no pyperclip needed."""
        import contextlib
        import ctypes

        CF_UNICODETEXT = 13
        GMEM_MOVEABLE = 0x0002
        user32 = ctypes.windll.user32
        kernel32 = ctypes.windll.kernel32
        if not user32.OpenClipboard(0):
            raise ComputerUseUnavailableError("cannot open the Windows clipboard")
        try:
            user32.EmptyClipboard()
            data = text.encode("utf-16-le") + b"\x00\x00"
            handle = kernel32.GlobalAlloc(GMEM_MOVEABLE, len(data))
            if not handle:
                raise ComputerUseUnavailableError("GlobalAlloc failed")
            target = kernel32.GlobalLock(handle)
            if not target:
                raise ComputerUseUnavailableError("GlobalLock failed")
            try:
                ctypes.memmove(target, data, len(data))
            finally:
                kernel32.GlobalUnlock(handle)
            if not user32.SetClipboardData(CF_UNICODETEXT, handle):
                kernel32.GlobalFree(handle)
                raise ComputerUseUnavailableError("SetClipboardData failed")
        finally:
            with contextlib.suppress(Exception):
                user32.CloseClipboard()

    def _paste_text(self, text: str) -> None:
        assert pyautogui is not None
        self._copy_to_clipboard(text)
        pyautogui.hotkey("ctrl", "v")

    def press_key(self, key: str) -> str:
        """Press a named key (``enter``, ``esc``, ``tab``, ``f5``, …)."""
        self._require_pyautogui()
        normalized = str(key).strip().lower()
        if not normalized:
            raise ValueError("key must be a non-empty key name")
        self._check_abort()
        with self._lock:
            assert pyautogui is not None
            started = time.monotonic()
            pyautogui.press(normalized)
            elapsed_ms = (time.monotonic() - started) * 1000.0
        self._session.record_action("press_key", key=normalized)
        self._audit("press_key", elapsed_ms, key=normalized)
        return normalized

    def scroll(self, amount: int) -> int:
        """Scroll the wheel; positive amounts scroll up, negative down."""
        self._require_pyautogui()
        clicks = int(amount)
        if clicks == 0:
            return 0
        with self._lock:
            assert pyautogui is not None
            started = time.monotonic()
            # Split large scrolls into human-paced wheel ticks that sum
            # exactly to the requested amount.
            tick_count = max(1, min(20, abs(clicks) // 3))
            per_tick, remainder = divmod(abs(clicks), tick_count)
            sign = 1 if clicks > 0 else -1
            for index in range(tick_count):
                self._check_abort()  # between wheel ticks
                tick = (per_tick + (1 if index < remainder else 0)) * sign
                pyautogui.scroll(tick)
                time.sleep(_jitter(0.03))
            elapsed_ms = (time.monotonic() - started) * 1000.0
        self._session.record_action("scroll", amount=clicks)
        self._audit("scroll", elapsed_ms, amount=clicks)
        return clicks

    # ------------------------------------------------------------------
    # Session lifecycle (driven by the MCP session_start/session_end tools)
    # ------------------------------------------------------------------

    def begin_session(
        self, theme: str = "dark", accent: str | None = None, accent2: str | None = None
    ) -> None:
        """Start a session: reset state, show banner + glow + standby cursor."""
        self._session.start(theme=theme, accent=accent)
        self._overlay.session_start(theme=theme, accent=accent, accent2=accent2)

    def end_session(self) -> None:
        """End a session: every visual element fades out and is destroyed."""
        self._overlay.session_end()
        self._session.end()

    def abort_session(self) -> None:
        """Immediate teardown after Esc: visuals gone, aborted persisted.

        Called by the MCP server's abort watcher (and defensively by
        :meth:`_check_abort` inside any step loop).
        """
        self._overlay.session_end()
        self._session.mark_aborted()
