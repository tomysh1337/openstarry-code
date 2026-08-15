"""Validation and redaction helpers for operator-defined provider headers."""

from __future__ import annotations

import re
from collections.abc import Mapping
from typing import Any

REDACTED_REQUEST_HEADER = "***"

_HEADER_NAME_RE = re.compile(r"^[!#$%&'*+.^_`|~0-9A-Za-z-]+$")
_MAX_REQUEST_HEADERS = 32
_MAX_HEADER_NAME_CHARS = 128
_MAX_HEADER_VALUE_CHARS = 8192

# These fields define HTTP framing or provider authentication.  Keeping them
# adapter-owned prevents a custom entry from replacing the API key selected by
# the credential resolver or changing how httpx frames the request body.
_RESERVED_HEADER_NAMES = frozenset(
    {
        "authorization",
        "connection",
        "content-length",
        "host",
        "proxy-authorization",
        "transfer-encoding",
        "upgrade",
        "x-api-key",
    }
)


def normalize_request_headers(value: object) -> dict[str, str]:
    """Return a validated, insertion-ordered custom request-header mapping."""

    if value is None:
        return {}
    if not isinstance(value, Mapping):
        raise ValueError("request_headers must be an object of header-name/value pairs")
    if len(value) > _MAX_REQUEST_HEADERS:
        raise ValueError(f"request_headers may contain at most {_MAX_REQUEST_HEADERS} entries")

    normalized: dict[str, str] = {}
    normalized_names: set[str] = set()
    for raw_name, raw_value in value.items():
        if not isinstance(raw_name, str):
            raise ValueError("request_headers names must be strings")
        name = raw_name.strip()
        if not name:
            raise ValueError("request_headers names must not be empty")
        if len(name) > _MAX_HEADER_NAME_CHARS or not _HEADER_NAME_RE.fullmatch(name):
            raise ValueError(f"invalid request header name: {name!r}")
        lower_name = name.lower()
        if lower_name in _RESERVED_HEADER_NAMES:
            raise ValueError(f"request header {name!r} is managed by the provider adapter")
        if lower_name in normalized_names:
            raise ValueError(f"duplicate request header name: {name!r}")
        if not isinstance(raw_value, str):
            raise ValueError(f"request header {name!r} value must be a string")
        header_value = raw_value.strip()
        if "\r" in header_value or "\n" in header_value or "\x00" in header_value:
            raise ValueError(f"request header {name!r} contains an invalid control character")
        if len(header_value) > _MAX_HEADER_VALUE_CHARS:
            raise ValueError(
                f"request header {name!r} exceeds {_MAX_HEADER_VALUE_CHARS} characters"
            )
        normalized_names.add(lower_name)
        normalized[name] = header_value
    return normalized


def merge_redacted_request_headers(
    existing: Mapping[str, str] | None,
    incoming: object,
    *,
    allow_preserve: bool,
) -> dict[str, str]:
    """Resolve masked public-config values without accepting a literal mask."""

    current = normalize_request_headers(existing or {})
    candidate = normalize_request_headers(incoming)
    current_by_name = {name.lower(): value for name, value in current.items()}
    merged: dict[str, str] = {}
    for name, value in candidate.items():
        if value == "[redacted]" or (value and set(value) == {"*"}):
            preserved = current_by_name.get(name.lower(), "") if allow_preserve else ""
            if not preserved:
                raise ValueError(f"request header {name!r} must be re-entered for this endpoint")
            merged[name] = preserved
        else:
            merged[name] = value
    return merged


def redact_request_headers(value: object, *, placeholder: str = REDACTED_REQUEST_HEADER) -> Any:
    """Mask every configured header value while retaining editable names."""

    if not isinstance(value, Mapping):
        return value
    return {
        str(name): (placeholder if str(header_value) else "")
        for name, header_value in value.items()
    }
