import logging
from datetime import datetime, timezone
from typing import Literal, Tuple, Dict, Any
from pydantic import BaseModel

from src.config import settings
from src.cache import cache_store
from src.budget import budget_tracker

logger = logging.getLogger("chickensoup.resource_ledger")

class LedgerDecision(BaseModel):
    allowed: bool
    ledger_type: Literal["paid", "free", "none"]
    charged_amount: float
    remaining: float
    reason: str

class ResourceLedgerStatus(BaseModel):
    paid_spent: float
    paid_ceiling: float
    paid_remaining: float
    free_requests_this_hour: int
    free_requests_ceiling: int
    free_remaining: int

class ResourceLedger:
    """
    Decoupled cost tracking ledger supporting independent Paid and Free buckets.
    """
    @staticmethod
    def _free_hour_key() -> str:
        # e.g., budget:free:hour:2026-07-12-16
        now = datetime.now(timezone.utc)
        return f"budget:free:hour:{now.strftime('%Y-%m-%d-%H')}"

    @staticmethod
    def check_budget(is_paid: bool = True) -> Tuple[bool, float, str]:
        """
        Pre-check: determines if a query is allowed under the specific ledger.
        """
        if not settings.LAST30DAYS_ENABLED:
            return False, 0.0, "Pulse globally disabled (LAST30DAYS_ENABLED=false)"

        if is_paid:
            cost = settings.LAST30DAYS_COST_PER_PULL_USD
            allowed, remaining, reason = budget_tracker.check_budget(cost)
            return allowed, remaining, reason
        else:
            if not getattr(settings, "FREE_TIER_ENABLED", True):
                return False, 0.0, "Free-tier pulls disabled (FREE_TIER_ENABLED=false)"
                
            if not cache_store.redis_client:
                # Fallback: allow classical calls
                return True, float(getattr(settings, "FREE_TIER_REQUESTS_PER_HOUR", 60)), "ok"
                
            key = ResourceLedger._free_hour_key()
            try:
                current = cache_store.redis_client.get(key)
                count = int(current) if current else 0
                ceiling = getattr(settings, "FREE_TIER_REQUESTS_PER_HOUR", 60)
                if count >= ceiling:
                    return False, 0.0, f"Free tier rate limit reached ({count}/{ceiling} reqs/hr)"
                return True, float(ceiling - count), "ok"
            except Exception as e:
                logger.warning(f"Error checking free tier rate limit: {e}")
                return True, 60.0, "ok"

    @staticmethod
    def record_spend(is_paid: bool, description: str = "") -> Tuple[float, str]:
        """
        Commit: records spent resource after a successful operation.
        """
        if is_paid:
            cost = settings.LAST30DAYS_COST_PER_PULL_USD
            status = budget_tracker.record_spend(cost, description)
            return status.remaining_usd, "recorded paid spend"
        else:
            key = ResourceLedger._free_hour_key()
            ceiling = getattr(settings, "FREE_TIER_REQUESTS_PER_HOUR", 60)
            try:
                if cache_store.redis_client:
                    new_val = cache_store.redis_client.incr(key)
                    if new_val == 1:
                        # Expiry set to 2 hours (sufficient for 1 hour block)
                        cache_store.redis_client.expire(key, 7200)
                    return float(max(0, ceiling - new_val)), "recorded free spend"
                return float(ceiling), "recorded free spend"
            except Exception as e:
                logger.warning(f"Failed to record free spend: {e}")
                return float(ceiling), "failed free spend write"

    @staticmethod
    def get_status() -> ResourceLedgerStatus:
        """
        Aggregates both Paid and Free ledger statuses.
        """
        paid_status = budget_tracker.get_status()
        
        free_count = 0
        free_ceiling = getattr(settings, "FREE_TIER_REQUESTS_PER_HOUR", 60)
        
        if cache_store.redis_client:
            try:
                val = cache_store.redis_client.get(ResourceLedger._free_hour_key())
                free_count = int(val) if val else 0
            except Exception:
                pass
                
        return ResourceLedgerStatus(
            paid_spent=paid_status.spent_usd,
            paid_ceiling=paid_status.ceiling_usd,
            paid_remaining=paid_status.remaining_usd,
            free_requests_this_hour=free_count,
            free_requests_ceiling=free_ceiling,
            free_remaining=max(0, free_ceiling - free_count)
        )
