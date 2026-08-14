from __future__ import annotations

from typing import Any

import pytest

from openstarry_code.channels._reactions import FeishuStatusReactor
from openstarry_code.channels.types import IncomingMessage


class _FakeResponse:
    def __init__(self, payload: dict[str, Any], status_code: int = 200) -> None:
        self._payload = payload
        self.status_code = status_code

    def json(self) -> dict[str, Any]:
        return self._payload

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise AssertionError(f"unexpected HTTP failure: {self.status_code}")


class _FakeClient:
    def __init__(
        self,
        post_response: _FakeResponse,
        delete_response: _FakeResponse | None = None,
    ) -> None:
        self.post_response = post_response
        self.delete_response = delete_response or _FakeResponse({"code": 0, "msg": "success"})
        self.posts: list[dict[str, Any]] = []
        self.deletes: list[dict[str, Any]] = []

    async def post(self, path: str, **kwargs: Any) -> _FakeResponse:
        self.posts.append({"path": path, **kwargs})
        return self.post_response

    async def delete(self, path: str, **kwargs: Any) -> _FakeResponse:
        self.deletes.append({"path": path, **kwargs})
        return self.delete_response


class _FakeChannel:
    def __init__(self, client: _FakeClient) -> None:
        self.client = client

    def _get_client(self) -> _FakeClient:
        return self.client

    async def _auth_headers(self) -> dict[str, str]:
        return {"Authorization": "Bearer token"}


class _FakeLogger:
    def __init__(self) -> None:
        self.warnings: list[dict[str, Any]] = []

    def warning(self, event: str, **kwargs: Any) -> None:
        self.warnings.append({"event": event, **kwargs})


def _message(message_id: str = "om_1") -> IncomingMessage:
    return IncomingMessage(
        sender_id="u1",
        channel_id="oc_1",
        content="hello",
        metadata={"message_id": message_id},
    )


@pytest.mark.asyncio
async def test_feishu_received_reaction_uses_acknowledgement_emoji() -> None:
    client = _FakeClient(
        _FakeResponse({"code": 0, "data": {"reaction_id": "react-ok"}, "msg": "success"})
    )
    reactor = FeishuStatusReactor(_FakeChannel(client), _FakeLogger())

    await reactor.received(_message())

    assert client.posts[0]["json"] == {"reaction_type": {"emoji_type": "OK"}}


@pytest.mark.asyncio
async def test_feishu_reactor_removes_by_reaction_id_returned_from_add() -> None:
    client = _FakeClient(
        _FakeResponse({"code": 0, "data": {"reaction_id": "react-eyes"}, "msg": "success"})
    )
    reactor = FeishuStatusReactor(_FakeChannel(client), _FakeLogger())

    await reactor.running(_message())
    await reactor.completed(_message())

    assert client.posts[0]["path"] == "/im/v1/messages/om_1/reactions"
    assert client.posts[0]["json"] == {"reaction_type": {"emoji_type": "EYES"}}
    assert client.deletes[0]["path"] == "/im/v1/messages/om_1/reactions/react-eyes"
    assert "EYES" not in client.deletes[0]["path"]


@pytest.mark.asyncio
async def test_feishu_reaction_http_error_is_best_effort() -> None:
    client = _FakeClient(_FakeResponse({"code": 999, "msg": "bad request"}, status_code=400))
    logger = _FakeLogger()
    reactor = FeishuStatusReactor(_FakeChannel(client), logger)

    await reactor.running(_message())
    await reactor.running(_message("om_2"))

    assert len(client.posts) == 1
    assert any(item["event"] == "channel.status_reaction_failed" for item in logger.warnings)
    assert any(item["event"] == "channel.status_reaction_disabled" for item in logger.warnings)


@pytest.mark.asyncio
async def test_feishu_reaction_delete_api_error_disables_reactor() -> None:
    client = _FakeClient(
        _FakeResponse({"code": 0, "data": {"reaction_id": "react-eyes"}, "msg": "success"}),
        delete_response=_FakeResponse({"code": 999, "msg": "delete denied"}),
    )
    logger = _FakeLogger()
    reactor = FeishuStatusReactor(_FakeChannel(client), logger)

    await reactor.running(_message())
    await reactor.completed(_message())
    await reactor.running(_message("om_2"))

    assert len(client.posts) == 1
    assert client.deletes[0]["path"] == "/im/v1/messages/om_1/reactions/react-eyes"
    assert any(item["event"] == "channel.status_reaction_failed" for item in logger.warnings)
    assert any(item["event"] == "channel.status_reaction_disabled" for item in logger.warnings)
