import os
import shutil
import pytest
import json
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

from src.idle_sentinel import IdleSentinel
from src.resource_ledger import ResourceLedger, ResourceLedgerStatus
from src.staleness_queue import (
    compute_staleness_score,
    record_pulse_completed,
    get_next_batch,
    rebuild_queue,
    QUEUE_REDIS_KEY
)
from src.discovery_agent import list_drafts, promote_draft, get_draft_path, DRAFT_DIR
from src.wiki.writer import write_page, read_page

@pytest.fixture(autouse=True)
def mock_redis():
    # Setup mock redis for tests
    with patch("src.cache.cache_store.redis_client") as mock_client:
        # Mock client storage using a simple dict
        store = {}
        
        def mock_get(key):
            val = store.get(key)
            if val is not None:
                return str(val).encode() if not isinstance(val, bytes) else val
            return None
            
        def mock_set(key, val, *args, **kwargs):
            store[key] = val
            return True
            
        def mock_incr(key):
            curr = store.get(key, 0)
            new_val = int(curr) + 1
            store[key] = new_val
            return new_val
            
        def mock_decr(key):
            curr = store.get(key, 0)
            new_val = int(curr) - 1
            store[key] = new_val
            return new_val

        def mock_zadd(key, mapping, *args, **kwargs):
            if key not in store:
                store[key] = {}
            for k, v in mapping.items():
                store[key][k] = float(v)
            return len(mapping)

        def mock_zrevrange(key, start, end):
            if key not in store or not isinstance(store[key], dict):
                return []
            # Sort keys by score descending
            sorted_items = sorted(store[key].items(), key=lambda item: item[1], reverse=True)
            res = [k for k, v in sorted_items[start:end+1]]
            return [k.encode() if isinstance(k, str) else k for k in res]
            
        def mock_delete(key):
            if key in store:
                del store[key]
                return 1
            return 0

        mock_client.get.side_effect = mock_get
        mock_client.set.side_effect = mock_set
        mock_client.incr.side_effect = mock_incr
        mock_client.decr.side_effect = mock_decr
        mock_client.zadd.side_effect = mock_zadd
        mock_client.zrevrange.side_effect = mock_zrevrange
        mock_client.delete.side_effect = mock_delete
        
        yield mock_client

# ── Idle Sentinel Tests ──────────────────────────────────────────────

def test_idle_sentinel_activity_updates():
    IdleSentinel.update_activity("query")
    IdleSentinel.update_activity("websocket")
    IdleSentinel.update_activity("tribunal", "start")
    
    assert not IdleSentinel.is_idle(threshold_minutes=5)
    
    # End tribunal
    IdleSentinel.update_activity("tribunal", "end")
    # Simulate time passing by manually updating redis keys to old timestamp
    old_time = datetime(2020, 1, 1, tzinfo=timezone.utc).isoformat()
    IdleSentinel.update_activity("query")
    with patch("src.cache.cache_store.redis_client.get") as mock_get:
        def get_side_effect(key):
            if "query" in key or "websocket" in key:
                return old_time.encode()
            return b"0" # tribunal active count
        mock_get.side_effect = get_side_effect
        assert IdleSentinel.is_idle(threshold_minutes=5)

# ── Resource Ledger Tests ────────────────────────────────────────────

def test_resource_ledger_paid_and_free():
    # Test paid ledger checks budget_tracker
    with patch("src.resource_ledger.budget_tracker") as mock_bt:
        mock_bt.check_budget.return_value = (True, 15.0, "ok")
        mock_bt.get_status.return_value = MagicMock(spent_usd=5.0, ceiling_usd=20.0, remaining_usd=15.0)
        
        allowed, remaining, reason = ResourceLedger.check_budget(is_paid=True)
        assert allowed
        assert remaining == 15.0
        
    # Test free ledger checking sliding window
    allowed, remaining, reason = ResourceLedger.check_budget(is_paid=False)
    assert allowed
    assert remaining > 0

# ── Staleness Priority Queue Tests ───────────────────────────────────

def test_staleness_priority_queue():
    # Record pulse for two entities
    record_pulse_completed("bob-lazar", divergence_risk=0.8, state_label="contested")
    record_pulse_completed("element-115", divergence_risk=0.2, state_label="corroborated")
    
    # Bob Lazar has higher divergence (0.8 vs 0.2) and contested bonus, so should be top
    batch = get_next_batch(2)
    assert len(batch) == 2
    assert batch[0] == "bob-lazar"
    assert batch[1] == "element-115"

# ── Discovery Agent & Gated Drafts Tests ─────────────────────────────

def test_gated_draft_creation_and_promotion(tmp_path):
    # Setup temporary wiki dirs
    wiki_dir = tmp_path / "wiki"
    entities_dir = wiki_dir / "entities"
    drafts_dir = wiki_dir / "raw" / "drafts"
    entities_dir.mkdir(parents=True, exist_ok=True)
    drafts_dir.mkdir(parents=True, exist_ok=True)
    
    with patch("src.config.settings.WIKI_DATA_DIR", str(wiki_dir)), \
         patch("src.wiki.writer.WIKI_DIR", str(wiki_dir)), \
         patch("src.discovery_agent.DRAFT_DIR", str(drafts_dir)):
         
         # 1. Writing a brand new entity should route to draft workspace
         slug, is_new = write_page(
             title="Roswell Alien",
             body="Alien body recovered in Roswell",
             tags=["ufo", "alien"],
             sources=["fbi-vault"],
             related=[]
         )
         
         assert slug == "roswell-alien"
         # Should create draft file, NOT published entities file
         draft_file = drafts_dir / "roswell-alien.md"
         pub_file = entities_dir / "roswell-alien.md"
         assert draft_file.exists()
         assert not pub_file.exists()
         
         # 2. Promoting draft should publish it
         success = promote_draft("roswell-alien")
         assert success
         assert not draft_file.exists()
         assert pub_file.exists()
         
         # 3. Writing updates to an already published entity should modify it directly
         slug2, is_new2 = write_page(
             title="Roswell Alien",
             body="Update: reverse engineered technology.",
             tags=["ufo", "alien"],
             sources=["fbi-vault"],
             related=[]
         )
         assert slug2 == "roswell-alien"
         assert not is_new2
         assert pub_file.exists()
         assert "Update: reverse" in pub_file.read_text()
