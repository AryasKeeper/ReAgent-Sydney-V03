import asyncio
import time
from typing import Callable, Awaitable, Optional, Tuple

import httpx


class CircuitBreaker:
    """Simple async circuit breaker for external HTTP calls."""

    def __init__(self, *, failure_threshold: int = 5, reset_seconds: int = 30):
        self.failure_threshold = failure_threshold
        self.reset_seconds = reset_seconds
        self._failures = 0
        self._opened_at: Optional[float] = None

    def is_open(self) -> bool:
        if self._opened_at is None:
            return False
        if (time.time() - self._opened_at) > self.reset_seconds:
            # Half-open: allow a trial
            return False
        return True

    def record_success(self) -> None:
        self._failures = 0
        self._opened_at = None

    def record_failure(self) -> None:
        self._failures += 1
        if self._failures >= self.failure_threshold:
            self._opened_at = time.time()


async def fetch_with_retries(
    request_fn: Callable[[], Awaitable[httpx.Response]],
    *,
    retries: int = 2,
    base_delay: float = 0.5,
    breaker: Optional[CircuitBreaker] = None,
) -> httpx.Response:
    if breaker and breaker.is_open():
        raise httpx.ConnectError("circuit_open")

    attempt = 0
    last_exc: Optional[Exception] = None
    while attempt <= retries:
        try:
            resp = await request_fn()
            if breaker:
                breaker.record_success()
            return resp
        except Exception as e:  # noqa: BLE001 broad to guard external calls
            last_exc = e
            if breaker:
                breaker.record_failure()
            if attempt == retries:
                break
            await asyncio.sleep(base_delay * (2 ** attempt))
            attempt += 1
    assert last_exc is not None
    raise last_exc


