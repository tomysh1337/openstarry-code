#!/usr/bin/env python3
"""Verify the deterministic parts of a signed static update release."""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime
from pathlib import Path

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

MAX_MANIFEST_BYTES = 1024 * 1024
SEMVER = re.compile(
    r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)"
    r"(?:-([0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?"
    r"(?:\+([0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?$"
)
SHA256 = re.compile(r"^[0-9a-f]{64}$")
TOP_LEVEL = {"schema_version", "product", "channel", "version", "published_at", "release_notes_url", "package"}
PACKAGE_LEVEL = {"url", "size", "sha256", "signature"}


def b64url_decode(value: str) -> bytes:
    if not isinstance(value, str) or not value or "=" in value:
        raise ValueError("signature must be non-empty unpadded base64url")
    raw = base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))
    if base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii") != value:
        raise ValueError("signature is not canonical base64url")
    return raw


def read_limited(response) -> bytes:
    declared = response.headers.get("Content-Length")
    if declared and int(declared) > MAX_MANIFEST_BYTES:
        raise ValueError("manifest exceeds size limit")
    data = response.read(MAX_MANIFEST_BYTES + 1)
    if len(data) > MAX_MANIFEST_BYTES:
        raise ValueError("manifest exceeds size limit")
    return data


class SameHostHttpsRedirects(urllib.request.HTTPRedirectHandler):
    def __init__(self, allowed_host: str):
        super().__init__()
        self.allowed_host = allowed_host.lower()

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        parsed = urllib.parse.urlparse(newurl)
        if parsed.scheme != "https" or (parsed.hostname or "").lower() != self.allowed_host:
            raise ValueError("redirect leaves the allowlisted HTTPS host")
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def load_source(source: str) -> tuple[bytes, bytes, str | None]:
    parsed = urllib.parse.urlparse(source)
    if parsed.scheme in {"http", "https"}:
        if parsed.scheme != "https" or not parsed.hostname:
            raise ValueError("remote manifest must use HTTPS")
        opener = urllib.request.build_opener(SameHostHttpsRedirects(parsed.hostname))
        with opener.open(source, timeout=20) as response:
            manifest = read_limited(response)
        with opener.open(source + ".sig", timeout=20) as response:
            signature = read_limited(response).strip()
        return manifest, signature, parsed.hostname.lower()
    path = Path(source)
    return path.read_bytes(), Path(str(path) + ".sig").read_bytes().strip(), None


def load_public_key(path: Path) -> Ed25519PublicKey:
    key = serialization.load_pem_public_key(path.read_bytes())
    if not isinstance(key, Ed25519PublicKey):
        raise ValueError("public key is not Ed25519")
    return key


def require_https_url(value: object, field: str, allowed_host: str | None) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{field} must be a string")
    parsed = urllib.parse.urlparse(value)
    if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password:
        raise ValueError(f"{field} must be an HTTPS URL without credentials")
    if allowed_host and parsed.hostname.lower() != allowed_host:
        raise ValueError(f"{field} host is not allowlisted")
    return value


def validate_document(raw: bytes, key: Ed25519PublicKey, detached_signature: bytes, allowed_host: str | None) -> dict:
    key.verify(b64url_decode(detached_signature.decode("ascii")), raw)
    document = json.loads(raw.decode("utf-8"))
    if not isinstance(document, dict) or set(document) != TOP_LEVEL:
        raise ValueError("manifest fields do not match the exact schema")
    package = document["package"]
    if not isinstance(package, dict) or set(package) != PACKAGE_LEVEL:
        raise ValueError("package fields do not match the exact schema")
    if document["schema_version"] != 1:
        raise ValueError("unsupported schema_version")
    if not isinstance(document["product"], str) or not document["product"].strip():
        raise ValueError("product must be a non-empty string")
    if document["channel"] != "stable":
        raise ValueError("only the stable channel is supported")
    if not isinstance(document["version"], str) or not SEMVER.fullmatch(document["version"]):
        raise ValueError("version is not semantic versioning")
    semver_key(document["version"])
    if not isinstance(document["published_at"], str) or not document["published_at"].endswith("Z"):
        raise ValueError("published_at must be UTC ISO-8601")
    datetime.fromisoformat(document["published_at"].replace("Z", "+00:00"))
    require_https_url(document["release_notes_url"], "release_notes_url", allowed_host)
    require_https_url(package["url"], "package.url", allowed_host)
    if not isinstance(package["size"], int) or isinstance(package["size"], bool) or package["size"] <= 0:
        raise ValueError("package.size must be a positive integer")
    if not isinstance(package["sha256"], str) or not SHA256.fullmatch(package["sha256"]):
        raise ValueError("package.sha256 must be lowercase hexadecimal")
    if len(b64url_decode(package["signature"])) != 64:
        raise ValueError("package.signature must be an Ed25519 signature")
    return document


def validate_package(path: Path, package: dict, key: Ed25519PublicKey) -> None:
    digest = hashlib.sha256()
    size = 0
    with path.open("rb") as stream:
        while chunk := stream.read(1024 * 1024):
            size += len(chunk)
            digest.update(chunk)
    if size != package["size"]:
        raise ValueError("package size mismatch")
    if digest.hexdigest() != package["sha256"]:
        raise ValueError("package SHA-256 mismatch")
    key.verify(b64url_decode(package["signature"]), digest.digest())


def semver_key(value: str) -> tuple[int, int, int, tuple]:
    match = SEMVER.fullmatch(value)
    if not match:
        raise ValueError(f"invalid semantic version: {value}")
    core = tuple(int(part) for part in match.group(1, 2, 3))
    prerelease = match.group(4)
    if prerelease is None:
        return (*core, ((1, ""),))
    identifiers = []
    for item in prerelease.split("."):
        if item.isdigit() and len(item) > 1 and item.startswith("0"):
            raise ValueError(f"numeric prerelease identifier has a leading zero: {value}")
        identifiers.append((0, int(item)) if item.isdigit() else (1, item))
    return (*core, ((0, ""), *identifiers))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--public-key", required=True, type=Path)
    parser.add_argument("--package", type=Path)
    parser.add_argument("--expected-product", required=True)
    parser.add_argument("--current-version")
    args = parser.parse_args()
    try:
        raw, signature, allowed_host = load_source(args.manifest)
        key = load_public_key(args.public_key)
        document = validate_document(raw, key, signature, allowed_host)
        if document["product"] != args.expected_product:
            raise ValueError("manifest product does not match the expected product")
        if args.current_version and semver_key(document["version"]) <= semver_key(args.current_version):
            raise ValueError("manifest version is not newer than the current version")
        print(f"OK:manifest-valid:{document['product']}:{document['version']}")
        if args.package:
            validate_package(args.package, document["package"], key)
            print(f"OK:package-crypto-valid:{args.package}")
        return 0
    except (OSError, UnicodeError, ValueError, InvalidSignature, json.JSONDecodeError, urllib.error.URLError, base64.binascii.Error) as exc:
        print(f"ERR:{exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
