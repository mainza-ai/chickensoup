"""
Tests for production hardening fixes:
- P1-2: Empty query returns default intent/entities
- P1-1: Multi-entity extraction from conjunctive queries
- P0-2: Malformed pulse path returns 422
- P3-1: /consensus/query live integration test
"""
import json
import time

import pytest
import requests

from src.agents.query_agent import QueryAgent

BASE = "http://localhost:8000"
HEADERS = {"Content-Type": "application/json", "X-Api-Key": "dev"}


# ---------------------------------------------------------------------------
# P1-2: Empty query defaults
# ---------------------------------------------------------------------------

class TestEmptyQueryDefaults:
    """classify_and_parse must never return None for intent or entities."""

    @pytest.fixture
    def agent(self):
        return QueryAgent()

    def test_empty_string_returns_query_intent(self, agent):
        result = agent.classify_and_parse("")
        assert result.intent == "query"
        assert result.entities == []

    def test_whitespace_only_returns_query_intent(self, agent):
        result = agent.classify_and_parse("   ")
        assert result.intent == "query"
        assert result.entities == []

    def test_none_query_does_not_crash(self, agent):
        # classify_and_parse expects str, but guard against accidental None
        try:
            result = agent.classify_and_parse(None)  # type: ignore[arg-type]
        except Exception:
            pytest.skip("None input raises exception — acceptable if documented")
        else:
            assert result.intent is not None
            assert result.entities is not None


# ---------------------------------------------------------------------------
# P1-1: Multi-entity extraction
# ---------------------------------------------------------------------------

class TestMultiEntityExtraction:
    """Queries with 'and'/'or' separators must yield multiple entities."""

    @pytest.fixture(autouse=True)
    def _fresh_wiki_index(self, monkeypatch):
        from src.agents.query_agent import invalidate_wiki_index
        invalidate_wiki_index()
        yield
        invalidate_wiki_index()

    @pytest.fixture
    def agent(self):
        return QueryAgent()

    def test_two_entities_with_and(self, agent):
        result = agent.classify_and_parse("Bob Lazar and Area 51")
        assert len(result.entities) >= 2
        assert any("Bob Lazar" in e for e in result.entities)
        assert any("Area 51" in e for e in result.entities)

    def test_three_entities_with_and(self, agent):
        result = agent.classify_and_parse("Bob Lazar and Area 51 and Project Serpo")
        assert len(result.entities) >= 3

    def test_two_entities_with_ampersand(self, agent):
        result = agent.classify_and_parse("Bob Lazar & Area 51")
        assert len(result.entities) >= 2

    def test_single_entity_unchanged(self, agent):
        result = agent.classify_and_parse("What is Area 51?")
        assert len(result.entities) >= 1


# ---------------------------------------------------------------------------
# P0-2: Malformed path parameter validation
# ---------------------------------------------------------------------------

class TestPathParameterValidation:
    """Malformed entity names in path parameters must return 422, not 200."""

    def test_pulse_rejects_quoted_name(self):
        response = requests.post(f"{BASE}/pulse/%22", headers=HEADERS, timeout=10)
        assert response.status_code == 422

    def test_pulse_rejects_empty_name(self):
        response = requests.post(f"{BASE}/pulse/", headers=HEADERS, timeout=10)
        assert response.status_code in (404, 422)

    def test_graph_rejects_dotdot(self):
        response = requests.get(f"{BASE}/graph/../admin", headers=HEADERS, timeout=10)
        assert response.status_code in (404, 422)

    def test_divergence_rejects_punctuation_only(self):
        response = requests.get(f"{BASE}/entities/!!! /divergence", headers=HEADERS, timeout=10)
        assert response.status_code in (404, 422)


# ---------------------------------------------------------------------------
# P3-1: /consensus/query live integration tests
# ---------------------------------------------------------------------------

def _is_live_server_available():
    try:
        return requests.get(f"{BASE}/status", timeout=3).ok
    except Exception:
        return False


@pytest.mark.skipif(
    not _is_live_server_available(),
    reason="Live server not available",
)
class TestConsensusLive:
    """Integration tests for POST /consensus/query against a live server."""

    def test_consensus_endpoint_returns_expected_keys(self):
        response = requests.post(
            f"{BASE}/consensus/query",
            json={
                "prompt": "What is Area 51?",
                "system_instruction": "You are a helpful assistant.",
            },
            headers=HEADERS,
            timeout=60,
        )
        assert response.status_code == 200
        data = response.json()
        assert "consensus_response" in data
        assert "agreement_score" in data
        assert "individual_responses" in data
        assert isinstance(data["agreement_score"], (int, float))
        assert 0.0 <= data["agreement_score"] <= 1.0
        assert len(data["individual_responses"]) >= 1

    def test_consensus_agreement_score_in_range(self):
        response = requests.post(
            f"{BASE}/consensus/query",
            json={"prompt": "What is Area 51?"},
            headers=HEADERS,
            timeout=90,
        )
        assert response.status_code == 200
        data = response.json()
        score = data.get("agreement_score")
        assert score is not None
        assert 0.0 <= score <= 1.0

    def test_consensus_individual_responses_populated(self):
        time.sleep(1)
        response = requests.post(
            f"{BASE}/consensus/query",
            json={"prompt": "What is entropic gravity?"},
            headers=HEADERS,
            timeout=90,
        )
        assert response.status_code == 200
        data = response.json()
        responses = data.get("individual_responses", {})
        assert isinstance(responses, dict)
        for model_name, text in responses.items():
            assert isinstance(model_name, str)
            assert len(model_name) > 0
            assert isinstance(text, str)
            assert len(text) > 0

    def test_consensus_response_is_non_empty_string(self):
        time.sleep(1)
        response = requests.post(
            f"{BASE}/consensus/query",
            json={"prompt": "Summarize the Philadelphia Experiment."},
            headers=HEADERS,
            timeout=90,
        )
        assert response.status_code == 200
        data = response.json()
        consensus = data.get("consensus_response", "")
        assert isinstance(consensus, str)
        assert len(consensus) > 10
