from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]

TIER_A_MYPY_PARTITION: tuple[str, ...] = (
    "src/openstarry_code/tool_boundary.py",
    "src/openstarry_code/tools/boundary.py",
    "src/openstarry_code/gateway/session_services.py",
    "src/openstarry_code/memory/protocols.py",
    "src/openstarry_code/provider/protocol.py",
    "src/openstarry_code/provider/openai.py",
    "src/openstarry_code/session/compaction.py",
    "src/openstarry_code/scheduler/routing.py",
    "src/openstarry_code/scheduler/delivery.py",
    "src/openstarry_code/scheduler/handlers.py",
    "src/openstarry_code/skills/hub/installer.py",
    "src/openstarry_code/skills/hub/scanner.py",
    "src/openstarry_code/skills/hub/lockfile.py",
    "src/openstarry_code/mcp/discovery.py",
    "src/openstarry_code/tools/builtin/web.py",
)


@pytest.mark.skipif(
    os.environ.get("GITHUB_ACTIONS") == "true"
    and os.environ.get("GITHUB_WORKFLOW") == "CI",
    reason="the ubuntu-quality job runs mypy over all of src/openstarry_code before pytest",
)
def test_tier_a_mypy_partition_stays_clean() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "mypy", *TIER_A_MYPY_PARTITION],
        cwd=REPO_ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )

    assert result.returncode == 0, result.stdout
