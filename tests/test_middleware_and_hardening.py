"""
Tests for P0-1 production hardening:
- Rate limiting middleware
- Request ID middleware
- Request size limit middleware
- /health endpoint
- Circuit breaker
"""
import time

import pytest
import requests

from src.rate_limiter import RateLimiter
from src.llm_circuit_breaker import CircuitBreaker

BASE = "http://localhost:8000"
HEADERS = {"Content-Type": "application/json", "X-Api-Key": "dev"}


# ---------------------------------------------------------------------------
# Rate limiter unit tests
# ---------------------------------------------------------------------------

class TestRateLimiter:
    """Unit tests for the sliding window rate limiter."""

    @pytest.fixture(autouse=True)
    def _fresh_limiter(self):
        from src.rate_limiter import rate_limiter
        old_limit = rate_limiter._windows.copy()
        old_key_limit = rate_limiter._api_key_windows.copy()
        yield
        rate_limiter._windows = old_limit
        rate_limiter._api_key_windows = old_key_limit

    @pytest.fixture
    def limiter(self):
        return RateLimiter()

    def test_ip_allowed_under_limit(self, limiter):
        for _ in range(20):
            allowed, remaining = limiter.check_ip("192.168.1.1")
        assert allowed is True

    def test_ip_blocked_over_limit(self, limiter):
        for _ in range(20):
            limiter.check_ip("192.168.1.2")
        allowed, _ = limiter.check_ip("192.168.1.2")
        assert allowed is False

    def test_api_key_burst_allowed_under_limit(self, limiter):
        for _ in range(5):
            allowed, remaining = limiter.check_api_key("test-key")
        assert allowed is True

    def test_api_key_burst_blocked_over_limit(self, limiter):
        for _ in range(5):
            limiter.check_api_key("test-key-2")
        allowed, _ = limiter.check_api_key("test-key-2")
        assert allowed is False

    def test_different_keys_independent(self, limiter):
        for _ in range(5):
            limiter.check_api_key("key-a")
        allowed, _ = limiter.check_api_key("key-b")
        assert allowed is True


# ---------------------------------------------------------------------------
# Circuit breaker unit tests
# ---------------------------------------------------------------------------

class TestCircuitBreaker:
    """Unit tests for the LLM circuit breaker."""

    def test_closed_state_allows_calls(self):
        cb = CircuitBreaker("test", failure_threshold=3, recovery_timeout=1.0)
        result = cb.call(lambda: 42)
        assert result == 42

    def test_opens_after_threshold_failures(self):
        cb = CircuitBreaker("test", failure_threshold=3, recovery_timeout=1.0)

        def fail():
            raise RuntimeError("fail")

        for _ in range(2):
            with pytest.raises(RuntimeError):
                cb.call(fail)

        # Third failure should open the circuit
        with pytest.raises(RuntimeError):
            cb.call(fail)

        # Fourth call should be rejected by circuit breaker (not reaching the function)
        with pytest.raises(RuntimeError, match="Circuit breaker"):
            cb.call(fail)

    def test_records_success(self):
        cb = CircuitBreaker("test", failure_threshold=2, recovery_timeout=1.0)

        def fail_once():
            if cb._failure_count < 1:
                raise RuntimeError("fail")
            return "ok"

        # First call fails
        with pytest.raises(RuntimeError):
            cb.call(fail_once)
        # Second call succeeds
        result = cb.call(fail_once)
        assert result == "ok"
        # Circuit should be closed again
        assert cb._state == "closed"


# ---------------------------------------------------------------------------
# Middleware integration tests (live server)
# ---------------------------------------------------------------------------

@pytest.mark.skipif(
    not requests.get(f"{BASE}/status", timeout=3).ok,
    reason="Live server not available",
)
class TestMiddlewareLive:
    """Integration tests for middleware against live server."""

    def test_health_endpoint_returns_checks(self):
        response = requests.get(f"{BASE}/health", timeout=10)
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "checks" in data
        checks = data["checks"]
        assert "redis" in checks
        assert "neo4j" in checks
        assert "llm" in checks
        assert "disk" in checks

    def test_request_id_header_present(self):
        response = requests.get(f"{BASE}/status", headers=HEADERS, timeout=10)
        assert response.status_code == 200
        assert "X-Request-ID" in response.headers
        request_id = response.headers["X-Request-ID"]
        assert len(request_id) > 0

    def test_request_size_limit_rejects_large_body(self):
        large_body = {"query": "x" * 2_000_000}
        response = requests.post(
            f"{BASE}/query",
            json=large_body,
            headers=HEADERS,
            timeout=10,
        )
        assert response.status_code == 413
        assert "too large" in response.json()["detail"].lower()

    def test_normal_request_under_limit_succeeds(self):
        response = requests.post(
            f"{BASE}/query",
            json={"query": "What is Area 51?", "structured": False},
            headers=HEADERS,
            timeout=30,
        )
        assert response.status_code == 200
        assert "X-Request-ID" in response.headers
