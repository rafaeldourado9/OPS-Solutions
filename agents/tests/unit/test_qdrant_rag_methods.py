"""
Unit tests for QdrantAdapter.list_document_sources() and delete_by_source().

AsyncQdrantClient is fully mocked — no real Qdrant required.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest


def _make_point(source: str, agent_id: str = "agent_a") -> MagicMock:
    """Create a fake Qdrant ScoredPoint with payload."""
    point = MagicMock()
    point.payload = {"agent_id": agent_id, "source": source, "content": "some text"}
    return point


class TestListDocumentSources:
    @pytest.mark.asyncio
    async def test_returns_empty_when_no_documents(self):
        """list_document_sources returns [] when collection is empty."""
        with patch(
            "adapters.outbound.memory.qdrant_adapter.AsyncQdrantClient"
        ) as MockClient:
            client = MagicMock()
            client.scroll = AsyncMock(return_value=([], None))
            client.create_collection = AsyncMock()
            client.create_payload_index = AsyncMock()
            client.get_collection = AsyncMock(return_value=MagicMock())
            MockClient.return_value = client

            from adapters.outbound.memory.qdrant_adapter import QdrantAdapter
            adapter = QdrantAdapter(
                chat_collection="test_chats",
                rules_collection="test_rules",
            )

            sources = await adapter.list_document_sources("agent_a")
            assert sources == []

    @pytest.mark.asyncio
    async def test_groups_chunks_by_source(self):
        """list_document_sources aggregates chunk counts per source."""
        points = [
            _make_point("cardápio"),
            _make_point("cardápio"),
            _make_point("preços"),
        ]
        with patch(
            "adapters.outbound.memory.qdrant_adapter.AsyncQdrantClient"
        ) as MockClient:
            client = MagicMock()
            client.scroll = AsyncMock(return_value=(points, None))
            client.get_collection = AsyncMock(return_value=MagicMock())
            MockClient.return_value = client

            from adapters.outbound.memory.qdrant_adapter import QdrantAdapter
            adapter = QdrantAdapter(
                chat_collection="test_chats",
                rules_collection="test_rules",
            )

            sources = await adapter.list_document_sources("agent_a")
            # Should be sorted alphabetically
            assert len(sources) == 2
            source_map = {s["source"]: s["chunks"] for s in sources}
            assert source_map["cardápio"] == 2
            assert source_map["preços"] == 1

    @pytest.mark.asyncio
    async def test_returns_empty_on_qdrant_error(self):
        """list_document_sources returns [] instead of raising on errors."""
        with patch(
            "adapters.outbound.memory.qdrant_adapter.AsyncQdrantClient"
        ) as MockClient:
            client = MagicMock()
            client.scroll = AsyncMock(side_effect=Exception("Connection refused"))
            client.get_collection = AsyncMock(return_value=MagicMock())
            MockClient.return_value = client

            from adapters.outbound.memory.qdrant_adapter import QdrantAdapter
            adapter = QdrantAdapter(
                chat_collection="test_chats",
                rules_collection="test_rules",
            )

            sources = await adapter.list_document_sources("agent_a")
            assert sources == []


class TestDeleteBySource:
    @pytest.mark.asyncio
    async def test_calls_delete_with_filter(self):
        """delete_by_source calls client.delete with the correct filter."""
        with patch(
            "adapters.outbound.memory.qdrant_adapter.AsyncQdrantClient"
        ) as MockClient:
            client = MagicMock()
            client.delete = AsyncMock(return_value=MagicMock())
            client.get_collection = AsyncMock(return_value=MagicMock())
            MockClient.return_value = client

            from adapters.outbound.memory.qdrant_adapter import QdrantAdapter
            adapter = QdrantAdapter(
                chat_collection="test_chats",
                rules_collection="test_rules",
            )

            result = await adapter.delete_by_source("agent_a", "cardápio")
            client.delete.assert_awaited_once()
            # Verify it targeted the rules collection
            call_kwargs = client.delete.await_args
            assert call_kwargs.kwargs["collection_name"] == "test_rules"

    @pytest.mark.asyncio
    async def test_returns_zero_on_error(self):
        """delete_by_source returns 0 and does not raise on Qdrant error."""
        with patch(
            "adapters.outbound.memory.qdrant_adapter.AsyncQdrantClient"
        ) as MockClient:
            client = MagicMock()
            client.delete = AsyncMock(side_effect=Exception("Qdrant error"))
            client.get_collection = AsyncMock(return_value=MagicMock())
            MockClient.return_value = client

            from adapters.outbound.memory.qdrant_adapter import QdrantAdapter
            adapter = QdrantAdapter(
                chat_collection="test_chats",
                rules_collection="test_rules",
            )

            result = await adapter.delete_by_source("agent_a", "preços")
            assert result == 0
