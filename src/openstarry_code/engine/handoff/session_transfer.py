"""Session transfer operations for moving state between sessions."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from .types import (
    HandoffPhase,
    HandoffRecord,
    SessionTransferRequest,
    TransferResult,
)

if TYPE_CHECKING:
    from .manager import HandoffManager

logger = logging.getLogger(__name__)

_TRANSFER_TIMEOUT_MS = 30000


def transfer_session_state(
    manager: HandoffManager,
    request: SessionTransferRequest,
) -> TransferResult:
    """Transfer session state from source to target session.
    
    Args:
        manager: Handoff manager instance
        request: Transfer request with source/target and data
        
    Returns:
        Transfer result with success status and details
    """
    try:
        handoff = manager.create_handoff(request)
        
        logger.info(
            "Created handoff for session transfer",
            extra={
                "handoff_id": handoff.handoff_id,
                "source": request.source_session_key,
                "target": request.target_session_key,
                "pending_count": len(request.pending_inputs),
            },
        )
        
        transferred_ids = tuple(
            inp.get("pending_input_id", "")
            for inp in request.pending_inputs
            if inp.get("pending_input_id")
        )
        
        return TransferResult(
            success=True,
            handoff_record=handoff,
            transferred_inputs=transferred_ids,
        )
    
    except Exception as exc:
        logger.error(
            "Failed to create handoff",
            extra={
                "source": request.source_session_key,
                "target": request.target_session_key,
                "error": str(exc),
            },
            exc_info=True,
        )
        return TransferResult(
            success=False,
            error_message=f"Transfer failed: {exc}",
        )


def accept_session_transfer(
    manager: HandoffManager,
    owner_request_id: str,
    accepted_session_key: str,
) -> TransferResult:
    """Accept a pending session transfer.
    
    Args:
        manager: Handoff manager instance
        owner_request_id: Request ID that initiated the handoff
        accepted_session_key: Session key accepting the transfer
        
    Returns:
        Transfer result with updated handoff record
    """
    try:
        handoff = manager.accept_handoff(owner_request_id, accepted_session_key)
        
        if not handoff:
            return TransferResult(
                success=False,
                error_message=f"Handoff not found for request {owner_request_id}",
            )
        
        logger.info(
            "Accepted handoff",
            extra={
                "handoff_id": handoff.handoff_id,
                "accepted_by": accepted_session_key,
            },
        )
        
        return TransferResult(
            success=True,
            handoff_record=handoff,
        )
    
    except Exception as exc:
        logger.error(
            "Failed to accept handoff",
            extra={
                "owner_request_id": owner_request_id,
                "accepted_by": accepted_session_key,
                "error": str(exc),
            },
            exc_info=True,
        )
        return TransferResult(
            success=False,
            error_message=f"Accept failed: {exc}",
        )


def complete_session_transfer(
    manager: HandoffManager,
    handoff_id: str,
) -> TransferResult:
    """Complete a session transfer operation.
    
    Args:
        manager: Handoff manager instance
        handoff_id: ID of the handoff to complete
        
    Returns:
        Transfer result with completed handoff record
    """
    handoff = manager.complete_handoff(handoff_id)
    
    if not handoff:
        return TransferResult(
            success=False,
            error_message=f"Handoff {handoff_id} not found",
        )
    
    logger.info(
        "Completed handoff",
        extra={"handoff_id": handoff_id, "phase": handoff.phase},
    )
    
    return TransferResult(
        success=True,
        handoff_record=handoff,
    )


def reject_session_transfer(
    manager: HandoffManager,
    handoff_id: str,
    reason: str = "",
) -> TransferResult:
    """Reject a pending session transfer.
    
    Args:
        manager: Handoff manager instance
        handoff_id: ID of the handoff to reject
        reason: Optional rejection reason
        
    Returns:
        Transfer result with rejected handoff record
    """
    handoff = manager.reject_handoff(handoff_id, reason)
    
    if not handoff:
        return TransferResult(
            success=False,
            error_message=f"Handoff {handoff_id} not found",
        )
    
    logger.warning(
        "Rejected handoff",
        extra={
            "handoff_id": handoff_id,
            "reason": reason or "unspecified",
        },
    )
    
    return TransferResult(
        success=True,
        handoff_record=handoff,
    )
