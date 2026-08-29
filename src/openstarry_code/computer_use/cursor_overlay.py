"""On-screen visual layer for the computer-use session (v2, Win32 layered).

Renders everything — breathing gradient border glow, frosted-glass banner,
Win11 cursor artwork — into **one** topmost click-through layered window
updated through ``UpdateLayeredWindow`` with a per-pixel-alpha (premultiplied
``RGBa``) DIB.  This replaces the v1 Tk implementation, whose
``-transparentcolor`` colorkey model cannot express alpha gradients (glow
faded to black) and whose windows could not get Aero acrylic.

Architecture: a dedicated render thread owns the Win32 window and a frame
loop (message-driven, throttled).  Callers only post commands to a
:class:`queue.Queue` through the :class:`CursorOverlay` facade, exactly as
before — controller/mcp code is unchanged.

Frame composition (all in the premultiplied domain):

    scene_premul  = _premultiply(glow breath blend)   # cached, rebuilt ~11fps
    frame         = scene_premul.copy()
                    + add(banner region)              # frosting + slide/fade
                    + add(cursor region)              # cursor + ripple + spinner
    → tobytes("raw","BGRA") → UpdateLayeredWindow

Mouse click-through comes from ``WM_NCHITTEST → HTTRANSPARENT`` (no
``WS_EX_TRANSPARENT``, which slows DWM composition).  Every failure path
degrades silently — a cosmetic layer must never take the controller down.
"""

from __future__ import annotations

import atexit
import math
import queue
import struct
import sys
import threading
import time
from pathlib import Path

_IS_WINDOWS = sys.platform == "win32"

try:
    from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont, ImageGrab
except ImportError:  # pragma: no cover
    Image = None  # type: ignore[assignment]

try:
    import numpy as _np
except ImportError:  # pragma: no cover
    _np = None  # type: ignore[assignment]

if _IS_WINDOWS:
    import ctypes
    from ctypes import wintypes

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

STATE_IDLE = "idle"
STATE_PRESSED = "pressed"

THEME_LIGHT = "light"
THEME_DARK = "dark"

_DEFAULT_ACCENT = "#5b8cff"
_DEFAULT_THEME = THEME_DARK

_CURSORS_DIR = Path(__file__).resolve().parent / "assets" / "cursors"
_CURSOR_PREFER_PX = 38  # which frame inside the multi-size .cur to choose

_CURSOR_HOT = (14, 14)  # artwork hotspot inside the 136px layer; tip on coords
_CURSOR_BOX = 136

# Glow: one continuous luminous frame (长方体) around the screen, breathing
# over ~3.4s.  Alpha is a true distance field to the nearest screen edge, so
# the four sides fuse into a single solid body — not four separate lines.
# (History: a thin 14px rim framed dark wallpaper corners into visible
# "black squares" — the falloff must dissolve INTO the corner, not outline
# it; 40px reads as a solid cuboid body instead of four separate lines.)
_GLOW_THICK = 40
_GLOW_SEGMENTS = 64
_GLOW_PERIOD_S = 3.4
_GLOW_HI = 0.92
_GLOW_LO = 0.62
_GLOW_TICK_MS = 90  # breathe cadence (full-screen premultiply is pricey)

# Banner (frosted glass strip, top-centered).
_BANNER_WIDTH_RATIO = 0.40
_BANNER_HEIGHT = 56
_BANNER_MARGIN = 14
_BANNER_TEXT = "Starry 正在使用你的电脑（按 Esc 退出）"
_BANNER_RADIUS = 18
_BANNER_SHADOW = 12  # soft drop shadow padding around the panel
_BANNER_SLIDE_MS = 520
_BANNER_FADE_MS = 400
_BANNER_EXIT_MS = 300

# Animation cadence.
_FRAME_MS = 16
_TICK_MIN_MS = 12  # never render faster than this, even on message floods
_HIDE_DELAY_S = 0.8
_HIDE_FADE_MS = 200
_RIPPLE_MS = 480
_SPIN_STEP_MS = 90

_FONT_PATH = Path(r"C:\Windows\Fonts\msyh.ttc")


# ---------------------------------------------------------------------------
# Color / image helpers (thread-agnostic)
# ---------------------------------------------------------------------------


def _sanitize_hex(value: object) -> str | None:
    """Return ``#rrggbb`` lowercase, or None when ``value`` is not a color."""
    if not isinstance(value, str):
        return None
    text = value.strip()
    if not text.startswith("#"):
        return None
    body = text[1:]
    if len(body) == 3:
        body = "".join(ch * 2 for ch in body)
    if len(body) != 6 or any(c not in "0123456789abcdefABCDEF" for c in body):
        return None
    return f"#{body.lower()}"


def _hex_to_rgb(value: str | None, fallback: tuple[int, int, int]) -> tuple[int, int, int]:
    clean = _sanitize_hex(value)
    if clean is None:
        return fallback
    return (int(clean[1:3], 16), int(clean[3:5], 16), int(clean[5:7], 16))


def _mix_rgb(
    c1: tuple[int, int, int], c2: tuple[int, int, int], t: float
) -> tuple[int, int, int]:
    """Linear interpolation between two RGB colours (``t`` in [0, 1])."""
    t = max(0.0, min(1.0, t))
    return (
        int(c1[0] + (c2[0] - c1[0]) * t),
        int(c1[1] + (c2[1] - c1[1]) * t),
        int(c1[2] + (c2[2] - c1[2]) * t),
    )


def _toward_white(rgb: tuple[int, int, int], ratio: float) -> tuple[int, int, int]:
    """Shift an RGB colour toward white — the default light-theme companion."""
    return _mix_rgb(rgb, (255, 255, 255), ratio)


