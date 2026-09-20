"""
security/rate_limiter.py — Per-IP Rate Limiting Middleware for Charaka IP.

Implements a sliding-window rate limiter using an in-memory store (Redis-ready).
Complies with OWASP API Security Top 10: API4 Unrestricted Resource Consumption.

Configuration (via environment variables):
  RATE_LIMIT_REQUESTS_PER_MINUTE : int  (default 30)  — max requests per IP per minute
  RATE_LIMIT_BURST                : int  (default 5)   — additional burst allowance
  RATE_LIMIT_WHITELIST            : str  (comma-separated IPs exempt from limiting)

Strategy:
  Sliding window counter. Each incoming IP is tracked in a dict:
    { ip_hash: deque([timestamp1, timestamp2, ...]) }
  Timestamps older than 60 seconds are evicted on each check.
  If count > limit, a 429 Too Many Requests response is raised.

Redis upgrade path:
  Replace the in-memory `_store` with a Redis ZADD/ZRANGEBYSCORE pipeline
  by swapping out `_SlidingWindowStore` for a `RedisSlidingWindowStore`.
"""

import os
import time
import threading
import hashlib
from collections import defaultdict, deque
from typing import Callable, Awaitable

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

# ── Configuration ──────────────────────────────────────────────────────────────

RATE_LIMIT_RPM: int = int(os.getenv("RATE_LIMIT_REQUESTS_PER_MINUTE", "30"))
RATE_LIMIT_BURST: int = int(os.getenv("RATE_LIMIT_BURST", "5"))
RATE_LIMIT_WINDOW_SECONDS: int = 60

_WHITELIST: set[str] = {
    ip.strip()
    for ip in os.getenv("RATE_LIMIT_WHITELIST", "127.0.0.1,::1").split(",")
    if ip.strip()
}

# ── In-Memory Sliding Window Store ─────────────────────────────────────────────

class _SlidingWindowStore:
    """
    Thread-safe in-memory sliding window counter.
    For production scale, swap with Redis ZSET implementation.
    """

    def __init__(self, window_seconds: int, limit: int):
        self._window = window_seconds
        self._limit = limit
        self._store: dict[str, deque] = defaultdict(deque)
        self._lock = threading.Lock()

    def is_allowed(self, key: str) -> tuple[bool, int, int]:
        """
        Check if the key is within its rate limit.
        Returns: (allowed, current_count, retry_after_seconds)
        """
        now = time.monotonic()
        cutoff = now - self._window

        with self._lock:
            q = self._store[key]

            # Evict timestamps outside the window
            while q and q[0] < cutoff:
                q.popleft()

            count = len(q)

            if count >= self._limit:
                # Calculate retry-after: time until oldest request exits window
                retry_after = int(self._window - (now - q[0])) + 1
                return False, count, retry_after

            # Record this request
            q.append(now)
            return True, count + 1, 0


_store = _SlidingWindowStore(
    window_seconds=RATE_LIMIT_WINDOW_SECONDS,
    limit=RATE_LIMIT_RPM + RATE_LIMIT_BURST,
)


# ── Helper functions ────────────────────────────────────────────────────────────

def _get_client_ip(request: Request) -> str:
    """Extract real client IP, respecting X-Forwarded-For for reverse proxies."""
    forwarded_for = request.headers.get("X-Forwarded-For", "")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    return request.client.host if request.client else "0.0.0.0"


def _hash_ip(ip: str) -> str:
    """Hash the IP for storage to avoid storing raw IPs in memory."""
    return hashlib.sha256(ip.encode()).hexdigest()[:16]


# ── Paths exempt from rate limiting ─────────────────────────────────────────────

_EXEMPT_PATHS = {"/health", "/api/localization/languages"}


# ── FastAPI Middleware ──────────────────────────────────────────────────────────

class RateLimiter(BaseHTTPMiddleware):
    """
    Starlette/FastAPI ASGI middleware implementing per-IP sliding-window rate limiting.
    Adds standard rate limit headers to all responses.
    """

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        # Exempt paths and whitelisted IPs
        if request.url.path in _EXEMPT_PATHS:
            return await call_next(request)

        client_ip = _get_client_ip(request)

        if client_ip in _WHITELIST:
            return await call_next(request)

        ip_key = _hash_ip(client_ip)
        allowed, count, retry_after = _store.is_allowed(ip_key)

        if not allowed:
            return JSONResponse(
                status_code=429,
                content={
                    "error": "Rate limit exceeded",
                    "detail": (
                        f"You have exceeded {RATE_LIMIT_RPM} requests per minute. "
                        f"Please wait {retry_after} seconds before retrying."
                    ),
                    "retry_after_seconds": retry_after,
                },
                headers={
                    "Retry-After": str(retry_after),
                    "X-RateLimit-Limit": str(RATE_LIMIT_RPM),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(int(time.time()) + retry_after),
                },
            )

        response = await call_next(request)

        remaining = max(0, (RATE_LIMIT_RPM + RATE_LIMIT_BURST) - count)
        response.headers["X-RateLimit-Limit"] = str(RATE_LIMIT_RPM)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(
            int(time.time()) + RATE_LIMIT_WINDOW_SECONDS
        )

        return response


# ── Standalone middleware function (for use with app.middleware decorator) ──────

async def rate_limit_middleware(request: Request, call_next) -> Response:
    """Functional middleware wrapper (alternative to class-based)."""
    limiter = RateLimiter(app=None)  # type: ignore[arg-type]
    return await limiter.dispatch(request, call_next)
