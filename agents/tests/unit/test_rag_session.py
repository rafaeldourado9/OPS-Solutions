"""
Unit tests for RagSessionStore.

Redis is fully mocked — no real Redis required.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from infrastructure.rag_session import RagSessionStore


def _make_redis_mock(*, get_returns=None, pipeline_execute_returns=None) -> MagicMock:
    """Build a minimal AsyncMock Redis client."""
    redis = MagicMock()
    redis.get = AsyncMock(return_value=get_returns)
    redis.setex = AsyncMock(return_value=True)
    redis.set = AsyncMock(return_value=True)
    redis.delete = AsyncMock(return_value=1)

    # Pipeline mock
    pipe = MagicMock()
    pipe.setex = MagicMock(return_value=pipe)
    pipe.set = MagicMock(return_value=pipe)
    pipe.delete = MagicMock(return_value=pipe)
    pipe.execute = AsyncMock(return_value=pipeline_execute_returns or [])
    redis.pipeline = MagicMock(return_value=pipe)
    return redis


class TestRagSessionStore:
    @pytest.mark.asyncio
    async def test_initial_state_is_idle(self):
        """get_state() returns 'idle' when no key is set."""
        redis = _make_redis_mock(get_returns=None)
        store = RagSessionStore(redis=redis, agent_id="test_agent")
        state = await store.get_state("chat_123")
        assert state == "idle"

    @pytest.mark.asyncio
    async def test_set_and_get_state(self):
        """set_state() stores state; get_state() reads it back."""
        redis = _make_redis_mock(get_returns="waiting_doc")
        store = RagSessionStore(redis=redis, agent_id="test_agent")

        await store.set_state("chat_123", "waiting_doc")
        redis.setex.assert_awaited_once()

        state = await store.get_state("chat_123")
        assert state == "waiting_doc"

    @pytest.mark.asyncio
    async def test_set_state_uses_ttl(self):
        """set_state should always set a TTL (uses setex, not set)."""
        redis = _make_redis_mock()
        store = RagSessionStore(redis=redis, agent_id="test_agent")
        await store.set_state("chat_123", "waiting_label")
        # setex was called (has TTL), not plain set
        redis.setex.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_clear_deletes_all_keys(self):
        """clear() pipeline should delete state, doc_data, and doc_name keys."""
        redis = _make_redis_mock()
        store = RagSessionStore(redis=redis, agent_id="test_agent")
        await store.clear("chat_123")
        # The pipeline was used for deletion
        pipe = redis.pipeline.return_value
        assert pipe.delete.call_count == 3  # state, doc_data, doc_name
        pipe.execute.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_set_pending_doc_raises_on_large_file(self):
        """Files over 10 MB should raise ValueError."""
        redis = _make_redis_mock()
        store = RagSessionStore(redis=redis, agent_id="test_agent")
        big_data = b"x" * (10 * 1024 * 1024 + 1)
        with pytest.raises(ValueError, match="10 MB"):
            await store.set_pending_doc("chat_123", "big.pdf", big_data)

    @pytest.mark.asyncio
    async def test_pending_doc_roundtrip(self):
        """set_pending_doc + get_pending_doc should return the same data."""
        data = b"PDF_BYTES_HERE"
        # get should return the filename on the first call, data on the second
        redis = MagicMock()
        call_count = 0

        async def fake_get(key):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return data
            return "my_doc.pdf"

        redis.get = AsyncMock(side_effect=fake_get)

        pipe = MagicMock()
        pipe.set = MagicMock(return_value=pipe)
        pipe.setex = MagicMock(return_value=pipe)
        pipe.execute = AsyncMock(return_value=[])
        redis.pipeline = MagicMock(return_value=pipe)

        store = RagSessionStore(redis=redis, agent_id="test_agent")
        await store.set_pending_doc("chat_123", "my_doc.pdf", data)
        # Verify pipeline was used
        pipe.execute.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_get_pending_doc_returns_none_when_missing(self):
        """get_pending_doc returns None when no doc is stored."""
        redis = _make_redis_mock(get_returns=None)
        store = RagSessionStore(redis=redis, agent_id="test_agent")
        result = await store.get_pending_doc("chat_123")
        assert result is None

    @pytest.mark.asyncio
    async def test_namespace_isolation(self):
        """Two stores with different agent_ids use different keys."""
        redis = _make_redis_mock(get_returns="idle")
        store_a = RagSessionStore(redis=redis, agent_id="agent_a")
        store_b = RagSessionStore(redis=redis, agent_id="agent_b")

        await store_a.get_state("chat_x")
        await store_b.get_state("chat_x")

        calls = redis.get.await_args_list
        keys = [str(call) for call in calls]
        # Keys for a and b should differ
        assert keys[0] != keys[1]
