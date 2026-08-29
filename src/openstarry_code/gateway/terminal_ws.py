"""Built-in WebSocket terminal: spawns a real shell and relays bytes.

Endpoint: ``/ws/builtin/terminal?token=...[&ssh_host=<host_id>]``

Shell selection (automatic):
  * Windows -> ``powershell.exe`` (Windows PowerShell, always present).
  * POSIX   -> ``$SHELL`` when set and executable, else ``bash``/``zsh``/``sh``.

With ``ssh_host=<id>`` the terminal instead spawns the system ``ssh`` client
(``ssh -p <port> <user>@<host>``) against an ``[[ssh.hosts]]`` entry from the
gateway config (see :mod:`openstarry_code.gateway.ssh_routes`). Unknown ids or
a missing ``ssh`` binary close the socket with code 1008.

Wire protocol (all frames are JSON text frames)::

    client -> server  {"type": "input",  "data": "ls\r"}
    client -> server  {"type": "resize", "cols": 120, "rows": 30}
    server -> client  {"type": "output", "data": "...terminal bytes..."}
    server -> client  {"type": "exit",   "code": 0}

Auth: the endpoint resolves a ``token`` query parameter exactly like the main
``/ws`` handshake (``resolve_auth``), so the same operator token works for
both. Origin is validated with the same guard as ``/ws``.
"""

from __future__ import annotations

import asyncio
import json
import os
import shutil
import sys
from typing import Any

import structlog
from starlette.websockets import WebSocket, WebSocketDisconnect

from openstarry_code.gateway.config import GatewayConfig
from openstarry_code.gateway.origin_guard import websocket_origin_allowed

log = structlog.get_logger(__name__)

# Bytes read per pump from the child's stdout pipe / PTY master.
_READ_CHUNK = 4096
# Hard cap on how much output we buffer for one client that stopped reading.
_OUTPUT_QUEUE_MAX = 1024 * 1024


def _pick_shell() -> list[str]:
    """Return the argv for the platform's default interactive shell."""
    if os.name == "nt":
        # Keep the child's stdout UTF-8 so CJK output survives the pipe.
        setup = (
            "[Console]::OutputEncoding = [System.Text.Encoding]::UTF8;"
            "$OutputEncoding = [System.Text.Encoding]::UTF8;"
        )
        return ["powershell.exe", "-NoLogo", "-NoExit", "-Command", setup]
    shell = os.environ.get("SHELL", "").strip()
    if shell and shutil.which(shell):
        return [shell, "-i"]
    for candidate in ("bash", "zsh", "sh"):
        resolved = shutil.which(candidate)
        if resolved:
            return [resolved, "-i"]
    return ["/bin/sh", "-i"]


def _ssh_argv(entry: Any) -> list[str]:
    """Return the argv carrying a session with the system ssh client.

    No key management here: authentication is whatever the user's ssh client
    is already configured for (agent, default keys, ssh_config, ...).
    """
    target = f"{entry.username}@{entry.host}" if entry.username else entry.host
    return ["ssh", "-p", str(entry.port), target]


def _resolve_ssh_argv(config: GatewayConfig, ssh_host: str) -> tuple[list[str] | None, str | None]:
    """Resolve the ``ssh_host`` query parameter to an ssh argv.

    Returns ``(argv, None)`` on success or ``(None, reason)`` when the host
    entry cannot be used (unknown id, disabled, or no ssh binary on PATH).
    """
    from openstarry_code.gateway.ssh_routes import find_ssh_host

    entry = find_ssh_host(config, ssh_host)
    if entry is None or not entry.enabled:
        return None, "unknown_ssh_host"
    if shutil.which("ssh") is None:
        return None, "ssh_binary_missing"
    return _ssh_argv(entry), None


