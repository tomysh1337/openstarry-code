#!/usr/bin/env python3
"""Static Java JAR inventory and local-tool probe with no third-party dependencies."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
import shutil
import struct
import subprocess
import sys
import zipfile
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


SCHEMA = "advanced-java-reverse-deobf/jar-probe/v1"
MAX_DEFAULT_CLASS_BYTES = 16 * 1024 * 1024
MAX_DEFAULT_CLASSES = 50_000
MAX_TOOL_RESULTS = 24
SKIP_TOOL_DIRS = {".git", ".gradle", ".idea", "build", "node_modules", "out", "target"}

JAVA_RELEASES = {
    45: "1.1", 46: "1.2", 47: "1.3", 48: "1.4", 49: "5", 50: "6", 51: "7",
    52: "8", 53: "9", 54: "10", 55: "11", 56: "12", 57: "13", 58: "14",
    59: "15", 60: "16", 61: "17", 62: "18", 63: "19", 64: "20", 65: "21",
    66: "22", 67: "23", 68: "24", 69: "25", 70: "26",
}

COMMANDS = {
    "java": ("-version",),
    "javap": ("--version",),
    "jar": ("--version",),
    "jarsigner": ("-help",),
}

TOOL_PATTERNS = {
    "recaf": re.compile(r"^recaf(?:[-_.].*)?\.jar$", re.IGNORECASE),
    "vineflower": re.compile(r"^(?:vineflower|fernflower)(?:[-_.].*)?\.jar$", re.IGNORECASE),
    "cfr": re.compile(r"^cfr(?:[-_.].*)?\.jar$", re.IGNORECASE),
    "java-deobfuscator": re.compile(r"^deobfuscator(?:[-_.].*)?\.jar$", re.IGNORECASE),
    "enigma": re.compile(r"^enigma(?:[-_.].*)?\.jar$", re.IGNORECASE),
    "bytecode-viewer": re.compile(r"^bytecode[-_.]?viewer(?:[-_.].*)?\.jar$", re.IGNORECASE),
    "xingkong-deobfuscator": re.compile(r"^xingkong-deobfuscator(?:[-_.].*)?\.jar$", re.IGNORECASE),
    "xingkong-shield": re.compile(r"^xingkong-shield(?:[-_.].*)?\.jar$", re.IGNORECASE),
}

FIXED_OPCODE_LENGTHS = {
    0x10: 2, 0x11: 3, 0x12: 2, 0x13: 3, 0x14: 3,
    **{opcode: 2 for opcode in range(0x15, 0x1A)},
    **{opcode: 2 for opcode in range(0x36, 0x3B)},
    0x84: 3,
    **{opcode: 3 for opcode in range(0x99, 0xA9)},
    0xA9: 2,
    **{opcode: 3 for opcode in range(0xB2, 0xB9)},
    0xB9: 5, 0xBA: 5, 0xBB: 3, 0xBC: 2, 0xBD: 3, 0xC0: 3, 0xC1: 3,
    0xC5: 4, 0xC6: 3, 0xC7: 3, 0xC8: 5, 0xC9: 5,
}


class ClassFormatError(ValueError):
    """Raised when a class file cannot be parsed safely."""


class Reader:
    def __init__(self, data: bytes) -> None:
        self.data = data
        self.offset = 0

    def take(self, count: int) -> bytes:
        if count < 0 or self.offset + count > len(self.data):
            raise ClassFormatError("truncated class file")
        value = self.data[self.offset:self.offset + count]
        self.offset += count
        return value

    def u1(self) -> int:
        return self.take(1)[0]

    def u2(self) -> int:
        return struct.unpack(">H", self.take(2))[0]

    def u4(self) -> int:
        return struct.unpack(">I", self.take(4))[0]


def decode_modified_utf8(raw: bytes) -> str:
    """Return a display-safe approximation for constant-pool UTF-8 strings."""
    return raw.replace(b"\xc0\x80", b"\x00").decode("utf-8", errors="replace")


def cp_utf8(pool: list[Any], index: int) -> str:
    if index <= 0 or index >= len(pool):
        return ""
    entry = pool[index]
    return entry[1] if entry and entry[0] == 1 else ""


def cp_class_name(pool: list[Any], index: int) -> str:
    if index <= 0 or index >= len(pool):
        return ""
    entry = pool[index]
    return cp_utf8(pool, entry[1]) if entry and entry[0] == 7 else ""


def opcode_counts(code: bytes) -> Counter[str]:
    """Count selected bytecode operations without interpreting operands as opcodes."""
    counts: Counter[str] = Counter()
    cursor = 0
    limit = len(code)
    try:
        while cursor < limit:
            start = cursor
            opcode = code[cursor]
            cursor += 1
            if opcode == 0xAA:  # tableswitch
                while cursor % 4:
                    cursor += 1
                if cursor + 12 > limit:
                    raise ClassFormatError("truncated tableswitch")
                low = struct.unpack(">i", code[cursor + 4:cursor + 8])[0]
                high = struct.unpack(">i", code[cursor + 8:cursor + 12])[0]
                entries = high - low + 1
                if entries < 0 or cursor + 12 + entries * 4 > limit:
                    raise ClassFormatError("invalid tableswitch")
                counts["tableswitch"] += 1
                cursor += 12 + entries * 4
            elif opcode == 0xAB:  # lookupswitch
                while cursor % 4:
                    cursor += 1
                if cursor + 8 > limit:
                    raise ClassFormatError("truncated lookupswitch")
                pairs = struct.unpack(">i", code[cursor + 4:cursor + 8])[0]
                if pairs < 0 or cursor + 8 + pairs * 8 > limit:
                    raise ClassFormatError("invalid lookupswitch")
                counts["lookupswitch"] += 1
                cursor += 8 + pairs * 8
            elif opcode == 0xC4:  # wide
                if cursor >= limit:
                    raise ClassFormatError("truncated wide")
                widened = code[cursor]
                cursor += 5 if widened == 0x84 else 3
            else:
                cursor += FIXED_OPCODE_LENGTHS.get(opcode, 1) - 1
            if cursor > limit:
                raise ClassFormatError("truncated bytecode instruction")
            if opcode == 0xA7:
                counts["goto"] += 1
            elif 0x99 <= opcode <= 0xA8 or opcode in (0xC6, 0xC7, 0xC8, 0xC9):
                counts["branch"] += 1
            elif opcode == 0xBF:
                counts["athrow"] += 1
            elif opcode == 0xBA:
                counts["invokedynamic"] += 1
            elif opcode in (0xAA, 0xAB):
                counts["switch"] += 1
            counts["instructions"] += 1
            if cursor <= start:
                raise ClassFormatError("non-advancing bytecode parser")
    except (IndexError, struct.error) as error:
        raise ClassFormatError(str(error)) from error
    return counts


def parse_code_attribute(data: bytes) -> tuple[Counter[str], Counter[str]]:
    reader = Reader(data)
    reader.u2()  # max_stack
    reader.u2()  # max_locals
    code = reader.take(reader.u4())
    opcodes = opcode_counts(code)
    exception_count = reader.u2()
    reader.take(exception_count * 8)
    nested_names: Counter[str] = Counter()
    for _ in range(reader.u2()):
        name_index = reader.u2()
        size = reader.u4()
        reader.take(size)
        nested_names[str(name_index)] += 1
    if reader.offset != len(data):
        raise ClassFormatError("unexpected bytes after Code attribute")
    return opcodes, nested_names


def parse_class(data: bytes) -> dict[str, Any]:
    reader = Reader(data)
    if reader.u4() != 0xCAFEBABE:
        raise ClassFormatError("missing CAFEBABE header")
    minor = reader.u2()
    major = reader.u2()
    count = reader.u2()
    pool: list[Any] = [None] * count
    index = 1
    while index < count:
        tag = reader.u1()
        if tag == 1:
            pool[index] = (tag, decode_modified_utf8(reader.take(reader.u2())))
        elif tag in (3, 4):
            pool[index] = (tag, reader.take(4))
        elif tag in (5, 6):
            pool[index] = (tag, reader.take(8))
            index += 1
        elif tag in (7, 8, 16, 19, 20):
            pool[index] = (tag, reader.u2())
        elif tag in (9, 10, 11, 12, 17, 18):
            pool[index] = (tag, reader.u2(), reader.u2())
        elif tag == 15:
            pool[index] = (tag, reader.u1(), reader.u2())
        else:
            raise ClassFormatError(f"unsupported constant-pool tag {tag}")
        index += 1

    access_flags = reader.u2()
    this_class = cp_class_name(pool, reader.u2())
    super_class = cp_class_name(pool, reader.u2())
    interfaces = [cp_class_name(pool, reader.u2()) for _ in range(reader.u2())]
    fields: list[str] = []
    methods: list[str] = []
    member_access: list[int] = []
    code_totals: Counter[str] = Counter()
    debug_attributes: Counter[str] = Counter()

    def read_members(target: list[str]) -> None:
        for _ in range(reader.u2()):
            member_access.append(reader.u2())
            target.append(cp_utf8(pool, reader.u2()))
            reader.u2()  # descriptor
            for _ in range(reader.u2()):
                attribute_name = cp_utf8(pool, reader.u2())
                attribute_data = reader.take(reader.u4())
                if attribute_name == "Code":
                    code_reader = Reader(attribute_data)
                    code_reader.u2()
                    code_reader.u2()
                    code = code_reader.take(code_reader.u4())
                    code_totals.update(opcode_counts(code))
                    exception_count = code_reader.u2()
                    code_reader.take(exception_count * 8)
                    for _ in range(code_reader.u2()):
                        nested_name = cp_utf8(pool, code_reader.u2())
                        code_reader.take(code_reader.u4())
                        if nested_name in {"LineNumberTable", "LocalVariableTable", "LocalVariableTypeTable"}:
                            debug_attributes[nested_name] += 1

    read_members(fields)
    read_members(methods)
    class_attributes: Counter[str] = Counter()
    for _ in range(reader.u2()):
        attribute_name = cp_utf8(pool, reader.u2())
        reader.take(reader.u4())
        class_attributes[attribute_name] += 1
    if reader.offset != len(data):
        raise ClassFormatError("unexpected trailing class bytes")

    strings = [cp_utf8(pool, entry[1]) for entry in pool if entry and entry[0] == 8]
    utf8_values = [entry[1] for entry in pool if entry and entry[0] == 1]
    return {
        "major": major,
        "minor": minor,
        "name": this_class,
        "super": super_class,
        "interfaces": interfaces,
        "access": access_flags,
        "fields": fields,
        "methods": methods,
        "member_access": member_access,
        "code": code_totals,
        "debug_attributes": debug_attributes,
        "class_attributes": class_attributes,
        "string_constants": strings,
        "constant_pool": Counter(str(entry[0]) for entry in pool if entry),
        "has_kotlin_metadata": "kotlin/Metadata" in utf8_values,
    }


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def parse_manifest(raw: bytes) -> dict[str, str]:
    text = raw.decode("utf-8", errors="replace").replace("\r\n", "\n").replace("\r", "\n")
    values: dict[str, str] = {}
    current_key: str | None = None
    for line in text.split("\n"):
        if line.startswith(" ") and current_key:
            values[current_key] += line[1:]
            continue
        if not line or ":" not in line:
            current_key = None
            continue
        key, value = line.split(":", 1)
        current_key = key.strip()
        values[current_key] = value.lstrip()
    return values


def entropy(value: str) -> float:
    if not value:
        return 0.0
    counts = Counter(value)
    length = len(value)
    return -sum((count / length) * math.log2(count / length) for count in counts.values())


def is_short_identifier(value: str) -> bool:
    return len(value) == 1 and value not in {"_", "$"}


def is_encoded_like(value: str) -> bool:
    if len(value) < 16:
        return False
    compact = value.rstrip("=")
    base64ish = bool(re.fullmatch(r"[A-Za-z0-9+/=_-]+", value)) and len(compact) >= 16
    return base64ish or entropy(value) >= 4.3


def add_signal(signals: list[dict[str, Any]], signal_id: str, count: int, detail: str, threshold: int = 1) -> None:
    if count >= threshold:
        signals.append({"id": signal_id, "count": count, "detail": detail})


def normalized_class_name(entry_name: str) -> str:
    name = entry_name[:-6] if entry_name.endswith(".class") else entry_name
    match = re.match(r"META-INF/versions/\d+/(.+)", name)
    return match.group(1) if match else name


def summarize_classes(
    archive: zipfile.ZipFile,
    entries: list[zipfile.ZipInfo],
    max_classes: int,
    max_class_bytes: int,
    max_samples: int,
) -> tuple[dict[str, Any], dict[str, Any]]:
    class_entries = [entry for entry in entries if entry.filename.endswith(".class") and not entry.is_dir()]
    version_counts: Counter[str] = Counter()
    package_counts: Counter[str] = Counter()
    parse_errors: list[dict[str, str]] = []
    samples: list[str] = []
    metrics: Counter[str] = Counter()
    all_code: Counter[str] = Counter()
    all_class_attributes: Counter[str] = Counter()
    all_debug_attributes: Counter[str] = Counter()
    all_cp: Counter[str] = Counter()
    analysis_limit = min(len(class_entries), max_classes)

    for entry in class_entries[:analysis_limit]:
        if entry.file_size > max_class_bytes:
            metrics["oversized_skipped"] += 1
            continue
        try:
            parsed = parse_class(archive.read(entry))
        except (ClassFormatError, OSError, RuntimeError, zipfile.BadZipFile) as error:
            metrics["parse_errors"] += 1
            if len(parse_errors) < max_samples:
                parse_errors.append({"entry": entry.filename, "error": str(error)})
            continue
        metrics["parsed"] += 1
        version_counts[str(parsed["major"])] += 1
        name = parsed["name"] or normalized_class_name(entry.filename)
        package = name.rsplit("/", 1)[0] if "/" in name else "<default>"
        package_counts[package] += 1
        if len(samples) < max_samples:
            samples.append(name.replace("/", "."))
        simple_name = name.rsplit("/", 1)[-1]
        if is_short_identifier(simple_name):
            metrics["short_class_names"] += 1
        if any(ord(character) > 127 for character in name):
            metrics["non_ascii_class_names"] += 1
        for segment in package.split("/"):
            if is_short_identifier(segment):
                metrics["short_package_segments"] += 1
        for member_name in parsed["fields"] + parsed["methods"]:
            if member_name not in {"<init>", "<clinit>"}:
                metrics["member_names"] += 1
                if is_short_identifier(member_name):
                    metrics["short_member_names"] += 1
                if any(ord(character) > 127 for character in member_name):
                    metrics["non_ascii_member_names"] += 1
        metrics["synthetic_members"] += sum(1 for flags in parsed["member_access"] if flags & 0x1000)
        if parsed["access"] & 0x1000:
            metrics["synthetic_classes"] += 1
        if parsed["has_kotlin_metadata"]:
            metrics["kotlin_metadata_classes"] += 1
        strings = parsed["string_constants"]
        metrics["string_constants"] += len(strings)
        metrics["encoded_like_strings"] += sum(1 for value in strings if is_encoded_like(value))
        all_code.update(parsed["code"])
        all_class_attributes.update(parsed["class_attributes"])
        all_debug_attributes.update(parsed["debug_attributes"])
        all_cp.update(parsed["constant_pool"])

    for entry in class_entries[analysis_limit:]:
        metrics["analysis_limit_skipped"] += 1
    metrics["total_classes"] = len(class_entries)
    metrics["analyzed_classes"] = analysis_limit
    metrics["sourcefile_classes"] = all_class_attributes.get("SourceFile", 0)
    metrics["bootstrap_methods_classes"] = all_class_attributes.get("BootstrapMethods", 0)
    metrics["line_number_tables"] = all_debug_attributes.get("LineNumberTable", 0)
    metrics["local_variable_tables"] = all_debug_attributes.get("LocalVariableTable", 0)
    metrics["constant_dynamic_entries"] = all_cp.get("17", 0)
    metrics["invoke_dynamic_entries"] = all_cp.get("18", 0)

    versions = {
        major: {"count": count, "java": JAVA_RELEASES.get(int(major), "unknown")}
        for major, count in sorted(version_counts.items(), key=lambda item: int(item[0]))
    }
    class_report = {
        "count": len(class_entries),
        "analyzed": analysis_limit,
        "skipped_by_limit": max(0, len(class_entries) - analysis_limit),
        "versions": versions,
        "package_counts": dict(package_counts.most_common(max_samples)),
        "samples": samples,
        "parse_errors": parse_errors,
        "metrics": dict(metrics),
        "bytecode": dict(all_code),
        "attributes": {
            "class": dict(all_class_attributes),
            "debug": dict(all_debug_attributes),
            "constant_pool_tags": dict(all_cp),
        },
    }
    return class_report, {"metrics": metrics, "code": all_code, "attributes": all_class_attributes}


def ecosystem_metadata(entry_names: set[str]) -> dict[str, Any]:
    services = sorted(name for name in entry_names if name.startswith("META-INF/services/") and not name.endswith("/"))
    mixins = sorted(name for name in entry_names if name.endswith(".mixins.json"))
    refmaps = sorted(name for name in entry_names if name.endswith(".refmap.json"))
    access_wideners = sorted(name for name in entry_names if name.endswith(".accesswidener"))
    return {
        "fabric_mod_json": "fabric.mod.json" in entry_names,
        "forge_mods_toml": "META-INF/mods.toml" in entry_names,
        "mixin_configs": mixins,
        "mixin_refmaps": refmaps,
        "access_wideners": access_wideners,
        "service_definitions": services,
        "module_info": any(name.endswith("module-info.class") for name in entry_names),
        "multi_release_entries": sorted(name for name in entry_names if name.startswith("META-INF/versions/"))[:50],
    }


def obfuscation_report(class_report: dict[str, Any], internal: dict[str, Any]) -> dict[str, Any]:
    metrics: Counter[str] = internal["metrics"]
    code: Counter[str] = internal["code"]
    attributes: Counter[str] = internal["attributes"]
    analyzed = max(metrics["parsed"], 1)
    member_total = max(metrics["member_names"], 1)
    signals: list[dict[str, Any]] = []
    add_signal(signals, "short-class-identifiers", metrics["short_class_names"], "One-character class names are common in name obfuscation.")
    add_signal(signals, "short-member-identifiers", metrics["short_member_names"], "One-character field or method names are common in name obfuscation.")
    add_signal(signals, "short-package-segments", metrics["short_package_segments"], "Short package segments can accompany bulk renaming.")
    add_signal(signals, "non-ascii-identifiers", metrics["non_ascii_class_names"] + metrics["non_ascii_member_names"], "Non-ASCII identifiers require Unicode-safe mapping and source export.")
    add_signal(signals, "encoded-string-candidates", metrics["encoded_like_strings"], "High-entropy or base64-like string constants may warrant decoder tracing.")
    add_signal(signals, "invokedynamic", code["invokedynamic"], "Inspect bootstrap methods and call-site descriptors before rewriting.")
    add_signal(signals, "constant-dynamic", metrics["constant_dynamic_entries"], "ConstantDynamic requires a decompiler/JDK that supports the class version.")
    add_signal(signals, "branch-dense-bytecode", code["branch"] + code["switch"], "Branch density is a cue for bytecode inspection, not proof of flattening.", threshold=max(20, analyzed * 8))
    if metrics["sourcefile_classes"] == 0 and analyzed:
        add_signal(signals, "debug-metadata-absent", analyzed, "No SourceFile attributes were observed in parsed classes.")
    if metrics["parse_errors"]:
        add_signal(signals, "class-parse-errors", metrics["parse_errors"], "Malformed or unsupported classes need matching-JDK javap inspection.")

    weights = {
        "short-class-identifiers": 2,
        "short-member-identifiers": 2,
        "short-package-segments": 1,
        "non-ascii-identifiers": 2,
        "encoded-string-candidates": 2,
        "invokedynamic": 1,
        "constant-dynamic": 2,
        "branch-dense-bytecode": 2,
        "debug-metadata-absent": 1,
        "class-parse-errors": 2,
    }
    score = sum(weights.get(signal["id"], 0) for signal in signals)
    level = "low" if score < 3 else "moderate" if score < 7 else "high"
    return {
        "heuristic_level": level,
        "heuristic_score": score,
        "note": "Heuristics guide inspection only; they do not identify an obfuscator or recover original names.",
        "signals": signals,
        "ratios": {
            "short_class_names": round(metrics["short_class_names"] / analyzed, 4),
            "short_member_names": round(metrics["short_member_names"] / member_total, 4),
            "encoded_like_strings": round(metrics["encoded_like_strings"] / max(metrics["string_constants"], 1), 4),
            "branch_per_instruction": round((code["branch"] + code["switch"]) / max(code["instructions"], 1), 4),
        },
    }


def command_probe() -> dict[str, Any]:
    result: dict[str, Any] = {}
    for name, version_args in COMMANDS.items():
        path = shutil.which(name)
        entry: dict[str, Any] = {"available": bool(path), "path": str(Path(path).resolve()) if path else None}
        if path:
            try:
                completed = subprocess.run(
                    [path, *version_args], stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                    text=True, timeout=4, check=False,
                )
                output = (completed.stdout or completed.stderr).strip().splitlines()
                entry["version"] = output[0][:300] if output else None
                entry["exit_code"] = completed.returncode
            except (OSError, subprocess.SubprocessError) as error:
                entry["version_error"] = str(error)
        result[name] = entry
    return result


def candidate_tool_roots(jar_path: Path, explicit: Iterable[Path]) -> list[Path]:
    roots: list[Path] = []
    candidates = [Path.cwd(), jar_path.parent, Path.cwd() / "tools", jar_path.parent / "tools"]
    candidates.extend(explicit)
    java_home = os.environ.get("JAVA_HOME")
    if java_home:
        candidates.append(Path(java_home))
    seen: set[Path] = set()
    for candidate in candidates:
        try:
            resolved = candidate.expanduser().resolve()
        except OSError:
            continue
        if resolved.is_dir() and resolved not in seen:
            roots.append(resolved)
            seen.add(resolved)
    return roots


def find_tool_jars(roots: list[Path], max_depth: int = 3) -> dict[str, list[str]]:
    found: dict[str, list[str]] = {name: [] for name in TOOL_PATTERNS}
    seen_paths: set[Path] = set()
    for root in roots:
        root_parts = len(root.parts)
        for current, dirs, files in os.walk(root):
            current_path = Path(current)
            if len(current_path.parts) - root_parts >= max_depth:
                dirs[:] = []
            else:
                dirs[:] = [name for name in dirs if name.lower() not in SKIP_TOOL_DIRS]
            for file_name in files:
                if not file_name.lower().endswith(".jar"):
                    continue
                path = current_path / file_name
                if path in seen_paths:
                    continue
                for tool_name, pattern in TOOL_PATTERNS.items():
                    if pattern.match(file_name):
                        found[tool_name].append(str(path.resolve()))
                        seen_paths.add(path)
                        break
    return {name: paths[:MAX_TOOL_RESULTS] for name, paths in found.items() if paths}


def recommendations(
    class_report: dict[str, Any], ecosystem: dict[str, Any], obfuscation: dict[str, Any], tools: dict[str, Any]
) -> list[str]:
    items = ["Preserve the original JAR and run this probe again after each stage."]
    versions = class_report["versions"]
    if versions:
        newest = max(int(major) for major in versions)
        items.append(f"Use a JDK compatible with class-file major {newest} (Java {JAVA_RELEASES.get(newest, 'unknown')}) before transformation.")
    if ecosystem["multi_release_entries"]:
        items.append("Treat META-INF/versions entries as a multi-release class family; do not flatten versioned classes.")
    if ecosystem["fabric_mod_json"] or ecosystem["mixin_configs"] or ecosystem["service_definitions"]:
        items.append("Inventory Fabric/Mixin/service metadata before any class rename and validate all rewritten references.")
    signal_ids = {signal["id"] for signal in obfuscation["signals"]}
    if {"short-class-identifiers", "short-member-identifiers"} & signal_ids:
        items.append("Export a neutral name map first; perform semantic renaming only after bytecode stabilization.")
    if "encoded-string-candidates" in signal_ids:
        items.append("Locate decoder call sites and validate decoded values with focused fixtures before literal replacement.")
    if {"invokedynamic", "constant-dynamic"} & signal_ids:
        items.append("Inspect bootstrap methods and call-site descriptors with javap before changing invokedynamic code.")
    if "xingkong-deobfuscator" in tools["jar_tools"]:
        items.append("A XingKong deobfuscator is available; select it only after confirming ShieldRuntime calls or its bootstrap pattern.")
    available = ", ".join(sorted(tools["jar_tools"]))
    if available:
        items.append(f"Local tool JARs detected: {available}. Select a tool only after matching it to observed evidence.")
    else:
        items.append("No named deobfuscator JAR was found under the supplied tool roots; use javap plus independent decompilers when available.")
    return items


def probe(path: Path, args: argparse.Namespace) -> dict[str, Any]:
    if not path.is_file():
        raise FileNotFoundError(f"input JAR does not exist: {path}")
    if not zipfile.is_zipfile(path):
        raise zipfile.BadZipFile("input is not a ZIP/JAR archive")
    with zipfile.ZipFile(path) as archive:
        entries = archive.infolist()
        names = [entry.filename for entry in entries]
        name_set = set(names)
        duplicates = [name for name, count in Counter(names).items() if count > 1]
        manifest: dict[str, str] = {}
        if "META-INF/MANIFEST.MF" in name_set:
            manifest = parse_manifest(archive.read("META-INF/MANIFEST.MF"))
        class_report, internal = summarize_classes(
            archive, entries, args.max_classes, args.max_class_bytes, args.max_samples
        )
        ecosystem = ecosystem_metadata(name_set)
        embedded_jars = sorted(
            entry.filename for entry in entries
            if re.search(r"(?:^|/)(?:lib|libs|libraries|BOOT-INF/lib|META-INF/lib)/[^/]+\.jar$", entry.filename, re.IGNORECASE)
        )
        native_libraries = sorted(
            entry.filename for entry in entries if entry.filename.lower().endswith((".dll", ".so", ".dylib"))
        )

    tool_roots = candidate_tool_roots(path, [Path(value) for value in args.tool_root])
    command_tools = command_probe()
    jar_tools = find_tool_jars(tool_roots) if not args.no_tool_search else {}
    tool_report = {
        "commands": command_tools,
        "jar_tools": jar_tools,
        "search_roots": [str(root) for root in tool_roots],
        "search_depth": 3,
    }
    obfuscation = obfuscation_report(class_report, internal)
    return {
        "schema": SCHEMA,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "input": {
            "path": str(path.resolve()),
            "size_bytes": path.stat().st_size,
            "sha256": sha256_file(path),
        },
        "archive": {
            "entries": len(entries),
            "classes": class_report["count"],
            "resources": len([entry for entry in entries if not entry.filename.endswith(".class") and not entry.is_dir()]),
            "uncompressed_bytes": sum(entry.file_size for entry in entries),
            "duplicate_entries": duplicates[:args.max_samples],
        },
        "manifest": manifest,
        "libraries": {
            "manifest_class_path": manifest.get("Class-Path", "").split(),
            "embedded_jars": embedded_jars[:args.max_samples],
            "native_libraries": native_libraries[:args.max_samples],
        },
        "ecosystem": ecosystem,
        "classes": class_report,
        "obfuscation": obfuscation,
        "tools": tool_report,
        "recommendations": recommendations(class_report, ecosystem, obfuscation, tool_report),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("jar", type=Path, help="input .jar or ZIP archive")
    parser.add_argument("--tool-root", action="append", default=[], metavar="DIR", help="local directory to scan for known Java tools")
    parser.add_argument("--output", type=Path, help="write the JSON report to this path as well as stdout")
    parser.add_argument("--max-classes", type=int, default=MAX_DEFAULT_CLASSES, help="maximum class entries to parse")
    parser.add_argument("--max-class-bytes", type=int, default=MAX_DEFAULT_CLASS_BYTES, help="skip individual classes larger than this size")
    parser.add_argument("--max-samples", type=int, default=50, help="maximum sampled entries per report field")
    parser.add_argument("--no-tool-search", action="store_true", help="skip local JAR tool discovery")
    args = parser.parse_args()
    if args.max_classes < 1 or args.max_class_bytes < 1 or args.max_samples < 1:
        parser.error("maximum values must be positive")
    return args


def main() -> int:
    args = parse_args()
    try:
        report = probe(args.jar, args)
        exit_code = 0
    except (FileNotFoundError, OSError, zipfile.BadZipFile, ClassFormatError) as error:
        report = {
            "schema": SCHEMA,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "input": {"path": str(args.jar)},
            "error": {"type": type(error).__name__, "message": str(error)},
        }
        exit_code = 2
    payload = json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload + "\n", encoding="utf-8")
    print(payload)
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
