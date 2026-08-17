#!/usr/bin/env python3
"""Quantify residual obfuscation and damaged decompiler output in Java sources."""

from __future__ import annotations

import argparse
import collections
import json
import re
from pathlib import Path


PATTERNS = {
    "decompiler_failure": re.compile(r"could not decompile|decompilation failed|illegal opcode", re.I),
    "pseudo_dynamic_call": re.compile(r"invokedynamic|bootstrap\$|\$deserializeLambda\$"),
    "opaque_runtime_call": re.compile(r"\b(?:bhc|decode|decrypt|stringDecoder|opaque)\s*\(", re.I),
    "synthetic_local": re.compile(r"\b(?:var|v)\d+(?:_\d+)?\b"),
    "illegal_source": re.compile(r"\b(?:goto|jsr|ret)\b|/\* synthetic \*/\s*\?"),
    "unresolved_marker": re.compile(r"TODO|FIXME|UnsupportedOperationException|throw new IllegalStateException\(\"Decomp", re.I),
    "obfuscated_identifier": re.compile(r"\b(?:class|interface|enum|record)\s+[a-zA-Z_$]{1,2}\b"),
}


def audit(root: Path) -> dict:
    counts: collections.Counter[str] = collections.Counter()
    files_by_signal: dict[str, list[str]] = {name: [] for name in PATTERNS}
    java_files = sorted(root.rglob("*.java"))
    for path in java_files:
        text = path.read_text(encoding="utf-8", errors="replace")
        relative = path.relative_to(root).as_posix()
        for name, pattern in PATTERNS.items():
            matches = list(pattern.finditer(text))
            if matches:
                counts[name] += len(matches)
                files_by_signal[name].append(relative)
    signals = {
        name: {"count": counts[name], "files": files_by_signal[name][:200]}
        for name in PATTERNS
    }
    return {
        "sourceRoot": str(root.resolve()),
        "javaFiles": len(java_files),
        "signals": signals,
        "residualTotal": sum(counts.values()),
        "clean": not any(counts.values()),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("source_root", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = audit(args.source_root)
    payload = json.dumps(result, indent=2, ensure_ascii=False)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload + "\n", encoding="utf-8")
    print(payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
