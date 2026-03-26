"""
PostgresAdapter — reliable ordered message history using PostgreSQL.

Responsibilities:
  - Persist every message (user + assistant) durably.
  - Return the N most recent messages for a chat (used in context window).
  - Upsert the ConversationRecord on each new message.

This class is used by HybridMemoryAdapter and does NOT implement
MemoryPort directly — it focuses on storage and retrieval, not vectors.
"""

from __future__ import annotations

import logging

from sqlalchemy import select, desc
from sqlalchemy.dialects.postgresql import insert as pg_insert

from core.domain.message import Message, Role
from infrastructure.postgres import (
    AsyncSession,
    ConversationRecord,
    MessageRecord,
    get_session_factory,
)

logger = logging.getLogger(__name__)


class PostgresMessageRepository:
    """
    Thin async repository wrapping the SQLAlchemy models.

    Uses the shared session factory from infrastructure/postgres.py.
    """

    # ------------------------------------------------------------------
    # Write
    # ------------------------------------------------------------------

    async def save(self, message: Message) -> None:
        """Insert a MessageRecord and upsert the ConversationRecord."""
        factory = get_session_factory()
        async with factory() as session:
            async with session.begin():
                await self._upsert_conversation(session, message)
                await self._insert_message(session, message)

    async def _insert_message(self, session: AsyncSession, message: Message) -> None:
        record = MessageRecord(
            chat_id=message.chat_id,
            agent_id=message.agent_id,
            role=message.role,
            content=message.content,
            media_type=message.media_type,
        )
        session.add(record)

    async def _upsert_conversation(
        self, session: AsyncSession, message: Message
    ) -> None:
        """
        Insert a ConversationRecord if none exists for this chat_id,
        otherwise update updated_at.

        Uses PostgreSQL-specific ON CONFLICT DO UPDATE for atomicity.
        """
        stmt = (
            pg_insert(ConversationRecord)
            .values(chat_id=message.chat_id, agent_id=message.agent_id)
            .on_conflict_do_update(
                index_elements=["chat_id"],
                set_={"agent_id": message.agent_id},
            )
        )
        await session.execute(stmt)

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------

    async def get_recent(
        self, chat_id: str, n: int = 15, agent_id: str = ""
    ) -> list[Message]:
        """
        Return the N most recent messages for chat_id, ordered oldest-first.

        Args:
            chat_id:  The conversation to fetch.
            n:        Maximum number of messages.
            agent_id: When provided, restricts results to this agent only,
                      preventing context leakage between agents sharing a chat_id.

        Returns:
            Ordered list of Message domain objects (oldest first).
        """
        factory = get_session_factory()
        async with factory() as session:
            stmt = select(MessageRecord).where(MessageRecord.chat_id == chat_id)
            if agent_id:
                stmt = stmt.where(MessageRecord.agent_id == agent_id)
            stmt = stmt.order_by(desc(MessageRecord.created_at)).limit(n)
            result = await session.execute(stmt)
            records = result.scalars().all()

        # Reverse so oldest is first (we fetched DESC to limit correctly)
        messages: list[Message] = []
        for rec in reversed(records):
            messages.append(
                Message(
                    id=str(rec.id),
                    chat_id=rec.chat_id,
                    agent_id=rec.agent_id,
                    role=rec.role,  # type: ignore[arg-type]
                    content=rec.content,
                    media_type=rec.media_type,
                    timestamp=rec.created_at,
                )
            )
        return messages
