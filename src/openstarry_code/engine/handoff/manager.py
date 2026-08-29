"""Session handoff manager for coordinating state transfers."""

from __future__ import annotations

import time
import uuid
from typing import TYPE_CHECKING, Any

from .types import (
    HandoffPhase,
    HandoffRecord,
    HandoffState,
    SessionTransferRequest,
    TransferResult,
)

if TYPE_CHECKING:
    from collections.abc import Sequence

_HANDOFF_EXPIRY_SECONDS = 3600
_MAX_PENDING_HANDOFFS = 100


class HandoffManager:
    """Manages session handoff operations and state transfers.
    
    Coordinates the transfer of pending inputs and context when switching
    between sessions (fork, return from subagent, meta command execution).
    """

    __slots__ = ("_active_handoffs", "_handoff_history")

    def __init__(self) -> None:
        self._active_handoffs: dict[str, HandoffRecord] = {}
        self._handoff_history: dict[str, HandoffRecord] = {}

    def create_handoff(
        self,
        request: SessionTransferRequest,
    ) -> HandoffRecord:
        """Create a new handoff record for session transfer.
        
        Args:
            request: Transfer request with source/target sessions and data
            
        Returns:
            Created handoff record
            
        Raises:
            ValueError: If max pending handoffs exceeded
        """
        if len(self._active_handoffs) >= _MAX_PENDING_HANDOFFS:
            self._cleanup_expired_handoffs()
            if len(self._active_handoffs) >= _MAX_PENDING_HANDOFFS:
                raise ValueError(
                    f"Maximum pending handoffs ({_MAX_PENDING_HANDOFFS}) exceeded"
                )

        now = int(time.time() * 1000)
        handoff_id = f"handoff-{uuid.uuid4().hex[:12]}"
        
        record = HandoffRecord(
            handoff_id=handoff_id,
            owner_request_id=request.request_id,
            source_session_key=request.source_session_key,
            target_session_key=request.target_session_key,
            state=HandoffState.PENDING,
            phase=HandoffPhase.CREATING,
            pending_input_count=len(request.pending_inputs),
            created_at=now,
            updated_at=now,
            metadata={
                "context_keys": list(request.context_data.keys()),
                "pending_input_ids": [
                    inp.get("pending_input_id", "") for inp in request.pending_inputs
                ],
            },
        )
        
        self._active_handoffs[handoff_id] = record
        return record

    def accept_handoff(
        self,
        owner_request_id: str,
        accepted_session_key: str,
    ) -> HandoffRecord | None:
        """Accept a pending handoff and update its state.
        
        Args:
            owner_request_id: Request ID that owns the handoff
            accepted_session_key: Session key that accepted the handoff
            
        Returns:
            Updated handoff record, or None if not found
        """
        handoff = self._find_by_request_id(owner_request_id)
        if not handoff:
            return None

        now = int(time.time() * 1000)
        updated = HandoffRecord(
            handoff_id=handoff.handoff_id,
            owner_request_id=handoff.owner_request_id,
            source_session_key=handoff.source_session_key,
            target_session_key=handoff.target_session_key,
            state=HandoffState.ACCEPTED,
            phase=HandoffPhase.ACTIVE,
            pending_input_count=handoff.pending_input_count,
            accepted_session_key=accepted_session_key,
            created_at=handoff.created_at,
            updated_at=now,
            metadata=handoff.metadata,
        )
        
        self._active_handoffs[handoff.handoff_id] = updated
        return updated

    def complete_handoff(
        self,
        handoff_id: str,
    ) -> HandoffRecord | None:
        """Mark a handoff as completed and move to history.
        
        Args:
            handoff_id: ID of the handoff to complete
            
        Returns:
            Completed handoff record, or None if not found
        """
        handoff = self._active_handoffs.get(handoff_id)
        if not handoff:
            return None

        now = int(time.time() * 1000)
        completed = HandoffRecord(
            handoff_id=handoff.handoff_id,
            owner_request_id=handoff.owner_request_id,
            source_session_key=handoff.source_session_key,
            target_session_key=handoff.target_session_key,
            state=handoff.state,
            phase=HandoffPhase.COMPLETED,
            pending_input_count=handoff.pending_input_count,
            accepted_session_key=handoff.accepted_session_key,
            created_at=handoff.created_at,
            updated_at=now,
            completed_at=now,
            metadata=handoff.metadata,
        )
        
        del self._active_handoffs[handoff_id]
        self._handoff_history[handoff_id] = completed
        return completed

    def reject_handoff(
        self,
        handoff_id: str,
        reason: str = "",
    ) -> HandoffRecord | None:
        """Reject a pending handoff.
        
        Args:
            handoff_id: ID of the handoff to reject
            reason: Optional rejection reason
            
        Returns:
            Rejected handoff record, or None if not found
        """
        handoff = self._active_handoffs.get(handoff_id)
        if not handoff:
            return None

        now = int(time.time() * 1000)
        rejected = HandoffRecord(
            handoff_id=handoff.handoff_id,
            owner_request_id=handoff.owner_request_id,
            source_session_key=handoff.source_session_key,
            target_session_key=handoff.target_session_key,
            state=HandoffState.REJECTED,
            phase=HandoffPhase.FAILED,
            pending_input_count=handoff.pending_input_count,
            accepted_session_key=handoff.accepted_session_key,
            created_at=handoff.created_at,
            updated_at=now,
            completed_at=now,
            metadata={**handoff.metadata, "rejection_reason": reason},
        )
        
        del self._active_handoffs[handoff_id]
        self._handoff_history[handoff_id] = rejected
        return rejected

    def get_handoff(self, handoff_id: str) -> HandoffRecord | None:
        """Retrieve a handoff by ID from active or history.
        
        Args:
            handoff_id: ID of the handoff
            
        Returns:
            Handoff record or None if not found
        """
        return (
            self._active_handoffs.get(handoff_id)
            or self._handoff_history.get(handoff_id)
        )

    def list_active_handoffs(
        self,
        session_key: str | None = None,
    ) -> tuple[HandoffRecord, ...]:
        """List all active handoffs, optionally filtered by session.
        
        Args:
            session_key: Optional session key to filter by
            
        Returns:
            Tuple of active handoff records
        """
        handoffs = self._active_handoffs.values()
        if session_key:
            handoffs = [
                h for h in handoffs
                if h.source_session_key == session_key
                or h.target_session_key == session_key
                or h.accepted_session_key == session_key
            ]
        return tuple(sorted(handoffs, key=lambda h: h.created_at, reverse=True))

    def _find_by_request_id(self, request_id: str) -> HandoffRecord | None:
        """Find a handoff by owner request ID."""
        for handoff in self._active_handoffs.values():
            if handoff.owner_request_id == request_id:
                return handoff
        return None

    def _cleanup_expired_handoffs(self) -> int:
        """Remove expired pending handoffs.
        
        Returns:
            Number of handoffs cleaned up
        """
        now = int(time.time() * 1000)
        expiry_threshold = now - (_HANDOFF_EXPIRY_SECONDS * 1000)
        
        expired_ids = [
            handoff_id
            for handoff_id, handoff in self._active_handoffs.items()
            if handoff.created_at < expiry_threshold
            and handoff.state == HandoffState.PENDING
        ]
        
        for handoff_id in expired_ids:
            handoff = self._active_handoffs[handoff_id]
            expired = HandoffRecord(
                handoff_id=handoff.handoff_id,
                owner_request_id=handoff.owner_request_id,
                source_session_key=handoff.source_session_key,
                target_session_key=handoff.target_session_key,
                state=HandoffState.EXPIRED,
                phase=HandoffPhase.FAILED,
                pending_input_count=handoff.pending_input_count,
                accepted_session_key=handoff.accepted_session_key,
                created_at=handoff.created_at,
                updated_at=now,
                completed_at=now,
                metadata=handoff.metadata,
            )
            del self._active_handoffs[handoff_id]
            self._handoff_history[handoff_id] = expired
        
        return len(expired_ids)
