#!/usr/bin/env python3
"""Search cached Awesome repository skills and audited external candidates."""

from __future__ import annotations

import argparse
import json
import os
import re
import unicodedata
from pathlib import Path


VALID_NAME = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


def normalize(value: str) -> str:
    value = unicodedata.normalize("NFKC", value).lower().replace("_", "-")
    return re.sub(r"[^a-z0-9\u4e00-\u9fff]+", "-", value).strip("-")


def query_tokens(value: str) -> list[str]:
    tokens: list[str] = []
    for part in normalize(value).split("-"):
        if len(part) < 2:
            continue
        tokens.append(part)
        if re.fullmatch(r"[\u4e00-\u9fff]+", part) and len(part) > 2:
            tokens.extend(part[index : index + 2] for index in range(len(part) - 1))
    return list(dict.fromkeys(tokens))


def codex_home() -> Path:
    return Path(os.environ.get("CODEX_HOME", Path.home() / ".codex"))


def default_source() -> Path:
    return codex_home() / "skill-sources" / "composiohq-awesome-claude-skills"


def default_manifest() -> Path:
    return Path(__file__).resolve().parent.parent / "references" / "candidates.jsonl"


def strip_quotes(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
        value = value[1:-1]
    return value.replace(r'\"', '"')


def parse_metadata(text: str, fallback: str) -> tuple[str, str]:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return fallback, ""
    try:
        end = next(index for index in range(1, len(lines)) if lines[index].strip() == "---")
    except StopIteration:
        return fallback, ""

    values: dict[str, str] = {}
    frontmatter = lines[1:end]
    index = 0
    while index < len(frontmatter):
        match = re.match(r"^([A-Za-z0-9_-]+):\s*(.*)$", frontmatter[index])
        if not match:
            index += 1
            continue
        key, raw = match.groups()
        if raw.strip() in {"|", ">", "|-", ">-"}:
            block: list[str] = []
            index += 1
            while index < len(frontmatter) and (
                not frontmatter[index].strip() or frontmatter[index][0].isspace()
            ):
                block.append(frontmatter[index].strip())
                index += 1
            values[key] = " ".join(part for part in block if part)
            continue
        values[key] = strip_quotes(raw)
        index += 1
    return values.get("name") or fallback, values.get("description", "")


def current_installed_names() -> set[str]:
    roots = [codex_home() / "skills", Path.home() / ".agents" / "skills"]
    names: set[str] = set()
    for root in roots:
        if not root.is_dir():
            continue
        for skill_file in root.rglob("SKILL.md"):
            if ".system" in skill_file.parts:
                continue
            text = skill_file.read_text(encoding="utf-8", errors="replace")
            name, _ = parse_metadata(text, skill_file.parent.name)
            names.add(normalize(name))
    return names


def internal_rows(source: Path, installed: set[str]) -> list[dict[str, object]]:
    selected: dict[str, dict[str, object]] = {}
    for skill_file in source.rglob("SKILL.md"):
        relative = skill_file.relative_to(source)
        if any(part in {".git", "__pycache__"} for part in relative.parts):
            continue
        text = skill_file.read_text(encoding="utf-8", errors="replace")
        name, description = parse_metadata(text, skill_file.parent.name)
        key = normalize(name)
        if not key:
            continue
        item = {
            "kind": "source-cache",
            "canonical_name": key,
            "name": name,
            "description": description,
            "repo": "ComposioHQ/awesome-claude-skills",
            "ref": "92568c1edaff1bde5371154f036d959346c145a8",
            "path": relative.as_posix(),
            "source_path": str(skill_file.resolve()),
            "installed_now": key in installed,
            "recommendation": "cached-source",
        }
        rank = (
            0 if VALID_NAME.fullmatch(name) else 1,
            0 if normalize(skill_file.parent.name) == key else 1,
            len(relative.parts),
            len(str(relative)),
        )
        previous = selected.get(key)
        if previous is None or rank < previous["_rank"]:
            item["_rank"] = rank
            selected[key] = item
    rows = list(selected.values())
    for row in rows:
        row.pop("_rank", None)
    return rows


def external_rows(
    manifest: Path,
    installed: set[str],
    include_skipped: bool,
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for line in manifest.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        if not include_skipped and row.get("recommendation") != "candidate":
            continue
        name = normalize(str(row.get("canonical_name") or row.get("name") or ""))
        row["kind"] = "external-candidate"
        row["installed_now"] = name in installed
        rows.append(row)
    return rows


def score(query: str, row: dict[str, object]) -> int:
    normalized_query = normalize(query)
    name = normalize(str(row.get("canonical_name") or row.get("name") or ""))
    description = normalize(str(row.get("description") or ""))
    repo = normalize(str(row.get("repo") or ""))
    path = normalize(str(row.get("path") or ""))
    haystack = f"{name}-{description}-{repo}-{path}"
    result = 0
    if normalized_query == name:
        result += 100
    if normalized_query and name.startswith(normalized_query):
        result += 30
    if normalized_query and f"-{normalized_query}-" in f"-{haystack}-":
        result += 20
    for token in query_tokens(query):
        if f"-{token}-" in f"-{name}-":
            result += 12
        elif f"-{token}-" in f"-{description}-":
            result += 3
        elif f"-{token}-" in f"-{haystack}-":
            result += 1
    if result and row.get("installed_now"):
        result += 6
    if result and row.get("kind") == "source-cache":
        result += 3
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("query", nargs="?", help="Task, skill name, or repository")
    parser.add_argument("--limit", type=int, default=10)
    parser.add_argument("--all", action="store_true", help="Include skipped external entries")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--summary", action="store_true")
    parser.add_argument(
        "--scope",
        choices=("all", "internal", "external"),
        default="all",
    )
    parser.add_argument("--source", type=Path, default=default_source())
    parser.add_argument("--manifest", type=Path, default=default_manifest())
    args = parser.parse_args()

    installed = current_installed_names()
    rows: list[dict[str, object]] = []
    if args.scope in {"all", "internal"}:
        if not args.source.is_dir():
            parser.error(f"Awesome source cache not found: {args.source}")
        rows.extend(internal_rows(args.source, installed))
    if args.scope in {"all", "external"}:
        if not args.manifest.is_file():
            parser.error(f"External candidate manifest not found: {args.manifest}")
        rows.extend(external_rows(args.manifest, installed, args.all))

    if args.summary:
        payload = {
            "internal_canonical": sum(row["kind"] == "source-cache" for row in rows),
            "external_candidates": sum(
                row["kind"] == "external-candidate"
                and row.get("recommendation") == "candidate"
                for row in rows
            ),
            "total_rows": len(rows),
        }
        print(json.dumps(payload, ensure_ascii=False, indent=2) if args.json else payload)
        return 0
    if not args.query:
        parser.error("query is required unless --summary is used")

    matches: list[dict[str, object]] = []
    for row in rows:
        row["score"] = score(args.query, row)
        if int(row["score"]) > 0:
            matches.append(row)
    matches.sort(
        key=lambda row: (
            -int(row["score"]),
            not bool(row.get("installed_now")),
            row.get("kind") != "source-cache",
            bool(row.get("external_name_collision")),
            str(row.get("canonical_name") or row.get("name") or ""),
        )
    )
    matches = matches[: max(1, args.limit)]

    if args.json:
        print(json.dumps(matches, ensure_ascii=False, indent=2))
    else:
        for row in matches:
            status = "installed" if row.get("installed_now") else str(row.get("kind"))
            print(
                f"{row['score']:>3}  {row.get('canonical_name') or row.get('name')}"
                f"  [{status}]\n"
                f"     {row.get('repo')}@{row.get('ref')}:{row.get('path')}"
            )
            if row.get("source_path"):
                print(f"     {row['source_path']}")
    return 0 if matches else 1


if __name__ == "__main__":
    raise SystemExit(main())

