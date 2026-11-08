"""A small sliding-window rate limiter used as a FastAPI dependency.

Counts are kept in memory, which is fine for a single server process. Running
several processes would need a shared store such as Redis.
"""

import math
import threading
import time
from collections import defaultdict, deque
from collections.abc import Callable

from fastapi import HTTPException, Request, status

from app.config import settings
from app.security import CurrentUser


class RateLimiter:
    def __init__(self) -> None:
        self._hits: dict[str, deque[float]] = defaultdict(deque)
        self._lock = threading.Lock()

    def hit(self, key: str, limit: int, window_seconds: int) -> float | None:
        """Record a request. Returns None if allowed, otherwise seconds until a retry is allowed."""
        now = time.monotonic()
        with self._lock:
            hits = self._hits[key]
            while hits and hits[0] <= now - window_seconds:
                hits.popleft()
            if len(hits) >= limit:
                return hits[0] + window_seconds - now
            hits.append(now)
            return None

    def reset(self) -> None:
        with self._lock:
            self._hits.clear()


limiter = RateLimiter()


def _check(key: str, limit: int, window_seconds: int) -> None:
    retry_after = limiter.hit(key, limit, window_seconds)
    if retry_after is not None:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many requests. Please wait a moment and try again.",
            headers={"Retry-After": str(math.ceil(retry_after))},
        )


def limit_per_user(name: str, limit: Callable[[], int], window_seconds: int):
    """Dependency: limit a logged-in user's requests to an endpoint group."""

    def dependency(user: CurrentUser) -> None:
        _check(f"{name}:user:{user.id}", limit(), window_seconds)

    return dependency


def limit_per_ip(name: str, limit: Callable[[], int], window_seconds: int):
    """Dependency: limit requests from one IP address to an endpoint group."""

    def dependency(request: Request) -> None:
        ip = request.client.host if request.client else "unknown"
        _check(f"{name}:ip:{ip}", limit(), window_seconds)

    return dependency


chat_limit = limit_per_user("chat", lambda: settings.chat_requests_per_minute, 60)
upload_limit = limit_per_user("upload", lambda: settings.uploads_per_hour, 3600)
login_limit = limit_per_ip("login", lambda: settings.login_attempts_per_minute, 60)
signup_limit = limit_per_ip("signup", lambda: settings.signups_per_hour, 3600)
