"""Read-only model tool for the active sandbox posture."""

from __future__ import annotations

import json
from typing import Any

from openstarry_code.sandbox.setup_runtime import (
    current_sandbox_capability_report,
    current_sandbox_setup_runtime_status,
)
from openstarry_code.sandbox.status import status_payload
from openstarry_code.tools.registry import tool
from openstarry_code.tools.types import (
    PlanAccess,
    RetryableToolInputError,
    SafeToolError,
    current_tool_context,
)


def _policy_payload(policy: Any) -> dict[str, object] | None:
    if policy is None:
        return None
    to_public_dict = getattr(policy, "to_public_dict", None)
    if not callable(to_public_dict):
        return None
    payload = to_public_dict()
    return payload if isinstance(payload, dict) else None


@tool(
    name="sandbox_status",
    description=(
        "Inspect the active sandbox posture, setup state, verified backend "
        "capabilities, and pinned file/network policy. This is read-only. Use "
        "refresh=true only when a fresh native capability probe is needed."
    ),
    params={
        "refresh": {
            "type": "boolean",
            "description": ("Bypass the cached capability report and run a fresh backend probe."),
            "default": False,
        }
    },
    plan_access=PlanAccess.READ_ONLY,
)
async def sandbox_status(refresh: bool = False) -> str:
    if not isinstance(refresh, bool):
        raise RetryableToolInputError("refresh must be a boolean")

    context = current_tool_context.get()
    config = getattr(context, "sandbox_gateway_config", None) if context else None
    if config is None:
        raise SafeToolError("Sandbox status is unavailable before gateway setup completes.")

    setup = await current_sandbox_setup_runtime_status(config)
    capability = await current_sandbox_capability_report(
        config,
        force_refresh=refresh,
    )
    payload = {
        "posture": status_payload(config),
        "setup": setup.to_payload(),
        "capability": capability.to_payload(),
        "policy": _policy_payload(getattr(context, "sandbox_policy", None)),
    }
    return json.dumps(payload, ensure_ascii=False, separators=(",", ":"))


__all__ = ["sandbox_status"]
