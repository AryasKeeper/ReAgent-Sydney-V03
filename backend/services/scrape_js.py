import httpx
from typing import Optional
from config import settings
from services.http_utils import fetch_with_retries, CircuitBreaker


class JSRenderer:
    base_url = "https://chrome.browserless.io/content"

    async def fetch_content(self, url: str) -> Optional[str]:
        token = getattr(settings, "BROWSERLESS_TOKEN", None)
        if not token:
            return None
        params = {
            "token": token,
            "url": url,
            "gotoOptions": {"waitUntil": "domcontentloaded"},
        }
        breaker = CircuitBreaker()
        async with httpx.AsyncClient(timeout=20.0) as client:
            resp = await fetch_with_retries(
                lambda: client.get(self.base_url, params=params),
                retries=2,
                base_delay=0.5,
                breaker=breaker,
            )
            if resp.status_code == 200:
                return resp.text
            return None


js_renderer = JSRenderer()


