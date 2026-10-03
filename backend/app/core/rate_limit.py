from collections import defaultdict, deque
from threading import Lock
from time import monotonic

from fastapi import HTTPException, Request, status

from app.core.config import get_settings

settings = get_settings()
_attempts: dict[str, deque[float]] = defaultdict(deque)
_lock = Lock()


def rate_limit(request: Request) -> None:
    key = f"{request.client.host if request.client else 'unknown'}:{request.url.path}"
    now = monotonic()
    with _lock:
        attempts = _attempts[key]
        while attempts and now - attempts[0] >= settings.auth_rate_window_seconds:
            attempts.popleft()
        if len(attempts) >= settings.auth_rate_limit:
            raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Too many requests")
        attempts.append(now)
