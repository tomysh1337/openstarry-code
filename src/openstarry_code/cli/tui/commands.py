"""Compatibility alias for TUI slash command presentation helpers."""

from __future__ import annotations

import sys

from openstarry_code.cli.tui.adapters import commands as _target

sys.modules[__name__] = _target