class _ShellProcess:
    """Async wrapper around a spawned shell process.

    POSIX gets a real PTY via ``pty.openpty``. Windows uses ConPTY through
    ``pywinpty`` when available — without a real console PowerShell gets no
    line discipline at all, so backspace/arrow keys arrive as raw control
    bytes and do nothing (the classic "can't backspace" web-terminal bug).
    Falls back to pipe-based stdio when pywinpty is missing.
    """

    def __init__(
        self,
        process: asyncio.subprocess.Process | None,
        master_fd: int | None = None,
        conpty: Any = None,
    ) -> None:
        self.process = process
        self.master_fd = master_fd
        self.conpty = conpty
        self._reader: asyncio.Future[None] | None = None
        self._write_lock = asyncio.Lock()

    @classmethod
    async def spawn(cls, argv: list[str] | None = None) -> "_ShellProcess":
        if argv is None:
            argv = _pick_shell()
        if os.name == "nt":
            try:
                from winpty import PtyProcess as _ConPTY

                conpty = _ConPTY.spawn(argv, dimensions=(30, 120))
                return cls(process=None, conpty=conpty)
            except ImportError:
                log.warning("terminal.conpty_unavailable", hint="pip install pywinpty")
        kwargs: dict[str, Any] = {
            "stdin": asyncio.subprocess.PIPE,
            "stdout": asyncio.subprocess.PIPE,
            "stderr": asyncio.subprocess.STDOUT,
            "start_new_session": True,
            "env": dict(os.environ),
        }
        master_fd: int | None = None
        if os.name == "posix":
            import pty  # POSIX only — imported lazily.

            master_fd, slave_fd = pty.openpty()
            kwargs.update(stdin=slave_fd, stdout=slave_fd, stderr=slave_fd)
            process = await asyncio.create_subprocess_exec(*argv, **kwargs)
            os.close(slave_fd)
        else:
            process = await asyncio.create_subprocess_exec(*argv, **kwargs)
        return cls(process=process, master_fd=master_fd)

    async def read_chunks(self, sink: "asyncio.Queue[bytes]") -> None:
        """Pump child output into ``sink`` until EOF."""
        loop = asyncio.get_running_loop()
        total_buffered = 0
        try:
            if self.conpty is not None:
                # ConPTY: PtyProcess.read blocks, so poll it in a worker
                # thread. An empty read on a dead process means EOF.
                while True:
                    data = await asyncio.to_thread(self.conpty.read, _READ_CHUNK)
                    if not data:
                        if not self.conpty.isalive():
                            break
                        continue
                    _enqueue(sink, data.encode("utf-8", errors="replace"))
                    if not self.conpty.isalive():
                        # Drain a final beat so the exit banner still lands.
                        try:
                            tail = await asyncio.wait_for(
                                asyncio.to_thread(self.conpty.read, _READ_CHUNK),
                                timeout=0.5,
                            )
                        except (TimeoutError, OSError):
                            tail = ""
                        if tail:
                            _enqueue(sink, tail.encode("utf-8", errors="replace"))
                        break
            elif self.master_fd is not None:
                # PTY master: poll-read in the loop (POSIX only).
                fut: asyncio.Future[None] = loop.create_future()

                def _on_readable() -> None:
                    if fut.done():
                        return
                    try:
                        data = os.read(self.master_fd, _READ_CHUNK)
                    except BlockingIOError:
                        return
                    except OSError:
                        if not fut.done():
                            fut.set_result(None)
                        return
                    if not data:
                        if not fut.done():
                            fut.set_result(None)
                        return
                    _enqueue(sink, data)

                loop.add_reader(self.master_fd, _on_readable)
                self._reader = fut
                await fut
                loop.remove_reader(self.master_fd)
            else:
                # Pipe-based (Windows): plain stream reads.
                while True:
                    data = await self.process.stdout.read(_READ_CHUNK)
                    if not data:
                        break
                    _enqueue(sink, data)
        finally:
            await sink.put(b"")  # EOF marker

    async def write(self, data: str) -> None:
        payload = data.encode("utf-8", errors="replace")
        async with self._write_lock:
            if self.conpty is not None:
                self.conpty.write(data)
            elif self.master_fd is not None:
                os.write(self.master_fd, payload)
            elif self.process is not None and self.process.stdin is not None:
                self.process.stdin.write(payload)
                await self.process.stdin.drain()

    async def terminate(self) -> None:
        try:
            if self.conpty is not None:
                try:
                    self.conpty.terminate(force=True)
                except (OSError, AttributeError):
                    pass
            elif self.process is not None and self.process.returncode is None:
                self.process.terminate()
                try:
                    await asyncio.wait_for(self.process.wait(), timeout=3)
                except asyncio.TimeoutError:
                    self.process.kill()
                    await self.process.wait()
        except ProcessLookupError:
            pass
        finally:
            if self.master_fd is not None:
                try:
                    os.close(self.master_fd)
                except OSError:
                    pass
                self.master_fd = None


