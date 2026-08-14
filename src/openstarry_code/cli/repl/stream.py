"""Compatibility alias for neutral TUI turn-stream helpers."""

from __future__ import annotations

import sys

from openstarry_code.cli.tui import turn_bridge as _target

sys.modules[__name__] = _target
