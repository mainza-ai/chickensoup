"""
P2-2: Human Approval Gate Live Tests.

Tests the force_human_approval parameter on ResearchAgent.run_research()
and the POST /research/{thread_id}/approve endpoint.
Tests use TestClient so MemorySaver state is shared between test and handler.
"""
import time

import pytest
from fastapi.testclient import TestClient

from src.agents.research_agent import ResearchAgent, research_graph

BASE = "http://localhost:8000"
HEADERS = {"Content-Type": "application/json", "X-Api-Key": "dev"}


# ---------------------------------------------------------------------------
# Unit tests — no server required
# ---------------------------------------------------------------------------

class TestForceHumanApprovalParam:
    """Tests the force_human_approval parameter directly on ResearchAgent."""

    @pytest.fixture
    def agent(self):
        return ResearchAgent()

    def test_force_human_approval_triggers(self, agent):
        result = agent.run_research(
            query="Test query",
            entities=["Area 51"],
            thread_id="test-force-01",
            force_human_approval=True,
        )
        assert result.get("human_approval_required") is True
        assert "credibility_scores" in result

    def test_normal_run_does_not_force_approval(self, agent):
        result = agent.run_research(
            query="Test query",
            entities=["Area 51"],
            thread_id="test-force-02",
            force_human_approval=False,
        )
        assert "human_approval_required" in result

    def test_force_human_approval_with_empty_entities(self, agent):
        result = agent.run_research(
            query="",
            entities=[],
            thread_id="test-force-03",
            force_human_approval=True,
        )
        assert result.get("human_approval_required") is True

    def test_force_human_approval_overrides_low_confidence(self, agent):
        result = agent.run_research(
            query="Obscure entity with no graph data",
            entities=["Xyzzzzzzzz"],
            thread_id="test-force-04",
            force_human_approval=True,
        )
        assert result.get("human_approval_required") is True


# ---------------------------------------------------------------------------
# Integration tests — use TestClient so MemorySaver state is shared
# ---------------------------------------------------------------------------

@pytest.fixture
def client():
    from src.main import app
    with TestClient(app) as c:
        yield c


def _gen_thread_id():
    return f"test-approve-{int(time.time() * 1000)}"


class TestApproveEndpoint:
    """Integration tests for POST /research/{thread_id}/approve.

    Seeds paused state via ResearchAgent.run_research(force_human_approval=True),
    then validates the HTTP approve endpoint resumes and completes the graph.
    TestClient ensures MemorySaver state is shared between test and handler.
    """

    def _seed_paused_state(self, thread_id: str) -> dict:
        agent = ResearchAgent()
        result = agent.run_research(
            query="What is the evidence for Area 51?",
            entities=["Area 51"],
            thread_id=thread_id,
            force_human_approval=True,
        )
        return result

    def test_approve_completes_paused_research(self, client):
        thread_id = _gen_thread_id()
        paused = self._seed_paused_state(thread_id)
        assert paused.get("human_approval_required") is True

        response = client.post(
            f"/research/{thread_id}/approve",
            json={},
            headers={"X-Api-Key": "dev"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data.get("success") is True
        assert "summary" in data
        assert len(data["summary"]) > 10

    def test_approve_endpoint_rejects_missing_thread(self, client):
        response = client.post(
            "/research/nonexistent-thread-id/approve",
            headers={"X-Api-Key": "dev"},
        )
        assert response.status_code == 404

    def test_approve_endpoint_rejects_non_paused_thread(self, client):
        thread_id = _gen_thread_id()
        # Create a completed research run (no force approval)
        agent = ResearchAgent()
        agent.run_research(
            query="Area 51",
            entities=["Area 51"],
            thread_id=thread_id,
            force_human_approval=False,
        )

        response = client.post(
            f"/research/{thread_id}/approve",
            headers={"X-Api-Key": "dev"},
        )
        # A completed (non-paused) thread should return 400
        assert response.status_code == 400

    def test_approve_resume_generates_summary(self, client):
        thread_id = _gen_thread_id()
        paused = self._seed_paused_state(thread_id)
        assert paused.get("human_approval_required") is True

        response = client.post(
            f"/research/{thread_id}/approve",
            json={},
            headers={"X-Api-Key": "dev"},
        )
        assert response.status_code == 200
        data = response.json()
        summary = data.get("summary", "")
        assert len(summary) > 10

    def test_approve_returns_entities(self, client):
        thread_id = _gen_thread_id()
        self._seed_paused_state(thread_id)

        response = client.post(
            f"/research/{thread_id}/approve",
            json={},
            headers={"X-Api-Key": "dev"},
        )
        assert response.status_code == 200
        data = response.json()
        entities = data.get("entities", [])
        assert len(entities) >= 1
        assert any("Area 51" in e for e in entities)
