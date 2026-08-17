#!/usr/bin/env python3
"""Query the installed Codex skill index through a stable single entry point."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


GROUPS = (
    "security-reverse",
    "engineering",
    "cloud-ops",
    "frontend-creative",
    "science-data",
    "docs-research",
    "marketing-content",
    "planning-product",
    "automation-catalog",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("task", help="Task description or skill name")
    parser.add_argument("--group", choices=GROUPS)
    parser.add_argument("--limit", type=int, default=8)
    parser.add_argument("--include-sources", action="store_true")
    parser.add_argument(
        "--no-auto-group",
        action="store_true",
        help="Search every domain instead of inferring one from task keywords.",
    )
    parser.add_argument("--json", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.limit < 1 or args.limit > 100:
        raise SystemExit("--limit must be between 1 and 100")

    skill_root = Path(__file__).resolve().parents[2]
    finder = skill_root / "skill-library-router" / "scripts" / "find_local_skill.py"
    if not finder.is_file():
        raise SystemExit(f"Local skill index was not found: {finder}")

    command = [sys.executable, str(finder), args.task, "--limit", str(args.limit)]
    if args.group:
        command.extend(("--group", args.group))
    elif not args.no_auto_group:
        command.append("--auto-group")
    if args.include_sources:
        command.append("--include-sources")
    if args.json:
        command.append("--json")

    return subprocess.run(command, check=False).returncode


if __name__ == "__main__":
    raise SystemExit(main())
