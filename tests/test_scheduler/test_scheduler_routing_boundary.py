from __future__ import annotations

from pathlib import Path


def test_gateway_routing_imports_stay_behind_scheduler_adapter() -> None:
    scheduler_root = Path("src/openstarry_code/scheduler")
    offenders = [
        str(path)
        for path in scheduler_root.glob("*.py")
        if path.name != "routing.py"
        and "openstarry_code.gateway.routing" in path.read_text(encoding="utf-8")
    ]

    assert offenders == []
