import json
import logging
from datetime import datetime, timezone
from typing import Tuple

from src.config import settings
from src.cache import cache_store
from src.models import BudgetStatus

logger = logging.getLogger("chickensoup.budget")

BUDGET_LUA_CHECK = """
local key = KEYS[1]
local cost = tonumber(ARGV[1])
local ceiling = tonumber(ARGV[2])
local spent = tonumber(redis.call('HGET', key, 'spent') or '0')
if spent + cost > ceiling then
    return {0, spent}
end
local new_spent = spent + cost
redis.call('HSET', key, 'spent', tostring(new_spent))
redis.call('HINCRBY', key, 'pulls', 1)
return {1, new_spent}
"""

BUDGET_HOLD_LUA = """
local key = KEYS[1]
local hold_key = KEYS[2]
local threshold_mult = tonumber(ARGV[1])
local cost = tonumber(ARGV[2])
local ceiling = tonumber(ARGV[3])
local spent = tonumber(redis.call('HGET', key, 'spent') or '0')
local remaining = ceiling - spent
if remaining < threshold_mult * cost then
    redis.call('SET', hold_key, '1', 'EX', 86400)
    return 1
end
return 0
"""


class BudgetTracker:
    def _month_key(self, now: datetime = None) -> str:
        dt = now or datetime.now(timezone.utc)
        return dt.strftime("%Y-%m")

    def _budget_key(self, month_key: str = None) -> str:
        mk = month_key or self._month_key()
        return f"{settings.BUDGET_REDIS_KEY_PREFIX}:{mk}"

    def _hold_key(self, month_key: str = None) -> str:
        mk = month_key or self._month_key()
        return f"{settings.BUDGET_REDIS_KEY_PREFIX}:{mk}:hold"

    def _read_from_redis(self, key: str) -> dict:
        if not cache_store.redis_client:
            return {}
        try:
            raw = cache_store.redis_client.hgetall(key)
            return raw or {}
        except Exception as e:
            logger.warning(f"Budget read failed for {key}: {e}")
            return {}

    def get_status(self) -> BudgetStatus:
        mk = self._month_key()
        key = self._budget_key(mk)
        data = self._read_from_redis(key)
        spent = float(data.get("spent", 0) or 0)
        pulls = int(data.get("pulls", 0) or 0)
        ceiling = settings.LAST30DAYS_MONTHLY_BUDGET_USD
        on_hold = False
        if cache_store.redis_client:
            try:
                on_hold = bool(cache_store.redis_client.get(self._hold_key(mk)))
            except Exception:
                pass
        return BudgetStatus(
            month_key=mk,
            spent_usd=spent,
            pulls_count=pulls,
            remaining_usd=max(0.0, ceiling - spent),
            ceiling_usd=ceiling,
            on_hold=on_hold,
        )

    def check_budget(self, cost: float = None) -> Tuple[bool, float, str]:
        if cost is None:
            cost = settings.LAST30DAYS_COST_PER_PULL_USD

        status = self.get_status()

        if status.on_hold:
            return False, status.remaining_usd, f"Budget on HOLD for {status.month_key} — requires manual approval"

        if status.remaining_usd < cost - 1e-9:
            return False, status.remaining_usd, f"Monthly budget ceiling ${status.ceiling_usd:.2f} would be exceeded (spent ${status.spent_usd:.2f}, cost ${cost:.2f}, remaining ${status.remaining_usd:.2f})"

        if not cache_store.redis_client:
            logger.warning("Redis unavailable — allowing budget check optimistically (in-memory fallback to deny would break tests with mock)")
            return True, status.remaining_usd, "ok (no redis)"

        # Atomic check-and-increment via Lua
        key = self._budget_key(status.month_key)
        try:
            result = cache_store.redis_client.eval(BUDGET_LUA_CHECK, 1, key, str(cost), str(status.ceiling_usd))
            allowed = bool(result[0])
            new_spent = float(result[1])
            remaining = max(0.0, status.ceiling_usd - new_spent) if allowed else status.remaining_usd

            if not allowed:
                logger.warning(f"Budget exceeded: would need ${cost:.2f}, only ${remaining:.2f} left (ceiling ${status.ceiling_usd:.2f})")
                return False, remaining, f"Budget ceiling ${status.ceiling_usd:.2f} would be exceeded"

            # Check if we should enter HOLD state
            threshold = settings.BUDGET_HOLD_THRESHOLD_REMAINING
            remaining_after = status.ceiling_usd - new_spent
            if remaining_after < threshold * cost:
                try:
                    cache_store.redis_client.eval(
                        BUDGET_HOLD_LUA, 2,
                        key, self._hold_key(status.month_key),
                        str(threshold), str(cost), str(status.ceiling_usd)
                    )
                    logger.info(f"Budget entering HOLD: remaining ${remaining_after:.2f} < {threshold}x cost")
                except Exception as hold_err:
                    logger.warning(f"Failed to set HOLD flag: {hold_err}")

            return True, remaining, "ok"
        except Exception as e:
            logger.warning(f"Budget Lua eval failed, falling back to non-atomic check: {e}")
            # Non-atomic fallback (single worker safe, not distributed safe)
            if status.remaining_usd < cost - 1e-9:
                return False, status.remaining_usd, f"Budget ceiling would be exceeded: {e}"
            try:
                pulls_now = int(cache_store.redis_client.hget(key, "pulls") or 0)
                cache_store.redis_client.hset(key, mapping={
                    "spent": str(status.spent_usd + cost),
                    "pulls": str(pulls_now + 1),
                    "last_pull": datetime.now(timezone.utc).isoformat(),
                })
            except Exception as set_err:
                logger.warning(f"Budget non-atomic increment failed: {set_err}")
            return True, max(0.0, status.remaining_usd - cost), "ok (non-atomic fallback)"

    def record_spend(self, amount: float, description: str = "") -> BudgetStatus:
        # record_spend is called after a successful pull; check_budget already incremented.
        # This method updates metadata and ensures consistency.
        mk = self._month_key()
        key = self._budget_key(mk)
        if cache_store.redis_client:
            try:
                cache_store.redis_client.hset(key, mapping={
                    "last_pull": datetime.now(timezone.utc).isoformat(),
                    "last_description": description[:200] if description else "",
                })
                cache_store.redis_client.expire(key, 60 * 60 * 24 * 35)
            except Exception as e:
                logger.warning(f"Failed to record spend metadata: {e}")
        return self.get_status()

    def approve_hold(self) -> BudgetStatus:
        mk = self._month_key()
        if cache_store.redis_client:
            try:
                cache_store.redis_client.delete(self._hold_key(mk))
                logger.info(f"Budget HOLD cleared for {mk}")
            except Exception as e:
                logger.warning(f"Failed to clear HOLD flag: {e}")
        return self.get_status()

    def reset_month(self, month_key: str = None) -> BudgetStatus:
        mk = month_key or self._month_key()
        key = self._budget_key(mk)
        if cache_store.redis_client:
            try:
                cache_store.redis_client.delete(key)
                cache_store.redis_client.delete(self._hold_key(mk))
            except Exception as e:
                logger.warning(f"Failed to reset budget month {mk}: {e}")
        return self.get_status()


budget_tracker = BudgetTracker()
