import logging
import asyncio
from datetime import datetime, timezone
from typing import Callable, Any

from src.cache import cache_store
from src.config import settings

logger = logging.getLogger("chickensoup.idle_sentinel")

class IdleSentinel:
    """
    System-wide activity tracker using Redis to ensure multi-process safety.
    """
    @staticmethod
    def _redis_key(activity_type: str) -> str:
        return f"idle:{activity_type}"

    @staticmethod
    def update_activity(activity_type: str, value: Any = None):
        """
        Updates the timestamp of the last activity or tracks active counts.
        activity_type can be: 'query', 'websocket', 'tribunal', 'chat_ingest'
        """
        if not cache_store.redis_client:
            return
        
        key = IdleSentinel._redis_key(activity_type)
        now_str = datetime.now(timezone.utc).isoformat()
        
        try:
            if activity_type in ("query", "websocket"):
                cache_store.redis_client.set(key, now_str)
            elif activity_type == "tribunal":
                # value can be 'start' or 'end'
                if value == "start":
                    cache_store.redis_client.incr(key)
                elif value == "end":
                    cache_store.redis_client.decr(key)
                    # Don't let it go below 0
                    val = cache_store.redis_client.get(key)
                    if val and int(val) < 0:
                        cache_store.redis_client.set(key, 0)
            elif activity_type == "chat_ingest":
                if value is True:
                    cache_store.redis_client.set(key, "running")
                else:
                    cache_store.redis_client.delete(key)
        except Exception as e:
            logger.warning(f"Failed to update activity in IdleSentinel: {e}")

    @staticmethod
    def is_idle(threshold_minutes: int = None) -> bool:
        """
        Checks if the system has been idle for the configured duration.
        """
        if threshold_minutes is None:
            threshold_minutes = getattr(settings, "IDLE_THRESHOLD_MINUTES", 5)
            
        if not cache_store.redis_client:
            # Classical fallback
            return True
            
        try:
            # 1. Check active count processes
            tribunal_active = cache_store.redis_client.get(IdleSentinel._redis_key("tribunal"))
            if tribunal_active and int(tribunal_active) > 0:
                return False
                
            chat_ingest_active = cache_store.redis_client.get(IdleSentinel._redis_key("chat_ingest"))
            if chat_ingest_active and chat_ingest_active.decode() == "running":
                return False
                
            # 2. Check timestamps of last interactive events
            now = datetime.now(timezone.utc)
            for activity in ("query", "websocket"):
                key = IdleSentinel._redis_key(activity)
                val = cache_store.redis_client.get(key)
                if val:
                    last_time = datetime.fromisoformat(val.decode())
                    if last_time.tzinfo is None:
                        last_time = last_time.replace(tzinfo=timezone.utc)
                    elapsed_min = (now - last_time).total_seconds() / 60.0
                    if elapsed_min < threshold_minutes:
                        return False
            
            return True
        except Exception as e:
            logger.warning(f"Error checking idle status: {e}")
            return True

    @staticmethod
    async def run_while_idle(
        work_unit_fn: Callable[[], Any],
        threshold_minutes: int = None,
        check_interval_seconds: int = 10,
    ) -> bool:
        """
        Cooperatively runs a unit of work ONLY when the system remains idle.
        Yields immediately if activity occurs between steps.
        Returns True if the work completed, False if it was preempted by activity.
        """
        if threshold_minutes is None:
            threshold_minutes = getattr(settings, "IDLE_THRESHOLD_MINUTES", 5)
            
        if not IdleSentinel.is_idle(threshold_minutes):
            return False
            
        try:
            if asyncio.iscoroutinefunction(work_unit_fn):
                await work_unit_fn()
            else:
                work_unit_fn()
            return True
        except Exception as e:
            logger.error(f"Error running work unit in IdleSentinel: {e}", exc_info=True)
            return False
