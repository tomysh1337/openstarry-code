from __future__ import annotations

import asyncio
from typing import Any

import pytest

from openstarry_code.gateway.config import GatewayConfig, LlmProviderConfig
from openstarry_code.onboarding.mutations import (
    duplicate_custom_llm_profile,
    upsert_llm_profile,
)
from openstarry_code.provider import anthropic as anthropic_module
from openstarry_code.provider import openai as openai_module
from openstarry_code.provider import openai_responses as responses_module
from openstarry_code.provider.anthropic import AnthropicProvider
from openstarry_code.provider.openai import OpenAIProvider
from openstarry_code.provider.openai_responses import OpenAIResponsesProvider
from openstarry_code.provider.protocol import provider_connection_config
from openstarry_code.provider.request_headers import normalize_request_headers
from openstarry_code.provider.selector import ProviderConfig, build_provider_from_config
from openstarry_code.provider.types import ChatConfig, Message


def test_custom_headers_are_validated_and_redacted_from_public_config() -> None:
    cfg = GatewayConfig(
        llm=LlmProviderConfig(
            provider="custom",
            model="model-a",
            base_url="https://llm.example.test/v1",
            custom_headers={"X-Tenant": "tenant-secret"},
        ),
        llm_profiles={
            "custom_2": {
                "model": "model-b",
                "base_url": "https://llm.example.test/v1",
                "custom_headers": {"X-Workspace": "workspace-secret"},
            }
        },
    )

    public = cfg.to_public_dict()
    assert public["llm"]["custom_headers"] == {"X-Tenant": "[redacted]"}
    assert public["llm_profiles"]["custom_2"]["custom_headers"] == {"X-Workspace": "[redacted]"}
    assert cfg.llm.custom_headers == {"X-Tenant": "tenant-secret"}


@pytest.mark.parametrize(
    "name",
    ["Authorization", "x-api-key", "Host", "Content-Length", "Connection"],
)
def test_custom_headers_reject_adapter_owned_names(name: str) -> None:
    with pytest.raises(ValueError, match="managed by the provider adapter"):
        normalize_request_headers({name: "value"})


def test_profile_custom_headers_follow_endpoint_origin_and_duplicate_server_side() -> None:
    cfg = GatewayConfig()
    saved = upsert_llm_profile(
        cfg,
        provider_id="custom",
        model="model-a",
        api_key="synthetic-key",
        base_url="https://llm.example.test/v1",
        proxy="http://127.0.0.1:7890",
        custom_headers={"X-Tenant": "tenant-secret"},
    ).config

    duplicated = duplicate_custom_llm_profile(
        saved,
        source_provider_id="custom",
        target_provider_id="custom_2",
    )
    copied = duplicated.config.llm_profiles["custom_2"]
    assert copied.model == "model-a"
    assert copied.api_key == "synthetic-key"
    assert copied.base_url == "https://llm.example.test/v1"
    assert copied.proxy == "http://127.0.0.1:7890"
    assert copied.custom_headers == {"X-Tenant": "tenant-secret"}
    assert duplicated.public_payload["api_key"] == "***"
    assert duplicated.public_payload["custom_headers"] == {"X-Tenant": "***"}

    changed_origin = upsert_llm_profile(
        saved,
        provider_id="custom",
        base_url="https://other.example.test/v1",
    ).config
    assert changed_origin.llm_profiles["custom"].custom_headers == {}


def test_selector_passes_custom_headers_to_all_generic_protocol_adapters() -> None:
    headers = {"X-Tenant": "tenant-secret"}
    rows = (
        ProviderConfig(
            provider="custom",
            model="chat-model",
            base_url="https://llm.example.test/v1",
            request_headers=headers,
        ),
        ProviderConfig(
            provider="custom_responses",
            model="responses-model",
            base_url="https://llm.example.test/v1",
            request_headers=headers,
        ),
        ProviderConfig(
            provider="custom_anthropic",
            model="messages-model",
            base_url="https://llm.example.test/v1",
            request_headers=headers,
        ),
    )

    for config in rows:
        provider = build_provider_from_config(config)
        assert provider._request_headers == headers
        assert provider._request_headers is not headers
        connection = provider_connection_config(provider)
        assert connection.request_headers == headers
        assert "tenant-secret" not in repr(connection)


@pytest.mark.parametrize(
    ("module", "provider"),
    [
        (
            openai_module,
            OpenAIProvider(
                api_key="synthetic-key",
                model="chat-model",
                base_url="https://llm.example.test/v1",
                request_headers={"X-Tenant": "tenant-secret"},
            ),
        ),
        (
            responses_module,
            OpenAIResponsesProvider(
                api_key="synthetic-key",
                model="responses-model",
                base_url="https://llm.example.test/v1",
                request_headers={"X-Tenant": "tenant-secret"},
            ),
        ),
    ],
)
def test_model_discovery_includes_custom_headers(
    monkeypatch: Any,
    module: Any,
    provider: Any,
) -> None:
    captured: dict[str, Any] = {}

    class StubResponse:
        status_code = 200

        def raise_for_status(self) -> None:
            return None

        def json(self, **kwargs: Any) -> dict[str, Any]:
            return {"data": []}

    class StubClient:
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            pass

        async def __aenter__(self) -> StubClient:
            return self

        async def __aexit__(self, *exc: Any) -> None:
            return None

        async def get(self, *args: Any, **kwargs: Any) -> StubResponse:
            captured.update(kwargs)
            return StubResponse()

    monkeypatch.setattr(module.httpx, "AsyncClient", StubClient)
    asyncio.run(provider.list_models(raise_on_error=True))
    assert captured["headers"]["X-Tenant"] == "tenant-secret"
    assert captured["headers"]["Authorization"] == "Bearer synthetic-key"


def test_anthropic_wire_includes_custom_headers(monkeypatch: Any) -> None:
    captured: dict[str, Any] = {}

    class StubResponse:
        status_code = 200

        async def aiter_lines(self):
            for line in ('data: {"type":"message_stop"}', ""):
                yield line

        async def aread(self) -> bytes:
            return b""

        async def __aenter__(self) -> StubResponse:
            return self

        async def __aexit__(self, *exc: Any) -> None:
            return None

    class StubClient:
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            pass

        async def __aenter__(self) -> StubClient:
            return self

        async def __aexit__(self, *exc: Any) -> None:
            return None

        def stream(self, *args: Any, **kwargs: Any) -> StubResponse:
            captured.update(kwargs)
            return StubResponse()

    monkeypatch.setattr(anthropic_module.httpx, "AsyncClient", StubClient)
    provider = AnthropicProvider(
        api_key="synthetic-key",
        model="claude-test",
        request_headers={"X-Tenant": "tenant-secret"},
    )

    async def run() -> None:
        async for _ in provider.chat(
            [Message(role="user", content="ping")],
            config=ChatConfig(max_tokens=1),
        ):
            pass

    asyncio.run(run())
    assert captured["headers"]["X-Tenant"] == "tenant-secret"
    assert captured["headers"]["x-api-key"] == "synthetic-key"
