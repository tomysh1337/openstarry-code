#!/usr/bin/env python3
"""Compile a recovered Java tree and emit grouped, reproducible diagnostics."""

from __future__ import annotations

import argparse
import collections
import json
import os
import re
import subprocess
import tempfile
from pathlib import Path


DIAGNOSTIC = re.compile(r"^(.*?\.java):(\d+):\s*(?:error|warning):\s*(.*)$", re.I)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--classes", type=Path)
    parser.add_argument("--classpath", default="")
    parser.add_argument("--release")
    parser.add_argument("--javac", default="javac")
    args = parser.parse_args()

    sources = sorted(args.source_root.rglob("*.java"))
    classes = (args.classes or args.output.parent / "compile-classes").resolve()
    classes.mkdir(parents=True, exist_ok=True)
    command = [args.javac, "-encoding", "UTF-8", "-d", str(classes)]
    if args.classpath:
        command += ["-classpath", args.classpath]
    if args.release:
        command += ["--release", args.release]

    with tempfile.NamedTemporaryFile("w", encoding="utf-8", suffix=".args", delete=False) as handle:
        argument_file = Path(handle.name)
        for source in sources:
            handle.write('"' + str(source.resolve()).replace("\\", "\\\\") + '"\n')
    try:
        completed = subprocess.run(
            command + ["@" + str(argument_file)],
            text=True,
            encoding="utf-8",
            errors="replace",
            capture_output=True,
            check=False,
        )
    finally:
        argument_file.unlink(missing_ok=True)

    diagnostics = []
    roots: collections.Counter[str] = collections.Counter()
    for line in completed.stderr.splitlines():
        match = DIAGNOSTIC.match(line)
        if not match:
            continue
        message = match.group(3).strip()
        root = re.sub(r"'[^']+'|\"[^\"]+\"|\b\d+\b", "<value>", message)
        roots[root] += 1
        diagnostics.append({"file": match.group(1), "line": int(match.group(2)), "message": message})

    result = {
        "sourceRoot": str(args.source_root.resolve()),
        "sourceFiles": len(sources),
        "exitCode": completed.returncode,
        "diagnosticCount": len(diagnostics),
        "rootCauses": [{"message": key, "count": value} for key, value in roots.most_common()],
        "diagnostics": diagnostics,
        "command": command + ["@SOURCES"],
        "stdout": completed.stdout,
        "stderr": completed.stderr,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({key: result[key] for key in ("sourceFiles", "exitCode", "diagnosticCount", "rootCauses")}, indent=2, ensure_ascii=False))
    return 0 if completed.returncode == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
