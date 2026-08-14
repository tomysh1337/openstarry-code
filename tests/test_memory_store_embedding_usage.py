"""Pin configured-provider-id propagation into embedding cost estimation.

On-device embedding runtimes (Ollama, …) are free, but a bare model id such
as ``nomic-embed-text`` is unqualified and would fall through to the cloud
default estimate. ``_estimate_embedding_cost_usd`` now takes the configured
provider id and forwards it to the layered price resolver, and
``_record_embedding_request`` sources it from ``self._provider.provider_id``.
"""

from __future__ import annotations

from typing import Any

from openstarry_code.memory.store import LongTermMemoryStore, _estimate_embedding_cost_usd
from openstarry_code.memory.types import MemorySource


def test_estimate_embedding_cost_local_provider_is_free() -> None:
    # Provider-less legacy call falls through to the cloud default estimate.
    legacy = _estimate_embedding_cost_usd("nomic-embed-text", 10_000)
    assert legacy > 0.0
    # Naming the local runtime short-circuits to free.
    local = _estimate_embedding_cost_usd("nomic-embed-text", 10_000, provider="ollama")
    assert local == 0.0


class _FakeEmbeddingProvider:
    """Minimal EmbeddingProvider stand-in for the record-usage path."""

    def __init__(self, model: str, provider_id: str) -> None:
        self._model = model
        self._provider_id = provider_id

    @property
    def provider_id(self) -> str:
        return self._provider_id

    @property
    def model(self) -> str:
        return self._model

    async def embed_query(self, text: str) -> list[float]:  # pragma: no cover - unused
        return []

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:  # pragma: no cover
        return []

    async def probe(self) -> tuple[bool, str | None]:  # pragma: no cover - unused
        return True, None


def test_record_embedding_request_threads_provider_id() -> None:
    """The store sources the configured provider id from its embedding
    provider, so a local runtime records zero estimated cost while still
    logging tokens and provenance."""
    store: Any = LongTermMemoryStore(
        db_path=":memory:",
        embedding_provider=_FakeEmbeddingProvider("nomic-embed-text", "ollama"),
    )
    store._record_embedding_request(["some text to embed"] * 20)

    usage = store.consume_embedding_usage()
    assert usage["provider"] == "ollama"
    assert usage["input_tokens"] > 0
    assert usage["cost_usd"] == 0.0


def test_record_embedding_request_cloud_provider_estimates_cost() -> None:
    """A cloud provider id keeps the non-zero pricing-table estimate."""
    store: Any = LongTermMemoryStore(
        db_path=":memory:",
        embedding_provider=_FakeEmbeddingProvider("text-embedding-3-small", "openai"),
    )
    store._record_embedding_request(["some text to embed"] * 20)

    usage = store.consume_embedding_usage()
    assert usage["provider"] == "openai"
    assert usage["cost_usd"] > 0.0


class _FlakyEmbeddingProvider:
    """Fails the first embed_batch call, then succeeds."""

    def __init__(self) -> None:
        self.embed_batch_calls = 0

    @property
    def provider_id(self) -> str:
        return "test"

    @property
    def model(self) -> str:
        return "test-embed-model"

    async def embed_query(self, text: str) -> list[float]:
        return [0.6, 0.8]

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        self.embed_batch_calls += 1
        if self.embed_batch_calls == 1:
            raise RuntimeError("503 service unavailable")
        return [[0.6, 0.8] for _ in texts]

    async def probe(self) -> tuple[bool, str | None]:  # pragma: no cover - unused
        return True, None


async def _chunk_embedding(store: LongTermMemoryStore, path: str) -> bytes | None:
    assert store._db is not None
    async with store._db.execute("SELECT embedding FROM chunks WHERE path = ?", (path,)) as cur:
        row = await cur.fetchone()
    assert row is not None
    return row[0]


async def test_index_file_retries_embedding_after_transient_failure(tmp_path) -> None:
    provider = _FlakyEmbeddingProvider()
    store = LongTermMemoryStore(tmp_path / "memory.db", embedding_provider=provider)
    await store.initialize()
    try:
        path = "notes/deploy.md"
        content = "# Deploy notes\n\nThe staging cluster restarts every Sunday at 03:00 UTC.\n"

        assert await store.index_file(path, content, source=MemorySource.memory) == 1
        assert provider.embed_batch_calls == 1
        assert await _chunk_embedding(store, path) is None

        # Same content, provider recovered: the vector-less chunk is re-embedded
        # instead of being skipped forever by the unchanged-hash short-circuit.
        await store.index_file(path, content, source=MemorySource.memory)

        assert provider.embed_batch_calls == 2
        assert await _chunk_embedding(store, path) is not None
    finally:
        await store.close()
