"""MCP stdio server exposing the built-in computer-use controller.

Speaks JSON-RPC 2.0 over stdio, one UTF-8 JSON object per line (the MCP
``2024-11-05`` newline-delimited framing, matching
:mod:`openstarry_code.mcp.stdio`). ``stdout`` carries protocol messages only —
all logging goes to ``stderr`` so it can never corrupt the stream.

Run it directly:

    python -m openstarry_code.computer_use.mcp_server

Tools: ``session_start`` / ``session_end`` bracket a visual session (glass
banner, breathing border glow, theme-matched cursor artwork, global Esc
abort hook); the action tools ``screenshot``, ``move``, ``left_click``,
``right_click``, ``double_click``, ``drag``, ``type_text``, ``press_key``,
``scroll`` are humanized by the controller and mirrored by the overlay.
Pressing Esc mid-action trips the abort event and the in-flight
``tools/call`` answers ``isError`` with 「用户按 Esc 中止了电脑使用」.
"""

from __future__ import annotations

import base64
import json
import os
import re
import sys
import threading
from typing import Any, Callable

import structlog

from openstarry_code.computer_use.session import (
    ComputerUseAbortedError,
    ComputerUseSession,
    EscapeAbortHook,
)

PROTOCOL_VERSION = "2024-11-05"
SERVER_NAME = "openstarry-computer-use"

_VALID_THEMES = frozenset({"light", "dark"})
_HEX_COLOR_RE = re.compile(r"^#[0-9a-fA-F]{6}$")


