"""
Redis client — async connection pool, MessageDebouncer, and keyspace
notification listener for debounce expiry events.
"""

from __future__ import annotations

import json
import logging
import os
from typing import Callable, Awaitable, Optional

import redis.asyncio as aioredis
from redis.asyncio import Redis

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Connection
# ---------------------------------------------------------------------------

_pool: Optional[aioredis.ConnectionPool] = None
_client: Optional[Redis] = None


def _redis_url() -> str:
    return os.environ.get("REDIS_URL", "redis://localhost:6379/0")


async def get_redis() -> Redis:
    """Return the shared async Redis client, initialising it on first call."""
    global _pool, _client
    if _client is None:
        _pool = aioredis.ConnectionPool.from_url(
            _redis_url(),
            max_connections=20,
            decode_responses=True,
        )
        _client = aioredis.Redis(connection_pool=_pool)
    return _client


async def close_redis() -> None:
    """Close the shared Redis connection pool."""
    global _pool, _client
    if _client is not None:
        await _client.aclose()
        _client = None
    if _pool is not None:
        await _pool.aclose()
        _pool = None


# ---------------------------------------------------------------------------
# MessageDebouncer
# ---------------------------------------------------------------------------

class MessageDebouncer:
    """
    Manages the per-chat message buffer and debounce timer in Redis.

    Keys used (with optional namespace prefix for multi-agent isolation):
      buffer:{[ns:]}chat_id      — Redis list of raw message JSON strings
      debounce:{[ns:]}chat_id    — Volatile key used as debounce timer
      active_task:{[ns:]}chat_id — Stores the currently active task ID

    The namespace is typically the agent_id when running multiple agents
    in the same process.  Omitting it keeps the original single-agent behaviour.
    """

    BUFFER_PREFIX = "buffer"
    DEBOUNCE_PREFIX = "debounce"
    ACTIVE_TASK_PREFIX = "active_task"
    PROCESSING_PREFIX = "processing"

    def __init__(
        self,
        redis_client: Redis,
        debounce_seconds: float = 2.5,
        namespace: str = "",
    ):
        self._redis = redis_client
        self._debounce_seconds = debounce_seconds
        self._ns = namespace  # agent_id or "" for single-agent mode

    def _k(self, prefix: str, chat_id: str) -> str:
        """Build a namespaced Redis key."""
        if self._ns:
            return f"{prefix}:{self._ns}:{chat_id}"
        return f"{prefix}:{chat_id}"

    # ------------------------------------------------------------------
    # Buffer management
    # ------------------------------------------------------------------

    async def push_message(self, chat_id: str, message_json: str) -> None:
        """
        Append a raw message JSON string to the buffer and reset the
        debounce timer.  When the timer expires Redis fires a keyspace
        notification that the worker listens to.
        
        If a task is currently processing this chat, mark it as superseded
        so it stops sending messages.
        """
        buffer_key = self._k(self.BUFFER_PREFIX, chat_id)
        debounce_key = self._k(self.DEBOUNCE_PREFIX, chat_id)

        # If there's an active task, it will be superseded by the new one
        # (the task checks is_task_active before sending each message part)
        
        pipe = self._redis.pipeline()
        pipe.rpush(buffer_key, message_json)
        # The debounce key value is irrelevant — only the expiry event matters.
        # Use int ceiling to satisfy Redis SETEX requirement (integer seconds).
        ttl_seconds = max(1, int(self._debounce_seconds + 0.5))
        pipe.setex(debounce_key, ttl_seconds, "1")
        await pipe.execute()

    async def get_and_clear_buffer(self, chat_id: str) -> list[str]:
        """
        Atomically drain and return all messages from the buffer.

        Uses a Lua script so no messages are lost between LRANGE and DEL
        even under concurrent access.
        """
        buffer_key = self._k(self.BUFFER_PREFIX, chat_id)
        lua_script = """
            local msgs = redis.call('LRANGE', KEYS[1], 0, -1)
            redis.call('DEL', KEYS[1])
            return msgs
        """
        result = await self._redis.eval(lua_script, 1, buffer_key)
        return result if result else []

    # ------------------------------------------------------------------
    # Active task tracking
    # ------------------------------------------------------------------

    async def set_active_task(self, chat_id: str, task_id: str) -> None:
        """Mark task_id as the currently active processing task for chat_id."""
        key = self._k(self.ACTIVE_TASK_PREFIX, chat_id)
        # Keep alive for 5 minutes as a safety TTL.
        await self._redis.setex(key, 300, task_id)

    async def get_active_task(self, chat_id: str) -> Optional[str]:
        """Return the currently active task_id for chat_id, or None."""
        key = self._k(self.ACTIVE_TASK_PREFIX, chat_id)
        return await self._redis.get(key)

    async def is_task_active(self, chat_id: str, task_id: str) -> bool:
        """Return True if task_id is still the active task for chat_id."""
        current = await self.get_active_task(chat_id)
        return current == task_id

    # ------------------------------------------------------------------
    # Processing lock — prevents overlapping responses for the same chat
    # ------------------------------------------------------------------

    async def set_processing(self, chat_id: str, ttl: int = 60) -> None:
        """Mark this chat as currently being processed by an agent task."""
        key = self._k(self.PROCESSING_PREFIX, chat_id)
        await self._redis.setex(key, ttl, "1")

    async def clear_processing(self, chat_id: str) -> None:
        """Release the processing lock for this chat."""
        key = self._k(self.PROCESSING_PREFIX, chat_id)
        await self._redis.delete(key)

    async def is_processing(self, chat_id: str) -> bool:
        """Return True if an agent task is currently processing this chat."""
        key = self._k(self.PROCESSING_PREFIX, chat_id)
        return bool(await self._redis.exists(key))

    async def requeue_messages(self, chat_id: str, raw_messages: list[str]) -> None:
        """Push messages back to the buffer and reset the debounce timer.

        Used when a new debounce fires while a task is still processing,
        so the messages are not lost and will be retried after the lock clears.
        """
        buffer_key = self._k(self.BUFFER_PREFIX, chat_id)
        debounce_key = self._k(self.DEBOUNCE_PREFIX, chat_id)
        ttl_seconds = max(1, int(self._debounce_seconds + 0.5))

        pipe = self._redis.pipeline()
        for msg in raw_messages:
            pipe.rpush(buffer_key, msg)
        pipe.setex(debounce_key, ttl_seconds, "1")
        await pipe.execute()

    @property
    def namespace(self) -> str:
        """Return the namespace (agent_id) this debouncer is scoped to."""
        return self._ns