def _load_cur_rgba(path, prefer: int = _CURSOR_PREFER_PX):
    """Parse one 32bpp frame out of a .cur file, preserving alpha.

    PIL's ``Image.open`` returns these cursors as flat RGB (it drops the
    alpha channel), so the ICO container is decoded by hand. The directory
    entry's ``wBitCount`` field cannot be trusted (some cursor packs store
    garbage there), so the frame's BITMAPINFOHEADER ``biBitCount`` decides
    whether a frame is 32bpp; the XOR bitmap is interpreted as bottom-up
    BGRA and flipped upright.
    """
    if Image is None:
        return None
    try:
        data = path.read_bytes()
        count = struct.unpack_from("<H", data, 4)[0]
        best = None
        for index in range(count):
            width, height, _colors, _res, _planes, _bitcount, size, offset = (
                struct.unpack_from("<BBBBHHII", data, 6 + 16 * index)
            )
            width = width or 256
            if offset + 40 > len(data):
                continue
            if struct.unpack_from("<H", data, offset + 14)[0] != 32:  # biBitCount
                continue
            if best is None or abs(width - prefer) < abs(best[0] - prefer):
                best = (width, height or 256, offset, size)
        if best is None:
            return None
        width, height, offset, size = best
        raw = data[offset + 40 : offset + 40 + min(size - 40, width * height * 4)]
        image = Image.frombytes("RGBA", (width, height), raw, "raw", "BGRA")
        return image.transpose(Image.Transpose.FLIP_TOP_BOTTOM)
    except Exception:
        return None


def _premultiply(img: Image.Image) -> Image.Image:
    """Convert a straight-alpha RGBA image to premultiplied ``RGBa``."""
    alpha = img.getchannel("A")
    return Image.merge(
        "RGBa",
        (
            ImageChops.multiply(img.getchannel("R"), alpha),
            ImageChops.multiply(img.getchannel("G"), alpha),
            ImageChops.multiply(img.getchannel("B"), alpha),
            alpha,
        ),
    )


def _clip_box(x: int, y: int, w: int, h: int, fw: int, fh: int) -> tuple[int, int, int, int, int, int] | None:
    """Intersection of a layer rect with the frame rect.

    Returns ``(sx, sy, dx, dy, cw, ch)`` — source offset and destination
    placement for the visible part — or None when fully off-screen.
    """
    ix0, iy0 = max(x, 0), max(y, 0)
    ix1, iy1 = min(x + w, fw), min(y + h, fh)
    if ix1 <= ix0 or iy1 <= iy0:
        return None
    return (ix0 - x, iy0 - y, ix0, iy0, ix1 - ix0, iy1 - iy0)


def _add_region(frame: Image.Image, layer: Image.Image, box: tuple[int, int]) -> None:
    """Add (premultiplied) ``layer`` onto ``frame`` at ``box`` — additive blend.

    Over-compositing in the premultiplied domain would need per-layer
    (1-alpha) scaling of the destination; additive blending is the standard
    cheap approximation and reads as a natural glow.  Cursor/hover regions
    are nearly transparent (alpha≈1 on the artwork only), so the visual
    error is negligible.
    """
    clipped = _clip_box(box[0], box[1], layer.width, layer.height, frame.width, frame.height)
    if clipped is None:
        return
    sx, sy, dx, dy, cw, ch = clipped
    src = layer.crop((sx, sy, sx + cw, sy + ch))
    dst = frame.crop((dx, dy, dx + cw, dy + ch))
    frame.paste(ImageChops.add(dst, src), (dx, dy))


def _font(size: int):
    try:
        return ImageFont.truetype(str(_FONT_PATH), size)
    except Exception:  # pragma: no cover — font missing: fall back to PIL default
        try:
            return ImageFont.load_default(size)
        except TypeError:
            return ImageFont.load_default()


def _ease_out_cubic(t: float) -> float:
    return 1.0 - (1.0 - t) ** 3


def _ease_in_cubic(t: float) -> float:
    return t**3


def _ease_out_quad(t: float) -> float:
    return 1.0 - (1.0 - t) * (1.0 - t)


def _clamp(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, v))


class _Tweens:
    """Tiny wall-clock timeline of eased animations."""

    def __init__(self) -> None:
        self._items: dict[str, tuple[float, float, str]] = {}

    def start(self, name: str, duration_ms: float, ease: str, now: float) -> None:
        self._items[name] = (now, duration_ms / 1000.0, ease)

    def get(self, name: str, now: float) -> float:
        """Eased progress 0..1 (1.0 when unknown/finished)."""
        item = self._items.get(name)
        if item is None:
            return 1.0
        t0, dur, ease = item
        t = _clamp((now - t0) / dur, 0.0, 1.0)
        if ease == "out_cubic":
            return _ease_out_cubic(t)
        if ease == "in_cubic":
            return _ease_in_cubic(t)
        if ease == "out_quad":
            return _ease_out_quad(t)
        return t

    def done(self, name: str, now: float) -> bool:
        item = self._items.get(name)
        return item is None or now - item[0] >= item[1]

    def active(self, name: str) -> bool:
        return name in self._items

    def drop(self, name: str) -> None:
        self._items.pop(name, None)


# ---------------------------------------------------------------------------
# Win32 layered-window plumbing (render thread only)
# ---------------------------------------------------------------------------

if _IS_WINDOWS:
    # WPARAM/LPARAM are pointer-sized on x64 — wintypes' 32-bit aliases lie.
    _WNDPROC = ctypes.WINFUNCTYPE(
        ctypes.c_ssize_t, wintypes.HWND, wintypes.UINT, ctypes.c_size_t, ctypes.c_ssize_t
    )

    class _WNDCLASSW(ctypes.Structure):
        _fields_ = [
            ("style", wintypes.UINT),
            ("lpfnWndProc", _WNDPROC),
            ("cbClsExtra", ctypes.c_int),
            ("cbWndExtra", ctypes.c_int),
            ("hInstance", wintypes.HINSTANCE),
            ("hIcon", wintypes.HANDLE),
            ("hCursor", wintypes.HANDLE),
            ("hbrBackground", wintypes.HANDLE),
            ("lpszMenuName", wintypes.LPCWSTR),
            ("lpszClassName", wintypes.LPCWSTR),
        ]

    class _BITMAPINFOHEADER(ctypes.Structure):
        _fields_ = [
            ("biSize", wintypes.DWORD),
            ("biWidth", wintypes.LONG),
            ("biHeight", wintypes.LONG),
            ("biPlanes", wintypes.WORD),
            ("biBitCount", wintypes.WORD),
            ("biCompression", wintypes.DWORD),
            ("biSizeImage", wintypes.DWORD),
            ("biXPelsPerMeter", wintypes.LONG),
            ("biYPelsPerMeter", wintypes.LONG),
            ("biClrUsed", wintypes.DWORD),
            ("biClrImportant", wintypes.DWORD),
        ]

    class _BLENDFUNCTION(ctypes.Structure):
        _fields_ = [
            ("BlendOp", ctypes.c_ubyte),
            ("BlendFlags", ctypes.c_ubyte),
            ("SourceConstantAlpha", ctypes.c_ubyte),
            ("AlphaFormat", ctypes.c_ubyte),
        ]

    _ULW_ALPHA = 0x00000002
    _AC_SRC_OVER = 0x00
    _AC_SRC_ALPHA = 0x01
    _WM_NCHITTEST = 0x0084
    _HTTRANSPARENT = -1
    _SW_SHOWNOACTIVATE = 4
    _DIB_RGB_COLORS = 0
    _WS_POPUP = 0x80000000
    _WS_EX_LAYERED = 0x00080000
    _WS_EX_TOPMOST = 0x00000008
    _WS_EX_TOOLWINDOW = 0x00000080
    _WS_EX_NOACTIVATE = 0x08000000


