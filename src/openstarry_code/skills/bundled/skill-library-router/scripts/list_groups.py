#!/usr/bin/env python3
"""List the installed skill library grouped by bilingual domain."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from find_local_skill import GROUP_ORDER, default_roots, load_skills


GROUP_LABELS = {
    "security-reverse": "安全与逆向 / Security and Reverse",
    "engineering": "软件工程 / Software Engineering",
    "cloud-ops": "云与运维 / Cloud and Operations",
    "frontend-creative": "前端与创意 / Frontend and Creative",
    "science-data": "科学与数据 / Science and Data",
    "docs-research": "文档与研究 / Docs and Research",
    "marketing-content": "营销与内容 / Marketing and Content",
    "planning-product": "规划与产品 / Planning and Product",
    "automation-catalog": "自动化与目录 / Automation and Catalog",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--group", choices=GROUP_ORDER)
    parser.add_argument("--include-sources", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--markdown", action="store_true")
    parser.add_argument(
        "--root",
        action="append",
        type=Path,
        dest="roots",
        help="Installed skill root. Repeat to search multiple roots.",
    )
    return parser.parse_args()


def grouped(skills: list[dict[str, object]], selected: str | None) -> dict[str, list[dict[str, object]]]:
    groups = {group: [] for group in GROUP_ORDER}
    for skill in skills:
        for group in skill["groups"]:
            if group in groups and (selected is None or group == selected):
                groups[group].append(
                    {
                        "name": skill["name"],
                        "description": skill["description"],
                        "path": skill["path"],
                        "origin": skill["origin"],
                        "installed": skill["installed"],
                    }
                )
    for entries in groups.values():
        entries.sort(key=lambda item: str(item["name"]).lower())
    return groups


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    args = parse_args()
    roots = args.roots or default_roots()
    if not roots:
        raise SystemExit("No installed skill roots were found")
    missing = [str(root) for root in roots if not root.is_dir()]
    if missing:
        raise SystemExit(f"Skill roots not found: {', '.join(missing)}")

    groups = grouped(load_skills(roots, args.include_sources), args.group)
    if args.json:
        print(json.dumps(groups, ensure_ascii=False, indent=2))
        return 0

    selected_groups = [args.group] if args.group else list(GROUP_ORDER)
    if args.markdown:
        print("# Skill Groups\n")
        print("Counts overlap when one skill serves more than one domain.\n")
        for group in selected_groups:
            entries = groups[group]
            print(f"## {GROUP_LABELS[group]} (`{group}`)\n")
            print(f"技能数：{len(entries)}\n")
            for entry in entries:
                print(f"- `{entry['name']}` - {entry['description']}")
            print()
        return 0

    for group in selected_groups:
        entries = groups[group]
        print(f"{group} ({len(entries)})")
        for entry in entries:
            print(f"  {entry['name']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
