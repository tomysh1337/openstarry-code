"""Compatibility alias for the TUI-owned slash input policy."""

from __future__ import annotations

import sys

from openstarry_code.cli.tui import slash_policy as _target

sys.modules[__name__] = _target