class _Win32Window:
    """One topmost, click-through, per-pixel-alpha layered window."""

    def __init__(self, width: int, height: int, x: int, y: int) -> None:
        self._hwnd = None
        self._memdc = None
        self._dib = None
        self._dib_ptr = None
        self._screen_dc = None
        self._old_bmp = None
        self._dib_w = 0
        self._dib_h = 0
        self._shown = False
        self._create(width, height, x, y)

    # -- creation ------------------------------------------------------------

    def _create(self, width: int, height: int, x: int, y: int) -> None:
        user32 = ctypes.windll.user32
        gdi32 = ctypes.windll.gdi32
        kernel32 = ctypes.windll.kernel32

        # ctypes defaults c_int restype, which truncates 64-bit handles.
        kernel32.GetModuleHandleW.restype = wintypes.HMODULE
        kernel32.GetModuleHandleW.argtypes = [wintypes.LPCWSTR]
        user32.RegisterClassW.argtypes = [ctypes.c_void_p]
        user32.RegisterClassW.restype = wintypes.ATOM
        user32.CreateWindowExW.argtypes = [
            wintypes.DWORD, wintypes.LPCWSTR, wintypes.LPCWSTR, wintypes.DWORD,
            ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int,
            wintypes.HWND, wintypes.HMENU, wintypes.HINSTANCE, wintypes.LPVOID,
        ]
        user32.CreateWindowExW.restype = wintypes.HWND
        user32.GetDC.argtypes = [wintypes.HWND]
        user32.GetDC.restype = wintypes.HDC
        user32.ReleaseDC.argtypes = [wintypes.HWND, wintypes.HDC]
        gdi32.CreateCompatibleDC.argtypes = [wintypes.HDC]
        gdi32.CreateCompatibleDC.restype = wintypes.HDC
        gdi32.CreateDIBSection.argtypes = [
            wintypes.HDC, ctypes.c_void_p, wintypes.UINT,
            ctypes.POINTER(ctypes.c_void_p), wintypes.HANDLE, wintypes.DWORD,
        ]
        gdi32.CreateDIBSection.restype = wintypes.HBITMAP
        gdi32.SelectObject.argtypes = [wintypes.HDC, wintypes.HGDIOBJ]
        gdi32.SelectObject.restype = wintypes.HGDIOBJ
        gdi32.DeleteObject.argtypes = [wintypes.HGDIOBJ]
        user32.UpdateLayeredWindow.argtypes = [
            wintypes.HWND, wintypes.HDC, ctypes.POINTER(wintypes.POINT),
            ctypes.POINTER(wintypes.SIZE), wintypes.HDC, ctypes.POINTER(wintypes.POINT),
            wintypes.COLORREF, ctypes.POINTER(_BLENDFUNCTION), wintypes.DWORD,
        ]
        user32.DefWindowProcW.argtypes = [
            wintypes.HWND, wintypes.UINT, ctypes.c_size_t, ctypes.c_ssize_t,
        ]
        user32.DefWindowProcW.restype = ctypes.c_ssize_t
        user32.DestroyWindow.argtypes = [wintypes.HWND]
        user32.ShowWindow.argtypes = [wintypes.HWND, ctypes.c_int]
        gdi32.DeleteDC.argtypes = [wintypes.HDC]
        user32.PeekMessageW.argtypes = [
            ctypes.POINTER(wintypes.MSG), wintypes.HWND, wintypes.UINT, wintypes.UINT, wintypes.UINT,
        ]
        user32.TranslateMessage.argtypes = [ctypes.POINTER(wintypes.MSG)]
        user32.DispatchMessageW.argtypes = [ctypes.POINTER(wintypes.MSG)]

        def wnd_proc(hwnd, msg, wparam, lparam):
            if msg == _WM_NCHITTEST:
                return _HTTRANSPARENT  # every pixel is click-through
            return user32.DefWindowProcW(hwnd, msg, wparam, lparam)

        self._wnd_proc_ref: object = _WNDPROC(wnd_proc)  # keep alive (GC!)

        class_name = "StarryOverlayV2"
        wnd_class = _WNDCLASSW()
        wnd_class.lpfnWndProc = self._wnd_proc_ref
        wnd_class.hInstance = kernel32.GetModuleHandleW(None)
        wnd_class.lpszClassName = class_name
        if not user32.RegisterClassW(ctypes.byref(wnd_class)):
            # 1410 = class already registered by a previous overlay thread.
            if ctypes.get_last_error() not in (0, 1410):
                raise RuntimeError("RegisterClassW failed")

        ex_style = (
            _WS_EX_LAYERED | _WS_EX_TOPMOST | _WS_EX_TOOLWINDOW | _WS_EX_NOACTIVATE
        )
        hwnd = user32.CreateWindowExW(
            ex_style,
            class_name,
            "openstarry-overlay",
            _WS_POPUP,
            x,
            y,
            width,
            height,
            None,
            None,
            wnd_class.hInstance,
            None,
        )
        if not hwnd:
            raise RuntimeError("CreateWindowExW failed")
        self._hwnd = hwnd

        self._screen_dc = user32.GetDC(None)
        self._memdc = gdi32.CreateCompatibleDC(self._screen_dc)
        self._resize_dib(width, height)
        # NOT shown here: a layered window displayed before its first
        # UpdateLayeredWindow paints an undefined (black) background.
        # blit() shows it right after the first upload.

    def _resize_dib(self, width: int, height: int) -> None:
        gdi32 = ctypes.windll.gdi32
        if self._hwnd is None or self._memdc is None:
            return
        if self._dib is not None and (width, height) == (self._dib_w, self._dib_h):
            return
        if self._dib is not None and self._old_bmp is not None:
            gdi32.SelectObject(self._memdc, self._old_bmp)
            gdi32.DeleteObject(self._dib)
        header = _BITMAPINFOHEADER()
        header.biSize = ctypes.sizeof(_BITMAPINFOHEADER)
        header.biWidth = width
        header.biHeight = -height  # negative => top-down
        header.biPlanes = 1
        header.biBitCount = 32
        header.biCompression = 0
        buf_ptr = ctypes.c_void_p()
        self._dib = gdi32.CreateDIBSection(
            self._memdc, ctypes.byref(header), _DIB_RGB_COLORS, ctypes.byref(buf_ptr), None, 0
        )
        if not self._dib:
            raise RuntimeError("CreateDIBSection failed")
        self._dib_ptr = buf_ptr
        self._dib_w = width
        self._dib_h = height
        self._old_bmp = gdi32.SelectObject(self._memdc, self._dib)

    # -- upload --------------------------------------------------------------

    def blit(self, buf: bytes, buf_w: int, buf_h: int) -> None:
        """Upload a full-window premultiplied BGRA buffer."""
        user32 = ctypes.windll.user32
        if not buf or self._hwnd is None:
            return
        self._resize_dib(buf_w, buf_h)
        ctypes.memmove(self._dib_ptr, buf, len(buf))
        point = wintypes.POINT(0, 0)
        size = wintypes.SIZE(buf_w, buf_h)
        blend = _BLENDFUNCTION(_AC_SRC_OVER, 0, 255, _AC_SRC_ALPHA)
        user32.UpdateLayeredWindow(
            self._hwnd,
            self._screen_dc,
            None,
            ctypes.byref(size),
            self._memdc,
            ctypes.byref(point),
            0,
            ctypes.byref(blend),
            _ULW_ALPHA,
        )
        if not self._shown:
            self._shown = True
            ctypes.windll.user32.ShowWindow(self._hwnd, _SW_SHOWNOACTIVATE)

    def pump(self) -> None:
        """Drain pending window messages (keeps WM_NCHITTEST responsive)."""
        if self._hwnd is None:
            return
        msg = wintypes.MSG()
        user32 = ctypes.windll.user32
        while user32.PeekMessageW(ctypes.byref(msg), self._hwnd, 0, 0, 1):
            user32.TranslateMessage(ctypes.byref(msg))
            user32.DispatchMessageW(ctypes.byref(msg))

    def hide_window(self) -> None:
        if self._hwnd is not None:
            ctypes.windll.user32.ShowWindow(self._hwnd, 0)

    def destroy(self) -> None:
        if self._hwnd is not None:
            ctypes.windll.user32.DestroyWindow(self._hwnd)
            self._hwnd = None
        if self._memdc is not None and self._dib is not None:
            if self._old_bmp is not None:
                ctypes.windll.gdi32.SelectObject(self._memdc, self._old_bmp)
            ctypes.windll.gdi32.DeleteObject(self._dib)
            self._dib = None
        if self._memdc is not None:
            ctypes.windll.gdi32.DeleteDC(self._memdc)
            self._memdc = None
        if self._screen_dc is not None:
            ctypes.windll.user32.ReleaseDC(None, self._screen_dc)
            self._screen_dc = None


