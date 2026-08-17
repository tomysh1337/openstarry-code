from __future__ import annotations

import asyncio
import hashlib
from types import SimpleNamespace
from typing import Any
from unittest.mock import AsyncMock

import httpx

from openstarry_code.channels.qq import QQChannel, QQChannelConfig
from openstarry_code.channels.types import Attachment, OutgoingMessage


def _make_channel() -> QQChannel:
    return QQChannel(QQChannelConfig(name="qq", app_id="app-id", app_secret="app-secret"))


def _raw_c2c(msg_id: str, openid: str, content: str) -> Any:
    return SimpleNamespace(
        id=msg_id,
        author=SimpleNamespace(user_openid=openid),
        content=content,
    )


def _raw_group(msg_id: str, member_openid: str, group_openid: str, content: str) -> Any:
    return SimpleNamespace(
        id=msg_id,
        author=SimpleNamespace(member_openid=member_openid),
        group_openid=group_openid,
        content=content,
    )


async def test_qq_streaming_reply_kwargs_pin_c2c_target() -> None:
    channel = _make_channel()
    channel._enqueue_message(_raw_c2c("m-1", "openid-1", "hi"), is_group=False)

    msg = await channel.receive()

    assert channel.streaming_reply_kwargs(msg) == {
        "chat_type": "c2c",
        "target": "openid-1",
        "msg_id": "m-1",
    }


async def test_qq_streaming_reply_kwargs_pin_group_target() -> None:
    channel = _make_channel()
    channel._enqueue_message(_raw_group("m-2", "member-1", "group-1", "hi"), is_group=True)

    msg = await channel.receive()

    assert channel.streaming_reply_kwargs(msg) == {
        "chat_type": "group",
        "target": "group-1",
        "msg_id": "m-2",
    }


async def test_qq_streamed_reply_targets_sender_even_after_newer_inbound() -> None:
    channel = _make_channel()
    channel.api = SimpleNamespace(post_c2c_message=AsyncMock(), post_group_message=AsyncMock())

    channel._enqueue_message(_raw_c2c("m-a", "openid-a", "question from a"), is_group=False)
    msg_a = await channel.receive()

    mid_stream = asyncio.Event()
    release = asyncio.Event()

    async def chunks() -> Any:
        yield "answer for a, part 1. "
        mid_stream.set()
        await release.wait()
        yield "part 2."

    stream_task = asyncio.create_task(
        channel.send_streaming(chunks(), **channel.streaming_reply_kwargs(msg_a))
    )
    await mid_stream.wait()

    # Another user's message is received while A's answer is still streaming.
    channel._enqueue_message(_raw_c2c("m-b", "openid-b", "unrelated"), is_group=False)
    await channel.receive()

    release.set()
    await asyncio.wait_for(stream_task, timeout=5)

    assert channel.api.post_c2c_message.await_count == 1
    kwargs = channel.api.post_c2c_message.await_args.kwargs
    assert "answer for a" in kwargs["content"]
    assert kwargs["openid"] == "openid-a"
    assert kwargs["msg_id"] == "m-a"
    assert kwargs["msg_seq"] == 1
    assert isinstance(kwargs["msg_seq"], int)


async def test_qq_passive_reply_budget_switches_later_updates_to_active_route() -> None:
    channel = _make_channel()
    channel.api = SimpleNamespace(post_c2c_message=AsyncMock(), post_group_message=AsyncMock())

    for index in range(6):
        await channel.send(
            OutgoingMessage(
                content=f"part-{index}",
                metadata={
                    "chat_type": "c2c",
                    "openid": "openid-budget",
                    "msg_id": "inbound-budget",
                },
            )
        )

    calls = channel.api.post_c2c_message.await_args_list
    assert [call.kwargs.get("msg_seq") for call in calls[:4]] == [1, 2, 3, 4]
    assert all(call.kwargs.get("msg_id") == "inbound-budget" for call in calls[:4])
    assert all("msg_id" not in call.kwargs for call in calls[4:])
    assert all(call.kwargs.get("msg_seq") == 1 for call in calls[4:])