def _enqueue(sink: "asyncio.Queue[bytes]", data: bytes) -> None:
    if sink.qsize() * _READ_CHUNK > _OUTPUT_QUEUE_MAX:
        # Drop the oldest frames under backpressure instead of unbounded growth.
        try:
            sink.get_nowait()
        except asyncio.QueueEmpty:
            pass
    sink.put_nowait(data)


async def _send(ws: WebSocket, frame: dict[str, Any]) -> bool:
    try:
        await ws.send_text(json.dumps(frame, ensure_ascii=False))
        return True
    except (WebSocketDisconnect, RuntimeError):
        return False


async def _pump_output(ws: WebSocket, queue: "asyncio.Queue[bytes]") -> None:
    while True:
        chunk = await queue.get()
        if not chunk:
            break
        if not await _send(ws, {"type": "output", "data": chunk.decode("utf-8", errors="replace")}):
            break


async def terminal_ws_endpoint(websocket: WebSocket, config: GatewayConfig) -> None:
    """Handle one terminal WebSocket connection."""
    if not websocket_origin_allowed(websocket, config):
        await websocket.close(code=1008)
        return

    from openstarry_code.gateway.auth import resolve_auth

    token = (websocket.query_params.get("token") or "").strip()
    peer_ip = websocket.client.host if websocket.client is not None else None
    principal = resolve_auth(
        config,
        auth_params={"token": token} if token else {},
        role_claim="operator",
        peer_ip=peer_ip,
    )
    if principal is None:
        await websocket.close(code=1008)
        return

    await websocket.accept()
    conn_log = log.bind(remote=str(websocket.client), peer_ip=peer_ip)

    # Optional SSH mode: ?ssh_host=<id> swaps the default shell argv for the
    # system ssh client against a saved [[ssh.hosts]] entry.
    ssh_host_param = (websocket.query_params.get("ssh_host") or "").strip()
    argv: list[str] | None = None
    if ssh_host_param:
        argv, reason = _resolve_ssh_argv(config, ssh_host_param)
        if argv is None:
            conn_log.warning(
                "terminal.ssh_rejected",
                ssh_host=ssh_host_param,
                reason=reason,
            )
            await websocket.close(code=1008)
            return

    shell: _ShellProcess | None = None
    output_queue: asyncio.Queue[bytes] = asyncio.Queue()
    pump_task: asyncio.Task[None] | None = None
    reader_task: asyncio.Task[None] | None = None
    try:
        shell = await _ShellProcess.spawn(argv)
        conn_log.info("terminal.started", argv=argv if argv is not None else _pick_shell())

        # Reader pushes child output into the queue; pump forwards to the WS.
        reader_task = asyncio.create_task(shell.read_chunks(output_queue))
        pump_task = asyncio.create_task(_pump_output(websocket, output_queue))

        while True:
            raw = await websocket.receive_text()
            try:
                frame = json.loads(raw)
            except (ValueError, RecursionError):
                continue
            if not isinstance(frame, dict):
                continue
            frame_type = frame.get("type")
            if frame_type == "input":
                data = frame.get("data")
                if isinstance(data, str):
                    await shell.write(data)
            elif frame_type == "resize":
                # Pipe/PTY resize is best-effort; ignored when the platform
                # cannot apply it (Windows pipe fallback). Kept in the protocol
                # so POSIX PTY terminals can drive window size later.
                cols = frame.get("cols")
                rows = frame.get("rows")
                if isinstance(cols, int) and isinstance(rows, int) and rows > 0 and cols > 0:
                    _best_effort_resize(shell, cols, rows)
            # Unknown frames are ignored for forward compatibility.
    except WebSocketDisconnect:
        pass
    except Exception:
        conn_log.exception("terminal.error")
    finally:
        if reader_task is not None:
            reader_task.cancel()
        if pump_task is not None:
            pump_task.cancel()
        if shell is not None:
            await shell.terminate()
        try:
            await websocket.close()
        except RuntimeError:
            pass


def _best_effort_resize(shell: _ShellProcess, cols: int, rows: int) -> None:
    if shell.conpty is not None:
        try:
            shell.conpty.set_size(rows, cols)
        except (OSError, AttributeError):
            pass
        return
    if os.name != "posix" or shell.master_fd is None:
        return
    import fcntl
    import struct
    import termios

    try:
        packed = struct.pack("HHHH", rows, cols, 0, 0)
        fcntl.ioctl(shell.master_fd, termios.TIOCSWINSZ, packed)
    except OSError:
        pass
