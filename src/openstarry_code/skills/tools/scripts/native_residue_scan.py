#!/usr/bin/env python3
"""Scan local artifacts for native-looking ``-3######``/``0x######`` residues.

The scanner is deliberately byte based so offsets remain useful to IDA/Ghidra.
It emits one JSON document on stdout and never rewrites the input artifact.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections.abc import Iterable
from pathlib import Path
from typing import BinaryIO

PATTERNS: tuple[tuple[str, re.Pattern[bytes]], ...] = (
    ("negative_decimal", re.compile(rb"-3\d{6}")),
    ("hex_address", re.compile(rb"0x[0-9A-Fa-f]{6}")),
)
_CHUNK_SIZE = 1024 * 1024
_OVERLAP = 7  # longest pattern is eight bytes


def _iter_files(target: Path) -> Iterable[Path]:
    if target.is_file():
        yield target
        return
    if target.is_dir():
        yield from (item for item in target.rglob("*") if item.is_file())


def _scan_stream(stream: BinaryIO, *, max_matches: int | None) -> list[dict[str, object]]:
    matches: list[dict[str, object]] = []
    carry = b""
    file_offset = 0
    while True:
        chunk = stream.read(_CHUNK_SIZE)
        if not chunk:
            break
        window = carry + chunk
        window_base = file_offset - len(carry)
        for kind, pattern in PATTERNS:
            for found in pattern.finditer(window):
                offset = window_base + found.start()
                # Skip only matches wholly contained in the previous window.
                # A match may begin in the overlap and finish in this chunk.
                if offset < file_offset and window_base + found.end() <= file_offset:
                    continue
                matches.append(
                    {"kind": kind, "value": found.group().decode("ascii"), "offset": offset}
                )
                if max_matches is not None and len(matches) >= max_matches:
                    return sorted(matches, key=lambda item: int(item["offset"]))
        file_offset += len(chunk)
        carry = window[-_OVERLAP:]
    return sorted(matches, key=lambda item: int(item["offset"]))


def scan_file(path: Path, *, max_matches: int | None) -> dict[str, object]:
    entry: dict[str, object] = {"path": str(path.resolve()), "matches": []}
    try:
        entry["size"] = path.stat().st_size
        with path.open("rb") as stream:
            entry["matches"] = _scan_stream(stream, max_matches=max_matches)
    except (OSError, ValueError) as exc:
        entry["error"] = f"{type(exc).__name__}: {exc}"
    return entry


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="+", type=Path, help="files or directories to scan")
    parser.add_argument(
        "--max-matches-per-file",
        type=int,
        default=None,
        metavar="N",
        help="stop after N matches in each file",
    )
    args = parser.parse_args(argv)
    if args.max_matches_per_file is not None and args.max_matches_per_file < 1:
        parser.error("--max-matches-per-file must be positive")

    files: list[Path] = []
    missing: list[str] = []
    for target in args.paths:
        if not target.exists():
            missing.append(str(target))
            continue
        files.extend(_iter_files(target))
    results = [
        scan_file(path, max_matches=args.max_matches_per_file)
        for path in sorted(set(files))
    ]
    payload = {
        "tool": "native_residue_scan",
        "patterns": ["-3######", "0x######"],
        "targets": [str(path.resolve()) for path in args.paths],
        "files": results,
        "summary": {
            "files_scanned": len(results),
            "files_with_matches": sum(bool(item.get("matches")) for item in results),
            "match_count": sum(len(item.get("matches", [])) for item in results),
            "missing_targets": missing,
            "errors": sum("error" in item for item in results),
        },
    }
    json.dump(payload, sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
