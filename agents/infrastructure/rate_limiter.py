"""
Redis-based rate limiter (fixed window counter).

Limits the number of messages processed per chat_id within a time window.
Used to protect against flood attacks and runaway clients.

Usage:
    limiter = RateLimiter(redis, max_messages=10, window_seconds=60)
    if not await limiter.is_allowed("5511@c.us"):
        return  # flood detected — skip processing
"""

from __future__ import annotations

import logging
from typing import Optional

from redis.asyncio import Redis

logger = logging.getLogger(__name__)

_KEY_PREFIX = "rate"


class RateLimiter:
    """
    Fixed-window rate limiter backed by Redis.

    Args:
        redis:          Async Redis client.
        max_messages:   Maximum messages allowed per window per chat_id.
        window_seconds: Duration of the counting window in seconds.
    """

    def __init__(
        self,
        redis: Redis,
        max_messages: int = 20,
        window_seconds: int = 60,
    ) -> None:
        self._redis = redis
        self._max = max_messages
        self._window = window_seconds

    async def is_allowed(self, chat_id: str) -> bool:
        """
        Return True if the chat_id is within rate limits, False if throttled.

        Uses a Redis counter with auto-expiry.  The first request in each window
        sets the TTL; subsequent requests increment the counter.
        """
        key = f"{_KEY_PREFIX}:{chat_id}"
        try:
            count = await self._redis.incr(key)
            if count == 1:
                # First message in this window — set TTL
                await self._redis.expire(key, self._window)
            if count > self._max:
                logger.warning(
                    "Rate limit exceeded for chat_id=%s: %d/%d messages in %ds window",
                    chat_id,
                    count,
                    self._max,
                    self._window,
                )
                return False
            return True
        except Exception:
            # If Redis is unavailable, fail open (allow the request)
            logger.exception("Rate limiter Redis error for chat_id=%s — allowing", chat_id)
            return True

    async def get_count(self, chat_id: str) -> int:
        """Return the current message count for a chat_id (0 if not set)."""
        key = f"{_KEY_PREFIX}:{chat_id}"
        try:
            value = await self._redis.get(key)
            return int(value) if value else 0
        except Exception:
            return 0

    async def reset(self, chat_id: str) -> None:
        """Delete the rate limit counter for a chat_id (for testing/admin)."""
        key = f"{_KEY_PREFIX}:{chat_id}"
        await self._redis.delete(key)
