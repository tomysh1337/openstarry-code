#!/usr/bin/env python3
"""Classify local artifacts by extension and magic bytes, emitting JSON."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections.abc import Iterable
from pathlib import Path

MAGIC = {
    b"MZ": "pe",
    b"\x7fELF": "elf",
    b"\xca\xfe\xba\xbe": "java_class",
    b"PK\x03\x04": "zip_container",
    b"PK\x05\x06": "zip_empty",
}
EXTENSIONS: dict[str, str] = {
    ".jar": "jar",
    ".class": "class",
    ".java": "java",
    ".exe": "exe",
    ".dll": "dll",
    ".so": "so",
    ".cpp": "cpp",
    ".cc": "cpp",
    ".cxx": "cpp",
    ".c": "cpp",
    ".py": "py",
    ".apk": "apk",
    ".aar": "aar",
    ".dex": "dex",
}


def _iter_files(target: Path) -> Iterable[Path]:
    if target.is_file():
        yield target
    elif target.is_dir():
        yield from (item for item in target.rglob("*") if item.is_file())


def _kind(extension: str, magic: list[str]) -> tuple[str, str]:
    if "pe" in magic:
        return ("exe" if extension == ".exe" else "dll", "high")
    if "elf" in magic:
        return ("native", "high")
    if "java_class" in magic:
        return ("class", "high")
    if "zip_container" in magic or "zip_empty" in magic:
        if extension in {".apk", ".aar", ".jar"}:
            return (EXTENSIONS[extension], "high")
        return ("zip_container", "medium")
    if extension in EXTENSIONS:
        return (EXTENSIONS[extension], "medium")
    return ("unknown", "low")


def _workflow(kind: str) -> list[dict[str, object]]:
    static: dict[str, object] = {"stage": "static", "status": "recommended"}
    debug: dict[str, object] = {"stage": "module_debug", "status": "recommended"}
    dynamic: dict[str, object] = {"stage": "dynamic_sandbox", "status": "recommended"}
    residue = {
        "stage": "native_residue_scan",
        "status": "recommended",
        "tools": ["native_residue_scan.py"],
        "trigger": "-3###### or 0x######",
    }
    if kind in {"jar", "class", "java"}:
        static["tools"] = ["Recaf", "enigma-mcp", "Vineflower/CFR", "javap"]
        debug["tools"] = ["Java JDWP", "jdb"]
        dynamic["tools"] = ["JVM trace", "dynamic sandbox"]
    elif kind in {"exe", "dll", "so", "native"}:
        static["tools"] = ["IDA", "Ghidra", "strings", "PE/ELF headers"]
        debug["tools"] = ["IDA debugger", "x64dbg/WinDbg", "GDB/LLDB"]
        dynamic["tools"] = ["Frida", "dynamic sandbox"]
    elif kind == "apk":
        static["tools"] = ["apktool", "jadx", "aapt2", "baksmali"]
        debug["tools"] = ["ADB/emulator", "Frida"]
        dynamic["tools"] = ["Logcat", "dynamic sandbox"]
    elif kind == "aar":
        static["tools"] = ["unzip", "jadx", "apktool"]
        debug["tools"] = ["Java JDWP", "ADB/emulator"]
        dynamic["tools"] = ["Frida", "dynamic sandbox"]
    elif kind == "dex":
        static["tools"] = ["jadx", "baksmali"]
        debug["tools"] = ["ADB/emulator", "Frida"]
        dynamic["tools"] = ["Logcat", "dynamic sandbox"]
    elif kind == "cpp":
        static["tools"] = ["compiler AST", "IDA", "Ghidra"]
        debug["tools"] = ["GDB/LLDB", "sanitizers"]
        dynamic["tools"] = ["dynamic sandbox"]
    elif kind == "py":
        static["tools"] = ["ast", "dis", "compileall"]
        debug["tools"] = ["Python trace", "pdb"]
        dynamic["tools"] = ["restricted Python sandbox"]
    else:
        static["tools"] = ["file", "strings"]
        debug["status"] = "conditional"
        dynamic["status"] = "conditional"
    return [static, debug, dynamic, residue]


def triage_file(path: Path) -> dict[str, object]:
    result: dict[str, object] = {"path": str(path.resolve())}
    try:
        data = path.read_bytes()[:16]
        extension = path.suffix.lower()
        magic = [name for signature, name in MAGIC.items() if data.startswith(signature)]
        kind, confidence = _kind(extension, magic)
        result.update(
            {
                "extension": extension or None,
                "magic": magic,
                "kind": kind,
                "confidence": confidence,
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                "workflow": _workflow(kind),
            }
        )
    except OSError as exc:
        result["error"] = f"{type(exc).__name__}: {exc}"
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="+", type=Path, help="files or directories to classify")
    args = parser.parse_args(argv)
    files: list[Path] = []
    missing: list[str] = []
    for target in args.paths:
        if not target.exists():
            missing.append(str(target))
            continue
        files.extend(_iter_files(target))
    results = [triage_file(path) for path in sorted(set(files))]
    payload = {
        "tool": "artifact_triage",
        "targets": [str(path.resolve()) for path in args.paths],
        "artifacts": results,
        "summary": {
            "artifacts": len(results),
            "errors": sum("error" in item for item in results),
            "missing_targets": missing,
        },
    }
    json.dump(payload, sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
