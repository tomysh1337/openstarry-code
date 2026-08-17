#!/usr/bin/env python3
"""Search the audited anbeime/skill source cache and report compatibility issues."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import unicodedata
from pathlib import Path


ALLOWED_KEYS = {"name", "description", "license", "allowed-tools", "metadata"}
VALID_NAME = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
STOPWORDS = {
    "a",
    "an",
    "and",
    "for",
    "help",
    "in",
    "of",
    "on",
    "or",
    "please",
    "the",
    "to",
    "use",
    "with",
    "我",
    "帮我",
    "需要",
    "一个",
    "一下",
    "如何",
    "怎么",
}
ALIASES = {
    "微信公众号": ("wechat", "post", "publish", "公众号", "发布"),
    "公众号": ("wechat", "post", "publish"),
    "微信": ("wechat",),
    "发布": ("post", "publish", "publisher"),
    "推送": ("post", "publish"),
    "文章": ("article", "content"),
    "排版": ("format", "markdown"),
    "视频下载": ("video", "download", "downloader"),
    "字幕": ("subtitle", "transcript"),
    "简历": ("resume",),
    "合同": ("contract", "legal"),
    "演示文稿": ("ppt", "pptx", "presentation"),
}


def normalize(value: str) -> str:
    value = unicodedata.normalize("NFKC", value).lower().replace("_", "-")
    return re.sub(r"[^a-z0-9\u4e00-\u9fff]+", "-", value).strip("-")


def query_tokens(value: str) -> list[str]:
    normalized = normalize(value)
    tokens: list[str] = []
    for part in normalized.split("-"):
        if not part or part in STOPWORDS:
            continue
        if re.fullmatch(r"[a-z0-9]+", part) and len(part) < 2:
            continue
        tokens.append(part)
        if re.fullmatch(r"[\u4e00-\u9fff]+", part) and len(part) > 2:
            tokens.extend(part[index : index + 2] for index in range(len(part) - 1))
    for phrase, aliases in ALIASES.items():
        if normalize(phrase) in normalized:
            tokens.extend(aliases)
    return list(dict.fromkeys(token for token in tokens if token not in STOPWORDS))


def default_source() -> Path:
    codex_home = Path(os.environ.get("CODEX_HOME", Path.home() / ".codex"))
    return codex_home / "skill-sources" / "anbeime-skill"


def strip_quotes(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
        value = value[1:-1]
    return value.replace(r'\"', '"')


def parse_frontmatter(text: str) -> tuple[dict[str, str], list[str]]:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}, ["no-frontmatter"]

    try:
        end = next(index for index in range(1, len(lines)) if lines[index].strip() == "---")
    except StopIteration:
        return {}, ["unterminated-frontmatter"]

    frontmatter = lines[1:end]
    values: dict[str, str] = {}
    keys: list[str] = []
    index = 0
    while index < len(frontmatter):
        match = re.match(r"^([A-Za-z0-9_-]+):\s*(.*)$", frontmatter[index])
        if not match:
            index += 1
            continue
        key, raw = match.groups()
        keys.append(key)
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

    issues = [f"extra-field:{key}" for key in keys if key not in ALLOWED_KEYS]
    return values, issues


def contains_token(value: str, token: str) -> bool:
    return f"-{normalize(token)}-" in f"-{normalize(value)}-"


def score(query: str, slug: str, name: str, description: str) -> int:
    normalized_query = normalize(query)
    normalized_name = normalize(name)
    normalized_description = normalize(description)
    tokens = query_tokens(query)
    result = 0
    if normalized_query in {slug, normalized_name}:
        result += 100
    if normalized_query and (
        slug.startswith(normalized_query) or normalized_name.startswith(normalized_query)
    ):
        result += 30
    if normalized_query and contains_token(f"{slug}-{normalized_name}", normalized_query):
        result += 20
    for token in tokens:
        if contains_token(slug, token) or contains_token(normalized_name, token):
            result += 16
        elif contains_token(normalized_description, token):
            result += 3
    return result


def find_matches(source: Path, query: str, limit: int) -> list[dict[str, object]]:
    unique: dict[tuple[str, str], dict[str, object]] = {}
    for skill_file in source.rglob("SKILL.md"):
        text = skill_file.read_text(encoding="utf-8", errors="replace")
        values, issues = parse_frontmatter(text)
        name = values.get("name") or skill_file.parent.name
        description = values.get("description", "")
        slug = normalize(name or skill_file.parent.name)
        if not VALID_NAME.fullmatch(name):
            issues.append("invalid-name")
        if normalize(skill_file.parent.name) != slug:
            issues.append("directory-name-mismatch")
        digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
        item = {
            "slug": slug,
            "name": name,
            "description": description,
            "path": str(skill_file.resolve()),
            "issues": sorted(set(issues)),
            "score": score(query, slug, name, description),
        }
        unique.setdefault((slug, digest), item)

    matches = [item for item in unique.values() if item["score"] > 0]
    matches.sort(
        key=lambda item: (
            -int(item["score"]),
            len(item["issues"]),
            str(item["slug"]),
            str(item["path"]),
        )
    )
    return matches[:limit]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("query", help="Skill name, product, or workflow")
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
            issues = ", ".join(item["issues"]) or "none"
            print(
                f"{item['score']:>3}  {item['slug']}  issues={issues}\n"
                f"     {item['path']}\n"
                f"     {item['description']}"
            )
    return 0 if matches else 1


if __name__ == "__main__":
    raise SystemExit(main())

