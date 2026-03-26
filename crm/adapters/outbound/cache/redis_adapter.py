from typing import Optional

import redis.asyncio as aioredis

from core.ports.outbound.cache_port import CachePort
from infrastructure.config import settings


class RedisCacheAdapter(CachePort):

    def __init__(self, url: str | None = None) -> None:
        self._url = url or settings.redis_url
        self._redis: Optional[aioredis.Redis] = None

    async def _get_redis(self) -> aioredis.Redis:
        if self._redis is None:
            self._redis = aioredis.from_url(self._url, decode_responses=True)
        return self._redis

    async def get(self, key: str) -> Optional[str]:
        r = await self._get_redis()
        return await r.get(key)

    async def set(self, key: str, value: str, ttl_seconds: int = 0) -> None:
        r = await self._get_redis()
        if ttl_seconds > 0:
            await r.setex(key, ttl_seconds, value)
        else:
            await r.set(key, value)

    async def delete(self, key: str) -> None:
        r = await self._get_redis()
        await r.delete(key)

    async def exists(self, key: str) -> bool:
        r = await self._get_redis()
        return bool(await r.exists(key))

    async def close(self) -> None:
        if self._redis:
            await self._redis.aclose()
            self._redis = None