# ---------------------------------------------------------------------------
# Element painters (pure PIL; render thread only)
# ---------------------------------------------------------------------------

_BUILD_GLOW_CACHE: dict[tuple, Image.Image] = {}


def _build_glow(
    size: tuple[int, int],
    r1: tuple[int, int, int],
    r2: tuple[int, int, int],
    mult: float,
) -> Image.Image:
    """One continuous luminous frame (长方体): every pixel's alpha comes from a
    true distance field to the nearest screen edge, and its colour is sampled
    from the perimeter gradient at that edge's projection — the four sides
    fuse into a single solid body with seamless colour flow around the corners.

    ``mult`` modulates the ALPHA (breath dims the glow to transparency), never
    the RGB: dimming the colour with alpha untouched paints an opaque dark
    ring that outlines dark wallpaper corners as black squares.
    """
    width, height = size
    mult = _clamp(mult, 0.0, 1.0)
    c1 = tuple(min(255, int(v)) for v in r1)
    c2 = tuple(min(255, int(v)) for v in r2)
    cache_key = (width, height, c1, c2, round(mult, 2))
    cached = _BUILD_GLOW_CACHE.get(cache_key)
    if cached is not None:
        return cached
    if len(_BUILD_GLOW_CACHE) > 64:  # breath phase drift → bounded growth
        _BUILD_GLOW_CACHE.clear()

    thick = _GLOW_THICK
    img = Image.new("RGBA", size, (0, 0, 0, 0))

    if _np is None:  # pragma: no cover — numpy ships with the runtime
        # Legacy band painter: per-edge colour strips + per-edge alpha masks
        # combined with ``lighter`` (per-pixel max), so corner overlaps keep
        # the brightest band instead of being overwritten.
        draw = ImageDraw.Draw(img)
        segments = _GLOW_SEGMENTS
        perimeter = 2 * (width + height)
        edges = [  # (x0, y0, x1, y1, horizontal, s_start, s_end)
            (0, 0, width, thick, True, 0.5 / perimeter, (width - 0.5) / perimeter),
            (0, height - thick, width, height, True,
             (width + height + 0.5) / perimeter, (2 * width + height - 0.5) / perimeter),
            (0, 0, thick, height, False,
             (2 * width + height + 0.5) / perimeter, (perimeter - 0.5) / perimeter),
            (width - thick, 0, width, height, False,
             (width + 0.5) / perimeter, (width + height - 0.5) / perimeter),
        ]
        for x0, y0, x1, y1, horizontal, s_start, s_end in edges:
            length = (x1 - x0) if horizontal else (y1 - y0)
            for seg in range(segments):
                t = (seg + 0.5) / segments
                rgb = _mix_rgb(c1, c2, s_start + t * (s_end - s_start))
                if horizontal:
                    seg_x0 = x0 + int(seg * length / segments)
                    seg_x1 = x0 + int((seg + 1) * length / segments)
                    draw.rectangle([seg_x0, y0, seg_x1, y1], fill=rgb)
                else:
                    seg_y0 = y0 + int(seg * length / segments)
                    seg_y1 = y0 + int((seg + 1) * length / segments)
                    draw.rectangle([x0, seg_y0, x1, seg_y1], fill=rgb)
        ramp = [int(255 * mult * (1.0 - i / thick) ** 1.6) for i in range(thick + 1)]
        alpha = Image.new("L", size, 0)
        for x0, y0, x1, y1, horizontal, _s_start, _s_end in edges:
            band_a = Image.new("L", size, 0)
            bd = ImageDraw.Draw(band_a)
            if horizontal:
                for i in range(thick):
                    bd.rectangle([x0, y0 + i, x1, y0 + i + 1], fill=ramp[i])
            else:
                for i in range(thick):
                    bd.rectangle([x0 + i, y0, x0 + i + 1, y1], fill=ramp[i])
            alpha = ImageChops.lighter(alpha, band_a)
        img.putalpha(alpha)
        _BUILD_GLOW_CACHE[cache_key] = img
        return img

    # --- numpy path: one solid rectangular distance field --------------------
    xs = _np.arange(width, dtype=_np.float32)[None, :]
    ys = _np.arange(height, dtype=_np.float32)[:, None]
    d_top = ys
    d_bot = (height - 1) - ys
    d_lef = xs
    d_rig = (width - 1) - xs

    # True distance field to the rectangle boundary: corners automatically get
    # the UNION of both adjacent bands (brighter than either straight run),
    # so the frame reads as one cuboid body instead of four separate lines.
    dist = _np.minimum(_np.minimum(d_top, d_bot), _np.minimum(d_lef, d_rig))
    alpha = _np.where(
        dist < thick, mult * 255.0 * _np.maximum(1.0 - dist / thick, 0.0) ** 1.6, 0.0
    ).clip(0.0, 255.0)

    # Colour: the gradient flows along the whole perimeter (TL → TR → BR → BL).
    # Blend each edge's own perimeter sample with a weight favouring the
    # NEAREST edge (0 beyond the band), so every corner morphs smoothly from
    # one side's colour into the other's instead of jumping at a hard seam.
    perimeter = 2.0 * (width + height)
    s_top = (xs + 0.5) / perimeter
    s_rig = (width + 0.5 + ys) / perimeter
    s_bot = (2 * width + height - 0.5 - xs) / perimeter
    s_lef = (2 * width + 2 * height - 0.5 - ys) / perimeter
    w_sum = _np.zeros((height, width), dtype=_np.float32)
    s_acc = _np.zeros((height, width), dtype=_np.float32)
    for d_edge, s_edge in ((d_top, s_top), (d_bot, s_bot), (d_lef, s_lef), (d_rig, s_rig)):
        w = _np.maximum(thick - d_edge, 0.0) ** 2
        s_acc += s_edge * w
        w_sum += w
    del d_top, d_bot, d_lef, d_rig
    s = s_acc / _np.maximum(w_sum, 1.0)
    del w_sum, s_acc

    # Premultiplied RGBa: colour scaled by alpha (never by ``mult`` directly).
    rgb = _np.empty((height, width, 3), dtype=_np.float32)
    for ch in range(3):
        rgb[:, :, ch] = c1[ch] + (c2[ch] - c1[ch]) * s
    del s
    premul = (rgb * (alpha / 255.0)[:, :, None]).clip(0.0, 255.0).astype(_np.uint8)
    rgba = _np.dstack([premul, alpha.astype(_np.uint8)])
    img = Image.fromarray(rgba, "RGBA")

    _BUILD_GLOW_CACHE[cache_key] = img
    return img


