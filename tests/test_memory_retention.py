from __future__ import annotations

import os
import time
from pathlib import Path

from openstarry_code.memory.retention import prune_expired_memory_files
from openstarry_code.memory.store import LongTermMemoryStore
from openstarry_code.memory.types import MemorySource


async def test_ttl_sweep_preserves_named_evergreen_notes(tmp_path: Path) -> None:
    workspace = tmp_path / "ws"
    memory_dir = workspace / "memory"
    memory_dir.mkdir(parents=True)
    forty_days_ago = time.time() - 40 * 86400

    named_note = memory_dir / "preferences.md"
    named_note.write_text("Always deploy from the release branch.\n", encoding="utf-8")
    os.utime(named_note, (forty_days_ago, forty_days_ago))

    dated_note = memory_dir / "2026-05-30.md"
    dated_note.write_text("Daily scratch note from May.\n", encoding="utf-8")
    os.utime(dated_note, (forty_days_ago, forty_days_ago))

    store = LongTermMemoryStore(db_path=tmp_path / "memory.db")
    await store.initialize()
    try:
        for note in (named_note, dated_note):
            await store.index_file(
                path=f"memory/{note.name}",
                content=note.read_text(encoding="utf-8"),
                source=MemorySource.memory,
            )

        await prune_expired_memory_files(
            memory_dir=memory_dir,
            store=store,
            ttl_days=30,
            workspace_dir=workspace,
        )

        assert not dated_note.exists()
        assert named_note.exists()

        results, _ = await store.search(
            query="release branch deploy", max_results=5, min_score=0.0
        )
        assert any(result.path == "memory/preferences.md" for result in results)
    finally:
        await store.close()
