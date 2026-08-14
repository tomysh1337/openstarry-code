"""Compatibility alias for the TUI backend output binding module."""

from __future__ import annotations

import sys

from openstarry_code.cli.tui.backend import output_binding as _target

sys.modules[__name__] = _target