def _banner_width(vw: int) -> int:
    """Adaptive banner panel width — always fits on-screen (incl. shadow pad)."""
    span = max(360, int(vw * _BANNER_WIDTH_RATIO))
    limit = vw - 2 * (_BANNER_MARGIN + _BANNER_SHADOW)
    if limit > 0:
        span = min(span, limit)
    return max(span, 1)


def _grab_desktop() -> Image.Image | None:
    """Full virtual-desktop screenshot (None on failure)."""
    try:
        return ImageGrab.grab(all_screens=True)
    except Exception:
        return None


def _build_banner(
    theme: str,
    accent_rgb: tuple[int, int, int],
    desktop: Image.Image | None,
    desktop_origin: tuple[int, int],
    dest_box: tuple[int, int, int, int],
    alpha: float,
) -> Image.Image:
    """Frosted-glass banner: blurred desktop backdrop + tint + rounded mask.

    ``dest_box`` is the panel rect ``(x0, y0, x1, y1)`` in global screen
    coordinates; the layer returned includes the soft shadow padding around
    it.
    """
    bx, by, bx1, by1 = dest_box
    bw = bx1 - bx
    bh = by1 - by
    pad = _BANNER_SHADOW
    layer_w, layer_h = bw + pad * 2, bh + pad * 2
    alpha_byte = int(_clamp(alpha, 0.0, 1.0) * 255)
    dark = theme == THEME_DARK

    # -- panel: blurred desktop crop + theme grade ----------------------------
    panel: Image.Image
    if desktop is not None:
        ox, oy = desktop_origin
        crop_box = (bx - ox, by - oy, bx - ox + bw, by - oy + bh)
        if (
            crop_box[0] >= 0
            and crop_box[1] >= 0
            and crop_box[2] <= desktop.width
            and crop_box[3] <= desktop.height
        ):
            blur = (
                desktop.crop(crop_box)
                .filter(ImageFilter.GaussianBlur(18))
                .convert("RGBA")
            )
            if dark:
                blur = ImageChops.multiply(
                    blur, Image.new("RGBA", (bw, bh), (168, 176, 192, 255))
                )
            # translucent wash + accent veil == frosting
            blur.alpha_composite(
                Image.new(
                    "RGBA",
                    (bw, bh),
                    (26, 31, 43, 176) if dark else (249, 252, 255, 214),
                )
            )
            blur.alpha_composite(Image.new("RGBA", (bw, bh), (*accent_rgb, 28)))
            panel = blur
        else:
            panel = Image.new(
                "RGBA", (bw, bh), (27, 32, 41, 215) if dark else (243, 246, 250, 235)
            )
    else:
        panel = Image.new(
            "RGBA", (bw, bh), (27, 32, 41, 215) if dark else (243, 246, 250, 235)
        )

    # -- rounded mask + hairline border (4x supersampled → anti-aliased) ------
    ss = 4
    mask_hi = Image.new("L", (bw * ss, bh * ss), 0)
    ImageDraw.Draw(mask_hi).rounded_rectangle(
        [0, 0, bw * ss - 1, bh * ss - 1], radius=_BANNER_RADIUS * ss, fill=255
    )
    mask = mask_hi.resize((bw, bh), Image.LANCZOS)
    panel.putalpha(mask)
    border = Image.new("RGBA", (bw * ss, bh * ss), (0, 0, 0, 0))
    ImageDraw.Draw(border).rounded_rectangle(
        [0, 0, bw * ss - 1, bh * ss - 1],
        radius=_BANNER_RADIUS * ss,
        outline=(255, 255, 255, 110) if dark else (255, 255, 255, 150),
        width=ss,
    )
    panel.alpha_composite(border.resize((bw, bh), Image.LANCZOS))

    # -- content: caption (centered) ------------------------------------------
    fg = "#eef1f7" if dark else "#1d2430"
    draw = ImageDraw.Draw(panel)
    caption_font = _font(14)
    text_w = draw.textlength(_BANNER_TEXT, font=caption_font)
    draw.text(((bw - text_w) / 2, bh / 2), _BANNER_TEXT, fill=fg, font=caption_font, anchor="lm")

    # -- soft shadow on the padded layer --------------------------------------
    shadow_mask = Image.new("L", (bw, bh), 0)
    ImageDraw.Draw(shadow_mask).rounded_rectangle(
        [0, 0, bw - 1, bh - 1], radius=_BANNER_RADIUS, fill=255
    )
    shadow = Image.new("RGBA", (layer_w, layer_h), (0, 0, 0, 0))
    shadow.paste(Image.new("RGBA", (bw, bh), (0, 0, 0, 190)), (pad, pad + 2), shadow_mask)
    shadow = shadow.filter(ImageFilter.GaussianBlur(6))

    final = Image.new("RGBA", (layer_w, layer_h), (0, 0, 0, 0))
    final.alpha_composite(shadow, (0, 0))
    final.alpha_composite(panel, (pad, pad))

    # overall layer alpha (slide-in fade)
    a_scale = Image.new("L", (layer_w, layer_h), alpha_byte)
    final.putalpha(ImageChops.multiply(final.getchannel("A"), a_scale))
    return final


