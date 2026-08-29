"""Unit tests for the code-interpreter diff endpoint (/api/ide/diff).

The endpoint computes per-line AI-change marks against a one-time in-memory
snapshot of the project, so these tests exercise the snapshot + SequenceMatcher
pipeline against a throwaway directory tree.
"""

from __future__ import annotations

import asyncio
import json

import pytest
from starlette.requests import Request

from openstarry_code.gateway import ide_routes


def _make_request(query: str) -> Request:
    scope = {
        "type": "http",
        "method": "GET",
        "path": "/api/ide/diff",
        "query_string": query.encode(),
        "headers": [],
        "scheme": "http",
        "server": ("testserver", 80),
        "client": ("testclient", 12345),
        "root_path": "",
        "http_version": "1.1",
    }
    return Request(scope)


def _call_diff(query: str):
    return asyncio.run(ide_routes.api_ide_diff(_make_request(query)))


def _json(response) -> dict:
    return json.loads(response.body.decode("utf-8"))


@pytest.fixture(autouse=True)
def _reset_snapshot() -> None:
    ide_routes._diff_snapshot = None
    yield
    ide_routes._diff_snapshot = None


def _bind_root(monkeypatch: pytest.MonkeyPatch, root) -> None:
    monkeypatch.setattr(ide_routes, "resolve_project_root", lambda: root)


def test_diff_no_changes_on_first_access(tmp_path, monkeypatch) -> None:
    (tmp_path / "a.py").write_text("old1\nold2\nold3\n", encoding="utf-8")
    _bind_root(monkeypatch, tmp_path)

    response = _call_diff("path=a.py")
    assert response.status_code == 200
    assert _json(response)["has_changes"] is False
    assert _json(response)["summary"] == {"added": 0, "modified": 0, "removed": 0}


def test_diff_marks_added_and_modified(tmp_path, monkeypatch) -> None:
    path = tmp_path / "app.py"
    path.write_text("line1\nline2\nline3\n", encoding="utf-8")
    _bind_root(monkeypatch, tmp_path)

    _call_diff("path=app.py")  # establish baseline
    path.write_text("line1\nline2-CHANGED\nline3\nline4\n", encoding="utf-8")

    body = _json(_call_diff("path=app.py"))
    assert body["has_changes"] is True
    assert body["summary"] == {"added": 1, "modified": 1, "removed": 0}
    assert [entry["type"] for entry in body["entries"]] == ["context", "mod", "context", "add"]
    assert [entry["line"] for entry in body["entries"]] == [
        "line1",
        "line2-CHANGED",
        "line3",
        "line4",
    ]


def test_diff_new_file_after_snapshot_is_all_added(tmp_path, monkeypatch) -> None:
    (tmp_path / "existing.txt").write_text("keep\n", encoding="utf-8")
    _bind_root(monkeypatch, tmp_path)
    _call_diff("path=existing.txt")  # snapshot time

    (tmp_path / "new.txt").write_text("a\nb\n", encoding="utf-8")
    body = _json(_call_diff("path=new.txt"))
    assert body["summary"] == {"added": 2, "modified": 0, "removed": 0}
    assert all(entry["type"] == "add" for entry in body["entries"])


def test_diff_skips_skipped_directories(tmp_path, monkeypatch) -> None:
    (tmp_path / "node_modules").mkdir()
    (tmp_path / "node_modules" / "dep.txt").write_text("x\n", encoding="utf-8")
    (tmp_path / "real.py").write_text("y\n", encoding="utf-8")
    _bind_root(monkeypatch, tmp_path)

    _call_diff("path=real.py")
    with ide_routes._diff_lock:
        baseline = ide_routes._diff_snapshot[2]
    assert "node_modules/dep.txt" not in baseline
    assert "real.py" in baseline


def test_diff_uncaptured_existing_file_is_not_all_added(tmp_path, monkeypatch) -> None:
    # Simulate a file that existed at snapshot time but was not captured
    # (over the per-file size cap or beyond the file-count limit).
    path = tmp_path / "big.py"
    path.write_text("a\nb\n", encoding="utf-8")
    _bind_root(monkeypatch, tmp_path)
    ide_routes._diff_snapshot = (str(tmp_path), float("inf"), {})

    # First access: file predates the snapshot -> baselined silently.
    body = _json(_call_diff("path=big.py"))
    assert body["has_changes"] is False
    assert body["summary"] == {"added": 0, "modified": 0, "removed": 0}

    # Now modify it -> real marks show up.
    path.write_text("a\nb-CHANGED\nc\n", encoding="utf-8")
    body = _json(_call_diff("path=big.py"))
    assert body["has_changes"] is True
    assert body["summary"]["modified"] >= 1


def test_diff_rejects_path_escape(tmp_path, monkeypatch) -> None:
    _bind_root(monkeypatch, tmp_path)
    response = _call_diff("path=../outside.py")
    assert response.status_code == 400


def test_diff_requires_path(tmp_path, monkeypatch) -> None:
    _bind_root(monkeypatch, tmp_path)
    response = _call_diff("")
    assert response.status_code == 400
