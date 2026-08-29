"""Session handoff system for transferring conversation state between sessions.

Handles transferring pending inputs, context, and state when switching between
parent and child sessions (e.g., forking, meta commands, subagent returns).
"""

from __future__ import annotations

from .manager import HandoffManager
from .types import (
    HandoffPhase,
    HandoffRecord,
    HandoffState,
    SessionTransferRequest,
    TransferResult,
)

__all__ = [
    "HandoffManager",
    "HandoffPhase",
    "HandoffRecord",
    "HandoffState",
    "SessionTransferRequest",
    "TransferResult",
]
