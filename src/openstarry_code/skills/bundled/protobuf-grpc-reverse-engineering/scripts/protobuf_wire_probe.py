#!/usr/bin/env python3
"""Inspect raw Protobuf wire data or gRPC length-prefixed messages."""

from __future__ import annotations

import argparse
import json
import struct
from pathlib import Path


def read_varint(data: bytes, offset: int) -> tuple[int, int]:
    value = 0
    shift = 0
    start = offset
    while offset < len(data) and shift < 70:
        byte = data[offset]
        offset += 1
        value |= (byte & 0x7F) << shift
        if byte < 0x80:
            return value, offset
        shift += 7
    raise ValueError(f"invalid varint at offset {start}")


def parse_message(data: bytes, depth: int = 0) -> list[dict]:
    fields = []
    offset = 0
    while offset < len(data):
        start = offset
        key, offset = read_varint(data, offset)
        number = key >> 3
        wire = key & 7
        if number == 0 or wire not in (0, 1, 2, 5):
            raise ValueError(f"invalid key at offset {start}: field={number}, wire={wire}")
        item = {"offset": start, "field": number, "wire": wire}
        if wire == 0:
            value, offset = read_varint(data, offset)
            item["value"] = value
        elif wire == 1:
            if offset + 8 > len(data):
                raise ValueError(f"truncated fixed64 at offset {offset}")
            raw = data[offset : offset + 8]
            offset += 8
            item.update(hex=raw.hex(), uint64=int.from_bytes(raw, "little"), double=struct.unpack("<d", raw)[0])
        elif wire == 5:
            if offset + 4 > len(data):
                raise ValueError(f"truncated fixed32 at offset {offset}")
            raw = data[offset : offset + 4]
            offset += 4
            item.update(hex=raw.hex(), uint32=int.from_bytes(raw, "little"), float=struct.unpack("<f", raw)[0])
        else:
            length, offset = read_varint(data, offset)
            end = offset + length
            if end > len(data):
                raise ValueError(f"truncated length-delimited field at offset {offset}")
            raw = data[offset:end]
            offset = end
            item.update(length=length, hex=raw.hex())
            try:
                item["utf8"] = raw.decode("utf-8")
            except UnicodeDecodeError:
                pass
            if raw and depth < 3:
                try:
                    item["nested"] = parse_message(raw, depth + 1)
                except ValueError:
                    pass
        fields.append(item)
    return fields


def split_grpc(data: bytes) -> list[dict]:
    frames = []
    offset = 0
    while offset < len(data):
        if offset + 5 > len(data):
            raise ValueError(f"truncated gRPC header at offset {offset}")
        compressed = data[offset]
        length = int.from_bytes(data[offset + 1 : offset + 5], "big")
        start = offset + 5
        end = start + length
        if end > len(data):
            raise ValueError(f"truncated gRPC message at offset {offset}")
        payload = data[start:end]
        frame = {"offset": offset, "compressed": compressed, "length": length, "payload_hex": payload.hex()}
        if compressed == 0:
            frame["fields"] = parse_message(payload)
        frames.append(frame)
        offset = end
    return frames


def main() -> int:
    parser = argparse.ArgumentParser()
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--hex", dest="hex_data")
    source.add_argument("--file", type=Path)
    parser.add_argument("--grpc", action="store_true", help="split five-byte gRPC frames first")
    args = parser.parse_args()
    data = bytes.fromhex(args.hex_data) if args.hex_data else args.file.read_bytes()
    result = split_grpc(data) if args.grpc else parse_message(data)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
