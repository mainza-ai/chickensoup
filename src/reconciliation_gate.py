"""
Redis-backed coordination gate for background tasks.

Prevents concurrent execution of:
  - reconciliation + idle ingestion
  - reconciliation + chat ingest
  - reconciliation + wiki watcher events

The gate uses a Redis key `reconciliation:busy` with a TTL to signal
that reconciliation is in progress. Background loops check `is_busy()`
before starting work and between items.

Stale gates from crashed or killed server instances are cleared at
server startup via `clear_stale_gate()`.
"""
import logging
from src.cache import cache_store

logger = logging.getLogger("chickensoup.reconciliation_gate")

_RECON_KEY = "reconciliation:busy"
_RECON_TTL = 7200  # 2 hours — auto-expire if process crashes


class ReconciliationGate:
    @staticmethod
    def acquire() -> bool:
        if not cache_store.redis_client:
            return True
        try:
            existing = cache_store.redis_client.get(_RECON_KEY)
            if existing:
                logger.debug("Reconciliation already in progress — skipping")
                return False
            cache_store.redis_client.set(_RECON_KEY, "1", ex=_RECON_TTL)
            return True
        except Exception as e:
            logger.warning(f"ReconciliationGate.acquire failed: {e}")
            return True

    @staticmethod
    def release():
        if not cache_store.redis_client:
            return
        try:
            cache_store.redis_client.delete(_RECON_KEY)
        except Exception as e:
            logger.warning(f"ReconciliationGate.release failed: {e}")

    @staticmethod
    def is_busy() -> bool:
        if not cache_store.redis_client:
            return False
        try:
            return bool(cache_store.redis_client.get(_RECON_KEY))
        except Exception as e:
            logger.warning(f"ReconciliationGate.is_busy failed: {e}")
            return False

    @staticmethod
    def refresh_ttl():
        if not cache_store.redis_client:
            return
        try:
            cache_store.redis_client.expire(_RECON_KEY, _RECON_TTL)
        except Exception as e:
            logger.warning(f"ReconciliationGate.refresh_ttl failed: {e}")


reconciliation_gate = ReconciliationGate()


def set_reconciliation_stop():
    """Set a Redis flag that reconciliation loops check between pages."""
    if not cache_store.redis_client:
        return
    try:
        cache_store.redis_client.set("reconciliation:stop", "1", ex=3600)
    except Exception as e:
        logger.warning(f"Failed to set reconciliation stop signal: {e}")


def clear_reconciliation_stop():
    if not cache_store.redis_client:
        return
    try:
        cache_store.redis_client.delete("reconciliation:stop")
    except Exception as e:
        logger.warning(f"Failed to clear reconciliation stop signal: {e}")


def stop_signal_flagged() -> bool:
    if not cache_store.redis_client:
        return False
    try:
        return bool(cache_store.redis_client.get("reconciliation:stop"))
    except Exception as e:
        logger.warning(f"Failed to check reconciliation stop signal: {e}")
        return False


def clear_stale_gate():
    """Remove a stale reconciliation gate from a crashed/killed server instance.
    Called at server startup to prevent a dead lock from a previous process."""
    if not cache_store.redis_client:
        return
    try:
        cache_store.redis_client.delete(_RECON_KEY)
        logger.info("Cleared stale reconciliation gate (if any)")
    except Exception as e:
        logger.warning(f"Failed to clear stale reconciliation gate: {e}")