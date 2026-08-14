from __future__ import annotations

import pytest

from openstarry_code.tools.builtin.nodes import canvas, nodes
from openstarry_code.tools.types import ToolError


@pytest.mark.asyncio
async def test_nodes_list_stub_reports_runtime_unavailable() -> None:
    with pytest.raises(ToolError, match="configured node runtime"):
        await nodes("list")


@pytest.mark.asyncio
async def test_canvas_stub_reports_runtime_unavailable() -> None:
    with pytest.raises(ToolError, match="configured node runtime"):
        await canvas("snapshot", "main")
