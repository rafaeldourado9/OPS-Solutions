"""
ActivityTracker — Redis-backed tracker for last-seen timestamps per chat_id.

Used by the proactive scheduler to detect inactivity and send motivational messages.
"""

from __future__ import annotations

import logging
import time
from typing import Optional

from redis.asyncio import Redis

logger = logging.getLogger(__name__)

_PREFIX = "activity"
_TTL = 60 * 60 * 24 * 90  # 90 days


class ActivityTracker:
    """
    Tracks when each chat_id last sent a message to an agent.

    Keys: activity:{agent_id}:{chat_id} = unix timestamp (string)
    """

    def __init__(self, redis: Redis, agent_id: str) -> None:
        self._redis = redis
        self._agent_id = agent_id

    def _key(self, chat_id: str) -> str:
        return f"{_PREFIX}:{self._agent_id}:{chat_id}"

    async def touch(self, chat_id: str) -> None:
        """Record that chat_id just sent a message (update last-seen timestamp)."""
        await self._redis.setex(self._key(chat_id), _TTL, str(time.time()))

    async def last_seen(self, chat_id: str) -> Optional[float]:
        """Return Unix timestamp of last activity for chat_id, or None if never seen."""
        value = await self._redis.get(self._key(chat_id))
        if value is None:
            return None
        try:
            return float(value)
        except (ValueError, TypeError):
            return None

    async def seconds_since_last_activity(self, chat_id: str) -> Optional[float]:
        """Return seconds since last activity, or None if chat_id never interacted."""
        ts = await self.last_seen(chat_id)
        if ts is None:
            return None
        return time.time() - ts

    async def get_all_tracked_chats(self) -> list[str]:
        """Return all chat_ids tracked for this agent."""
        pattern = f"{_PREFIX}:{self._agent_id}:*"
        keys = []
        async for key in self._redis.scan_iter(pattern):
            suffix = key[len(f"{_PREFIX}:{self._agent_id}:"):]
            if suffix:
                keys.append(suffix)
        return keys
