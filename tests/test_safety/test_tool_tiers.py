from __future__ import annotations

from openstarry_code.safety.permission_matrix import Principal, is_tool_allowed
from openstarry_code.safety.tool_tiers import HARDCODED_ADMIN_ONLY, RiskTier, get_tier


def test_execute_code_is_pinned_admin_only() -> None:
    assert "execute_code" in HARDCODED_ADMIN_ONLY
    assert get_tier("execute_code") is RiskTier.ADMIN_ONLY


def test_execute_code_denied_on_channel_dm_like_shell_tools() -> None:
    principal = Principal(role="user")

    assert is_tool_allowed("exec_command", "dm", principal).reason == "admin_only_denied_in_dm"

    decision = is_tool_allowed("execute_code", "dm", principal)
    assert decision.allowed is False
    assert decision.reason == "admin_only_denied_in_dm"
