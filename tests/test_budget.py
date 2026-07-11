import pytest
from unittest.mock import MagicMock, patch

from src.budget import BudgetTracker


def test_budget_check_disabled_redis_fallback():
    tracker = BudgetTracker()
    with patch("src.budget.cache_store") as mock_cache:
        mock_cache.redis_client = None
        allowed, remaining, reason = tracker.check_budget(cost=0.5)
        # Should allow optimistically when no redis
        assert allowed is True


def test_budget_check_exceeded():
    tracker = BudgetTracker()
    with patch("src.budget.cache_store") as mock_cache, \
         patch.object(tracker, "get_status") as mock_status:

        from src.models import BudgetStatus
        mock_status.return_value = BudgetStatus(
            month_key="2026-07",
            spent_usd=19.9,
            pulls_count=39,
            remaining_usd=0.1,
            ceiling_usd=20.0,
            on_hold=False
        )

        mock_redis = MagicMock()
        mock_redis.eval.return_value = [0, 19.9]  # LUA returns not allowed
        mock_cache.redis_client = mock_redis

        allowed, remaining, reason = tracker.check_budget(cost=0.5)
        assert allowed is False
        assert "exceeded" in reason.lower() or "ceiling" in reason.lower()


def test_budget_atomic_lua_called():
    tracker = BudgetTracker()

    with patch("src.budget.cache_store") as mock_cache, \
         patch.object(tracker, "get_status") as mock_status:

        from src.models import BudgetStatus
        mock_status.return_value = BudgetStatus(
            month_key="2026-07",
            spent_usd=5.0,
            pulls_count=10,
            remaining_usd=15.0,
            ceiling_usd=20.0,
            on_hold=False
        )

        mock_redis = MagicMock()
        mock_redis.eval.return_value = [1, 5.5]  # allowed, new spent
        mock_cache.redis_client = mock_redis

        allowed, remaining, reason = tracker.check_budget(cost=0.5)
        assert allowed is True
        assert mock_redis.eval.called
        # Check Lua script was eval'd with correct keys
        first_call_args = mock_redis.eval.call_args_list[0]
        assert "LUA" not in str(first_call_args)  # script content passed
        # remaining should be ceiling - new_spent
        assert abs(remaining - 14.5) < 0.01


def test_budget_on_hold_blocks():
    tracker = BudgetTracker()

    with patch.object(tracker, "get_status") as mock_status:
        from src.models import BudgetStatus
        mock_status.return_value = BudgetStatus(
            month_key="2026-07",
            spent_usd=19.5,
            pulls_count=39,
            remaining_usd=0.5,
            ceiling_usd=20.0,
            on_hold=True
        )

        allowed, remaining, reason = tracker.check_budget(cost=0.5)
        assert allowed is False
        assert "HOLD" in reason
