"""QQ Bot Platform channel adapter.

Drives the official QQ Bot Platform via ``qq-botpy`` (``botpy`` package). The
SDK exposes a persistent WebSocket via :class:`botpy.Client`; we subclass it
and override ``on_c2c_message_create`` / ``on_group_at_message_create`` to
push parsed :class:`~openstarry_code.channels.types.IncomingMessage` instances into an
internal queue consumed by :meth:`QQChannel.receive`.

Coverage limit
--------------
``qq-botpy`` covers the **official QQ Bot Platform only** — not consumer QQ.

Streaming
---------
QQ has **no message-edit primitive**, so :meth:`send_streaming` emits bounded
append-only updates instead of editing a single message.
:meth:`edit` and :meth:`delete` are unsupported and exist to satisfy the
:class:`~openstarry_code.channels.types.ManagedChannel` Protocol surface.
"""

from __future__ import annotations

import asyncio
import contextlib
import hashlib
from collections.abc import AsyncIterator
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast

import httpx
import structlog
from pydantic import BaseModel

from openstarry_code.channels._util import EventDedupeCache
from openstarry_code.channels.contract import (
    ChannelCapabilityProfile,
    ChannelLengthUnit,
    ChannelPlatformCapability,
    ChannelPlatformCapabilityStatus,
    ChannelPlatformCategories,
    ChannelPlatformManifest,
    ChannelSendResult,
)
from openstarry_code.channels.types import (
    Attachment,
    AuthenticatedPrincipal,
    ChannelHealth,
    IncomingMessage,
    IngressProvenance,
    IngressVerification,
    OutgoingMessage,
    UnsupportedChannelOperation,
)

log = structlog.get_logger(__name__)

# Channel-contract constants — downstream consumers read the same shape
# across adapters.
CAPABILITY_TIER = "YELLOW-experimental"

# QQ official bot is a DM/group channel — the permission matrix denies
# admin-only.
DM_SAFETY_TIERS: tuple[str, ...] = ("safe", "confirm")

RETRYABLE_ERROR_CLASSES: tuple[str, ...] = (
    "transport_transient",
    "rate_limited",
    "channel_degraded",
)
FATAL_ERROR_CLASSES: tuple[str, ...] = (
    "auth_invalid",
    "payload_rejected",
    "target_missing",
    "contract_violation",
)

_DEDUPE_SIZE = 4096
_STREAM_FLUSH_SECONDS = 0.8
_STREAM_FLUSH_CHARS = 600
_STREAM_MESSAGE_CHARS = 1800
_QQ_MD5_PREFIX_BYTES = 10_002_432
_QQ_PASSIVE_REPLY_LIMITS = {"c2c": 4, "group": 5}
_QQ_MSG_SEQ_CACHE_LIMIT = 8192


def _qq_file_type(path: Path) -> int:
    suffix = path.suffix.lower()
    if suffix in {".png", ".jpg", ".jpeg", ".gif", ".webp"}:
        return 1
    if suffix == ".mp4":
        return 2
    if suffix == ".silk":
        return 3
    return 4


def _qq_attachment_file_type(attachment: Attachment) -> int:
    mime = (attachment.mime_type or "").lower()
    if mime in {"image/png", "image/jpeg"}:
        return 1
    if mime == "video/mp4":
        return 2
    if mime in {"audio/silk", "audio/vnd.tencent.silk"}:
        return 3
    return _qq_file_type(Path(attachment.name))


class QQChannelConfig(BaseModel):
    """Adapter-level config for the QQ Bot Platform channel.

    Defaults are empty so the existing ``ChannelManager.from_config``
    branch (which currently passes only ``name``) keeps working until a
    follow-up wires the real entry fields, populating ``app_id`` and
    ``app_secret`` from
    :class:`openstarry_code.gateway.config.QQChannelEntry`.
    """

    name: str = "qq"
    app_id: str = ""
    app_secret: str = ""

    model_config = {}


