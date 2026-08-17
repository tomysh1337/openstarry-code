#!/usr/bin/env python3
"""Find the closest Composio app workflow without loading the full catalog."""

from __future__ import annotations

import argparse
import json
import os
import re
import unicodedata
from pathlib import Path


VALID_NAME = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
STOPWORDS = {
    "a",
    "an",
    "and",
    "for",
    "from",
    "help",
    "in",
    "of",
    "on",
    "or",
    "please",
    "the",
    "to",
    "use",
    "using",
    "with",
    "我",
    "帮我",
    "使用",
    "需要",
    "查找",
}


def normalize(value: str) -> str:
    value = unicodedata.normalize("NFKC", value).lower().replace("_", "-")
    return re.sub(r"[^a-z0-9\u4e00-\u9fff]+", "-", value).strip("-")


def query_tokens(value: str) -> list[str]:
    tokens: list[str] = []
    for part in normalize(value).split("-"):
        if not part or part in STOPWORDS:
            continue
        if re.fullmatch(r"[a-z0-9]+", part) and len(part) < 2:
            continue
        tokens.append(part)
        if re.fullmatch(r"[\u4e00-\u9fff]+", part) and len(part) > 2:
            tokens.extend(part[index : index + 2] for index in range(len(part) - 1))
    return list(dict.fromkeys(token for token in tokens if token not in STOPWORDS))


def default_source() -> Path:
    codex_home = Path(os.environ.get("CODEX_HOME", Path.home() / ".codex"))
    return (
        codex_home
        / "skill-sources"
        / "composiohq-awesome-claude-skills"
        / "composio-skills"
    )


def frontmatter_value(text: str, key: str) -> str:
    match = re.search(rf"(?m)^{re.escape(key)}:\s*(.+)$", text)
    if not match:
        return ""
    value = match.group(1).strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
        value = value[1:-1]
    return value.replace(r'\"', '"')


def contains_token(value: str, token: str) -> bool:
    return f"-{normalize(token)}-" in f"-{normalize(value)}-"


def score(query: str, slug: str, name: str, description: str) -> int:
    normalized_query = normalize(query)
    normalized_name = normalize(name)
    normalized_description = normalize(description)
    tokens = query_tokens(query)
    app_slug = slug.removesuffix("-automation")
    app_parts = [part for part in app_slug.split("-") if len(part) > 1]

    result = 0
    if normalized_query in {slug, normalized_name, app_slug}:
        result += 100
    if normalized_query and (
        slug.startswith(normalized_query)
        or normalized_name.startswith(normalized_query)
        or app_slug.startswith(normalized_query)
    ):
        result += 30
    if any(token == app_slug for token in tokens):
        result += 60
    result += sum(35 for part in app_parts if part in tokens)
    result += sum(12 for token in tokens if contains_token(slug, token))
    result += sum(10 for token in tokens if contains_token(normalized_name, token))
    result += sum(2 for token in tokens if contains_token(normalized_description, token))
    return result


def canonical_rank(path: Path, name: str) -> tuple[int, int, str]:
    return (
        0 if VALID_NAME.fullmatch(name) else 1,
        path.name.count("_"),
        path.name,
    )


def find_matches(source: Path, query: str, limit: int) -> list[dict[str, object]]:
    canonical: dict[str, dict[str, object]] = {}
    for skill_file in source.glob("*/SKILL.md"):
        text = skill_file.read_text(encoding="utf-8", errors="replace")
        name = frontmatter_value(text, "name") or skill_file.parent.name
        description = frontmatter_value(text, "description")
        slug = normalize(skill_file.parent.name)
        item = {
            "slug": slug,
            "name": name,
            "description": description,
            "path": str(skill_file.resolve()),
            "score": score(query, slug, name, description),
            "_rank": canonical_rank(skill_file.parent, name),
        }
        previous = canonical.get(slug)
        if previous is None or item["_rank"] < previous["_rank"]:
            canonical[slug] = item

    matches = [item for item in canonical.values() if item["score"] > 0]
    matches.sort(key=lambda item: (-int(item["score"]), str(item["slug"])))
    for item in matches:
        item.pop("_rank", None)
    return matches[:limit]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("query", help="App name or workflow phrase")
    parser.add_argument("--source", type=Path, default=default_source())
    parser.add_argument("--limit", type=int, default=10)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    if not args.source.is_dir():
        parser.error(f"Catalog source not found: {args.source}")

    matches = find_matches(args.source, args.query, max(1, args.limit))
    if args.json:
        print(json.dumps(matches, ensure_ascii=False, indent=2))
    else:
        for item in matches:
            print(
                f"{item['score']:>3}  {item['slug']}\n"
                f"     {item['path']}\n"
                f"     {item['description']}"
            )
    return 0 if matches else 1


if __name__ == "__main__":
    raise SystemExit(main())

