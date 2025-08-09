import time
from typing import Optional

try:
    from services.redis_store import redis_store
except Exception:  # pragma: no cover
    redis_store = None  # type: ignore


async def incr_counter(name: str, by: int = 1) -> None:
    if not redis_store:
        return
    try:
        await redis_store.incr(f"m:cnt:{name}", ttl_seconds=3600)
    except Exception:
        pass


async def record_latency(name: str, ms: float) -> None:
    if not redis_store:
        return
    try:
        # Keep last 100 samples in a Redis list
        key = f"m:lat:{name}"
        r = await redis_store.connect()
        await r.lpush(key, f"{ms:.1f}")
        await r.ltrim(key, 0, 99)
        await r.expire(key, 3600)
    except Exception:
        pass


class Stopwatch:
    def __init__(self, name: str):
        self.name = name
        self._t0: Optional[float] = None

    def start(self):
        self._t0 = time.perf_counter()
        return self

    async def stop(self):
        if self._t0 is None:
            return
        ms = (time.perf_counter() - self._t0) * 1000.0
        await record_latency(self.name, ms)


