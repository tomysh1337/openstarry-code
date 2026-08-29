"""SSH/FTP/WSL/MCP remote browsing + FTP host CRUD route tests.

Covers the two gateway modules added for the IDE panel's Remote tab:
:mod:`openstarry_code.gateway.remote_routes` (pure parsing helpers and the
deterministic dispatch error paths) and :mod:`openstarry_code.gateway.ftp_routes`
(payload validation plus the full HTTP CRUD surface). Network-backed listing
paths are deliberately not exercised here — the dispatch helpers return stable
errors for unknown keys, which pins the wiring without a live server.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from starlette.applications import Starlette
from starlette.testclient import TestClient

from openstarry_code.gateway import ftp_routes as ftp_mod
from openstarry_code.gateway import remote_routes as remote_mod
from openstarry_code.gateway.config import (
    FTPHostEntry,
    GatewayConfig,
    MCPServerEntry,
    SSHHostEntry,
)


# ---------------------------------------------------------------------------
# remote_routes — pure helpers
# ---------------------------------------------------------------------------


def test_parse_long_listing() -> None:
    parsed = remote_mod._parse_long_listing(
        "-rw-r--r--   1 owner   group      1234 Jun  5 10:30 main.py"
    )
    assert parsed == {"name": "main.py", "type": "file", "size": 1234}

    parsed_dir = remote_mod._parse_long_listing(
        "drwxr-xr-x   2 owner   group      4096 Jun  5 10:30 src"
    )
    assert parsed_dir == {"name": "src", "type": "dir", "size": 4096}

    # Symlinks parse as files.
    assert remote_mod._parse_long_listing(
        "lrwxrwxrwx   1 a b   5 Jun  1 00:00 link"
    )["type"] == "file"

    # Banners, malformed lines and dot entries are ignored.
    assert remote_mod._parse_long_listing("total 42") is None
    assert remote_mod._parse_long_listing("-rw-r--r-- owner") is None
    assert remote_mod._parse_long_listing("d--------- 1 a b 1 Jun 1 00:00 .") is None
    assert remote_mod._parse_long_listing("d--------- 1 a b 1 Jun 1 00:00 ..") is None


def test_join_path() -> None:
    assert remote_mod._join_path("", "x") == "/x"
    assert remote_mod._join_path("/", "x") == "/x"
    assert remote_mod._join_path("/a", "b") == "/a/b"
    assert remote_mod._join_path("/a/", "b") == "/a/b"


def test_language_for_name() -> None:
    assert remote_mod._language_for_name("main.py") == "python"
    assert remote_mod._language_for_name("Dockerfile") == "dockerfile"
    assert remote_mod._language_for_name("README") is None


def test_build_file_response() -> None:
    text = remote_mod._build_file_response("a/b.py", "b.py", b"print(1)")
    assert text["binary"] is False
    assert text["content"] == "print(1)"
    assert text["language"] == "python"
    assert text["size"] == 8

    binary = remote_mod._build_file_response("a/img.png", "img.png", b"\x89PNG\r\n")
    assert binary["binary"] is True
    assert "content" not in binary

    truncated = remote_mod._build_file_response(
        "a/big.txt",
        "big.txt",
        b"x" * (remote_mod._MAX_FILE_BYTES + 10),
    )
    assert truncated["truncated"] is True
    assert len(truncated["content"]) == remote_mod._MAX_FILE_BYTES


def test_sorted_entries() -> None:
    entries = [
        {"name": "b.txt", "type": "file"},
        {"name": "A", "type": "dir"},
        {"name": "a.txt", "type": "file"},
    ]
    assert [e["name"] for e in remote_mod._sorted_entries(entries)] == [
        "A",
        "a.txt",
        "b.txt",
    ]


def test_parse_mcp_dir() -> None:
    content = json.dumps(
        [
            {"name": "src", "type": "dir"},
            {"name": "main.py", "type": "file", "size": 12},
            {"name": ".", "type": "dir"},
            {"name": "..", "type": "dir"},
            "junk",
        ]
    )
    entries = remote_mod._parse_mcp_dir(content)
    assert isinstance(entries, list)
    names = [e["name"] for e in entries]
    assert "src" in names and "main.py" in names
    assert "." not in names and ".." not in names

    assert remote_mod._parse_mcp_dir("not json") == "MCP directory result was not JSON"
    assert remote_mod._parse_mcp_dir(json.dumps({"a": 1})) == (
        "MCP directory result was not a list"
    )


def test_wsl_distros_without_binary(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(remote_mod, "_wsl_binary", lambda: None)
    assert remote_mod.wsl_distros() == []


# ---------------------------------------------------------------------------
# remote_routes — deterministic dispatch error paths (async)
# ---------------------------------------------------------------------------


def test_dispatch_unknown_keys() -> None:
    """Dispatch error paths for unknown keys / unsupported types.

    Driven through ``asyncio.run`` since this suite does not enable a pytest
    asyncio plugin; the handlers themselves are async.
    """
    import asyncio

    async def _run() -> None:
        config = GatewayConfig()
        assert await remote_mod._list_for(config, "ssh", "nope", "") == "No such SSH host"
        raw, error = await remote_mod._read_for(config, "ftp", "nope", "x")
        assert raw is None
        assert error == "No such FTP host"
        assert await remote_mod._list_for(config, "bogus", "k", "") == "Unsupported remote type"
        raw, error = await remote_mod._read_for(config, "bogus", "k", "x")
        assert raw is None
        assert error == "Unsupported remote type"
        assert await remote_mod._list_for(config, "git", "nope", "") == "No such git repository"
        raw, error = await remote_mod._read_for(config, "git", "nope", "x")
        assert raw is None
        assert error == "No such git repository"

    asyncio.run(_run())


# ---------------------------------------------------------------------------
# ftp_routes — validation / serialization / lookup
# ---------------------------------------------------------------------------


def test_parse_port() -> None:
    assert ftp_mod._parse_port(None) == (21, None)
    assert ftp_mod._parse_port("") == (21, None)
    assert ftp_mod._parse_port("2121") == (2121, None)
    assert ftp_mod._parse_port(22) == (22, None)
    assert ftp_mod._parse_port(True)[1] is not None
    assert ftp_mod._parse_port("abc")[1] is not None
    assert ftp_mod._parse_port(0)[1] is not None
    assert ftp_mod._parse_port(70000)[1] is not None


def test_validate_payload() -> None:
    fields, error = ftp_mod._validate_payload(
        {
            "name": " box ",
            "host": " ftp.example.com ",
            "port": "2121",
            "username": " deploy ",
            "password": "secret",
            "tls": True,
            "enabled": False,
        }
    )
    assert error is None
    assert fields == {
        "name": "box",
        "host": "ftp.example.com",
        "port": 2121,
        "username": "deploy",
        "password": "secret",
        "tls": True,
        "enabled": False,
    }

    assert ftp_mod._validate_payload({})[1] == "Name is required"
    assert ftp_mod._validate_payload({"name": "x"})[1] == "Host is required"
    assert ftp_mod._validate_payload({"name": "x", "host": "h", "port": "nope"})[1] is not None
    assert ftp_mod._validate_payload({"name": "x", "host": "h", "tls": "yes"})[1] == (
        "TLS must be a boolean"
    )
    assert ftp_mod._validate_payload({"name": "x", "host": "h", "enabled": 1})[1] == (
        "Enabled must be a boolean"
    )


def test_serialize_and_find() -> None:
    entry = FTPHostEntry(
        id="id-1",
        name="n",
        host="h",
        port=21,
        username="u",
        password="p",
        tls=True,
        enabled=False,
    )
    assert ftp_mod._serialize(entry) == {
        "id": "id-1",
        "name": "n",
        "host": "h",
        "port": 21,
        "username": "u",
        "password": "p",
        "tls": True,
        "enabled": False,
    }

    config = GatewayConfig()
    config.ftp.hosts = [
        FTPHostEntry(id="id-1", name="box", host="h", port=21),
        FTPHostEntry(id="", name="legacy", host="h2", port=21),
    ]
    assert ftp_mod.find_ftp_host(config, "id-1").name == "box"
    assert ftp_mod.find_ftp_host(config, "legacy").host == "h2"
    assert ftp_mod.find_ftp_host(config, "missing") is None


# ---------------------------------------------------------------------------
# HTTP surface — FTP host CRUD + remote sources / error paths
# ---------------------------------------------------------------------------


@pytest.fixture
def app_pair(tmp_path: pytest.TempPathFactory, monkeypatch: pytest.MonkeyPatch):
    """A bare app with just the new routes and a config we own (initially empty).

    The handlers read from the same mutable ``config`` at request time, so the
    sources test seeds hosts on it before calling ``GET /api/remote/sources``.
    """
    config = GatewayConfig()
    config.config_path = str(tmp_path / "config.toml")
    # Isolate the git-clone scan so the fixture never touches the real
    # developer workspace (it does not exist yet -> zero git sources).
    config.workspace_dir = str(tmp_path / "workspace")
    # Persistence writes the real config TOML; keep the handler under test
    # without touching the developer's filesystem.
    monkeypatch.setattr(ftp_mod, "_persist_config", lambda _config: None)

    app = Starlette(
        routes=[*ftp_mod.ftp_host_routes(config), *remote_mod.remote_routes(config)]
    )
    client = TestClient(app, base_url="http://127.0.0.1:18791")
    return client, config


def test_ftp_hosts_crud(app_pair) -> None:
    client, _config = app_pair

    assert client.get("/api/ftp/hosts").json() == {"hosts": []}

    resp = client.post(
        "/api/ftp/hosts",
        json={"name": "box", "host": "ftp.example.com", "port": 21},
    )
    assert resp.status_code == 201
    created = resp.json()
    assert created["id"]
    assert created["name"] == "box"
    assert created["port"] == 21
    host_id = created["id"]

    assert len(client.get("/api/ftp/hosts").json()["hosts"]) == 1

    resp = client.put(
        f"/api/ftp/hosts/{host_id}",
        json={"name": "renamed", "host": "h2", "port": 2121, "enabled": False},
    )
    assert resp.status_code == 200
    assert resp.json()["name"] == "renamed"
    assert resp.json()["enabled"] is False

    resp = client.delete(f"/api/ftp/hosts/{host_id}")
    assert resp.status_code == 200
    assert resp.json()["deleted"] is True
    assert client.get("/api/ftp/hosts").json()["hosts"] == []

    assert client.delete("/api/ftp/hosts/missing").status_code == 404


def test_ftp_hosts_validation_errors(app_pair) -> None:
    client, _config = app_pair
    assert client.post("/api/ftp/hosts", json={}).status_code == 400
    assert client.post("/api/ftp/hosts", json={"name": "x"}).status_code == 400
    assert (
        client.post(
            "/api/ftp/hosts",
            json={"name": "x", "host": "h", "port": "abc"},
        ).status_code
        == 400
    )
    # Non-object bodies are rejected outright.
    assert client.post("/api/ftp/hosts", json="not-an-object").status_code == 400


def test_remote_sources_shape(app_pair) -> None:
    client, config = app_pair
    config.ssh.hosts = [
        SSHHostEntry(id="s1", name="box", host="h", port=22, username="u", enabled=True),
        SSHHostEntry(id="s2", name="off", host="h2", port=22, enabled=False),
    ]
    config.ftp.hosts = [
        FTPHostEntry(id="f1", name="ftpbox", host="h", port=21, tls=True, enabled=True),
        FTPHostEntry(id="f2", name="ftpoff", host="h2", port=21, enabled=False),
    ]
    config.mcp.servers = [
        MCPServerEntry(id="m1", name="fs", transport="stdio", command="npx", enabled=True)
    ]

    resp = client.get("/api/remote/sources")
    assert resp.status_code == 200
    body = resp.json()
    assert set(body) == {"ssh", "ftp", "wsl", "mcp", "git"}
    # Disabled entries are hidden; enabled ones carry the source wire shape.
    assert body["ssh"] == [
        {"id": "s1", "name": "box", "host": "h", "port": 22, "username": "u"}
    ]
    assert body["ftp"] == [
        {"id": "f1", "name": "ftpbox", "host": "h", "port": 21, "username": "", "tls": True}
    ]
    assert body["mcp"] == [
        {"id": "m1", "name": "fs", "transport": "stdio"}
    ]
    assert isinstance(body["wsl"], list)


def test_remote_tree_and_file_errors(app_pair) -> None:
    client, _config = app_pair

    assert client.get("/api/remote/tree", params={"type": "bogus"}).status_code == 400
    assert client.get("/api/remote/tree", params={"type": "ssh"}).status_code == 400
    missing = client.get("/api/remote/tree", params={"type": "ssh", "id": "missing"})
    assert missing.status_code == 502
    assert missing.json()["error"] == "No such SSH host"

    assert client.get("/api/remote/file", params={"type": "ssh", "id": "s1"}).status_code == 400
    missing_file = client.get(
        "/api/remote/file",
        params={"type": "ftp", "id": "missing", "path": "/x"},
    )
    assert missing_file.status_code == 502
    assert missing_file.json()["error"] == "No such FTP host"


# ---------------------------------------------------------------------------
# git transport — cloned-repo discovery, browsing and traversal protection
# ---------------------------------------------------------------------------


def _make_workspace_repo(workspace: Path, name: str, files: dict[str, str]) -> Path:
    repo = workspace / name
    (repo / ".git").mkdir(parents=True, exist_ok=True)
    for rel, content in files.items():
        target = repo / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        # Write raw bytes so LF stays LF regardless of the host platform.
        target.write_bytes(content.encode("utf-8"))
    return repo


def test_git_discover_tree_and_file(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    repo = _make_workspace_repo(workspace, "hello", {"src/main.py": "print(1)\n", "README.md": "# Hi\n"})
    # A nested clone deeper in the tree is also discovered.
    nested = _make_workspace_repo(workspace / "vendor", "lib", {"lib.py": "x = 1\n"})
    # A plain directory without .git is not reported.
    (workspace / "notes").mkdir(parents=True, exist_ok=True)

    config = GatewayConfig()
    config.workspace_dir = str(workspace)

    sources = remote_mod._discover_git_repos(config)
    ids = {Path(s["id"]).resolve() for s in sources}
    assert Path(repo).resolve() in ids
    assert Path(nested).resolve() in ids
    assert len(sources) == 2

    # Root listing: dirs first, skip-dirs/file hygiene applies.
    entries = remote_mod._git_list(repo, "")
    assert isinstance(entries, list)
    names = {e["name"]: e["type"] for e in entries}
    assert names == {"src": "dir", "README.md": "file"}

    # Nested directory listing + file read.
    src = remote_mod._git_list(repo, "src")
    assert isinstance(src, list)
    assert [e["name"] for e in src] == ["main.py"]

    raw, error = remote_mod._git_read(repo, "src/main.py")
    assert error is None
    assert raw == b"print(1)\n"


def test_git_traversal_and_unknown_blocked(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    repo = _make_workspace_repo(workspace, "hello", {"main.py": "print(1)\n"})
    outside = tmp_path / "outside.py"
    outside.write_text("secret\n", encoding="utf-8")

    config = GatewayConfig()
    config.workspace_dir = str(workspace)

    # Escaping the repo root is rejected for both files and directories.
    assert remote_mod._git_read(repo, "../outside.py")[1] == "Path escapes the repository root"
    assert remote_mod._git_list(repo, "../") == "Path escapes the repository root"

    # Unknown ids (including paths outside the workspace) never resolve.
    assert remote_mod._find_git_repo(config, str(outside)) is None
    assert remote_mod._find_git_repo(config, "nope") is None


def test_git_http_browse(tmp_path: Path, app_pair) -> None:
    client, config = app_pair
    workspace = tmp_path / "workspace"
    config.workspace_dir = str(workspace)
    repo = _make_workspace_repo(workspace, "hello", {"main.py": "print(1)\n"})

    body = client.get("/api/remote/sources").json()
    assert body["git"] == [
        {"id": str(repo.resolve()), "name": "hello", "path": str(repo.resolve())}
    ]

    tree = client.get("/api/remote/tree", params={"type": "git", "id": str(repo), "path": ""})
    assert tree.status_code == 200
    assert [e["name"] for e in tree.json()["entries"]] == ["main.py"]

    f = client.get("/api/remote/file", params={"type": "git", "id": str(repo), "path": "main.py"})
    assert f.status_code == 200
    assert f.json()["content"] == "print(1)\n"
    assert f.json()["language"] == "python"

    # Unknown / escaping ids are rejected by the route.
    assert client.get("/api/remote/tree", params={"type": "git", "id": "missing"}).status_code == 502
    escaped = client.get(
        "/api/remote/tree",
        params={"type": "git", "id": str(repo), "path": "../outside"},
    )
    assert escaped.status_code == 502
    assert escaped.json()["error"] == "Path escapes the repository root"
