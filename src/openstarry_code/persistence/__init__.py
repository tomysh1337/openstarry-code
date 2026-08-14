"""Persistence layer: schema migration + related primitives.

Public entry point is :func:`openstarry_code.persistence.migrator.apply_pending`.
"""

from openstarry_code.persistence.migrator import apply_pending

__all__ = ["apply_pending"]