# ---------------------------------------------------------------------------
# Keyspace notification listener
# ---------------------------------------------------------------------------

ExpiredCallback = Callable[[str], Awaitable[None]]


async def listen_for_expired_keys(
    callback: ExpiredCallback,
    pattern: str = "__keyevent@0__:expired",
    redis_url: Optional[str] = None,
) -> None:
    """
    Subscribe to Redis keyspace expiry notifications on a dedicated connection
    and call ``callback(key)`` whenever a key expires.

    This coroutine runs indefinitely; wrap it in an asyncio.Task.

    The Redis server must be configured with::

        notify-keyspace-events KEA

    which is done via the ``command`` directive in docker-compose.yml.

    Args:
        callback: Async callable that receives the expired key name.
        pattern: Pub/Sub pattern to subscribe to.
        redis_url: Override the REDIS_URL env var.
    """
    url = redis_url or _redis_url()
    # Use a separate connection so we don't block the main pool.
    listener_client = aioredis.from_url(url, decode_responses=True)

    try:
        pubsub = listener_client.pubsub()
        await pubsub.psubscribe(pattern)
        logger.info("Redis keyspace listener started — pattern: %s", pattern)

        async for message in pubsub.listen():
            if message is None:
                continue
            if message.get("type") not in ("pmessage", "message"):
                continue
            key: str = message.get("data", "")
            if not key:
                continue
            try:
                await callback(key)
            except Exception:
                logger.exception("Error in expired-key callback for key '%s'", key)
    finally:
        await pubsub.close()
        await listener_client.aclose()
