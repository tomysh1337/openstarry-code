#!/usr/bin/env python3
"""Perform deterministic static triage for a candidate agent skill."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


ALLOWED_KEYS = {"name", "description", "license", "compatibility", "allowed-tools", "metadata"}
CODE_SUFFIXES = {".bat", ".cmd", ".js", ".mjs", ".ps1", ".py", ".sh", ".ts"}
SIGNALS = {
    "network": re.compile(r"https?://|\bcurl\b|\bwget\b|Invoke-WebRequest", re.I),
    "credentials": re.compile(r"token|secret|password|private[_ -]?key|credential", re.I),
    "persistence": re.compile(r"hook|startup|profile|crontab|scheduled task|autorun", re.I),
    "dynamic_execution": re.compile(r"\beval\s*\(|\bexec\s*\(|os\.system|child_process|subprocess", re.I),
    "destructive": re.compile(r"rm\s+-rf|Remove-Item\s+.*-Recurse|rmdir\s+/s|format\s+[a-z]:", re.I),
    "encoded_payload": re.compile(r"base64|fromCharCode|certutil\s+-decode", re.I),
}


def frontmatter(path: Path) -> tuple[dict[str, str], list[str]]:
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    if not lines or lines[0].strip() != "---":
        return {}, ["missing YAML frontmatter"]
    try:
        end = next(index for index in range(1, len(lines)) if lines[index].strip() == "---")
    except StopIteration:
        return {}, ["unterminated YAML frontmatter"]
    values: dict[str, str] = {}
    for line in lines[1:end]:
        if line and not line[0].isspace() and ":" in line:
            key, value = line.split(":", 1)
            values[key.strip()] = value.strip().strip("\"'")
    issues: list[str] = []
    if not values.get("name"):
        issues.append("missing name")
    if not values.get("description"):
        issues.append("missing description")
    invalid = sorted(set(values) - ALLOWED_KEYS)
    if invalid:
        issues.append(f"unsupported top-level keys: {', '.join(invalid)}")
    name = values.get("name", "")
    if name and not re.fullmatch(r"[a-z0-9-]{1,64}", name):
        issues.append("name must use lowercase letters, digits, and hyphens")
    return values, issues


def collisions(name: str, root: Path | None, current: Path) -> list[str]:
    if not name or root is None or not root.is_dir():
        return []
    found: list[str] = []
    for path in root.rglob("SKILL.md"):
        if current in path.parents:
            continue
        values, _ = frontmatter(path)
        if values.get("name", "").lower() == name.lower():
            found.append(str(path.resolve()))
    return found


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", type=Path)
    parser.add_argument("--compare-root", type=Path)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    skill_file = args.path / "SKILL.md" if args.path.is_dir() else args.path
    if not skill_file.is_file():
        parser.error(f"SKILL.md not found: {skill_file}")
    root = skill_file.parent
    metadata, issues = frontmatter(skill_file)
    files = [
        path
        for path in root.rglob("*")
        if path.is_file() and "__pycache__" not in path.parts and path.suffix != ".pyc"
    ]
    code_files = [path for path in files if path.suffix.lower() in CODE_SUFFIXES]
    signal_hits: dict[str, list[str]] = {key: [] for key in SIGNALS}
    for path in files:
        if path.stat().st_size > 2_000_000:
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        for key, pattern in SIGNALS.items():
            if pattern.search(text):
                signal_hits[key].append(str(path.relative_to(root)))
    payload = {
        "path": str(root.resolve()),
        "name": metadata.get("name", ""),
        "description": metadata.get("description", ""),
        "issues": issues,
        "file_count": len(files),
        "code_files": [str(path.relative_to(root)) for path in code_files],
        "signals": {key: value for key, value in signal_hits.items() if value},
        "collisions": collisions(metadata.get("name", ""), args.compare_root, root),
    }
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(f"name={payload['name']} files={payload['file_count']} code={len(code_files)}")
        for issue in issues:
            print(f"issue: {issue}")
        for key, paths in payload["signals"].items():
            print(f"signal:{key}: {', '.join(paths)}")
        for path in payload["collisions"]:
            print(f"collision: {path}")
    return 1 if issues else 0


if __name__ == "__main__":
    raise SystemExit(main())
