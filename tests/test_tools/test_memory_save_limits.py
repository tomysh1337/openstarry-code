from __future__ import annotations

from types import SimpleNamespace

from openstarry_code.tools.builtin.memory_tools import create_memory_tools
from openstarry_code.tools.registry import ToolRegistry


class _Store:
    async def index_file(self, *, path, content, source) -> int:
        return 1

    async def remove_file(self, path: str) -> None:
        return None

    async def total_size(self) -> int:
        return 0


class _Retriever:
    async def search(self, query, opts, *, intent):
        return []


def _make_memory_save(workspace: str, max_files: int):
    registry = ToolRegistry()
    memory_config = SimpleNamespace(
        max_file_size_kb=0,
        max_total_size_kb=0,
        max_files=max_files,
        entry_ttl_days=0,
    )
    create_memory_tools(
        stores=_Store(),
        retrievers=_Retriever(),
        memory_dir=workspace,
        registry=registry,
        memory_config=memory_config,
        memory_source="workspace",
    )
    runtime_tool = registry.get("memory_save")
    assert runtime_tool is not None
    return runtime_tool.handler


async def test_max_files_cap_ignores_non_memory_markdown(tmp_path):
    workspace = tmp_path / "ws"
    docs = workspace / "docs"
    docs.mkdir(parents=True)
    for i in range(3):
        (docs / f"guide-{i}.md").write_text(f"# project doc {i}\n", encoding="utf-8")

    memory_save = _make_memory_save(str(workspace), max_files=3)

    result = await memory_save(content="durable fact", path="memory/2026-07-09.md")
    assert "Saved to memory/2026-07-09.md" in result
    assert (workspace / "memory" / "2026-07-09.md").exists()
