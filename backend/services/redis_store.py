import os
import asyncio
from typing import Optional
import logging

logger = logging.getLogger(__name__)

# Try to import aioredis, but make it optional
try:
    import aioredis
    REDIS_AVAILABLE = True
except (ImportError, TypeError) as e:
    logger.warning(f"Redis not available: {e}. Using mock redis store.")
    REDIS_AVAILABLE = False
    aioredis = None


class RedisStore:
    def __init__(self, url: Optional[str] = None):
        self.url = url or os.getenv("REDIS_URL", "redis://localhost:6379/0")
        self._pool: Optional[aioredis.Redis] = None

    async def connect(self):
        if not REDIS_AVAILABLE:
            return None
        if self._pool is None:
            try:
                self._pool = await aioredis.from_url(self.url, encoding="utf-8", decode_responses=True)
            except Exception as e:
                logger.warning(f"Failed to connect to Redis: {e}")
                return None
        return self._pool

    async def close(self):
        if self._pool is not None:
            await self._pool.close()
            self._pool = None

    async def get_json(self, key: str) -> Optional[str]:
        if not REDIS_AVAILABLE:
            return None
        try:
            r = await self.connect()
            if r:
                return await r.get(key)
        except Exception as e:
            logger.debug(f"Redis get failed: {e}")
        return None

    async def set_json(self, key: str, value: str, ttl_seconds: int):
        if not REDIS_AVAILABLE:
            return
        try:
            r = await self.connect()
            if r:
                await r.set(key, value, ex=ttl_seconds)
        except Exception as e:
            logger.debug(f"Redis set failed: {e}")

    async def incr(self, key: str, ttl_seconds: int) -> int:
        if not REDIS_AVAILABLE:
            return 1  # Mock behavior
        try:
            r = await self.connect()
            if r:
                val = await r.incr(key)
                if val == 1:
                    await r.expire(key, ttl_seconds)
                return val
        except Exception as e:
            logger.debug(f"Redis incr failed: {e}")
        return 1  # Mock behavior


redis_store = RedisStore()


