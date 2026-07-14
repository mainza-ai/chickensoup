"""
Simple in-memory rate limiter for FastAPI middleware.

Uses sliding window algorithm. For multi-worker deployments, replace
with Redis-backed implementation.
"""
import time
import threading
from collections import defaultdict, deque
from typing import Tuple

from src.config import settings


class RateLimiter:
    """Thread-safe sliding window rate limiter."""

    def __init__(self):
        self._lock = threading.Lock()
        self._windows: dict[str, deque] = defaultdict(deque)
        self._api_key_windows: dict[str, deque] = defaultdict(deque)

    def _clean_window(self, window: deque, now: float, window_seconds: int):
        while window and window[0] < now - window_seconds:
            window.popleft()

    def is_allowed(self, key: str, max_requests: int, window_seconds: int) -> Tuple[bool, int]:
        """Check if request is allowed. Returns (allowed, remaining)."""
        now = time.time()
        with self._lock:
            window = self._windows[key]
            self._clean_window(window, now, window_seconds)
            remaining = max(0, max_requests - len(window))
            allowed = len(window) < max_requests
            if allowed:
                window.append(now)
            return allowed, remaining

    def check_ip(self, client_ip: str) -> Tuple[bool, int]:
        """Per-IP rate limit: 20 requests/minute."""
        max_requests = settings.REQUEST_RATE_LIMIT_PER_MINUTE
        window_seconds = 60
        return self.is_allowed(f"ip:{client_ip}", max_requests, window_seconds)

    def check_api_key(self, api_key: str) -> Tuple[bool, int]:
        """Per-API-key burst limit: 5 requests in 10 seconds."""
        max_requests = settings.REQUEST_RATE_LIMIT_BURST
        window_seconds = 10
        return self.is_allowed(f"key:{api_key}", max_requests, window_seconds)


# Global rate limiter instance
rate_limiter = RateLimiter()
