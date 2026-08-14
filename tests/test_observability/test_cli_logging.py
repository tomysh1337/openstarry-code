"""Tests for the CLI-wide structlog default (stderr output, WARNING+ filter)."""

from __future__ import annotations

import contextlib
from collections.abc import Iterator

import structlog

from openstarry_code.observability.cli_logging import (
    configure_cli_structlog,
    is_cli_default_active,
)


@contextlib.contextmanager
def _restore_structlog_config() -> Iterator[None]:
    was_configured = structlog.is_configured()
    old_config = structlog.get_config()
    try:
        yield
    finally:
        if was_configured:
            structlog.configure(**old_config)
        else:
            structlog.reset_defaults()


def test_cli_default_keeps_stdout_clean_and_routes_warnings_to_stderr(capsys) -> None:
    with _restore_structlog_config():
        configure_cli_structlog()
        log = structlog.get_logger("opensquilla.test_cli_logging")

        log.debug("cli_debug_event")
        log.info("cli_info_event")
        log.warning("cli_warning_event")
        log.error("cli_error_event")

        captured = capsys.readouterr()
        assert captured.out == ""
        assert "cli_debug_event" not in captured.err
        assert "cli_info_event" not in captured.err
        assert "cli_warning_event" in captured.err
        assert "cli_error_event" in captured.err


def test_cli_default_resolves_current_stderr_per_emission(capsys) -> None:
    """The stream must late-bind: harnesses swap sys.stderr between calls."""
    with _restore_structlog_config():
        configure_cli_structlog()
        log = structlog.get_logger("opensquilla.test_cli_logging")

        log.warning("first_stderr_event")
        first = capsys.readouterr()
        # capsys installed a fresh replacement stream after readouterr; the
        # logger must follow it rather than the stream seen at configure time.
        log.warning("second_stderr_event")
        second = capsys.readouterr()

        assert "first_stderr_event" in first.err
        assert "second_stderr_event" in second.err
        assert first.out == "" and second.out == ""


def test_is_cli_default_active_tracks_configuration() -> None:
    with _restore_structlog_config():
        structlog.reset_defaults()
        assert not is_cli_default_active()

        configure_cli_structlog()
        assert is_cli_default_active()

        # Any later explicit configuration (interactive TUI, gateway bridge,
        # tests) must win: the marker self-invalidates.
        structlog.configure(logger_factory=structlog.ReturnLoggerFactory())
        assert not is_cli_default_active()


def test_is_cli_default_active_survives_processor_only_swaps() -> None:
    """capture_logs swaps processors only; the default must stay recognized."""
    with _restore_structlog_config():
        configure_cli_structlog()
        with structlog.testing.capture_logs() as captured:
            assert is_cli_default_active()
            structlog.get_logger("opensquilla.test_cli_logging").warning("captured_event")
        assert any(event["event"] == "captured_event" for event in captured)
        assert is_cli_default_active()