def _resolve_botpy_client_base() -> type:
    """Return the ``botpy.Client`` class.

    Imported lazily so the module stays importable for unit tests that
    mock the SDK out of the picture without the ``[qq]`` extra
    installed.
    """
    from botpy import Client as BotpyClient  # type: ignore[import-untyped]

    return cast(type, BotpyClient)


class _QQClientFallback:
    """Sentinel placeholder so :class:`QQChannel` can still be defined
    when the ``qq-botpy`` extra is not installed.

    :meth:`start` re-raises a clear error if the extra is missing.
    """

    async def start(self, *args: Any, **kwargs: Any) -> None:  # noqa: D401
        raise RuntimeError("QQ adapter dependency missing — reinstall OpenStarry Code")

    async def close(self) -> None:  # noqa: D401
        return None


try:  # pragma: no cover — exercised whenever the qq extra is installed
    _QQClientBase: type = _resolve_botpy_client_base()
except ImportError:  # pragma: no cover — kept for environments without [qq]
    _QQClientBase = _QQClientFallback


class QQChannel(_QQClientBase):  # type: ignore[misc, valid-type]
    """Channel adapter for the official QQ Bot Platform.

    Subclasses :class:`botpy.Client` so the SDK's name-based dispatcher
    can find ``on_c2c_message_create`` / ``on_group_at_message_create``
    overrides via ``getattr``. Inbound messages are normalized into
    :class:`IncomingMessage` and pushed into an :class:`asyncio.Queue`
    consumed by :meth:`receive`.

    Outbound text routes by ``metadata['chat_type']`` to either
    ``post_c2c_message`` (``c2c``) or ``post_group_message``
    (``group``). A per-target ``msg_seq`` counter satisfies the QQ API
    dedup rules. There is no edit/delete API on the official platform.
    """

    config: QQChannelConfig
    # QQ has no edit primitive, so progress is delivered as bounded messages.
    # Keep this explicit so a future adapter policy change cannot hide the
    # thinking and execution stream behind a final-only response.
    STREAM_UPDATE_STRATEGY = "adapter_stream"

    def __init__(self, config: QQChannelConfig) -> None:
        # Lazy SDK import — keeps the adapter usable even when the
        # ``[qq]`` extra isn't installed and the test suite injects a
        # mocked ``api``.
        try:
            from botpy import Intents  # type: ignore[import-untyped]
        except ImportError:  # pragma: no cover — only triggered without [qq]
            super().__init__()  # type: ignore[call-arg]
            self.config = config
            self._init_state()
            return

        intents = Intents(public_messages=True, direct_message=True)
        try:
            asyncio.get_running_loop()
        except RuntimeError:
            # qq-botpy still captures an event loop during construction.  On
            # Python 3.13+, get_event_loop() without a current loop is
            # deprecated, so establish one explicitly for synchronous config
            # and capability-inspection call sites.
            asyncio.set_event_loop(asyncio.new_event_loop())
        # ``ext_handlers=False`` prevents the default file handler from
        # writing ``botpy.log`` and crashing on read-only filesystems.
        super().__init__(intents=intents, ext_handlers=False)
        self.config = config
        self._init_state()

    def _init_state(self) -> None:
        self._inbound_queue: asyncio.Queue[IncomingMessage] = asyncio.Queue()
        self._dedupe = EventDedupeCache(max_size=_DEDUPE_SIZE)
        self._run_task: asyncio.Task[None] | None = None
        self._last_message_at: datetime | None = None
        # Cache the most recent envelope so ``send_streaming(chunks)``
        # invocations from the dispatcher (which carry no target kwarg)
        # can derive ``chat_type`` / target from the original message.
        self._last_incoming_envelope: IncomingMessage | None = None
        self._msg_count: int = 0
        self._connected: bool = False
        self._msg_seq: dict[str, int] = {}

    @property
    def capability_profile(self) -> ChannelCapabilityProfile:
        return ChannelCapabilityProfile(
            channel_type="qq",
            max_message_len=2000,
            length_unit=ChannelLengthUnit.CODE_POINTS,
            splits_natively=False,
            group_chat=True,
            mentions=True,
            reply=True,
            native_file_upload=True,
            media=True,
            transports=("websocket",),
            notes=(
                "QQ Bot Platform media and file delivery use direct multipart upload, "
                "with URL upload retained for compatibility.",
            ),
        )

    @property
    def platform_capability_manifest(self) -> ChannelPlatformManifest:
        return ChannelPlatformManifest.from_channel_profile(
            self.capability_profile,
        ).with_capabilities(
            ChannelPlatformCapability(
                category=ChannelPlatformCategories.FILES,
                status=ChannelPlatformCapabilityStatus.SUPPORTED,
                notes=("Local files use the QQ multipart upload_prepare flow.",),
            ),
            ChannelPlatformCapability(
                category=ChannelPlatformCategories.MEDIA,
                status=ChannelPlatformCapabilityStatus.SUPPORTED,
                notes=("Images, MP4 video, and silk audio use QQ rich-media messages.",),
            ),
        )

    @property
    def capabilities(self) -> frozenset[str]:
        return self.capability_profile.capability_tags()

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    async def start(self) -> None:  # type: ignore[override]
        """Spawn the WebSocket loop as a background task and return."""
        cfg = self.config
        if not cfg.app_id or not cfg.app_secret:
            raise ValueError("qq.start: app_id and app_secret are required")

        self._run_task = asyncio.create_task(self._run_forever(), name="qq:gateway")
        log.info("qq.starting", name=cfg.name, app_id=cfg.app_id)

    async def _run_forever(self) -> None:
        """Drive the underlying ``botpy.Client.start`` coroutine.

        ``botpy.Client.start`` returns when the websocket session
        terminates. Treat one return as one iteration; surface the
        exception via the structured log and exit so the supervising
        task can be inspected by ``health_check``.
        """
        cfg = self.config
        try:
            # Reach over the override to invoke the SDK's ``start``.
            await super().start(appid=cfg.app_id, secret=cfg.app_secret)  # type: ignore[misc]
        except asyncio.CancelledError:
            raise
        except Exception as exc:  # pragma: no cover — surfaces only at runtime
            log.warning("qq.gateway_loop_failed", error=str(exc))
        finally:
            self._connected = False

    async def on_ready(self) -> None:
        """Mark the adapter connected only after the SDK authenticates."""
        self._connected = True
        log.info("qq.started", name=self.config.name, app_id=self.config.app_id)

    async def stop(self) -> None:
        """Cancel the WebSocket task and close the underlying SDK client."""
        task = self._run_task
        self._run_task = None
        if task is not None and not task.done():
            task.cancel()
            try:
                await task
            except (asyncio.CancelledError, Exception):
                pass
        # ``botpy.Client.close`` is async (verified via help()).
        try:
            await super().close()  # type: ignore[misc]
        except Exception:
            # Closing twice / before start is harmless.
            pass
        self._connected = False
        log.info("qq.stopped", name=self.config.name)

    async def health_check(self) -> ChannelHealth:
        running = self._connected and self._run_task is not None and not self._run_task.done()
        return ChannelHealth(
            connected=running,
            last_message_at=self._last_message_at,
            extra={
                "transport": "ws",
                "msg_count": self._msg_count,
            },
        )

    # ------------------------------------------------------------------
    # Inbound — botpy event hooks
    # ------------------------------------------------------------------

    async def on_c2c_message_create(self, message: Any) -> None:  # noqa: D401
        """Dispatched by ``botpy`` for direct (C2C) messages."""
        self._enqueue_message(message, is_group=False)

    async def on_group_at_message_create(self, message: Any) -> None:  # noqa: D401
        """Dispatched by ``botpy`` for group ``@bot`` messages."""
        self._enqueue_message(message, is_group=True)

    def _enqueue_message(self, raw: Any, *, is_group: bool) -> None:
        msg_id = getattr(raw, "id", None) or ""
        if msg_id and not self._dedupe.check_and_add(msg_id):
            log.debug("qq.dedup_drop", msg_id=msg_id, is_group=is_group)
            return

        author = getattr(raw, "author", None)
        if is_group:
            author_id = getattr(author, "member_openid", "") or ""
            group_openid = getattr(raw, "group_openid", "") or ""
            channel_id = group_openid or msg_id
            chat_type = "group"
        else:
            author_id = getattr(author, "user_openid", "") or ""
            group_openid = ""
            channel_id = author_id or msg_id
            chat_type = "c2c"

        content = (getattr(raw, "content", "") or "").strip()

        metadata: dict[str, Any] = {
            "is_group": is_group,
            "chat_type": chat_type,
            "msg_id": msg_id,
            "author_id": author_id,
        }
        if group_openid:
            metadata["group_openid"] = group_openid

        sender_id = author_id or "unknown"
        msg = IncomingMessage(
            sender_id=sender_id,
            channel_id=channel_id or "unknown",
            content=content,
            metadata=metadata,
            provenance=IngressProvenance(
                provider="qq",
                account_id=self.config.app_id,
                transport="websocket",
                verification=IngressVerification.SDK_SESSION,
                event_id=msg_id or None,
                principal=AuthenticatedPrincipal(subject_id=sender_id),
            ),
        )
        from openstarry_code.channels.delivery_store import durable_enqueue

        durable_enqueue(self, msg, self._inbound_queue)
        self._msg_count += 1
        self._last_message_at = datetime.now(UTC)
        log.debug(
            "qq.inbound_received",
            msg_id=msg_id,
            is_group=is_group,
            chat_type=chat_type,
        )

    async def receive(self) -> IncomingMessage:
        msg = await self._inbound_queue.get()
        self._last_incoming_envelope = msg
        return msg

    # ------------------------------------------------------------------
    # Outbound
    # ------------------------------------------------------------------

    def _next_msg_seq(self, target: str) -> int:
        if target not in self._msg_seq and len(self._msg_seq) >= _QQ_MSG_SEQ_CACHE_LIMIT:
            self._msg_seq.pop(next(iter(self._msg_seq)))
        seq = self._msg_seq.get(target, 0) + 1
        self._msg_seq[target] = seq
        return seq

    def _passive_msg_seq(self, chat_type: str, msg_id: str | None, target: str) -> int | None:
        """Reserve a passive reply slot, or return ``None`` for an active send.

        QQ limits replies tied to one inbound ``msg_id`` to four C2C or five
        group messages. Once the budget is exhausted, omitting ``msg_id``
        switches the same endpoint to an active message addressed by the
        OpenID, preserving later final text and media delivery.
        """
        if not msg_id:
            return None
        limit = _QQ_PASSIVE_REPLY_LIMITS.get(chat_type)
        if limit is None:
            return None
        key = f"{chat_type}:{msg_id}"
        current = self._msg_seq.get(key, 0)
        if current >= limit:
            log.info(
                "qq.passive_reply_budget_exhausted",
                chat_type=chat_type,
                target=target,
                msg_id=msg_id,
                limit=limit,
            )
            return None
        return self._next_msg_seq(key)

    def is_group_mentioned(self, msg: IncomingMessage) -> bool:
        """QQ group callbacks are already scoped to ``@bot`` messages."""
        if not bool(msg.metadata.get("is_group")):
            return True
        return msg.metadata.get("chat_type") == "group" and bool(msg.metadata.get("msg_id"))

    def build_reply_message(self, content: str, inbound: IncomingMessage) -> OutgoingMessage:
        """Build a passive QQ reply from the triggering inbound envelope."""
        meta = inbound.metadata or {}
        chat_type = meta.get("chat_type", "")
        msg_id = meta.get("msg_id") or meta.get("reply_to_msg_id")

        if chat_type == "group":
            target = meta.get("group_openid") or inbound.channel_id
            out_meta: dict[str, Any] = {"chat_type": "group"}
            if target:
                out_meta["group_openid"] = target
            if msg_id:
                out_meta["msg_id"] = msg_id
            return OutgoingMessage(content=content, metadata=out_meta, reply_to=msg_id)

        if chat_type == "c2c":
            target = (
                meta.get("openid")
                or meta.get("user_openid")
                or meta.get("author_id")
                or inbound.sender_id
            )
            out_meta = {"chat_type": "c2c"}
            if target:
                out_meta["openid"] = target
            if msg_id:
                out_meta["msg_id"] = msg_id
            return OutgoingMessage(content=content, metadata=out_meta, reply_to=msg_id)

        return OutgoingMessage(content=content)

    def streaming_reply_kwargs(self, inbound: IncomingMessage) -> dict[str, Any]:
        """Pin the streamed reply to the triggering message, not ``_last_incoming``.

        Without this, ``send_streaming`` resolves the target from the shared
        ``_last_incoming_envelope`` slot, which a concurrent inbound message
        overwrites — leaking user A's answer to user B. Derive the target from
        the inbound envelope exactly as :meth:`build_reply_message` does.
        """
        meta = inbound.metadata or {}
        chat_type = meta.get("chat_type", "")
        msg_id = meta.get("msg_id") or meta.get("reply_to_msg_id")
        kwargs: dict[str, Any] = {}
        if chat_type == "group":
            kwargs["chat_type"] = "group"
            kwargs["target"] = meta.get("group_openid") or inbound.channel_id or ""
        elif chat_type == "c2c":
            kwargs["chat_type"] = "c2c"
            kwargs["target"] = (
                meta.get("openid")
                or meta.get("user_openid")
                or meta.get("author_id")
                or inbound.sender_id
                or ""
            )
        if msg_id:
            kwargs["msg_id"] = msg_id
        return kwargs

    async def send(self, message: OutgoingMessage) -> None:
        """Route by ``metadata['chat_type']`` to the right SDK call.

        ``c2c``  → ``self.api.post_c2c_message(openid=..., msg_type=0, ...)``
        ``group`` → ``self.api.post_group_message(group_openid=..., msg_type=0, ...)``

        ``msg_id`` (when supplied) and a per-inbound-message ``msg_seq`` counter
        satisfy the QQ API's passive-reply dedup rules.
        """
        meta = message.metadata or {}
        chat_type = meta.get("chat_type", "")
        msg_id = meta.get("msg_id") or meta.get("reply_to_msg_id") or message.reply_to

        api = self.api
        if chat_type == "group":
            target = meta.get("group_openid", "")
            if not target:
                raise ValueError("qq.send: metadata['group_openid'] required for group chat_type")
            if message.content:
                seq = self._passive_msg_seq("group", msg_id, target)
                kwargs: dict[str, Any] = {
                    "group_openid": target,
                    "msg_type": 0,
                    "content": message.content,
                    "msg_seq": seq or 1,
                }
                if seq is not None:
                    kwargs["msg_id"] = msg_id
                await api.post_group_message(**kwargs)
        elif chat_type == "c2c":
            target = meta.get("openid", "") or meta.get("user_openid", "")
            if not target:
                raise ValueError("qq.send: metadata['openid'] required for c2c chat_type")
            if message.content:
                seq = self._passive_msg_seq("c2c", msg_id, target)
                kwargs = {
                    "openid": target,
                    "msg_type": 0,
                    "content": message.content,
                    "msg_seq": seq or 1,
                }
                if seq is not None:
                    kwargs["msg_id"] = msg_id
                await api.post_c2c_message(**kwargs)
        else:
            raise ValueError(
                f"qq.send: metadata['chat_type'] must be 'c2c' or 'group', got {chat_type!r}"
            )
        for attachment in message.attachments:
            url = (attachment.url or "").strip()
            if not url.lower().startswith(("https://", "http://")):
                raise ValueError("qq.send: outbound attachments require an HTTP(S) URL")
            file_type = _qq_attachment_file_type(attachment)
            if chat_type == "group":
                await api.post_group_file(
                    group_openid=target,
                    file_type=file_type,
                    url=url,
                    srv_send_msg=True,
                )
            else:
                await api.post_c2c_file(
                    openid=target,
                    file_type=file_type,
                    url=url,
                    srv_send_msg=True,
                )
        log.debug(
            "qq.outbound_sent",
            chat_type=chat_type,
            length=len(message.content),
            attachment_count=len(message.attachments),
        )

    @staticmethod
    def _artifact_public_url(artifact: dict[str, Any] | None) -> str:
        if not isinstance(artifact, dict):
            return ""
        for key in ("channel_download_url", "signed_download_url"):
            value = artifact.get(key)
            if isinstance(value, str) and value.strip().lower().startswith(("https://", "http://")):
                return value.strip()
        return ""

    async def _multipart_upload(
        self,
        *,
        chat_type: str,
        target: str,
        file_path: Path,
        file_type: int,
        srv_send_msg: bool,
    ) -> dict[str, Any]:
        raw = file_path.read_bytes()
        digest_md5 = hashlib.md5(raw, usedforsecurity=False).hexdigest()
        digest_sha1 = hashlib.sha1(raw, usedforsecurity=False).hexdigest()
        prefix_md5 = hashlib.md5(
            raw[:_QQ_MD5_PREFIX_BYTES],
            usedforsecurity=False,
        ).hexdigest()
        api_http = getattr(self.api, "_http", None)
        if api_http is None or not callable(getattr(api_http, "request", None)):
            raise RuntimeError("qq media upload requires the botpy HTTP transport")

        from botpy.http import Route  # type: ignore[import-untyped]

        if chat_type == "group":
            prepare_route = Route(
                "POST",
                "/v2/groups/{group_id}/upload_prepare",
                group_id=target,
            )
            finish_path = "/v2/groups/{group_id}/upload_part_finish"
            files_route = Route(
                "POST",
                "/v2/groups/{group_openid}/files",
                group_openid=target,
            )
            route_target_key = "group_id"
        elif chat_type == "c2c":
            prepare_route = Route(
                "POST",
                "/v2/users/{user_id}/upload_prepare",
                user_id=target,
            )
            finish_path = "/v2/users/{user_id}/upload_part_finish"
            files_route = Route(
                "POST",
                "/v2/users/{user_openid}/files",
                user_openid=target,
            )
            route_target_key = "user_id"
        else:
            raise ValueError(f"qq media upload has invalid chat_type {chat_type!r}")

        prepared = await api_http.request(
            prepare_route,
            json={
                "file_type": file_type,
                "file_size": str(len(raw)),
                "file_name": file_path.name,
                "md5": digest_md5,
                "sha1": digest_sha1,
                "md5_10m": prefix_md5,
            },
        )
        if not isinstance(prepared, dict):
            raise RuntimeError("qq media upload_prepare returned an invalid response")
        upload_id = str(prepared.get("upload_id") or "")
        parts = prepared.get("parts")
        block_size = int(prepared.get("block_size") or 0)
        if not upload_id or not isinstance(parts, list) or not parts or block_size <= 0:
            raise RuntimeError("qq media upload_prepare omitted upload metadata")

        async with httpx.AsyncClient(follow_redirects=True, timeout=90.0) as client:
            for ordinal, part in enumerate(parts):
                if not isinstance(part, dict):
                    raise RuntimeError("qq media upload_prepare returned an invalid part")
                part_index = int(part.get("index", ordinal))
                start = part_index * block_size
                chunk_size = int(part.get("block_size") or block_size)
                chunk = raw[start : start + chunk_size]
                presigned_url = str(part.get("presigned_url") or "")
                if not presigned_url.lower().startswith(("https://", "http://")):
                    raise RuntimeError("qq media upload part omitted its presigned URL")
                response = await client.put(presigned_url, content=chunk)
                response.raise_for_status()
                finish_route = Route(
                    "POST",
                    finish_path,
                    **{route_target_key: target},
                )
                await api_http.request(
                    finish_route,
                    json={
                        "upload_id": upload_id,
                        "part_index": part_index,
                        "block_size": str(len(chunk)),
                        "md5": hashlib.md5(chunk, usedforsecurity=False).hexdigest(),
                    },
                )

        media = await api_http.request(
            files_route,
            json={
                "file_type": file_type,
                "file_name": file_path.name,
                "upload_id": upload_id,
                "srv_send_msg": srv_send_msg,
            },
        )
        if not isinstance(media, dict) or not media.get("file_info"):
            raise RuntimeError("qq media upload did not return file_info")
        return media

    async def _upload_media(
        self,
        *,
        chat_type: str,
        target: str,
        file_path: Path,
        artifact: dict[str, Any] | None,
        srv_send_msg: bool,
    ) -> dict[str, Any]:
        public_url = self._artifact_public_url(artifact)
        file_type = _qq_file_type(file_path)
        if public_url:
            if chat_type == "group":
                media = await self.api.post_group_file(
                    group_openid=target,
                    file_type=file_type,
                    url=public_url,
                    srv_send_msg=srv_send_msg,
                )
            elif chat_type == "c2c":
                media = await self.api.post_c2c_file(
                    openid=target,
                    file_type=file_type,
                    url=public_url,
                    srv_send_msg=srv_send_msg,
                )
            else:
                raise ValueError(f"qq media upload has invalid chat_type {chat_type!r}")
            if not isinstance(media, dict) or not media.get("file_info"):
                raise RuntimeError("qq media URL upload did not return file_info")
            return media
        return await self._multipart_upload(
            chat_type=chat_type,
            target=target,
            file_path=file_path,
            file_type=file_type,
            srv_send_msg=srv_send_msg,
        )

    async def send_artifact(
        self,
        inbound: IncomingMessage,
        file_path: str,
        artifact: dict[str, Any] | None = None,
    ) -> ChannelSendResult:
        """Upload an artifact and bind it to the exact passive QQ reply route."""
        route = self.streaming_reply_kwargs(inbound)
        chat_type = str(route.get("chat_type") or "")
        target = str(route.get("target") or "")
        msg_id = str(route.get("msg_id") or "")
        path = Path(file_path)
        if not target or not path.is_file():
            return ChannelSendResult.failed(
                capability="native_file_upload",
                target_id=target,
                reason="invalid_target_or_file",
            )
        try:
            passive_seq = self._passive_msg_seq(chat_type, msg_id or None, target)
            passive_msg_id = msg_id if passive_seq is not None else ""
            media = await self._upload_media(
                chat_type=chat_type,
                target=target,
                file_path=path,
                artifact=artifact,
                srv_send_msg=not bool(passive_msg_id),
            )
            if passive_msg_id:
                if chat_type == "group":
                    sent = await self.api.post_group_message(
                        group_openid=target,
                        msg_type=7,
                        media=media,
                        msg_id=passive_msg_id,
                        msg_seq=passive_seq,
                    )
                else:
                    sent = await self.api.post_c2c_message(
                        openid=target,
                        msg_type=7,
                        media=media,
                        msg_id=passive_msg_id,
                        msg_seq=passive_seq,
                    )
            else:
                sent = media
        except Exception as exc:  # noqa: BLE001 - preserve artifact fallback upstream.
            log.warning(
                "qq.artifact_send_failed",
                chat_type=chat_type,
                target=target,
                error_type=type(exc).__name__,
                error=str(exc),
            )
            return ChannelSendResult.failed(
                capability="native_file_upload",
                target_id=target,
                reason=type(exc).__name__,
                retryable=isinstance(exc, (httpx.HTTPError, TimeoutError)),
            )
        provider_message_id = sent.get("id", "") if isinstance(sent, dict) else ""
        provider_file_id = media.get("file_uuid", "") if isinstance(media, dict) else ""
        return ChannelSendResult.sent(
            capability="native_file_upload",
            target_id=target,
            provider_message_id=str(provider_message_id or ""),
            provider_file_id=str(provider_file_id or ""),
        )

    async def edit(self, message_id: str, content: str) -> None:
        """Raise: QQ Bot Platform has no message-edit primitive."""
        raise UnsupportedChannelOperation(
            channel="qq",
            operation="edit",
            reason="QQ official bot messages do not expose a generic edit endpoint",
        )

    async def delete(self, message_id: str) -> None:
        """Raise: QQ Bot Platform has no message-delete primitive."""
        raise UnsupportedChannelOperation(
            channel="qq",
            operation="delete",
            reason="QQ official bot messages do not expose a generic delete endpoint",
        )

    # ------------------------------------------------------------------
    # Streaming — bounded real-time message batches
    # ------------------------------------------------------------------

    async def send_streaming(
        self,
        chunks: AsyncIterator[str],
        *,
        chat_type: str = "",
        target: str = "",
        msg_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Flush bounded progress messages while the model is still running."""
        out_meta: dict[str, Any] = dict(metadata or {})

        # Implicit-context fallback: the dispatcher calls
        # ``send_streaming(chunks)`` with no kwargs, so default the
        # reply target to the last received envelope's metadata.
        last = self._last_incoming_envelope
        if last is not None:
            last_meta = last.metadata or {}
            if not chat_type:
                chat_type = last_meta.get("chat_type", "")
            if msg_id is None:
                msg_id = last_meta.get("msg_id") or last_meta.get("reply_to_msg_id")
            if not target:
                if chat_type == "group":
                    target = last_meta.get("group_openid", "") or ""
                elif chat_type == "c2c":
                    target = (
                        last_meta.get("openid", "")
                        or last_meta.get("user_openid", "")
                        or last_meta.get("author_id", "")
                        or last.sender_id
                    )

        if chat_type:
            out_meta["chat_type"] = chat_type
        if msg_id and "msg_id" not in out_meta:
            out_meta["msg_id"] = msg_id
        if target:
            ct = out_meta.get("chat_type", "")
            if ct == "group" and "group_openid" not in out_meta:
                out_meta["group_openid"] = target
            elif ct == "c2c" and "openid" not in out_meta:
                out_meta["openid"] = target

        async def flush(text: str) -> None:
            remaining = text
            while remaining:
                piece = remaining[:_STREAM_MESSAGE_CHARS]
                remaining = remaining[_STREAM_MESSAGE_CHARS:]
                if piece.strip():
                    await self.send(OutgoingMessage(content=piece, metadata=out_meta))

        iterator = chunks.__aiter__()
        pending: asyncio.Task[str] | None = None
        buffer = ""
        try:
            pending = asyncio.create_task(iterator.__anext__())
            while pending is not None:
                try:
                    chunk = await asyncio.wait_for(
                        asyncio.shield(pending),
                        timeout=_STREAM_FLUSH_SECONDS,
                    )
                except TimeoutError:
                    if buffer:
                        await flush(buffer)
                        buffer = ""
                    continue
                except StopAsyncIteration:
                    pending = None
                    break
                buffer += chunk
                pending = asyncio.create_task(iterator.__anext__())
                if len(buffer) >= _STREAM_FLUSH_CHARS or "\n\n" in chunk:
                    await flush(buffer)
                    buffer = ""
            if buffer:
                await flush(buffer)
        finally:
            if pending is not None and not pending.done():
                pending.cancel()
                with contextlib.suppress(asyncio.CancelledError):
                    await pending
            aclose = getattr(iterator, "aclose", None)
            if callable(aclose):
                with contextlib.suppress(Exception):
                    await aclose()
