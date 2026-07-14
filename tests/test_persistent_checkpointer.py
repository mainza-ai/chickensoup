"""
P3-2: Persistent Checkpointer Tests.

Tests that RedisSaver integrates with research_agent's compiled LangGraph,
gracefully falls back to MemorySaver when Redis is unavailable,
and that checkpoint data persists across instances.
"""
import time
from unittest.mock import patch, MagicMock
import uuid

import pytest
from langgraph.checkpoint.base import Checkpoint
from langgraph.checkpoint.memory import MemorySaver as InMemorySaver, BaseCheckpointSaver

from src.agents.research_agent import research_graph, _create_checkpointer
from src.config import settings


def _make_checkpoint(
    thread_id: str,
    step: int = 0,
    channel_versions: dict | None = None,
) -> Checkpoint:
    return Checkpoint(
        v=1,
        id=f"{thread_id}-{step}-{uuid.uuid4().hex[:8]}",
        ts=time.strftime("%Y-%m-%dT%H:%M:%S+00:00", time.gmtime()),
        channel_values={"query": f"test-query-{thread_id}", "entities": ["Area 51"]},
        channel_versions=channel_versions or {},
        versions_seen={},
    )


def _make_config(thread_id: str) -> dict:
    return {"configurable": {"thread_id": thread_id, "checkpoint_ns": ""}}


class TestCheckpointerInitialization:
    """Verifies the compiled graph uses a valid checkpointer (Redis or fallback)."""

    def test_checkpointer_is_base_checkpoint_saver(self):
        cp = research_graph.checkpointer
        assert isinstance(cp, BaseCheckpointSaver)

    def test_fallback_to_memory_when_redis_fails(self):
        with patch("langgraph.checkpoint.redis.RedisSaver.setup", side_effect=Exception("Redis down")):
            cp = _create_checkpointer()
            assert isinstance(cp, InMemorySaver)

    def test_checkpointer_type_detected(self):
        cp = research_graph.checkpointer
        from langgraph.checkpoint.redis import RedisSaver as _RS
        is_redis = isinstance(cp, _RS)
        is_memory = isinstance(cp, InMemorySaver)
        assert is_redis or is_memory, f"Unexpected checkpointer type: {type(cp).__name__}"


class TestCheckpointerPutGet:
    """Tests the full put/get cycle through the graph's checkpointer."""

    def test_put_and_get_checkpoint(self):
        cp = research_graph.checkpointer
        tid = f"test-p3-2-putget-{int(time.time() * 1000)}"
        config = _make_config(tid)
        channel_versions = {"query": "1", "entities": "1", "foo": "1"}
        checkpoint = _make_checkpoint(tid, channel_versions=channel_versions)

        result_config = cp.put(config, checkpoint, {"source": "input", "step": 0}, channel_versions)
        assert result_config is not None
        assert "checkpoint_id" in result_config["configurable"]

        retrieved = cp.get(result_config)
        assert retrieved is not None
        assert retrieved["channel_values"]["query"] == checkpoint["channel_values"]["query"]

    def test_get_tuple_returns_full_metadata(self):
        cp = research_graph.checkpointer
        tid = f"test-p3-2-tuple-{int(time.time() * 1000)}"
        config = _make_config(tid)
        channel_versions = {"query": "1", "entities": "1"}
        checkpoint = _make_checkpoint(tid, channel_versions=channel_versions)

        result_config = cp.put(config, checkpoint, {"source": "input", "step": 1}, channel_versions)

        tup = cp.get_tuple(result_config)
        assert tup is not None
        assert tup.checkpoint["channel_values"]["query"] == checkpoint["channel_values"]["query"]
        assert tup.metadata["step"] == 1

    def test_get_nonexistent_returns_none(self):
        cp = research_graph.checkpointer
        config = _make_config("no-such-thread-id")
        config["configurable"]["checkpoint_id"] = "no-such-id"
        result = cp.get(config)
        assert result is None

    def test_delete_thread_removes_checkpoint(self):
        cp = research_graph.checkpointer
        tid = f"test-p3-2-delete-{int(time.time() * 1000)}"
        config = _make_config(tid)
        channel_versions = {"query": "1"}
        checkpoint = _make_checkpoint(tid, channel_versions=channel_versions)
        cp.put(config, checkpoint, {"source": "input", "step": 0}, channel_versions)

        cp.delete_thread(tid)
        list_result = list(cp.list(_make_config(tid), limit=5))
        assert len(list_result) == 0


class TestRedisPersistenceAcrossInstances:
    """Tests that RedisSaver persists state across separate instances.

    These tests require a running Redis with RediSearch module.
    Skipped when RedisSaver is not the active checkpointer.
    """

    @pytest.fixture
    def skip_if_not_redis(self):
        from langgraph.checkpoint.redis import RedisSaver as _RS
        if not isinstance(research_graph.checkpointer, _RS):
            pytest.skip("RedisSaver not active — skipping cross-instance test")

    def test_separate_instance_reads_written_checkpoint(self, skip_if_not_redis):
        from langgraph.checkpoint.redis import RedisSaver as _RS
        tid = f"test-p3-2-cross-{int(time.time() * 1000)}"
        config = _make_config(tid)
        checkpoint = _make_checkpoint(tid)

        research_graph.checkpointer.put(config, checkpoint, {"source": "input", "step": 0}, {})

        cp2 = _RS(redis_url=settings.REDIS_URL)
        cp2.setup()

        retrieved = cp2.get(config)
        assert retrieved is not None
        assert retrieved["channel_values"]["query"] == checkpoint["channel_values"]["query"]
