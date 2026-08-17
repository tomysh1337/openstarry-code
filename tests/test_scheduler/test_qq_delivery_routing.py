from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock

from openstarry_code.scheduler.delivery import DeliveryChain


async def test_scheduler_qq_direct_delivery_builds_proactive_route() -> None:
    adapter = SimpleNamespace(send=AsyncMock())
    manager = SimpleNamespace(get=lambda name: adapter if name == "qq" else None)
    chain = DeliveryChain(channel_manager_ref=lambda: manager)

    result = await chain._post_to_channel(
        job_id="job-1",
        text="scheduled result",
        channel_name="qq",
        channel_id="user-openid",
        thread_id="",
        session_key="agent:main:qq:direct:user-openid",
    )

    assert result == "delivered"
    sent = adapter.send.await_args.args[0]
    assert sent.reply_to is None
    assert sent.metadata == {"chat_type": "c2c", "openid": "user-openid"}
