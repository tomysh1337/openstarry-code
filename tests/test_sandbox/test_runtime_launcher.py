from __future__ import annotations

import sys

import pytest

from openstarry_code.sandbox.runtime_launcher import (
    ChildRole,
    InternalChildDispatchError,
    dispatch_internal_child,
    internal_child_argv,
)


@pytest.mark.parametrize(
    ("role", "module"),
    [
        (ChildRole.FILESYSTEM_WORKER, "openstarry_code.sandbox.filesystem_worker"),
        (ChildRole.LINUX_HELPER, "openstarry_code.sandbox.backend.linux_helper"),
        (
            ChildRole.WINDOWS_DEFAULT_RUNNER,
            "openstarry_code.sandbox.backend.windows_default_runner",
        ),
        (
            ChildRole.DIRECTORY_PICKER,
            "openstarry_code.gateway.windows_directory_picker",
        ),
    ],
)
def test_source_child_uses_python_module(
    monkeypatch: pytest.MonkeyPatch,
    role: ChildRole,
    module: str,
) -> None:
    monkeypatch.delattr(sys, "frozen", raising=False)
    monkeypatch.setattr(sys, "executable", "/runtime/python")

    assert internal_child_argv(role, args=("--probe",)) == (
        "/runtime/python",
        "-m",
        module,
        "--probe",
    )


@pytest.mark.parametrize(
    "role",
    [
        ChildRole.FILESYSTEM_WORKER,
        ChildRole.LINUX_HELPER,
        ChildRole.WINDOWS_DEFAULT_RUNNER,
        ChildRole.DIRECTORY_PICKER,
    ],
)
def test_frozen_child_uses_internal_role(
    monkeypatch: pytest.MonkeyPatch,
    role: ChildRole,
) -> None:
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setattr(sys, "executable", "C:\\OpenStarry Code\\gateway.exe")

    assert internal_child_argv(role, args=("--probe",)) == (
        "C:\\OpenStarry Code\\gateway.exe",
        "--internal-child",
        role.value,
        "--probe",
    )


def test_internal_child_argv_rejects_unregistered_role() -> None:
    with pytest.raises(ValueError, match="unknown internal child role"):
        internal_child_argv("shell")


def test_dispatch_rejects_missing_or_unknown_role() -> None:
    with pytest.raises(InternalChildDispatchError, match="missing"):
        dispatch_internal_child([])
    with pytest.raises(InternalChildDispatchError, match="unknown"):
        dispatch_internal_child(["shell"])
