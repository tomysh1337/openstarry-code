"""delete_session cascades V017 router_decisions rows (no SQL FK exists)."""

from __future__ import annotations

import sqlite3
from pathlib import Path

from openstarry_code.persistence.migrator import apply_pending
from openstarry_code.session.models import SessionNode
from openstarry_code.session.storage import SessionStorage

MIGRATIONS_DIR = Path(__file__).resolve().parents[2] / "migrations"


def _insert_decision(db: str, decision_id: str, session_key: str) -> None:
    conn = sqlite3.connect(db)
    try:
        conn.execute(
            "INSERT INTO router_decisions (decision_id, session_key, ts_ms, executed_kind) "
            "VALUES (?, ?, ?, 'single')",
            (decision_id, session_key, 1_000),
        )
        conn.commit()
    finally:
        conn.close()


def _decision_session_keys(db: str) -> set[str]:
    conn = sqlite3.connect(db)
    try:
        return {
            row[0]
            for row in conn.execute("SELECT session_key FROM router_decisions").fetchall()
        }
    finally:
        conn.close()


async def test_delete_session_purges_router_decisions(tmp_path: Path) -> None:
    db = str(tmp_path / "sessions.sqlite")
    apply_pending(db, MIGRATIONS_DIR)

    storage = SessionStorage(db_path=db)
    await storage.connect()
    try:
        await storage.upsert_session(
            SessionNode(session_key="agent:main:webchat:a", session_id="sid-a")
        )
        await storage.upsert_session(
            SessionNode(session_key="agent:main:webchat:b", session_id="sid-b")
        )
        _insert_decision(db, "d1", "agent:main:webchat:a")
        _insert_decision(db, "d2", "agent:main:webchat:a")
        _insert_decision(db, "d3", "agent:main:webchat:b")

        await storage.delete_session("agent:main:webchat:a")
    finally:
        await storage.close()

    # Only the deleted session's decision rows are gone.
    assert _decision_session_keys(db) == {"agent:main:webchat:b"}


async def test_delete_session_tolerates_missing_router_decisions_table() -> None:
    """In-memory DBs never run yoyo — the purge must stay a silent no-op."""
    storage = SessionStorage(db_path=":memory:")
    await storage.connect()
    try:
        await storage.upsert_session(
            SessionNode(session_key="agent:main:webchat:m", session_id="sid-m")
        )
        await storage.delete_session("agent:main:webchat:m")
        assert await storage.get_session("agent:main:webchat:m") is None
    finally:
        await storage.close()
