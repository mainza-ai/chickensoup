"""
Lightweight circuit breaker for LLM provider calls.

Tracks consecutive failures and opens the circuit after threshold,
rejecting calls immediately for a cooldown period.
"""
import time
import logging
from threading import Lock
from typing import Optional

logger = logging.getLogger("chickensoup.circuit_breaker")


class CircuitBreaker:
    def __init__(
        self,
        name: str,
        failure_threshold: int = None,
        recovery_timeout: float = None,
    ):
        self.name = name
        self.failure_threshold = failure_threshold or 5
        self.recovery_timeout = recovery_timeout or 60.0
        self._failure_count = 0
        self._last_failure_time: Optional[float] = None
        self._state = "closed"  # closed | open | half-open
        self._lock = Lock()

    def _is_open(self) -> bool:
        with self._lock:
            if self._state == "closed":
                return False
            if self._state == "open":
                if self._last_failure_time and (time.time() - self._last_failure_time) >= self.recovery_timeout:
                    self._state = "half-open"
                    logger.info(f"Circuit breaker '{self.name}' entering half-open state")
                    return False
                return True
            # half-open: allow one through
            return False

    def record_success(self) -> None:
        with self._lock:
            if self._state == "half-open":
                logger.info(f"Circuit breaker '{self.name}' closed after successful probe")
            self._failure_count = 0
            self._state = "closed"

    def record_failure(self) -> None:
        with self._lock:
            self._failure_count += 1
            self._last_failure_time = time.time()
            if self._failure_count >= self.failure_threshold:
                self._state = "open"
                logger.warning(
                    f"Circuit breaker '{self.name}' OPENED after {self._failure_count} failures. "
                    f"Will retry in {self.recovery_timeout}s."
                )

    def call(self, func, *args, **kwargs):
        """Execute func(*args, **kwargs) through the circuit breaker."""
        if self._is_open():
            raise RuntimeError(f"Circuit breaker '{self.name}' is open. LLM provider temporarily unavailable.")
        try:
            result = func(*args, **kwargs)
            self.record_success()
            return result
        except Exception as e:
            self.record_failure()
            raise


# Global circuit breaker instance for LLM calls
llm_circuit_breaker = CircuitBreaker(
    name="llm_provider",
    failure_threshold=5,
    recovery_timeout=60.0,
)
