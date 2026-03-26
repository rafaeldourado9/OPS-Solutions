"""
Unit tests for HybridMemoryAdapter.

Qdrant and Postgres are replaced with async mocks so no infrastructure is needed.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from adapters.outbound.memory.hybrid_memory_adapter import HybridMemoryAdapter
from core.domain.memory import Memory
from core.domain.message import Message


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_message(role: str = "user", content: str = "Olá") -> Message:
    return Message(
        id=str(uuid4()),
        chat_id="5511@c.us",
        agent_id="empresa_x",
        role=role,
        content=content,
    )


def _make_memory(content: str = "lembrei") -> Memory:
    return Memory(id=str(uuid4()), chat_id="5511@c.us", content=content, score=0.9)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestHybridMemoryAdapter:
    @pytest.mark.asyncio
    async def test_save_message_calls_postgres(self):
        qdrant = MagicMock()
        qdrant.save_message_vector = AsyncMock()
        postgres = MagicMock()
        postgres.save = AsyncMock()

        adapter = HybridMemoryAdapter(qdrant=qdrant, postgres=postgres)
        msg = _make_message()

        await adapter.save_message(msg)

        postgres.save.assert_awaited_once_with(msg)

    @pytest.mark.asyncio
    async def test_get_recent_delegates_to_postgres(self):
        messages = [_make_message("user"), _make_message("assistant", "Oi!")]
        postgres = MagicMock()
        postgres.get_recent = AsyncMock(return_value=messages)
        qdrant = MagicMock()

        adapter = HybridMemoryAdapter(qdrant=qdrant, postgres=postgres)
        result = await adapter.get_recent("5511@c.us", n=10)

        postgres.get_recent.assert_awaited_once_with(chat_id="5511@c.us", n=10)
        assert result == messages

    @pytest.mark.asyncio
    async def test_search_semantic_delegates_to_qdrant(self):
        memories = [_make_memory("resultado")]
        qdrant = MagicMock()
        qdrant.search_semantic = AsyncMock(return_value=memories)
        postgres = MagicMock()

        adapter = HybridMemoryAdapter(qdrant=qdrant, postgres=postgres)
        result = await adapter.search_semantic("5511@c.us", "pedido", k=3)

        qdrant.search_semantic.assert_awaited_once_with(
            chat_id="5511@c.us", query="pedido", k=3
        )
        assert result == memories

    @pytest.mark.asyncio
    async def test_search_business_rules_delegates_to_qdrant(self):
        qdrant = MagicMock()
        qdrant.search_business_rules = AsyncMock(return_value=["regra 1", "regra 2"])
        postgres = MagicMock()

        adapter = HybridMemoryAdapter(qdrant=qdrant, postgres=postgres)
        result = await adapter.search_business_rules("prazo", k=4, agent_id="empresa_x")

        qdrant.search_business_rules.assert_awaited_once_with(
            query="prazo", k=4, agent_id="empresa_x"
        )
        assert result == ["regra 1", "regra 2"]

    @pytest.mark.asyncio
    async def test_postgres_failure_propagates(self):
        qdrant = MagicMock()
        postgres = MagicMock()
        postgres.save = AsyncMock(side_effect=Exception("DB down"))

        adapter = HybridMemoryAdapter(qdrant=qdrant, postgres=postgres)

        with pytest.raises(Exception, match="DB down"):
            await adapter.save_message(_make_message())

    @pytest.mark.asyncio
    async def test_empty_recent_returns_empty_list(self):
        postgres = MagicMock()
        postgres.get_recent = AsyncMock(return_value=[])
        qdrant = MagicMock()

        adapter = HybridMemoryAdapter(qdrant=qdrant, postgres=postgres)
        result = await adapter.get_recent("new_chat@c.us", n=15)
        assert result == []
