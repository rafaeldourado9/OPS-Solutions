"""
HybridMemoryAdapter — MemoryPort implementation combining Qdrant + PostgreSQL.

Strategy:
  - save_message():          writes to both Postgres (reliable) and Qdrant (semantic)
  - get_recent():            reads from Postgres (ordered, transactional)
  - search_semantic():       reads from Qdrant (vector similarity)
  - search_business_rules(): reads from Qdrant RAG collection
"""

from __future__ import annotations

import asyncio
import logging

from adapters.outbound.memory.postgres_adapter import PostgresMessageRepository
from adapters.outbound.memory.qdrant_adapter import QdrantAdapter
from core.domain.memory import Memory
from core.domain.message import Message
from core.ports.memory_port import MemoryPort

logger = logging.getLogger(__name__)


class HybridMemoryAdapter(MemoryPort):
    """
    MemoryPort that uses PostgreSQL for history and Qdrant for semantic search.

    Args:
        qdrant:    QdrantAdapter instance.
        postgres:  PostgresMessageRepository instance.
    """

    def __init__(
        self,
        qdrant: QdrantAdapter,
        postgres: PostgresMessageRepository,
    ) -> None:
        self._qdrant = qdrant
        self._postgres = postgres

    async def save_message(self, message: Message) -> None:
        """
        Persist to PostgreSQL and embed+store in Qdrant concurrently.

        Postgres failure raises (message must be saved reliably).
        Qdrant failure is logged but does not propagate — semantic search
        can degrade gracefully without blocking the conversation.
        """
        # Save to Postgres first (must succeed)
        await self._postgres.save(message)

        # Embed and store in Qdrant (best-effort)
        asyncio.create_task(self._qdrant_save_safe(message))

    async def _qdrant_save_safe(self, message: Message) -> None:
        try:
            await self._qdrant.save_message_vector(message)
        except Exception:
            logger.exception(
                "Qdrant vector save failed for message %s — continuing without it",
                message.id,
            )

    async def get_recent(self, chat_id: str, n: int = 15, agent_id: str = "") -> list[Message]:
        """Return N most recent messages from PostgreSQL (oldest first)."""
        return await self._postgres.get_recent(chat_id=chat_id, n=n, agent_id=agent_id)

    async def search_semantic(
        self,
        chat_id: str,
        query: str,
        k: int = 6,
    ) -> list[Memory]:
        """Return K semantically similar past messages from Qdrant."""
        return await self._qdrant.search_semantic(chat_id=chat_id, query=query, k=k)

    async def search_business_rules(
        self,
        query: str,
        k: int = 4,
        agent_id: str = "",
    ) -> list[str]:
        """Return K relevant RAG chunks from the Qdrant rules collection."""
        return await self._qdrant.search_business_rules(
            query=query, k=k, agent_id=agent_id
        )
