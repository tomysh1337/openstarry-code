"""Type definitions for session handoff system."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class HandoffPhase(StrEnum):
    """Phase of session handoff lifecycle."""

    CREATING = "creating"
    OPENING = "opening"
    ACTIVE = "active"
    RETURNING = "returning"
    COMPLETED = "completed"
    FAILED = "failed"


class HandoffState(StrEnum):
    """State of a handoff record."""

    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    EXPIRED = "expired"


@dataclass(frozen=True, slots=True)
class SessionTransferRequest:
    """Request to transfer session state from source to target."""

    source_session_key: str
    target_session_key: str
    request_id: str
    pending_inputs: tuple[dict[str, Any], ...] = field(default_factory=tuple)
    context_data: dict[str, Any] = field(default_factory=dict)
    created_at: int = 0


@dataclass(frozen=True, slots=True)
class HandoffRecord:
    """Durable record of a session handoff operation."""

    handoff_id: str
    owner_request_id: str
    source_session_key: str
    target_session_key: str | None
    state: HandoffState
    phase: HandoffPhase
    pending_input_count: int = 0
    accepted_session_key: str | None = None
    created_at: int = 0
    updated_at: int = 0
    completed_at: int | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class TransferResult:
    """Result of a session transfer operation."""

    success: bool
    handoff_record: HandoffRecord | None = None
    transferred_inputs: tuple[str, ...] = field(default_factory=tuple)
    error_message: str = ""