async def test_qq_passive_c2c_artifact_upload_replies_with_media(tmp_path) -> None:
    channel = _make_channel()
    channel.api = SimpleNamespace(
        post_c2c_file=AsyncMock(return_value={"file_info": "media-token", "file_uuid": "f1"}),
        post_c2c_message=AsyncMock(return_value={"id": "sent-1"}),
    )
    channel._enqueue_message(_raw_c2c("m-image", "openid-image", "draw"), is_group=False)
    inbound = await channel.receive()
    image_path = tmp_path / "result.png"
    image_path.write_bytes(b"png")

    result = await channel.send_artifact(
        inbound,
        str(image_path),
        {"channel_download_url": "https://example.test/result.png"},
    )

    assert result.is_delivered()
    channel.api.post_c2c_file.assert_awaited_once_with(
        openid="openid-image",
        file_type=1,
        url="https://example.test/result.png",
        srv_send_msg=False,
    )
    channel.api.post_c2c_message.assert_awaited_once_with(
        openid="openid-image",
        msg_type=7,
        media={"file_info": "media-token", "file_uuid": "f1"},
        msg_id="m-image",
        msg_seq=1,
    )


async def test_qq_active_group_attachment_uses_proactive_media_send() -> None:
    channel = _make_channel()
    channel.api = SimpleNamespace(
        post_group_file=AsyncMock(return_value={"id": "active-1"}),
        post_group_message=AsyncMock(),
    )

    await channel.send(
        OutgoingMessage(
            content="",
            attachments=[
                Attachment(
                    name="result.jpg",
                    mime_type="image/jpeg",
                    url="https://example.test/result.jpg",
                )
            ],
            metadata={"chat_type": "group", "group_openid": "group-active"},
        )
    )

    channel.api.post_group_file.assert_awaited_once_with(
        group_openid="group-active",
        file_type=1,
        url="https://example.test/result.jpg",
        srv_send_msg=True,
    )
    channel.api.post_group_message.assert_not_awaited()


async def test_qq_multipart_upload_matches_official_payload(monkeypatch, tmp_path) -> None:
    channel = _make_channel()
    requests: list[tuple[str, dict[str, Any]]] = []
    raw = b"multipart-content"
    file_path = tmp_path / "result.png"
    file_path.write_bytes(raw)

    class FakeHTTP:
        async def request(self, route, *, json):
            requests.append((route.url, json))
            if route.url.endswith("/upload_prepare"):
                return {
                    "upload_id": "upload-1",
                    "block_size": str(len(raw)),
                    "parts": [
                        {
                            "index": 0,
                            "presigned_url": "https://upload.example.test/part-0",
                            "block_size": str(len(raw)),
                        }
                    ],
                }
            if route.url.endswith("/files"):
                return {"file_info": "media-token", "file_uuid": "file-1"}
            return {}

    puts: list[tuple[str, bytes]] = []

    class FakeResponse:
        def raise_for_status(self) -> None:
            return None

    class FakeAsyncClient:
        def __init__(self, **kwargs) -> None:
            del kwargs

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args) -> None:
            del args

        async def put(self, url: str, *, content: bytes):
            puts.append((url, content))
            return FakeResponse()

    monkeypatch.setattr(httpx, "AsyncClient", FakeAsyncClient)
    channel.api = SimpleNamespace(_http=FakeHTTP())

    media = await channel._multipart_upload(
        chat_type="group",
        target="group-1",
        file_path=file_path,
        file_type=1,
        srv_send_msg=False,
    )

    assert media["file_info"] == "media-token"
    assert puts == [("https://upload.example.test/part-0", raw)]
    prepare = requests[0][1]
    assert prepare == {
        "file_type": 1,
        "file_size": str(len(raw)),
        "file_name": "result.png",
        "md5": hashlib.md5(raw, usedforsecurity=False).hexdigest(),
        "sha1": hashlib.sha1(raw, usedforsecurity=False).hexdigest(),
        "md5_10m": hashlib.md5(raw, usedforsecurity=False).hexdigest(),
    }
    assert requests[1][1] == {
        "upload_id": "upload-1",
        "part_index": 0,
        "block_size": str(len(raw)),
        "md5": hashlib.md5(raw, usedforsecurity=False).hexdigest(),
    }
    assert requests[2][1] == {
        "file_type": 1,
        "file_name": "result.png",
        "upload_id": "upload-1",
        "srv_send_msg": False,
    }
