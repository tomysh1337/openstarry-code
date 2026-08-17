from __future__ import annotations

import json
from types import SimpleNamespace
from unittest.mock import AsyncMock

from openstarry_code.tools.builtin.messaging import (
    _outgoing_metadata,
    message,
    register_channel,
    unregister_channel,
)


def test_qq_outgoing_metadata_supports_group_and_c2c_targets() -> None:
    assert _outgoing_metadata("qq", "group:group-1", None) == {
        "chat_type": "group",
        "group_openid": "group-1",
    }
    assert _outgoing_metadata("qq", "c2c:user-1", None) == {
        "chat_type": "c2c",
        "openid": "user-1",
    }
    assert _outgoing_metadata("qq", "user-2", None) == {
        "chat_type": "c2c",
        "openid": "user-2",
    }


async def test_message_tool_sends_qq_attachment_with_explicit_route() -> None:
    adapter = SimpleNamespace(send=AsyncMock())
    register_channel("qq", adapter)
    try:
        result = await message(
            channel="qq",
            target="group:group-1",
            text="screenshot",
            attachment_url="https://example.test/result.png",
            attachment_name="result.png",
            mime_type="image/png",
        )
    finally:
        unregister_channel("qq")

    assert json.loads(result)["status"] == "sent"
    sent = adapter.send.await_args.args[0]
    assert sent.metadata == {"chat_type": "group", "group_openid": "group-1"}
    assert sent.attachments[0].url == "https://example.test/result.png"
    assert sent.attachments[0].name == "result.png"
