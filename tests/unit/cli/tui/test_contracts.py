from __future__ import annotations

import ast
import importlib
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[4]
SRC_ROOT = PROJECT_ROOT / "src/openstarry_code/cli"
TUI_ROOT = SRC_ROOT / "tui"
REMOVED_TEXT_BACKEND = "text" + "ual"
REMOVED_TERMINAL = "terminal"
PROMPT_TOOLKIT = "prompt" + "_toolkit"


REMOVED_FRONTEND_PATHS = (
    TUI_ROOT / "terminal",
    TUI_ROOT / REMOVED_TEXT_BACKEND,
    TUI_ROOT / "app.py",
    TUI_ROOT / "prompt.py",
    TUI_ROOT / "paste.py",
    TUI_ROOT / "stream.py",
    TUI_ROOT / "signal_handlers.py",
    TUI_ROOT / f"{REMOVED_TERMINAL}_bridge.py",
    TUI_ROOT / f"{REMOVED_TERMINAL}_chat_adapter.py",
    TUI_ROOT / f"{REMOVED_TERMINAL}_renderer.py",
    TUI_ROOT / f"{REMOVED_TERMINAL}_surface.py",
    TUI_ROOT / f"adapters/{REMOVED_TERMINAL}_bridge.py",
    TUI_ROOT / f"adapters/{REMOVED_TERMINAL}_chat_adapter.py",
    TUI_ROOT / f"adapters/{REMOVED_TEXT_BACKEND}_bridge.py",
    TUI_ROOT / f"renderers/{REMOVED_TEXT_BACKEND}_backend.py",
    SRC_ROOT / f"repl/{REMOVED_TERMINAL}_bridge.py",
    SRC_ROOT / f"repl/{REMOVED_TERMINAL}_chat_adapter.py",
    SRC_ROOT / f"repl/{REMOVED_TERMINAL}_renderer.py",
    SRC_ROOT / f"repl/{REMOVED_TERMINAL}_surface.py",
)


def _imported_modules(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.update(alias.name for alias in node.names)
            continue
        if isinstance(node, ast.ImportFrom) and node.module is not None:
            modules.add(node.module)
    return modules


def _live_tui_python_paths() -> list[Path]:
    return [
        path
        for path in TUI_ROOT.rglob("*.py")
        if "__pycache__" not in path.parts
    ]


def test_removed_frontend_files_are_absent() -> None:
    assert [path for path in REMOVED_FRONTEND_PATHS if path.exists()] == []


def test_live_tui_modules_do_not_import_removed_frontends() -> None:
    forbidden_prefixes = (
        f"openstarry_code.cli.tui.{REMOVED_TERMINAL}",
        f"openstarry_code.cli.tui.{REMOVED_TEXT_BACKEND}",
        f"openstarry_code.cli.tui.adapters.{REMOVED_TERMINAL}_bridge",
        f"openstarry_code.cli.tui.adapters.{REMOVED_TERMINAL}_chat_adapter",
        f"openstarry_code.cli.tui.adapters.{REMOVED_TEXT_BACKEND}_bridge",
        f"openstarry_code.cli.repl.{REMOVED_TERMINAL}_bridge",
        f"openstarry_code.cli.repl.{REMOVED_TERMINAL}_chat_adapter",
        f"openstarry_code.cli.repl.{REMOVED_TERMINAL}_renderer",
        f"openstarry_code.cli.repl.{REMOVED_TERMINAL}_surface",
        PROMPT_TOOLKIT,
        REMOVED_TEXT_BACKEND,
    )

    offenders: dict[str, list[str]] = {}
    for path in _live_tui_python_paths():
        imports = sorted(
            module
            for module in _imported_modules(path)
            if module == REMOVED_TEXT_BACKEND
            or any(
                module == prefix or module.startswith(f"{prefix}.")
                for prefix in forbidden_prefixes
            )
        )
        if imports:
            offenders[str(path.relative_to(PROJECT_ROOT))] = imports

    assert offenders == {}


def test_shared_tui_contracts_remain_importable() -> None:
    modules = (
        "openstarry_code.cli.tui.backend.contracts",
        "openstarry_code.cli.tui.backend.runtime",
        "openstarry_code.cli.tui.backend.streaming",
        "openstarry_code.cli.tui.backend.transcript",
        "openstarry_code.cli.tui.backend.render_summary",
        "openstarry_code.cli.tui.plugins",
        "openstarry_code.cli.tui.plugins.router_hud",
        "openstarry_code.cli.tui.adapters.runtime_helpers",
        "openstarry_code.cli.tui.adapters.runtime_bridge",
        "openstarry_code.cli.tui.opentui.runtime",
        "openstarry_code.cli.tui.opentui.renderer",
    )

    for module in modules:
        assert importlib.import_module(module)


def test_tui_package_exports_only_neutral_and_opentui_surfaces() -> None:
    import openstarry_code.cli.tui as tui

    exported = set(tui.__all__)

    assert "backend" in exported
    assert "opentui" in exported
    assert "turn_bridge" in exported
    assert "terminal" not in exported
    assert REMOVED_TEXT_BACKEND not in exported
    assert not any(name.startswith("terminal_") for name in exported)
