"""
NullMemoryAdapter — MemoryPort no-op implementation.

Used in Sprint 1 before Qdrant/PostgreSQL adapters are wired up,
and in tests where memory is not under test.
All read operations return empty results; save operations are no-ops.
"""

from __future__ import annotations

import logging

from core.domain.memory import Memory
from core.domain.message import Message
from core.ports.memory_port import MemoryPort

logger = logging.getLogger(__name__)


class NullMemoryAdapter(MemoryPort):
    """MemoryPort implementation that stores nothing and returns nothing."""

    async def save_message(self, message: Message) -> None:
        logger.debug(
            "NullMemoryAdapter: skipping save for chat_id=%s role=%s",
            message.chat_id,
            message.role,
        )

    async def search_semantic(
        self,
        chat_id: str,
        query: str,
        k: int = 6,
    ) -> list[Memory]:
        return []

    async def get_recent(
        self,
        chat_id: str,
        n: int = 15,
        agent_id: str = "",
    ) -> list[Message]:
        return []

    async def search_business_rules(
        self,
        query: str,
        k: int = 4,
        agent_id: str = "",
    ) -> list[str]:
        return []
