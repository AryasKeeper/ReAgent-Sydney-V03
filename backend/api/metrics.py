from fastapi import APIRouter, HTTPException
from typing import Dict, Any

from config import settings
from services.redis_store import redis_store

router = APIRouter()


@router.get("/metrics")
async def get_metrics() -> Dict[str, Any]:
    if not settings.DEBUG:
        raise HTTPException(status_code=403, detail="Metrics available in DEBUG mode only")

    r = await redis_store.connect()
    out: Dict[str, Any] = {"counters": {}, "latency": {}}
    # Counters
    async for key in r.scan_iter(match="m:cnt:*", count=100):
        name = key.split(":", 2)[-1]
        try:
            out["counters"][name] = int(await r.get(key) or 0)
        except Exception:
            out["counters"][name] = 0
    # Latency samples (last up to 10)
    async for key in r.scan_iter(match="m:lat:*", count=100):
        name = key.split(":", 2)[-1]
        try:
            samples = await r.lrange(key, 0, 9)
            out["latency"][name] = [float(x) for x in samples]
        except Exception:
            out["latency"][name] = []
    return out


