#!/usr/bin/env python3
"""Read-only inventory for Android archives and ELF shared libraries."""

from __future__ import annotations

import argparse
import hashlib
import json
import struct
import sys
import zipfile
from pathlib import Path, PurePosixPath
from typing import BinaryIO, Iterable


ARCHIVE_SUFFIXES = {".apk", ".aab", ".aar", ".zip"}
ELF_TYPES = {1: "ET_REL", 2: "ET_EXEC", 3: "ET_DYN", 4: "ET_CORE"}
ELF_MACHINES = {
    3: "x86",
    8: "MIPS",
    40: "ARM",
    62: "x86-64",
    183: "AArch64",
    243: "RISC-V",
}


def parse_int(value: str) -> int:
    try:
        return int(value, 0)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"invalid integer: {value}") from exc


def hash_stream(stream: BinaryIO) -> tuple[str, bytes]:
    digest = hashlib.sha256()
    head = bytearray()
    while True:
        chunk = stream.read(1024 * 1024)
        if not chunk:
            break
        digest.update(chunk)
        if len(head) < 64:
            head.extend(chunk[: 64 - len(head)])
    return digest.hexdigest(), bytes(head)


def parse_elf_header(data: bytes) -> dict[str, object]:
    if len(data) < 52 or data[:4] != b"\x7fELF":
        raise ValueError("not an ELF file")

    elf_class = data[4]
    data_encoding = data[5]
    if elf_class not in (1, 2):
        raise ValueError(f"unsupported ELF class: {elf_class}")
    if data_encoding not in (1, 2):
        raise ValueError(f"unsupported ELF byte order: {data_encoding}")

    endian = "<" if data_encoding == 1 else ">"
    if elf_class == 1:
        fmt = endian + "HHIIIIIHHHHHH"
        names = (
            "type_id",
            "machine_id",
            "version",
            "entry",
            "phoff",
            "shoff",
            "flags",
            "ehsize",
            "phentsize",
            "phnum",
            "shentsize",
            "shnum",
            "shstrndx",
        )
    else:
        fmt = endian + "HHIQQQIHHHHHH"
        names = (
            "type_id",
            "machine_id",
            "version",
            "entry",
            "phoff",
            "shoff",
            "flags",
            "ehsize",
            "phentsize",
            "phnum",
            "shentsize",
            "shnum",
            "shstrndx",
        )

    needed = 16 + struct.calcsize(fmt)
    if len(data) < needed:
        raise ValueError("truncated ELF header")

    values = dict(zip(names, struct.unpack_from(fmt, data, 16), strict=True))
    values.update(
        {
            "bits": 32 if elf_class == 1 else 64,
            "endian": "little" if data_encoding == 1 else "big",
            "type": ELF_TYPES.get(values["type_id"], f"type-{values['type_id']}"),
            "machine": ELF_MACHINES.get(
                values["machine_id"], f"machine-{values['machine_id']}"
            ),
        }
    )
    return values


def read_elf_header(path: Path) -> tuple[str, dict[str, object]]:
    with path.open("rb") as stream:
        digest, head = hash_stream(stream)
    return digest, parse_elf_header(head)


