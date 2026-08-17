#!/usr/bin/env python3
"""Inventory cached skill sources without loading their bodies into context."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
from pathlib import Path


SKIP_PARTS = {
    ".git",
    ".system",
    ".venv",
    "__pycache__",
    "node_modules",
    "test",
    "tests",
    "template",
    "templates",
}


def codex_home() -> Path:
    return Path(os.environ.get("CODEX_HOME", Path.home() / ".codex"))


def git_value(root: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(root), *args],
        capture_output=True,
        check=False,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    return result.stdout.strip() if result.returncode == 0 else ""


def skill_files(root: Path):
    for path in root.rglob("SKILL.md"):
        relative = path.relative_to(root)
        if any(part.lower() in SKIP_PARTS for part in relative.parts):
            continue
        yield path


def parse_header(path: Path) -> tuple[str, str]:
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    if not lines or lines[0].strip() != "---":
        return path.parent.name, ""
    values: dict[str, str] = {}
    for line in lines[1:]:
        if line.strip() == "---":
            break
        if line and not line[0].isspace() and ":" in line:
            key, value = line.split(":", 1)
            values[key.strip()] = value.strip().strip("\"'")
    return values.get("name") or path.parent.name, values.get("description", "")


def source_row(root: Path, query: str | None) -> dict[str, object]:
    skills = list(skill_files(root))
    matches: list[dict[str, str]] = []
    if query:
        terms = [part.lower() for part in query.split() if part]
        for path in skills:
            name, description = parse_header(path)
            haystack = f"{name} {description}".lower()
            if all(term in haystack for term in terms):
                matches.append({"name": name, "path": str(path.resolve())})
    is_git = (root / ".git").is_dir()
    return {
        "source": root.name,
        "path": str(root.resolve()),
        "kind": "git" if is_git else "catalog",
        "skill_count": len(skills),
        "commit": git_value(root, "rev-parse", "HEAD") if is_git else "",
        "remote": git_value(root, "remote", "get-url", "origin") if is_git else "",
        "matches": matches[:50],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=codex_home() / "skill-sources")
    parser.add_argument("--query")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    if not args.root.is_dir():
        parser.error(f"Source root not found: {args.root}")
    rows = [
        source_row(path, args.query)
        for path in sorted(args.root.iterdir())
        if path.is_dir() and not path.name.startswith(".")
    ]
    if args.json:
        print(json.dumps(rows, ensure_ascii=False, indent=2))
    else:
        for row in rows:
            suffix = f" matches={len(row['matches'])}" if args.query else ""
            print(f"{row['source']}: kind={row['kind']} skills={row['skill_count']}{suffix}")
            for match in row["matches"][:10]:
                print(f"  {match['name']}  {match['path']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