def _configure_logging() -> None:
    """Route structlog output to stderr; stdout stays protocol-only."""
    structlog.configure(
        processors=[
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.dev.ConsoleRenderer(colors=False),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(20),
        logger_factory=structlog.PrintLoggerFactory(file=sys.stderr),
        cache_logger_on_first_use=True,
    )


log = structlog.get_logger(__name__)

try:
    from openstarry_code import __version__ as _PACKAGE_VERSION
except Exception:  # pragma: no cover - running outside an install
    _PACKAGE_VERSION = "0.0.0"


# ---------------------------------------------------------------------------
# Tool definitions (input schemas + Chinese descriptions)
# ---------------------------------------------------------------------------


def _number(description: str, **kwargs: Any) -> dict[str, Any]:
    return {"type": "number", "description": description, **kwargs}


def _integer(description: str, **kwargs: Any) -> dict[str, Any]:
    return {"type": "integer", "description": description, **kwargs}


def _string(description: str) -> dict[str, Any]:
    return {"type": "string", "description": description}


def _boolean(description: str) -> dict[str, Any]:
    return {"type": "boolean", "description": description}


def _schema(properties: dict[str, Any], required: list[str]) -> dict[str, Any]:
    return {
        "type": "object",
        "properties": properties,
        "required": required,
        "additionalProperties": False,
    }


TOOLS: list[dict[str, Any]] = [
    {
        "name": "session_start",
        "description": (
            "开始一次电脑使用会话：屏幕顶部显示毛玻璃横幅、四周出现呼吸泛光、"
            "待命光标亮出（浅色/深色光标由主题决定），并启用全局 Esc 中止钩子。"
            "执行任何鼠标/键盘动作前必须先调用本工具。"
        ),
        "inputSchema": _schema(
            {
                "theme": _string(
                    "界面主题：'light'（浅色光标+浅色横幅）或 'dark'（深色），"
                    "建议与当前系统主题一致"
                ),
                "accent": _string(
                    "可选强调色（泛光与点缀），十六进制格式如 '#5b8cff'"
                ),
                "accent2": _string(
                    "可选第二渐变色：边框泛光会沿屏幕四周从 accent 渐变到本色"
                    "（如 '#ff9ecf' 粉色），不传则默认向白色渐变"
                ),
            },
            ["theme"],
        ),
    },
    {
        "name": "session_end",
        "description": (
            "结束电脑使用会话：横幅、边框泛光与光标全部淡出退场，并卸载 Esc 中止钩子。"
        ),
        "inputSchema": _schema({}, []),
    },
    {
        "name": "screenshot",
        "description": (
            "截取当前屏幕并返回 PNG 图片。执行任何鼠标/键盘动作前请先截图观察屏幕，"
            "再根据画面决定坐标。"
        ),
        "inputSchema": _schema({}, []),
    },
    {
        "name": "move",
        "description": "仿人手将鼠标沿平滑缓动路径移动到绝对坐标 (x, y)，单位为屏幕像素。",
        "inputSchema": _schema(
            {
                "x": _number("目标 X 坐标（像素，屏幕左上角为原点）"),
                "y": _number("目标 Y 坐标（像素）"),
                "duration": _number("移动总时长（秒），默认 0.5"),
            },
            ["x", "y"],
        ),
    },
    {
        "name": "left_click",
        "description": "先仿人手移动到 (x, y)，停顿后单击左键。",
        "inputSchema": _schema(
            {
                "x": _number("目标 X 坐标（像素）"),
                "y": _number("目标 Y 坐标（像素）"),
                "duration": _number("移动总时长（秒），默认 0.5"),
            },
            ["x", "y"],
        ),
    },
    {
        "name": "right_click",
        "description": "先仿人手移动到 (x, y)，停顿后单击右键（通常用于打开上下文菜单）。",
        "inputSchema": _schema(
            {
                "x": _number("目标 X 坐标（像素）"),
                "y": _number("目标 Y 坐标（像素）"),
                "duration": _number("移动总时长（秒），默认 0.5"),
            },
            ["x", "y"],
        ),
    },
    {
        "name": "double_click",
        "description": "先仿人手移动到 (x, y)，停顿后双击左键。",
        "inputSchema": _schema(
            {
                "x": _number("目标 X 坐标（像素）"),
                "y": _number("目标 Y 坐标（像素）"),
                "duration": _number("移动总时长（秒），默认 0.5"),
            },
            ["x", "y"],
        ),
    },
    {
        "name": "drag",
        "description": (
            "在 (x1, y1) 按下左键，沿缓动曲线拖拽到 (x2, y2) 后松开。"
            "适用于拖动滑块、移动窗口、框选等操作。"
        ),
        "inputSchema": _schema(
            {
                "x1": _number("起点 X 坐标（像素）"),
                "y1": _number("起点 Y 坐标（像素）"),
                "x2": _number("终点 X 坐标（像素）"),
                "y2": _number("终点 Y 坐标（像素）"),
                "duration": _number("拖拽总时长（秒），默认 0.8"),
                "virtual": _boolean(
                    "虚拟模式（第二层虚拟鼠标）：拖拽完成后立即还原你的真实光标。默认 false。"
                ),
            },
            ["x1", "y1", "x2", "y2"],
        ),
    },
    {
        "name": "type_text",
        "description": (
            "仿人手逐字输入文本（字符间带随机停顿）。中文等非 ASCII 字符会自动"
            "写入剪贴板后粘贴，可放心输入中文。virtual=true 时改用 WM_CHAR "
            "直投前台窗口：不抢焦点、不受输入法影响，中英文/空格/标点原样落键。"
        ),
        "inputSchema": _schema(
            {
                "text": _string("要输入的文本内容"),
                "virtual": _boolean(
                    "虚拟打字模式：不改变焦点、绕过输入法，默认 false。"
                ),
            },
            ["text"],
        ),
    },
    {
        "name": "press_key",
        "description": (
            "按下并释放一个按键，如 'enter'、'esc'、'tab'、'backspace'、'delete'、"
            "'space'、'f5'、'up'、'down' 等。"
        ),
        "inputSchema": _schema(
            {"key": _string("按键名称，如 enter / esc / tab / f5 / up")},
            ["key"],
        ),
    },
    {
        "name": "scroll",
        "description": "滚动鼠标滚轮：正数向上滚动，负数向下滚动，数值大致对应滚动格数。",
        "inputSchema": _schema(
            {"amount": _integer("滚动量，正数向上、负数向下")},
            ["amount"],
        ),
    },
]


# ---------------------------------------------------------------------------
# Argument parsing
# ---------------------------------------------------------------------------


class _ArgumentError(ValueError):
    """Raised when tools/call arguments fail validation."""


def _as_number(arguments: dict[str, Any], name: str) -> float:
    value = arguments.get(name)
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise _ArgumentError(f"参数 {name!r} 必须是数字")
    return float(value)


def _as_optional_number(arguments: dict[str, Any], name: str, default: float) -> float:
    if arguments.get(name) is None:
        return default
    return _as_number(arguments, name)


def _as_string(arguments: dict[str, Any], name: str) -> str:
    value = arguments.get(name)
    if not isinstance(value, str):
        raise _ArgumentError(f"参数 {name!r} 必须是字符串")
    return value


# ---------------------------------------------------------------------------
# Server
# ---------------------------------------------------------------------------


class ComputerUseMcpServer:
    """Line-delimited JSON-RPC 2.0 MCP server over stdio."""

    def __init__(self, stdin: Any = None, stdout: Any = None) -> None:
        self._stdin = stdin if stdin is not None else sys.stdin.buffer
        self._stdout = stdout if stdout is not None else sys.stdout.buffer
        self._controller: Any = None
        self._controller_error: Exception | None = None
        self._session = ComputerUseSession()
        self._abort_hook = EscapeAbortHook(self._session.abort_event)
        self._abort_watcher: threading.Thread | None = None
        self._handlers: dict[str, Callable[[dict[str, Any]], Any]] = {
            "session_start": self._tool_session_start,
            "session_end": self._tool_session_end,
            "screenshot": self._tool_screenshot,
            "move": self._tool_move,
            "left_click": self._tool_left_click,
            "right_click": self._tool_right_click,
            "double_click": self._tool_double_click,
            "drag": self._tool_drag,
            "type_text": self._tool_type_text,
            "press_key": self._tool_press_key,
            "scroll": self._tool_scroll,
        }

    # -- controller lifecycle ------------------------------------------------

    def _get_controller(self) -> Any:
        """Instantiate the controller lazily (pyautogui loads at first use)."""
        if self._controller is None:
            if self._controller_error is not None:
                raise self._controller_error
            from openstarry_code.computer_use.controller import ComputerUseController

            self._controller = ComputerUseController()
        return self._controller

    def _controller_error_result(self, exc: Exception) -> dict[str, Any]:
        return {
            "content": [
                {
                    "type": "text",
                    "text": f"电脑使用功能当前不可用：{type(exc).__name__}: {exc}",
                }
            ],
            "isError": True,
        }

    # -- tool implementations ------------------------------------------------

    def _tool_session_start(self, arguments: dict[str, Any]) -> dict[str, Any]:
        theme = str(arguments.get("theme") or "").strip().lower()
        if theme not in _VALID_THEMES:
            raise _ArgumentError("参数 theme 必须是 'light' 或 'dark'")
        accent = arguments.get("accent")
        if accent is not None:
            accent = str(accent).strip()
            if not _HEX_COLOR_RE.match(accent):
                raise _ArgumentError("参数 accent 必须是 '#RRGGBB' 格式的十六进制颜色")
        accent2 = arguments.get("accent2")
        if accent2 is not None:
            accent2 = str(accent2).strip()
            if not _HEX_COLOR_RE.match(accent2):
                raise _ArgumentError("参数 accent2 必须是 '#RRGGBB' 格式的十六进制颜色")
        controller = self._get_controller()
        controller.begin_session(theme=theme, accent=accent, accent2=accent2)
        self._abort_hook.start()  # global Esc listener for this session
        self._start_abort_watcher()
        accent_note = f"，强调色 {accent}" if accent else ""
        return {
            "content": [
                {
                    "type": "text",
                    "text": (
                        f"已开始电脑使用会话（主题 {theme}{accent_note}）。屏幕上会显示"
                        "「Starry 正在使用你的电脑」横幅与边框泛光；用户随时可以按 "
                        "Esc 中止，此时当前动作会立即失败。"
                    ),
                }
            ]
        }

    def _tool_session_end(self, arguments: dict[str, Any]) -> dict[str, Any]:
        del arguments
        controller = self._get_controller()
        controller.end_session()
        self._abort_hook.stop()
        return {
            "content": [
                {
                    "type": "text",
                    "text": "已结束电脑使用会话，屏幕上的横幅、泛光与光标均已退场。",
                }
            ]
        }

    def _start_abort_watcher(self) -> None:
        """One daemon thread that reacts to Esc the moment it is pressed.

        The keyboard hook itself only sets the abort event; this watcher does
        the teardown (visual exit + state persistence + hook unload) off the
        hook thread and off the tool-call thread.
        """
        if self._abort_watcher is not None and self._abort_watcher.is_alive():
            return

        def watch() -> None:
            self._session.abort_event.wait()
            try:
                self._get_controller().abort_session()
            except Exception as exc:
                log.error("computer_use.abort_teardown_failed", error=repr(exc))
            self._abort_hook.stop()

        self._abort_watcher = threading.Thread(
            target=watch, name="openstarry-cu-abort-watcher", daemon=True
        )
        self._abort_watcher.start()

    def shutdown(self) -> None:
        """Best-effort cleanup when the stdio loop ends (hook, visuals, state)."""
        try:
            self._abort_hook.stop()
        except Exception:
            pass
        try:
            if self._controller is not None:
                self._controller.end_session()
        except Exception:
            pass

    def _tool_screenshot(self, arguments: dict[str, Any]) -> dict[str, Any]:
        del arguments
        png = self._get_controller().screenshot()
        return {
            "content": [
                {
                    "type": "image",
                    "data": base64.b64encode(png).decode("ascii"),
                    "mimeType": "image/png",
                }
            ]
        }

    def _tool_move(self, arguments: dict[str, Any]) -> dict[str, Any]:
        x = _as_number(arguments, "x")
        y = _as_number(arguments, "y")
        duration = _as_optional_number(arguments, "duration", 0.5)
        virtual = bool(arguments.get("virtual", False))
        cx, cy = self._get_controller().move(x, y, duration=duration, virtual=virtual)
        suffix = "（虚拟模式，已还原你的光标）" if virtual else ""
        return {"content": [{"type": "text", "text": f"已将鼠标移动到 ({cx}, {cy}){suffix}"}]}

    def _tool_left_click(self, arguments: dict[str, Any]) -> dict[str, Any]:
        x = _as_number(arguments, "x")
        y = _as_number(arguments, "y")
        duration = _as_optional_number(arguments, "duration", 0.5)
        virtual = bool(arguments.get("virtual", False))
        cx, cy = self._get_controller().left_click(x, y, duration=duration, virtual=virtual)
        suffix = "（虚拟模式，已还原你的光标）" if virtual else ""
        return {"content": [{"type": "text", "text": f"已在 ({cx}, {cy}) 左键单击{suffix}"}]}

    def _tool_right_click(self, arguments: dict[str, Any]) -> dict[str, Any]:
        x = _as_number(arguments, "x")
        y = _as_number(arguments, "y")
        duration = _as_optional_number(arguments, "duration", 0.5)
        virtual = bool(arguments.get("virtual", False))
        cx, cy = self._get_controller().right_click(x, y, duration=duration, virtual=virtual)
        suffix = "（虚拟模式，已还原你的光标）" if virtual else ""
        return {"content": [{"type": "text", "text": f"已在 ({cx}, {cy}) 右键单击{suffix}"}]}

    def _tool_double_click(self, arguments: dict[str, Any]) -> dict[str, Any]:
        x = _as_number(arguments, "x")
        y = _as_number(arguments, "y")
        duration = _as_optional_number(arguments, "duration", 0.5)
        virtual = bool(arguments.get("virtual", False))
        cx, cy = self._get_controller().double_click(x, y, duration=duration, virtual=virtual)
        suffix = "（虚拟模式，已还原你的光标）" if virtual else ""
        return {"content": [{"type": "text", "text": f"已在 ({cx}, {cy}) 双击{suffix}"}]}

    def _tool_drag(self, arguments: dict[str, Any]) -> dict[str, Any]:
        x1 = _as_number(arguments, "x1")
        y1 = _as_number(arguments, "y1")
        x2 = _as_number(arguments, "x2")
        y2 = _as_number(arguments, "y2")
        duration = _as_optional_number(arguments, "duration", 0.8)
        virtual = bool(arguments.get("virtual", False))
        ex, ey = self._get_controller().drag(
            x1, y1, x2, y2, duration=duration, virtual=virtual
        )
        suffix = "（虚拟模式，已还原你的光标）" if virtual else ""
        return {
            "content": [
                {
                    "type": "text",
                    "text": f"已从 ({int(x1)}, {int(y1)}) 拖拽到 ({ex}, {ey}){suffix}",
                }
            ]
        }

    def _tool_type_text(self, arguments: dict[str, Any]) -> dict[str, Any]:
        text = _as_string(arguments, "text")
        virtual = bool(arguments.get("virtual", False))
        typed = self._get_controller().type_text(text, virtual=virtual)
        suffix = "（虚拟模式，未抢焦点）" if virtual else ""
        return {"content": [{"type": "text", "text": f"已输入 {typed} 个字符{suffix}"}]}

    def _tool_press_key(self, arguments: dict[str, Any]) -> dict[str, Any]:
        key = _as_string(arguments, "key")
        normalized = self._get_controller().press_key(key)
        return {"content": [{"type": "text", "text": f"已按下 {normalized} 键"}]}

    def _tool_scroll(self, arguments: dict[str, Any]) -> dict[str, Any]:
        amount = _as_number(arguments, "amount")
        moved = self._get_controller().scroll(int(amount))
        if moved == 0:
            text = "滚动量为 0，未执行滚动"
        else:
            direction = "向上" if moved > 0 else "向下"
            text = f"已{direction}滚动 {abs(moved)} 格"
        return {"content": [{"type": "text", "text": text}]}

    # -- JSON-RPC dispatch ---------------------------------------------------

    def handle_message(self, message: Any) -> dict[str, Any] | None:
        """Return the JSON-RPC response for ``message`` (None = no response)."""
        if not isinstance(message, dict):
            return self._error(None, -32600, "Invalid Request")
        msg_id = message.get("id")
        method = message.get("method")
        if not isinstance(method, str):
            if msg_id is None:
                return None
            return self._error(msg_id, -32600, "Invalid Request")
        # Notifications never get a response; tolerate unknown ones too.
        if msg_id is None:
            if method == "notifications/initialized":
                log.debug("computer_use.mcp_initialized")
            return None

        params = message.get("params") or {}
        if not isinstance(params, dict):
            return self._error(msg_id, -32602, "Invalid params")

        if method == "initialize":
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {
                    "protocolVersion": PROTOCOL_VERSION,
                    "capabilities": {"tools": {}},
                    "serverInfo": {
                        "name": SERVER_NAME,
                        "version": _PACKAGE_VERSION,
                    },
                },
            }
        if method == "ping":
            return {"jsonrpc": "2.0", "id": msg_id, "result": {}}
        if method == "tools/list":
            return {"jsonrpc": "2.0", "id": msg_id, "result": {"tools": TOOLS}}
        if method == "tools/call":
            return {"jsonrpc": "2.0", "id": msg_id, "result": self._call_tool(params)}
        return self._error(
            msg_id, -32601, f"Method not found: {method}"
        )

    def _call_tool(self, params: dict[str, Any]) -> dict[str, Any]:
        name = params.get("name")
        arguments = params.get("arguments") or {}
        if not isinstance(name, str) or name not in self._handlers:
            return {
                "content": [{"type": "text", "text": f"未知工具：{name!r}"}],
                "isError": True,
            }
        if not isinstance(arguments, dict):
            return {
                "content": [{"type": "text", "text": "arguments 必须是对象"}],
                "isError": True,
            }
        try:
            return self._handlers[name](arguments)
        except _ArgumentError as exc:
            return {"content": [{"type": "text", "text": str(exc)}], "isError": True}
        except ComputerUseAbortedError:
            # Esc was pressed while the action ran. The watcher thread already
            # tore the visuals down and persisted aborted=true; persist again
            # here so the state is on disk before this response is written.
            try:
                self._session.mark_aborted()
            except Exception:
                pass
            return {
                "content": [{"type": "text", "text": "用户按 Esc 中止了电脑使用"}],
                "isError": True,
            }
        except Exception as exc:
            log.error("computer_use.tool_failed", tool=name, error=repr(exc))
            return self._controller_error_result(exc)

    @staticmethod
    def _error(msg_id: Any, code: int, message: str) -> dict[str, Any]:
        return {
            "jsonrpc": "2.0",
            "id": msg_id,
            "error": {"code": code, "message": message},
        }

    # -- stdio loop ----------------------------------------------------------

    def serve(self) -> int:
        """Read one JSON message per line until stdin closes."""
        log.info("computer_use.mcp_server_start", pid=os.getpid())
        while True:
            line = self._stdin.readline()
            if not line:
                return 0
            if isinstance(line, bytes):
                line = line.decode("utf-8", errors="replace")
            line = line.strip()
            if not line:
                continue
            try:
                message = json.loads(line)
            except json.JSONDecodeError:
                self._send(self._error(None, -32700, "Parse error"))
                continue
            try:
                response = self.handle_message(message)
            except Exception as exc:  # never let the loop die
                log.error("computer_use.mcp_handler_crashed", error=repr(exc))
                msg_id = message.get("id") if isinstance(message, dict) else None
                response = self._error(msg_id, -32603, "Internal error")
            if response is not None:
                self._send(response)

    def _send(self, payload: dict[str, Any]) -> None:
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8") + b"\n"
        self._stdout.write(data)
        self._stdout.flush()


def main() -> int:
    _configure_logging()
    server = ComputerUseMcpServer()
    code = 0
    try:
        code = server.serve()
    except KeyboardInterrupt:
        code = 0
    finally:
        # Unhook the Esc listener and tear the visual session down *before*
        # os._exit skips atexit handlers.
        server.shutdown()
    # Leave via os._exit: the cursor overlay's Tcl interpreter lives on a
    # daemon thread, and CPython's interpreter finalization would otherwise
    # trip Tcl's cross-thread async-handler teardown (the "Tcl_AsyncDelete:
    # async handler deleted by the wrong thread" noise on stderr). Protocol
    # output is already flushed after every message, so nothing is lost.
    sys.stdout.flush()
    sys.stderr.flush()
    os._exit(code)
    return code  # pragma: no cover - unreachable, keeps type checkers happy


if __name__ == "__main__":
    raise SystemExit(main())