def read_load_segments(path: Path, header: dict[str, object]) -> list[dict[str, int | str]]:
    endian = "<" if header["endian"] == "little" else ">"
    if header["bits"] == 32:
        fmt = endian + "IIIIIIII"
    else:
        fmt = endian + "IIQQQQQQ"

    expected_size = struct.calcsize(fmt)
    entry_size = int(header["phentsize"])
    if entry_size < expected_size:
        raise ValueError(
            f"program-header entry is too small: {entry_size} < {expected_size}"
        )

    segments: list[dict[str, int | str]] = []
    with path.open("rb") as stream:
        for index in range(int(header["phnum"])):
            stream.seek(int(header["phoff"]) + index * entry_size)
            raw = stream.read(entry_size)
            if len(raw) != entry_size:
                raise ValueError("truncated program-header table")
            values = struct.unpack_from(fmt, raw)
            if header["bits"] == 32:
                p_type, p_offset, p_vaddr, _p_paddr, p_filesz, p_memsz, p_flags, p_align = values
            else:
                p_type, p_flags, p_offset, p_vaddr, _p_paddr, p_filesz, p_memsz, p_align = values
            if p_type != 1:
                continue
            flags = "".join(
                letter if p_flags & bit else "-"
                for letter, bit in (("R", 4), ("W", 2), ("X", 1))
            )
            segments.append(
                {
                    "index": index,
                    "offset": p_offset,
                    "vaddr": p_vaddr,
                    "filesz": p_filesz,
                    "memsz": p_memsz,
                    "align": p_align,
                    "flags": flags,
                }
            )
    return segments


def map_elf_va(segments: Iterable[dict[str, int | str]], va: int) -> dict[str, object]:
    segment_list = list(segments)
    for segment in segment_list:
        start = int(segment["vaddr"])
        file_end = start + int(segment["filesz"])
        if start <= va < file_end:
            return {
                "elf_va": va,
                "file_offset": int(segment["offset"]) + (va - start),
                "segment_index": segment["index"],
                "segment_flags": segment["flags"],
                "file_backed": True,
            }
    for segment in segment_list:
        start = int(segment["vaddr"])
        file_end = start + int(segment["filesz"])
        memory_end = start + int(segment["memsz"])
        if file_end <= va < memory_end:
            return {
                "elf_va": va,
                "segment_index": segment["index"],
                "segment_flags": segment["flags"],
                "file_backed": False,
                "reason": "address is in zero-filled segment memory beyond p_filesz",
            }
    return {"elf_va": va, "file_backed": False, "reason": "no PT_LOAD segment contains address"}


def archive_abi(member: str) -> str:
    parts = PurePosixPath(member).parts
    for marker in ("lib", "jni", "libs"):
        for index, part in enumerate(parts[:-1]):
            if part == marker and index + 1 < len(parts):
                abi = parts[index + 1]
                return abi.removeprefix("android.")
    return "unknown"


def inspect_archive(path: Path) -> tuple[list[dict[str, object]], list[str]]:
    records: list[dict[str, object]] = []
    errors: list[str] = []
    try:
        with zipfile.ZipFile(path) as archive:
            members = [
                info
                for info in archive.infolist()
                if not info.is_dir() and info.filename.lower().endswith(".so")
            ]
            for info in members:
                try:
                    with archive.open(info) as stream:
                        digest, head = hash_stream(stream)
                    elf = parse_elf_header(head)
                    records.append(
                        {
                            "kind": "archive-member",
                            "container": str(path.resolve()),
                            "member": info.filename,
                            "abi": archive_abi(info.filename),
                            "size": info.file_size,
                            "compressed_size": info.compress_size,
                            "sha256": digest,
                            "elf": elf,
                        }
                    )
                except (OSError, ValueError, RuntimeError) as exc:
                    errors.append(f"{path}!{info.filename}: {exc}")
    except (OSError, zipfile.BadZipFile) as exc:
        errors.append(f"{path}: {exc}")
    return records, errors


def inspect_elf(
    path: Path,
    include_segments: bool,
    target_va: int | None,
) -> tuple[dict[str, object] | None, list[str]]:
    errors: list[str] = []
    try:
        digest, header = read_elf_header(path)
        record: dict[str, object] = {
            "kind": "elf-file",
            "path": str(path.resolve()),
            "size": path.stat().st_size,
            "sha256": digest,
            "elf": header,
        }
        if include_segments or target_va is not None:
            segments = read_load_segments(path, header)
            record["segments"] = segments
            if target_va is not None:
                record["mapping"] = map_elf_va(segments, target_va)
        return record, errors
    except (OSError, ValueError, struct.error) as exc:
        errors.append(f"{path}: {exc}")
        return None, errors


