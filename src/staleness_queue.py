import logging
import os
from datetime import datetime, timezone
from typing import List, Dict, Any

from src.cache import cache_store
from src.config import settings
from src.scheduler import _get_reinforcement_count

logger = logging.getLogger("chickensoup.staleness_queue")

QUEUE_REDIS_KEY = "staleness:queue"

def _last_pulse_key(slug: str) -> str:
    return f"staleness:last_pulse_at:{slug}"

def _divergence_key(slug: str) -> str:
    return f"staleness:divergence_risk:{slug}"

def _state_label_key(slug: str) -> str:
    return f"staleness:state_label:{slug}"

def compute_staleness_score(slug: str) -> float:
    """
    Computes composite priority score:
      S = w_t * T_elapsed + w_r * C_reinforcement + w_d * D_divergence + C_contested_bonus
    """
    if not cache_store.redis_client:
        return 0.0

    try:
        # 1. Days since last pulse (T_elapsed)
        now = datetime.now(timezone.utc)
        last_pulse_val = cache_store.redis_client.get(_last_pulse_key(slug))
        if last_pulse_val:
            last_pulse = datetime.fromisoformat(last_pulse_val)
            if last_pulse.tzinfo is None:
                last_pulse = last_pulse.replace(tzinfo=timezone.utc)
            days_stale = (now - last_pulse).total_seconds() / 86400.0
        else:
            # Never pulsed — high baseline staleness
            days_stale = 30.0

        # 2. Reinforcement count (C_reinforcement)
        reinforcement = _get_reinforcement_count(slug)

        # 3. Divergence risk (D_divergence)
        div_val = cache_store.redis_client.get(_divergence_key(slug))
        divergence = float(div_val) if div_val else 0.0

        # 4. State label contested bonus
        label_val = cache_store.redis_client.get(_state_label_key(slug))
        state_label = label_val if label_val else "unverified"
        contested_bonus = 5.0 if state_label == "contested" else 0.0

        # Weights
        w_t = 1.0
        w_r = 2.0
        w_d = 10.0

        score = (w_t * days_stale) + (w_r * reinforcement) + (w_d * divergence) + contested_bonus
        return float(score)
    except Exception as e:
        logger.warning(f"Failed to compute staleness score for '{slug}': {e}")
        return 0.0

def record_pulse_completed(slug: str, divergence_risk: float = 0.0, state_label: str = "unverified"):
    """
    Updates last pulse timestamp and cached metrics in Redis, then recalculates priority.
    """
    if not cache_store.redis_client:
        return
        
    try:
        now_str = datetime.now(timezone.utc).isoformat()
        cache_store.redis_client.set(_last_pulse_key(slug), now_str)
        cache_store.redis_client.set(_divergence_key(slug), str(divergence_risk))
        cache_store.redis_client.set(_state_label_key(slug), state_label)
        
        # Recalculate score and update Redis sorted set
        # Use a very low score so this entity sinks to the bottom of zrevrange
        # preventing it from being re-pulsed until the queue is rebuilt
        cache_store.redis_client.zadd(QUEUE_REDIS_KEY, {slug: -999999})
        logger.info(f"Recorded pulse complete for '{slug}' — moved to bottom of queue")
    except Exception as e:
        logger.warning(f"Failed to record pulse complete for '{slug}': {e}")

def get_next_batch(n: int) -> List[str]:
    """
    Returns the top n highest-priority (staleness score) entity slugs.
    """
    if not cache_store.redis_client:
        return []
        
    try:
        # zrevrange gets highest scores first
        elements = cache_store.redis_client.zrevrange(QUEUE_REDIS_KEY, 0, n - 1)
        return [el.decode() if isinstance(el, bytes) else el for el in elements]
    except Exception as e:
        logger.warning(f"Failed to get next batch from staleness queue: {e}")
        return []

def rebuild_queue():
    """
    Scans all published wiki pages, calculates priority, and updates Redis sorted set.
    """
    if not cache_store.redis_client:
        return

    logger.info("Rebuilding staleness priority queue...")
    try:
        wiki_dir = settings.WIKI_DATA_DIR
        slugs = []

        for page_type in ("entities", "concepts", "projects"):
            type_dir = os.path.join(wiki_dir, page_type)
            if not os.path.isdir(type_dir):
                continue
            for filename in os.listdir(type_dir):
                if filename.endswith(".md"):
                    slugs.append(filename[:-3])

        if not slugs:
            return

        mapping = {}
        for slug in slugs:
            score = compute_staleness_score(slug)
            mapping[slug] = score

        cache_store.redis_client.delete(QUEUE_REDIS_KEY)
        cache_store.redis_client.zadd(QUEUE_REDIS_KEY, mapping)
        logger.info(f"Rebuilt staleness queue with {len(mapping)} pages across entities/concepts/projects.")
    except Exception as e:
        logger.warning(f"Failed to rebuild staleness queue: {e}")
