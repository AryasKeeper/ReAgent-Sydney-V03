import httpx
from typing import Optional, List, Dict
from config import settings
from services.http_utils import fetch_with_retries, CircuitBreaker


class BraveSearchService:
    base_url = "https://api.search.brave.com/res/v1/web/search"

    async def search(self, query: str, count: int = 5) -> Optional[Dict]:
        if not getattr(settings, "BRAVE_API_KEY", None):
            return None
        headers = {"X-Subscription-Token": settings.BRAVE_API_KEY}
        params = {"q": query, "count": count, "safesearch": "moderate"}
        breaker = CircuitBreaker()
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await fetch_with_retries(
                lambda: client.get(self.base_url, headers=headers, params=params),
                retries=2,
                base_delay=0.5,
                breaker=breaker,
            )
            if resp.status_code == 200:
                return resp.json()
            return None

    async def search_cached(self, query: str, count: int = 5, *, cache_key: str) -> Optional[Dict]:
        """Try Redis cache, then perform search."""
        try:
            from services.redis_store import redis_store
            cached = await redis_store.get_json(cache_key)
            if cached:
                import json
                return json.loads(cached)
            result = await self.search(query, count)
            if result:
                import json
                await redis_store.set_json(cache_key, json.dumps(result), ttl_seconds=3600)
            return result
        except Exception:
            return await self.search(query, count)

    def extract_urls(self, data: Dict, limit: int = 3) -> List[str]:
        urls: List[str] = []
        for item in (data.get("web", {}).get("results", []) or []):
            u = item.get("url")
            if u:
                urls.append(u)
            if len(urls) >= limit:
                break
        return urls


brave_search = BraveSearchService()


