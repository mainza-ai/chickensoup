"""
Thread-safe, Redis-backed progress tracker for background operations.

Each background section writes to a Redis hash keyed `progress:<section>`.
All updates are atomic via the pipeline. The `get_all()` endpoint aggregates
all sections into a single dict for the `/status/progress` API endpoint.

Sections tracked:
  - reconciliation   Page-by-page ingest progress
  - idle_ingestion   last30days pulse loop
  - chat_ingest      Periodic conversation ingest
  - fallback_retry   LLM retry loop for low-quality pages
  - wiki_watcher     Filesystem event processing
  - llm_client       Aggregate call counts and breaker status
  - neo4j            Current node/relationship totals
"""
import json
import logging
import time
from datetime import datetime, timezone
from typing import Optional

from src.cache import cache_store

logger = logging.getLogger("chickensoup.progress_tracker")

PREFIX = "progress"

SECTIONS = frozenset({
    "reconciliation", "idle_ingestion", "chat_ingest",
    "fallback_retry", "wiki_watcher", "llm_client", "neo4j",
    "neo4j_backup",
})


def _key(section: str) -> Optional[str]:
    return f"{PREFIX}:{section}" if section in SECTIONS else None


def update(section: str, **kwargs):
    key = _key(section)
    if not key:
        return
    if not cache_store.redis_client:
        return
    try:
        pipe = cache_store.redis_client.pipeline()
        for k, v in kwargs.items():
            if isinstance(v, (dict, list)):
                v = json.dumps(v)
            elif isinstance(v, float):
                v = f"{v:.3f}"
            elif isinstance(v, bool):
                v = "true" if v else "false"
            else:
                v = str(v)
            pipe.hset(key, k, v)
        pipe.execute()
    except Exception as e:
        logger.debug(f"ProgressTracker.update({section}) error: {e}")


def increment(section: str, key: str, amount: int = 1):
    key_name = _key(section)
    if not key_name:
        return
    if not cache_store.redis_client:
        return
    try:
        cache_store.redis_client.hincrby(key_name, key, amount)
    except Exception as e:
        logger.debug(f"ProgressTracker.increment({section}, {key}) error: {e}")


def get_all() -> dict:
    if not cache_store.redis_client:
        return {}
    try:
        keys = cache_store.redis_client.keys(f"{PREFIX}:*")
        result: dict = {}
        for key in keys:
            raw_key = key.decode() if isinstance(key, bytes) else key
            section = raw_key.split(":", 1)[1]
            raw = cache_store.redis_client.hgetall(raw_key)
            data: dict = {}
            for k, v in raw.items():
                dk = k.decode() if isinstance(k, bytes) else k
                dv = v.decode() if isinstance(v, bytes) else v
                data[dk] = dv
            result[section] = data
        return result
    except Exception as e:
        logger.debug(f"ProgressTracker.get_all error: {e}")
        return {}