def _cursor_art(theme: str, state: str, busy: bool, accent_rgb: tuple[int, int, int], cache: dict) -> Image.Image | None:
    key = (theme, state, busy, accent_rgb)
    art = cache.get(key)
    if art is not None:
        return art
    kind = "link" if state == STATE_PRESSED else "pointer"
    raw = _load_cur_rgba(_CURSORS_DIR / theme / f"{kind}.cur")
    if raw is None:
        return None
    if busy:
        raw = raw.copy()
        raw.alpha_composite(Image.new("RGBA", raw.size, (*accent_rgb, 110)))
    cache[key] = raw
    return raw


def _build_cursor_layer(
    theme: str,
    state: str,
    ripple: float,
    busy: bool,
    spin: float,
    accent_rgb: tuple[int, int, int],
    art_cache: dict,
) -> Image.Image:
    """Cursor artwork (+ ripple + busy spinner) as a straight-alpha layer."""
    layer = Image.new("RGBA", (_CURSOR_BOX, _CURSOR_BOX), (0, 0, 0, 0))
    hx, hy = _CURSOR_HOT
    art = _cursor_art(theme, state, busy, accent_rgb, art_cache)
    if art is not None:
        layer.alpha_composite(art, (hx, hy))
    cx = hx + 19  # ripple/spinner centre
    cy = hy + 19

    if ripple > 0.0 and ripple < 1.0:
        draw = ImageDraw.Draw(layer)
        r = 6 + ripple * 40
        draw.ellipse(
            [cx - r, cy - r, cx + r, cy + r],
            outline=(*accent_rgb, int(200 * (1.0 - ripple))),
            width=max(1, int(5 - ripple * 4)),
        )
    if busy:
        draw = ImageDraw.Draw(layer)
        start = spin * 60
        draw.arc(
            [cx - 30, cy - 30, cx + 30, cy + 30],
            start=start,
            end=start + 200,
            fill=(*accent_rgb, 230),
            width=3,
        )
    return layer


# ---------------------------------------------------------------------------
# Thread-safe façade
# ---------------------------------------------------------------------------


