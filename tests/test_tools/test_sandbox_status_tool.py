from __future__ import annotations

import json

import pytest

from openstarry_code.tools.builtin import sandbox_status as sandbox_status_module
from openstarry_code.tools.registry import get_default_registry
from openstarry_code.tools.types import (
    PlanAccess,
    RetryableToolInputError,
    SafeToolError,
    ToolContext,
    current_tool_context,
)


class _Payload:
    def __init__(self, payload: dict[str, object]) -> None:
        self.payload = payload

    def to_payload(self) -> dict[str, object]:
        return dict(self.payload)


class _Policy:
    def to_public_dict(self) -> dict[str, object]:
        return {
            "files": {"customDenyWritePaths": ["protected"]},
            "network": {"blockAllNetwork": True},
        }


def test_sandbox_status_is_registered_as_read_only() -> None:
    registered = get_default_registry().get("sandbox_status")

    assert registered is not None
    assert registered.spec.plan_access is PlanAccess.READ_ONLY
    assert registered.spec.required == []
    assert registered.spec.parameters["refresh"]["type"] == "boolean"


@pytest.mark.asyncio
async def test_sandbox_status_combines_runtime_reports(monkeypatch) -> None:
    config = object()
    refresh_values: list[bool] = []

    async def fake_setup(received_config):
        assert received_config is config
        return _Payload({"state": "ready", "platform": "win32"})

    async def fake_capability(received_config, *, force_refresh=False):
        assert received_config is config
        refresh_values.append(force_refresh)
        return _Payload(
            {
                "available": True,
                "backend": "windows_native",
                "capabilities": ["process"],
            }
        )

    monkeypatch.setattr(
        sandbox_status_module,
        "current_sandbox_setup_runtime_status",
        fake_setup,
    )
    monkeypatch.setattr(
        sandbox_status_module,
        "current_sandbox_capability_report",
        fake_capability,
    )
    monkeypatch.setattr(
        sandbox_status_module,
        "status_payload",
        lambda received_config: (
            {
                "run_mode": "safe",
                "backend": "auto",
                "sandbox": {"network_default": "proxy_allowlist"},
            }
            if received_config is config
            else pytest.fail("unexpected config")
        ),
    )
    context = ToolContext(
        is_owner=True,
        sandbox_gateway_config=config,
        sandbox_policy=_Policy(),
    )
    token = current_tool_context.set(context)
    try:
        payload = json.loads(await sandbox_status_module.sandbox_status(refresh=True))
    finally:
        current_tool_context.reset(token)

    assert refresh_values == [True]
    assert payload == {
        "posture": {
            "run_mode": "safe",
            "backend": "auto",
            "sandbox": {"network_default": "proxy_allowlist"},
        },
        "setup": {"state": "ready", "platform": "win32"},
        "capability": {
            "available": True,
            "backend": "windows_native",
            "capabilities": ["process"],
        },
        "policy": {
            "files": {"customDenyWritePaths": ["protected"]},
            "network": {"blockAllNetwork": True},
        },
    }


@pytest.mark.asyncio
async def test_sandbox_status_requires_gateway_context() -> None:
    token = current_tool_context.set(ToolContext(is_owner=True))
    try:
        with pytest.raises(SafeToolError, match="gateway setup"):
            await sandbox_status_module.sandbox_status()
    finally:
        current_tool_context.reset(token)


@pytest.mark.asyncio
async def test_sandbox_status_rejects_non_boolean_refresh() -> None:
    with pytest.raises(RetryableToolInputError, match="refresh must be a boolean"):
        await sandbox_status_module.sandbox_status(refresh="yes")  # type: ignore[arg-type]
