#!/usr/bin/env python3
"""Search SkillHub metadata with bounded multi-query ranking."""

from __future__ import annotations

import argparse
import json
import math
import re
import sys
import unicodedata
import urllib.error
import urllib.parse
import urllib.request


API_URL = "https://api.skillhub.cn/api/skills"
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
    "有没有",
    "技能",
}
ALIASES = {
    "文字提取": ("OCR", "文本提取"),
    "图片文字": ("OCR",),
    "扫描件": ("OCR", "PDF"),
    "公众号": ("微信公众号", "微信发布"),
    "发布": ("发布", "publisher"),
    "视频下载": ("视频下载", "yt-dlp"),
    "字幕": ("字幕", "transcript"),
    "表格": ("Excel", "spreadsheet"),
    "演示文稿": ("PPT", "presentation"),
    "简历": ("简历", "resume"),
    "合同": ("合同", "contract"),
}


def normalize(value: str) -> str:
    value = unicodedata.normalize("NFKC", value).lower().replace("_", "-")
    return re.sub(r"[^a-z0-9\u4e00-\u9fff]+", "-", value).strip("-")


def tokens(value: str) -> list[str]:
    parts: list[str] = []
    for part in normalize(value).split("-"):
        if not part or part in STOPWORDS:
            continue
        if re.fullmatch(r"[a-z0-9]+", part) and len(part) < 2:
            continue
        parts.append(part)
        if re.fullmatch(r"[\u4e00-\u9fff]+", part) and len(part) > 3:
            parts.extend(part[index : index + 2] for index in range(len(part) - 1))
    return list(dict.fromkeys(part for part in parts if part not in STOPWORDS))


def search_keywords(query: str, maximum: int) -> list[str]:
    candidates = [query.strip()]
    candidates.extend(
        match.group(0)
        for match in re.finditer(r"[A-Za-z0-9][A-Za-z0-9.+#-]{1,}", query)
    )
    candidates.extend(
        match.group(0)
        for match in re.finditer(r"[\u4e00-\u9fff]{2,}", query)
    )
    normalized_query = normalize(query)
    for phrase, aliases in ALIASES.items():
        if normalize(phrase) in normalized_query:
            candidates.extend(aliases)
    result: list[str] = []
    seen: set[str] = set()
    for candidate in candidates:
        key = normalize(candidate)
        if not key or key in STOPWORDS or key in seen:
            continue
        seen.add(key)
        result.append(candidate)
        if len(result) >= maximum:
            break
    return result


def fetch_page(
    keyword: str,
    category: str | None,
    page_size: int,
    timeout: float,
) -> list[dict[str, object]]:
    params = {
        "keyword": keyword,
        "sortBy": "score",
        "pageSize": str(page_size),
        "page": "1",
    }
    if category:
        params["category"] = category
    request = urllib.request.Request(
        f"{API_URL}?{urllib.parse.urlencode(params)}",
        headers={
            "Accept": "application/json",
            "User-Agent": "Codex-SkillHub-Catalog/1.0",
        },
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        payload = json.load(response)
    if payload.get("code") != 0:
        raise RuntimeError(str(payload.get("message") or "SkillHub API error"))
    data = payload.get("data") or {}
    rows = data.get("skills") or []
    return [row for row in rows if isinstance(row, dict)]


def contains(value: object, token: str) -> bool:
    return f"-{normalize(token)}-" in f"-{normalize(str(value or ''))}-"


def relevance(query: str, row: dict[str, object]) -> float:
    name = row.get("name") or ""
    slug = row.get("slug") or ""
    description = row.get("description_zh") or row.get("description") or ""
    normalized_query = normalize(query)
    normalized_name = normalize(str(name))
    normalized_slug = normalize(str(slug))
    result = 0.0
    if normalized_query in {normalized_name, normalized_slug}:
        result += 100.0
    if normalized_query and (
        normalized_name.startswith(normalized_query)
        or normalized_slug.startswith(normalized_query)
    ):
        result += 30.0
    for token in tokens(query):
        if contains(name, token) or contains(slug, token):
            result += 14.0
        elif contains(description, token):
            result += 3.0
    result += min(6.0, math.log1p(int(row.get("installs") or 0)))
    result += min(4.0, math.log1p(int(row.get("downloads") or 0)) / 2)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("query", help="Natural-language task or skill name")
    parser.add_argument("--category")
    parser.add_argument("--limit", type=int, default=5)
    parser.add_argument("--page-size", type=int, default=20)
    parser.add_argument("--max-queries", type=int, default=4)
    parser.add_argument("--timeout", type=float, default=20.0)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    merged: dict[str, dict[str, object]] = {}
    errors: list[str] = []
    keywords = search_keywords(args.query, max(1, args.max_queries))
    for keyword in keywords:
        try:
            rows = fetch_page(
                keyword,
                args.category,
                max(args.limit, args.page_size),
                args.timeout,
            )
        except (OSError, RuntimeError, urllib.error.URLError) as exc:
            errors.append(f"{keyword}: {exc}")
            continue
        for row in rows:
            slug = str(row.get("slug") or "")
            if not slug:
                continue
            current = merged.setdefault(slug, row)
            matches = current.setdefault("_matched_keywords", [])
            if keyword not in matches:
                matches.append(keyword)

    if not merged:
        for error in errors:
            print(f"warning: {error}", file=sys.stderr)
        return 2

    rows = list(merged.values())
    for row in rows:
        row["_relevance"] = relevance(args.query, row)
    rows.sort(
        key=lambda row: (
            -float(row["_relevance"]),
            -int(row.get("installs") or 0),
            -int(row.get("downloads") or 0),
            str(row.get("slug") or ""),
        )
    )
    rows = rows[: max(1, args.limit)]

    if args.json:
        print(json.dumps(rows, ensure_ascii=False, indent=2))
    else:
        for row in rows:
            description = row.get("description_zh") or row.get("description") or ""
            homepage = row.get("homepage") or (
                "https://skillhub.cn/skills/" + str(row.get("slug"))
            )
            print(
                f"{row['_relevance']:>6.1f}  {row.get('name')}  slug={row.get('slug')}\n"
                f"        category={row.get('category')} "
                f"downloads={row.get('downloads', 0)} installs={row.get('installs', 0)}\n"
                f"        {description}\n"
                f"        {homepage}"
            )
    for error in errors:
        print(f"warning: {error}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

