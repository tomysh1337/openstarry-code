"""Handoff recovery operations for handling failed transfers."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from .types import HandoffPhase, HandoffState

if TYPE_CHECKING:
    from .manager import HandoffManager
    from .types import HandoffRecord

logger = logging.getLogger(__name__)

_RECOVERY_RETRY_LIMIT = 3


def recover_pending_handoffs(
    manager: HandoffManager,
    session_key: str,
) -> tuple[HandoffRecord, ...]:
    """Recover pending handoffs for a session.
    
    Finds all active handoffs associated with the session and returns them
    for potential retry or cleanup.
    
    Args:
        manager: Handoff manager instance
        session_key: Session key to recover handoffs for
        
    Returns:
        Tuple of recoverable handoff records
    """
    active_handoffs = manager.list_active_handoffs(session_key)
    
    recoverable = tuple(
        h for h in active_handoffs
        if h.state == HandoffState.PENDING
        and h.phase in (HandoffPhase.CREATING, HandoffPhase.OPENING)
    )
    
    if recoverable:
        logger.info(
            "Found recoverable handoffs",
            extra={
                "session_key": session_key,
                "count": len(recoverable),
                "handoff_ids": [h.handoff_id for h in recoverable],
            },
        )
    
    return recoverable


def cleanup_stale_handoffs(
    manager: HandoffManager,
    max_age_ms: int = 3600000,
) -> int:
    """Clean up stale handoffs that exceed max age.
    
    Args:
        manager: Handoff manager instance
        max_age_ms: Maximum age in milliseconds (default: 1 hour)
        
    Returns:
        Number of handoffs cleaned up
    """
    import time
    
    now = int(time.time() * 1000)
    threshold = now - max_age_ms
    
    all_active = manager.list_active_handoffs()
    stale = [
        h for h in all_active
        if h.created_at < threshold
    ]
    
    cleaned = 0
    for handoff in stale:
        result = manager.reject_handoff(
            handoff.handoff_id,
            reason="Exceeded maximum age",
        )
        if result:
            cleaned += 1
    
    if cleaned:
        logger.info(
            "Cleaned up stale handoffs",
            extra={
                "count": cleaned,
                "max_age_ms": max_age_ms,
            },
        )
    
    return cleaned


def retry_failed_handoff(
    manager: HandoffManager,
    handoff_id: str,
) -> bool:
    """Attempt to retry a failed handoff.
    
    Args:
        manager: Handoff manager instance
        handoff_id: ID of the handoff to retry
        
    Returns:
        True if retry initiated, False otherwise
    """
    handoff = manager.get_handoff(handoff_id)
    
    if not handoff:
        logger.warning("Handoff not found for retry", extra={"handoff_id": handoff_id})
        return False
    
    if handoff.phase != HandoffPhase.FAILED:
        logger.warning(
            "Cannot retry non-failed handoff",
            extra={"handoff_id": handoff_id, "phase": handoff.phase},
        )
        return False
    
    retry_count = handoff.metadata.get("retry_count", 0)
    if retry_count >= _RECOVERY_RETRY_LIMIT:
        logger.warning(
            "Handoff exceeded retry limit",
            extra={
                "handoff_id": handoff_id,
                "retry_count": retry_count,
                "limit": _RECOVERY_RETRY_LIMIT,
            },
        )
        return False
    
    logger.info(
        "Retrying failed handoff",
        extra={
            "handoff_id": handoff_id,
            "retry_count": retry_count + 1,
        },
    )
    
    return True
