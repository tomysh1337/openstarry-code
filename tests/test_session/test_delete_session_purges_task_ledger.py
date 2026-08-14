"""Session delete purges agent_tasks and memory_durable_receipts rows."""

from __future__ import annotations

from openstarry_code.session.models import (
    AgentTaskRecord,
    AgentTaskStatus,
    MemoryDurableReceipt,
    SessionNode,
)
from openstarry_code.session.storage import SessionStorage

KEY = "agent:main:webchat:default"


async def test_delete_session_purges_agent_tasks(tmp_path) -> None:
    storage = SessionStorage(str(tmp_path / "sessions.db"))
    await storage.connect()
    try:
        await storage.upsert_session(SessionNode(session_key=KEY, session_id="sid-old"))
        await storage.create_agent_task(
            AgentTaskRecord(
                task_id="task-1",
                session_key=KEY,
                source_kind="webui",
                queue_mode="followup",
                run_kind="web_turn",
                status=AgentTaskStatus.RUNNING,
            )
        )

        await storage.delete_session(KEY)

        assert await storage.get_session(KEY) is None
        assert await storage.list_agent_tasks(session_key=KEY) == []
    finally:
        await storage.close()


async def test_delete_session_purges_memory_durable_receipts(tmp_path) -> None:
    storage = SessionStorage(str(tmp_path / "sessions.db"))
    await storage.connect()
    try:
        await storage.upsert_session(SessionNode(session_key=KEY, session_id="sid-old"))
        await storage.upsert_memory_durable_receipt(
            MemoryDurableReceipt(
                session_key=KEY,
                session_id="sid-old",
                scope="checkpoint",
                source_path="memory/2026-01-01.md",
                idempotency_key="idem-1",
                status="failed",
                reason="disk full",
            )
        )

        await storage.delete_session(KEY)

        assert await storage.get_session(KEY) is None
        assert await storage.list_memory_durable_receipts(session_key=KEY) == []
    finally:
        await storage.close()


async def test_recreated_session_key_does_not_inherit_deleted_tasks(tmp_path) -> None:
    storage = SessionStorage(str(tmp_path / "sessions.db"))
    await storage.connect()
    try:
        await storage.upsert_session(SessionNode(session_key=KEY, session_id="sid-old"))
        await storage.create_agent_task(
            AgentTaskRecord(
                task_id="task-1",
                session_key=KEY,
                source_kind="webui",
                queue_mode="followup",
                run_kind="web_turn",
                status=AgentTaskStatus.FAILED,
                terminal_reason="error",
            )
        )
        await storage.delete_session(KEY)

        await storage.upsert_session(SessionNode(session_key=KEY, session_id="sid-new"))

        grouped = await storage.list_agent_tasks_for_sessions([KEY])
        assert grouped[KEY] == []
    finally:
        await storage.close()
