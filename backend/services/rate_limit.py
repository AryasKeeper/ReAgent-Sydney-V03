from typing import Tuple

from services.redis_store import redis_store


async def check_rate_limit(identifier: str, *, limit: int = 60, window_seconds: int = 60) -> Tuple[bool, int]:
    """Increment a counter for `identifier` and return (allowed, remaining).

    If Redis is unavailable, allow by default (fail-open) to avoid blocking.
    """
    try:
        key = f"rl:{identifier}:{window_seconds}"
        count = await redis_store.incr(key, ttl_seconds=window_seconds)
        remaining = max(0, limit - count)
        return (count <= limit), remaining
    except Exception:
        return True, limit


