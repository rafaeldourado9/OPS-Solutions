"""
RagSessionStore — Redis-backed state machine for the /rag admin command flow.

States per chat_id:
  idle          → no active RAG session (default)
  waiting_doc   → admin typed /rag, waiting for the document to arrive
  waiting_label → document received, waiting for the description text

All keys have a TTL of 10 minutes so abandoned sessions are cleaned up automatically.
"""

from __future__ import annotations

import base64
import logging
from typing import Optional

from redis.asyncio import Redis

logger = logging.getLogger(__name__)

_TTL = 600  # 10 minutes

_STATE_PREFIX = "rag_state"
_DOC_DATA_PREFIX = "rag_doc_data"
_DOC_NAME_PREFIX = "rag_doc_name"


class RagSessionStore:
    """
    Manages the per-chat RAG ingestion state for admin commands.

    Args:
        redis:  AsyncRedis client (shared pool).
        agent_id: Agent namespace to avoid key collisions across agents.
    """

    def __init__(self, redis: Redis, agent_id: str) -> None:
        self._redis = redis
        self._ns = agent_id

    # ------------------------------------------------------------------
    # Key builders
    # ------------------------------------------------------------------

    def _state_key(self, chat_id: str) -> str:
        return f"{_STATE_PREFIX}:{self._ns}:{chat_id}"

    def _doc_data_key(self, chat_id: str) -> str:
        return f"{_DOC_DATA_PREFIX}:{self._ns}:{chat_id}"

    def _doc_name_key(self, chat_id: str) -> str:
        return f"{_DOC_NAME_PREFIX}:{self._ns}:{chat_id}"

    # ------------------------------------------------------------------
    # State management
    # ------------------------------------------------------------------

    async def get_state(self, chat_id: str) -> str:
        """Return the current state for chat_id ('idle' if none set)."""
        value = await self._redis.get(self._state_key(chat_id))
        return value or "idle"

    async def set_state(self, chat_id: str, state: str) -> None:
        """Set rhe state for chat_id with TTL refresh."""
        await self._redis.setex(self._state_key(chat_id), _TTL, state)

    async def clear(self, chat_id: str) -> None:
        """Delete all RAG session keys for chat_id (return to idle)."""
        pipe = self._redis.pipeline()
        pipe.delete(self._state_key(chat_id))
        pipe.delete(self._doc_data_key(chat_id))
        pipe.delete(self._doc_name_key(chat_id))
        await pipe.execute()

    # ------------------------------------------------------------------
    # Pending document storage (bytes stored as-is, Redis supports binary)
    # ------------------------------------------------------------------

    async def set_pending_doc(
        self,
        chat_id: str,
        filename: str,
        data: bytes,
    ) -> None:
        """
        Store the pending document bytes and filename temporarily in Redis.
        Data is base64-encoded so the shared decode_responses=True client works.
        Limited to 10 MB to avoid Redis memory issues.
        """
        if len(data) > 10 * 1024 * 1024:
            raise ValueError("Document too large for temporary storage (max 10 MB).")
        b64 = base64.b64encode(data).decode("ascii")
        pipe = self._redis.pipeline()
        pipe.setex(self._doc_data_key(chat_id), _TTL, b64)
        pipe.setex(self._doc_name_key(chat_id), _TTL, filename)
        await pipe.execute()

    async def get_pending_doc(self, chat_id: str) -> Optional[tuple[str, bytes]]:
        """Retrieve the pending document (filename, bytes) or None if not set."""
        b64 = await self._redis.get(self._doc_data_key(chat_id))
        name = await self._redis.get(self._doc_name_key(chat_id))
        if b64 is None or name is None:
            return None
        try:
            data = base64.b64decode(b64)
        except Exception:
            # Corrupted or legacy binary data — clear and treat as expired
            logger.warning("Corrupted RAG doc data for chat_id=%s — clearing session", chat_id)
            await self.clear(chat_id)
            return None
        return (name if isinstance(name, str) else name.decode(), data)