def expand_paths(paths: list[Path]) -> list[Path]:
    expanded: list[Path] = []
    for path in paths:
        if path.is_dir():
            expanded.extend(
                candidate
                for candidate in sorted(path.rglob("*"))
                if candidate.is_file()
                and (candidate.suffix.lower() == ".so" or candidate.suffix.lower() in ARCHIVE_SUFFIXES)
            )
        else:
            expanded.append(path)
    return expanded


def print_text(records: list[dict[str, object]], errors: list[str]) -> None:
    if not records:
        print("No native ELF records found.")
    for record in records:
        elf = record["elf"]
        location = record.get("member") or record.get("path")
        if record.get("container"):
            location = f"{record['container']}!{location}"
        print(
            f"{record.get('abi', '-'):12} {elf['machine']:10} {elf['bits']:>2}-bit "
            f"{elf['endian']:6} {elf['type']:7} {record['size']:>10} "
            f"{record['sha256'][:16]}  {location}"
        )
        for segment in record.get("segments", []):
            print(
                "  PT_LOAD[{index}] {flags} off=0x{offset:x} va=0x{vaddr:x} "
                "filesz=0x{filesz:x} memsz=0x{memsz:x} align=0x{align:x}".format(**segment)
            )
        if "mapping" in record:
            mapping = record["mapping"]
            if mapping.get("file_backed"):
                print(
                    f"  map va=0x{mapping['elf_va']:x} -> file=0x{mapping['file_offset']:x} "
                    f"segment={mapping['segment_index']} {mapping['segment_flags']}"
                )
            else:
                print(f"  map va=0x{mapping['elf_va']:x}: {mapping['reason']}")
    for error in errors:
        print(f"warning: {error}", file=sys.stderr)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Inventory Android native libraries and map proven ELF virtual addresses without modifying artifacts."
    )
    parser.add_argument("paths", nargs="+", type=Path, help="APK, AAB, AAR, ZIP, ELF .so, or directory")
    parser.add_argument("--json", action="store_true", help="emit structured JSON")
    parser.add_argument("--segments", action="store_true", help="show PT_LOAD segments for direct ELF files")
    address = parser.add_mutually_exclusive_group()
    address.add_argument("--elf-va", type=parse_int, help="map an ELF virtual address to a file offset")
    address.add_argument("--runtime-address", type=parse_int, help="runtime address to map; requires --load-bias")
    parser.add_argument("--load-bias", type=parse_int, help="proven ELF load bias for --runtime-address")
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    if args.runtime_address is not None and args.load_bias is None:
        parser.error("--runtime-address requires --load-bias")
    if args.load_bias is not None and args.runtime_address is None:
        parser.error("--load-bias is valid only with --runtime-address")

    candidates = expand_paths(args.paths)
    target_va = args.elf_va
    if args.runtime_address is not None:
        target_va = args.runtime_address - args.load_bias
        if target_va < 0:
            parser.error("runtime address is below load bias")

    if target_va is not None:
        if len(candidates) != 1 or candidates[0].suffix.lower() in ARCHIVE_SUFFIXES:
            parser.error("address mapping requires exactly one direct ELF file")

    records: list[dict[str, object]] = []
    errors: list[str] = []
    for path in candidates:
        if not path.exists():
            errors.append(f"{path}: path does not exist")
            continue
        if path.suffix.lower() in ARCHIVE_SUFFIXES:
            archive_records, archive_errors = inspect_archive(path)
            records.extend(archive_records)
            errors.extend(archive_errors)
        else:
            record, file_errors = inspect_elf(path, args.segments, target_va)
            if record is not None:
                records.append(record)
            errors.extend(file_errors)

    if args.json:
        print(json.dumps({"records": records, "errors": errors}, indent=2, sort_keys=True))
    else:
        print_text(records, errors)
    return 0 if records else 1


if __name__ == "__main__":
    raise SystemExit(main())
