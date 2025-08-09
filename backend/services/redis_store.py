import os
import asyncio
from typing import Optional

import aioredis


class RedisStore:
    def __init__(self, url: Optional[str] = None):
        self.url = url or os.getenv("REDIS_URL", "redis://localhost:6379/0")
        self._pool: Optional[aioredis.Redis] = None

    async def connect(self):
        if self._pool is None:
            self._pool = await aioredis.from_url(self.url, encoding="utf-8", decode_responses=True)
        return self._pool

    async def close(self):
        if self._pool is not None:
            await self._pool.close()
            self._pool = None

    async def get_json(self, key: str) -> Optional[str]:
        r = await self.connect()
        return await r.get(key)

    async def set_json(self, key: str, value: str, ttl_seconds: int):
        r = await self.connect()
        await r.set(key, value, ex=ttl_seconds)

    async def incr(self, key: str, ttl_seconds: int) -> int:
        r = await self.connect()
        val = await r.incr(key)
        if val == 1:
            await r.expire(key, ttl_seconds)
        return val


redis_store = RedisStore()