class CursorOverlay:
    """Thread-safe façade that forwards visual commands to the overlay thread."""

    def __init__(self) -> None:
        self._queue: queue.Queue[tuple] = queue.Queue()
        self._lock = threading.Lock()
        self._thread: threading.Thread | None = None
        self._exit_hook_installed = False
        self._broken = not _IS_WINDOWS or Image is None

    def is_available(self) -> bool:
        return not self._broken

    # ------------------------------------------------------------------
    # Public API (thread-safe, non-blocking)
    # ------------------------------------------------------------------

    def show(self, x: float, y: float, state: str = STATE_IDLE) -> None:
        self._post(("show", int(x), int(y), state))

    def move(self, x: float, y: float) -> None:
        self._post(("move", int(x), int(y)))

    def hide(self) -> None:
        self._post(("hide",))

    def set_busy(self, busy: bool) -> None:
        self._post(("set_busy", bool(busy)))

    def session_start(
        self,
        theme: str = THEME_DARK,
        accent: str | None = None,
        accent2: str | None = None,
    ) -> None:
        self._post(("session_start", theme, accent, accent2))

    def session_end(self) -> None:
        self._post(("session_end",))

    def close(self) -> None:
        self._post(("quit",))
        thread = getattr(self, "_thread", None)
        if thread is not None and thread is not threading.current_thread():
            thread.join(timeout=3.0)

    def _post(self, message: tuple) -> None:
        if self._broken:
            return
        with self._lock:
            if self._thread is None or not self._thread.is_alive():
                self._thread = threading.Thread(
                    target=self._run, name="openstarry-overlay", daemon=True
                )
                self._thread.start()
                if not self._exit_hook_installed:
                    self._exit_hook_installed = True
                    atexit.register(self._shutdown_at_exit)
        self._queue.put(message)

    def _shutdown_at_exit(self) -> None:
        self._queue.put(("quit",))
        thread = self._thread
        if thread is not None:
            thread.join(timeout=2.0)

    # ------------------------------------------------------------------
    # Render thread
    # ------------------------------------------------------------------

    def _run(self) -> None:
        try:
            self._render_loop()
        except Exception:
            import traceback

            print(
                "[computer_use] overlay error:",
                traceback.format_exc(limit=4),
                file=sys.stderr,
                flush=True,
            )
            self._broken = True

    def _screen_metrics(self) -> tuple[int, int, int, int]:
        user32 = ctypes.windll.user32
        return (
            user32.GetSystemMetrics(76),  # SM_XVIRTUALSCREEN
            user32.GetSystemMetrics(77),  # SM_YVIRTUALSCREEN
            user32.GetSystemMetrics(78),  # SM_CXVIRTUALSCREEN
            user32.GetSystemMetrics(79),  # SM_CYVIRTUALSCREEN
        )

    def _render_loop(self) -> None:
        vx, vy, vw, vh = self._screen_metrics()
        if vw <= 0 or vh <= 0:
            self._broken = True
            return

        window = _Win32Window(vw, vh, vx, vy)
        desktop = _grab_desktop()
        if desktop is None or desktop.size != (vw, vh):
            desktop = None  # multi-screen mismatch → solid-banner fallback

        # ---- session state ---------------------------------------------------
        state = {
            "theme": _DEFAULT_THEME,
            "r1": (91, 140, 255),      # accent
            "r2": (173, 198, 255),     # accent2 (toward white)
            "active": False,
            "exiting": False,
            "phase": 0.0,              # glow breath phase
            "last_glow_tick": 0.0,
            "scene": None,             # premultiplied glow scene
            # cursor
            "cx": vw // 2, "cy": vh // 2,
            "cstate": STATE_IDLE,
            "cvisible": False,
            "cfading": False,
            "cfade_t0": 0.0,
            "chidden_at": 0.0,
            "ripple_t0": None,
            "busy": False,
            "spin": 0.0,
            "last_spin": 0.0,
            "art_cache": {},
            # banner
            "banner_layer": None,
            "banner_pos": (0, 0),
            "banner_box": None,
            "banner_visible": False,
            "banner_alpha1": 1.0,      # final stationary alpha
        }
        tweens = _Tweens()
        last_render = 0.0

        def glow_level_multiplier() -> float:
            breath = 0.5 + 0.5 * math.sin(state["phase"])
            return _GLOW_LO + (_GLOW_HI - _GLOW_LO) * breath

        def rebuild_scene(mult: float | None = None, alpha_fade: float = 1.0) -> None:
            mult = glow_level_multiplier() if mult is None else mult
            img = _build_glow((vw, vh), state["r1"], state["r2"], mult)
            if alpha_fade < 1.0:
                # Fade the ALPHA, never the RGB: premultiplied colour x (1-t) with
                # untouched alpha renders as an opaque black frame (the corner
                # "black squares" seen at session exit).
                fade = _clamp(alpha_fade, 0.0, 1.0)
                a = ImageChops.multiply(
                    img.getchannel("A"), Image.new("L", (vw, vh), int(255 * fade))
                )
                img.putalpha(a)
            state["scene"] = _premultiply(img)

        def current_ripple(now: float) -> float:
            t0 = state["ripple_t0"]
            if t0 is None:
                return 0.0
            return _clamp((now - t0) / (_RIPPLE_MS / 1000.0), 0.0, 1.0)

        def banner_final_state() -> tuple[float, float]:
            """(final y position, alpha) once the entrance is done."""
            return float(_BANNER_MARGIN), state["banner_alpha1"]

        def render(now: float) -> None:
            scene = state["scene"]
            frame = (
                scene.copy()
                if scene is not None
                else Image.new("RGBa", (vw, vh), (0, 0, 0, 0))
            )

            # -- banner ---------------------------------------------------------
            box = state["banner_box"]
            layer = state["banner_layer"]
            if box is not None and (state["banner_visible"] or tweens.active("slide") or tweens.active("slide_out")):
                x0, y0, x1, y1 = box
                bh = y1 - y0
                bx = x0 - _BANNER_SHADOW
                if tweens.active("slide_out"):
                    t = tweens.get("slide_out", now)
                    start_y = -bh - _BANNER_SHADOW - _BANNER_MARGIN
                    by = _BANNER_MARGIN + (start_y - _BANNER_MARGIN) * _ease_in_cubic(t)
                    fade = 1.0 - tweens.get("bfade_out", now)
                else:
                    t = tweens.get("slide", now)
                    start_y = -bh - _BANNER_SHADOW - _BANNER_MARGIN
                    by = start_y + (_BANNER_MARGIN - start_y) * t
                    fade = tweens.get("bfade", now)
                layer = _build_banner(state["theme"], state["r1"], desktop, (vx, vy), box, fade)
                state["banner_layer"] = layer
                state["banner_pos"] = (bx, int(by))
                state["banner_visible"] = fade > 0.02
                if fade > 0.02:
                    _add_region(frame, _premultiply(layer), state["banner_pos"])

            # -- cursor ---------------------------------------------------------
            if state["cvisible"] and (state["active"] or not state["exiting"]):
                fade = 1.0
                if state["cfading"]:
                    t = _clamp((now - state["cfade_t0"]) / (_HIDE_FADE_MS / 1000.0), 0.0, 1.0)
                    fade = 1.0 - t
                if fade > 0.02:
                    layer = _build_cursor_layer(
                        state["theme"],
                        state["cstate"],
                        current_ripple(now),
                        state["busy"],
                        state["spin"],
                        state["r1"],
                        state["art_cache"],
                    )
                    if fade < 1.0:
                        a_scale = Image.new("L", layer.size, int(255 * fade))
                        layer.putalpha(ImageChops.multiply(layer.getchannel("A"), a_scale))
                    _add_region(
                        frame,
                        _premultiply(layer),
                        (state["cx"] - _CURSOR_HOT[0], state["cy"] - _CURSOR_HOT[1]),
                    )

            window.blit(frame.tobytes("raw", "BGRa"), vw, vh)

        # ---- message handling ------------------------------------------------
        def handle(message: tuple, now: float) -> bool:
            """Process one queued message. Returns False to end the loop."""
            kind = message[0]
            st = state

            if kind == "quit":
                return False

            if kind == "session_start":
                _theme, _accent, _accent2 = message[1], message[2], message[3]
                st["theme"] = _theme if _theme in (THEME_LIGHT, THEME_DARK) else _DEFAULT_THEME
                st["r1"] = _hex_to_rgb(_accent, (91, 140, 255))
                st["r2"] = _hex_to_rgb(_accent2, (173, 198, 255))
                if st["r2"] == st["r1"]:
                    st["r2"] = _toward_white(st["r1"], 0.5)
                st["art_cache"].clear()
                st["active"] = True
                st["exiting"] = False
                st["phase"] = 0.0
                st["cstate"] = STATE_IDLE
                st["busy"] = False
                st["ripple_t0"] = None

                bw = _banner_width(vw)
                bh = _BANNER_HEIGHT
                st["banner_box"] = ((vw - bw) // 2, _BANNER_MARGIN, (vw - bw) // 2 + bw, _BANNER_MARGIN + bh)
                st["banner_visible"] = False
                tweens.start("slide", _BANNER_SLIDE_MS, "out_cubic", now)
                tweens.start("bfade", _BANNER_FADE_MS, "out_quad", now)
                rebuild_scene()
                st["cx"], st["cy"] = vw // 2, vh // 2
                st["cvisible"] = True
                st["chidden_at"] = now + _HIDE_DELAY_S
                render(now)

            elif kind == "session_end":
                if not st["active"]:
                    return True
                st["exiting"] = True
                st["active"] = False
                st["busy"] = False
                tweens.start("slide_out", _BANNER_EXIT_MS, "in_cubic", now)
                tweens.start("bfade_out", _BANNER_EXIT_MS, "in_cubic", now)
                tweens.start("glow_out", _BANNER_EXIT_MS + 150, "in_cubic", now)

            elif kind == "show":
                _, x, y, state_kind = message
                if state_kind == STATE_PRESSED and st["cstate"] != STATE_PRESSED:
                    st["cstate"] = STATE_PRESSED
                elif state_kind == STATE_IDLE and st["cstate"] == STATE_PRESSED:
                    st["cstate"] = STATE_IDLE
                    st["ripple_t0"] = now  # click moment: ripple + hand→arrow
                else:
                    st["cstate"] = state_kind
                st["cx"], st["cy"] = x, y
                st["cvisible"] = True
                st["cfading"] = False
                st["chidden_at"] = now + _HIDE_DELAY_S
                if st["active"] or not st["exiting"]:
                    render(now)

            elif kind == "move":
                if st["cvisible"] and (st["active"] or not st["exiting"]):
                    st["cx"], st["cy"] = message[1], message[2]
                    st["chidden_at"] = now + _HIDE_DELAY_S
                    render(now)

            elif kind == "hide":
                st["cvisible"] = False
                st["ripple_t0"] = None
                render(now)

            elif kind == "set_busy":
                st["busy"] = bool(message[1])

            return True

        # ---- main loop ---------------------------------------------------------
        while True:
            now = time.monotonic()
            window.pump()

            try:
                while True:
                    if not handle(self._queue.get_nowait(), now):
                        raise SystemExit
            except queue.Empty:
                pass
            except SystemExit:
                break

            dirty = False
            st = state

            # glow breathing (session active only)
            if st["active"] and not st["exiting"]:
                if now - st["last_glow_tick"] >= _GLOW_TICK_MS / 1000.0:
                    st["phase"] += (2 * math.pi * (_GLOW_TICK_MS / 1000.0)) / _GLOW_PERIOD_S
                    st["last_glow_tick"] = now
                    rebuild_scene()
                    dirty = True
            elif st["exiting"] and tweens.active("glow_out"):
                t = tweens.get("glow_out", now)
                rebuild_scene(glow_level_multiplier(), alpha_fade=1.0 - t)
                dirty = True
                if tweens.done("glow_out", now):
                    tweens.drop("glow_out")
                    window.hide_window()
                    st["scene"] = None
                    st["banner_layer"] = None
                    st["banner_visible"] = False
                    st["cvisible"] = False
                    dirty = False

            # entrance/exit tweens drive the banner
            if tweens.active("slide") or tweens.active("slide_out"):
                dirty = True

            # ripple / spinner / hide-fade
            if st["cvisible"] and (st["ripple_t0"] is not None or st["busy"] or st["cfading"]):
                dirty = True
            if st["busy"] and now - st["last_spin"] >= _SPIN_STEP_MS / 1000.0:
                st["spin"] = (st["spin"] + 0.1) % 6.0
                st["last_spin"] = now
                if st["cvisible"]:
                    dirty = True
            if (
                st["cvisible"]
                and not st["exiting"]
                and not st["cfading"]
                and now > st["chidden_at"]
            ):
                st["cfading"] = True
                st["cfade_t0"] = now
                dirty = True
            if st["cfading"] and now - st["cfade_t0"] >= _HIDE_FADE_MS / 1000.0:
                st["cvisible"] = False
                st["cfading"] = False
                dirty = True

            if not dirty or (now - last_render) * 1000.0 < _TICK_MIN_MS:
                time.sleep(_FRAME_MS / 1000.0)
                continue
            last_render = now
            render(now)

        window.destroy()