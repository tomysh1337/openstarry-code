"""SSRF resolver regressions for poisoned public-domain DNS answers."""

from __future__ import annotations

import socket

import pytest

from openstarry_code.tools import ssrf
from openstarry_code.tools.types import SSRFBlockedError


def test_public_dns_fallback_replaces_loopback_hosts_mapping(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        socket,
        "getaddrinfo",
        lambda *_args, **_kwargs: [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("127.0.0.1", 0))],
    )
    monkeypatch.setattr(ssrf, "_resolve_public_dns", lambda _hostname: [ssrf.ipaddress.IPv4Address("93.184.216.34")])

    assert ssrf.validate_http_url_for_fetch("https://public.example") == ["93.184.216.34"]


def test_ip_literal_never_uses_public_dns_fallback(monkeypatch: pytest.MonkeyPatch) -> None:
    called = False

    def fail_if_called(_hostname: str):
        nonlocal called
        called = True
        return [ssrf.ipaddress.IPv4Address("93.184.216.34")]

    monkeypatch.setattr(ssrf, "_resolve_public_dns", fail_if_called)

    with pytest.raises(SSRFBlockedError):
        ssrf.validate_http_url_for_fetch("http://127.0.0.1")

    assert called is False
