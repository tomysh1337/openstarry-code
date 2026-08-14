"""Compatibility alias for the TUI backend contracts module."""

from __future__ import annotations

import sys

from openstarry_code.cli.tui.backend import contracts as _target

sys.modules[__name__] = _target
