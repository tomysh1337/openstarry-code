"""Web search abstraction layer."""

from openstarry_code.search.canonical import run_canonical_web_search
from openstarry_code.search.registry import get_provider, register_provider
from openstarry_code.search.types import (
    SearchDiagnostics,
    SearchHit,
    SearchOptions,
    SearchProvider,
    SearchProviderError,
    SearchProviderSpec,
    SearchRequest,
    SearchResult,
)

__all__ = [
    "SearchDiagnostics",
    "SearchHit",
    "SearchOptions",
    "SearchResult",
    "SearchRequest",
    "SearchProviderSpec",
    "SearchProviderError",
    "SearchProvider",
    "get_provider",
    "register_provider",
    "run_canonical_web_search",
]
