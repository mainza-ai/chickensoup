"""
Simple in-memory rate limiter for FastAPI middleware.

Uses sliding window algorithm with differentiated limits per route category.
For multi-worker deployments, replace with Redis-backed implementation.
"""
import time
import threading
from collections import defaultdict, deque
from typing import Tuple

from src.config import settings


class RateLimiter:
    """Thread-safe sliding window rate limiter with per-category limits."""

    def __init__(self):
        self._lock = threading.Lock()
        self._windows: dict[str, deque] = defaultdict(deque)
        self._api_key_windows: dict[str, deque] = defaultdict(deque)

    CATEGORY_LIMITS = {
        "search": (60, 60),    # 60 req/min, 60s window
        "read": (30, 60),      # 30 req/min, 60s window
        "write": (10, 60),     # 10 req/min, 60s window
        "general": (20, 60),   # 20 req/min, 60s window (default)
    }

    CATEGORY_BURST = {
        "search": (20, 10),    # 20 req/10s burst
        "read": (10, 10),      # 10 req/10s burst
        "write": (3, 10),      # 3 req/10s burst
        "general": (5, 10),    # 5 req/10s burst (default)
    }

    def _clean_window(self, window: deque, now: float, window_seconds: int):
        while window and window[0] < now - window_seconds:
            window.popleft()

    def is_allowed(self, key: str, max_requests: int, window_seconds: int) -> Tuple[bool, int]:
        now = time.time()
        with self._lock:
            window = self._windows[key]
            self._clean_window(window, now, window_seconds)
            remaining = max(0, max_requests - len(window))
            allowed = len(window) < max_requests
            if allowed:
                window.append(now)
            return allowed, remaining

    def check_ip(self, client_ip: str, category: str = "general") -> Tuple[bool, int]:
        max_requests, window_seconds = self.CATEGORY_LIMITS.get(category, self.CATEGORY_LIMITS["general"])
        return self.is_allowed(f"ip:{client_ip}:{category}", max_requests, window_seconds)

    def check_api_key(self, api_key: str, category: str = "general") -> Tuple[bool, int]:
        max_requests, window_seconds = self.CATEGORY_BURST.get(category, self.CATEGORY_BURST["general"])
        return self.is_allowed(f"key:{api_key}:{category}", max_requests, window_seconds)


rate_limiter = RateLimiter()

