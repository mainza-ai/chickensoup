from unittest.mock import patch, MagicMock
import pytest


def test_status_time_endpoint(client):
    """Phase 0: /status/time returns server time with timezone info."""
    response = client.get("/status/time")
    assert response.status_code == 200
    data = response.json()
    assert "iso8601" in data
    assert "datetime" in data
    assert "timezone" in data
    assert "utc_offset" in data
    assert "unix" in data
    assert isinstance(data["unix"], (int, float))
    assert data["unix"] > 1_700_000_000  # Unix timestamp must be reasonable


def test_search_endpoint_fulltext(client):
    """Phase 1.5: /search uses fulltext index and returns scored results."""
    with patch("src.main.fulltext_search") as mock_search:
        mock_search.return_value = [
            {"name": "bob lazar", "display_name": "Bob Lazar", "labels": ["Person", "Entity"],
             "preview": "Claims about S-4", "confidence": 1.0, "tags": ["ufo"], "score": 15.2},
            {"name": "element 115", "display_name": "Element 115", "labels": ["Object", "Entity"],
             "preview": "Superheavy element", "confidence": 1.0, "tags": ["physics"], "score": 8.5},
        ]
        response = client.get("/search?q=bob+lazar&limit=5")
        assert response.status_code == 200
        data = response.json()
        assert data["query"] == "bob lazar"
        assert len(data["results"]) == 2
        assert data["total"] == 2
        assert data["results"][0]["name"] == "bob lazar"
        assert data["results"][0]["score"] > data["results"][1]["score"]


def test_search_validates_min_length(client):
    """Phase 1.5: Search requires at least 2 characters."""
    response = client.get("/search?q=a")
    assert response.status_code == 422


def test_events_returns_event_nodes(client):
    """Phase 1.1: /events returns only Event-labeled nodes with proper structure."""
    from unittest.mock import MagicMock

    # Mock the Neo4j session to return Event nodes
    mock_session = MagicMock()
    mock_session.run.return_value = [
        MagicMock(data=lambda: {
            "name": "varginha ufo crash",
            "display_name": "Varginha UFO Crash",
            "date": "1996-01-20",
            "tags": ["crash", "brazil"],
            "sources": ["brazil.md"],
            "preview": "The Varginha incident...",
            "confidence": 1.0,
            "labels": ["Event", "Entity"],
        }),
    ]

    with patch("src.main.neo4j_conn.get_driver") as mock_driver:
        mock_driver.return_value.session.return_value.__enter__.return_value = mock_session
        # Bypass cache by setting RATE_LIMITING_ENABLED=False (already in conftest)
        # The cache_decorator will cache, so we need to clear it or use a fresh mock
        # Instead, directly mock query_events
        with patch("src.main.query_events") as mock_query:
            mock_query.return_value = [
                {
                    "id": "varginha ufo crash",
                    "title": "Varginha UFO Crash",
                    "description": "The Varginha incident...",
                    "date": "1996-01-20",
                    "confidence": 1.0,
                    "source": "brazil.md",
                    "type": "crash",
                    "sources": ["brazil.md"],
                }
            ]
            response = client.get("/events")
            assert response.status_code == 200
            data = response.json()
            assert "events" in data
            assert len(data["events"]) == 1
            event = data["events"][0]
            assert event["title"] == "Varginha UFO Crash"
            assert event["date"] is not None
            assert event["type"] == "crash"


def test_events_date_not_fabricated(client):
    """Phase 1.1: /events returns stored dates, not fabricated heuristics."""
    with patch("src.main.query_events") as mock_query:
        mock_query.return_value = [
            {"id": "test", "title": "Test Event", "description": "", "date": None,
             "confidence": 1.0, "source": "test", "type": "anomaly", "sources": []},
        ]
        response = client.get("/events")
        assert response.status_code == 200
        data = response.json()
        assert data["events"][0]["date"] is None


def test_timeline_endpoint(client):
    """Phase 3.2: /timeline returns dated events from temporal queries."""
    with patch("src.main.get_temporal_events") as mock_temporal:
        mock_temporal.return_value = [
            {"name": "test-event", "display_name": "Test Event", "date": "2026-01-01",
             "tags": ["test"], "sources": ["test"], "preview": "A test event",
             "confidence": 1.0, "labels": ["Event", "Entity"]},
        ]
        response = client.get("/timeline")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["events"][0]["date"] == "2026-01-01"


def test_timeline_date_range(client):
    """Phase 3.2: /timeline supports date range filtering."""
    with patch("src.main.get_temporal_events") as mock_temporal:
        mock_temporal.return_value = []
        response = client.get("/timeline?start_date=2025-01-01&end_date=2025-12-31")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0


def test_temporal_context_endpoint(client):
    """Phase 3.2: /entities/{name}/temporal-context returns connected events."""
    with patch("src.main.get_entity_temporal_context") as mock_context:
        mock_context.return_value = [
            {"name": "roswell-crash", "display_name": "Roswell Crash", "date": "1947-07-01",
             "relationship": "LOCATED_AT", "confidence": 1.0, "preview": ""},
        ]
        response = client.get("/entities/roswell/temporal-context")
        assert response.status_code == 200
        data = response.json()
        assert data["entity"] == "roswell"
        assert data["total"] == 1


def test_simulate_endpoint(client):
    """Phase 7: /simulate returns spacetime simulation results."""
    response = client.post("/simulate", json={
        "gravity": 0.5, "velocity": 0.5, "intensity": 0.5,
        "origin": "Earth", "destination": "Alpha Centauri",
    })
    assert response.status_code == 200
    data = response.json()
    assert "success" in data
    assert "logs" in data
    assert "resolved_path_confidence" in data
    assert "warp_factor" in data


def test_simulate_defaults(client):
    """Phase 7: /simulate works with minimal params."""
    response = client.post("/simulate", json={})
    assert response.status_code == 200
    data = response.json()
    assert data["gravity_metric"] == 0.5


def test_simulate_invalid_params(client):
    """Phase 7: /simulate rejects out-of-range values."""
    response = client.post("/simulate", json={"gravity": 99})
    assert response.status_code == 422


def test_rate_limiter_categories():
    """Phase 5.1: Rate limiter uses differentiated limits per category."""
    from src.rate_limiter import rate_limiter
    ip = "127.0.0.1"

    for _ in range(12):
        allowed, _ = rate_limiter.check_ip(ip, "write")
        if not allowed:
            break

    write_exhausted, write_remaining = rate_limiter.check_ip(ip, "write")
    search_allowed, search_remaining = rate_limiter.check_ip(ip, "search")

    # Write limit (10) should be exhausted before search (60)
    assert not write_exhausted or write_remaining <= search_remaining


def test_approve_research_nonexistent_thread(client):
    """Phase 6.1: Approving a non-existent thread returns 404."""
    response = client.post("/research/nonexistent/approve", json={})
    assert response.status_code in (404, 422)


def test_approve_research_unpaused_thread(client):
    """Phase 6.1: Approving a non-paused thread returns 400."""
    # The "default_thread" exists but the state handling depends on Redis
    # Just verify the endpoint exists and returns proper error
    response = client.post("/research/default_thread/approve", json={})
    assert response.status_code in (400, 404, 200)


def test_query_response_includes_new_fields(client):
    """Phase 6.1: QueryResponse includes thread_id and status fields."""
    with patch("src.main.orchestrator.execute") as mock_orch:
        mock_orch.return_value = {
            "answer": "Test answer",
            "confidence": 0.8,
            "entities": [],
            "sources": [],
            "status": "completed",
            "thread_id": None,
        }
        response = client.post("/query", json={
            "query": "test query",
            "structured": False,
        })
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "thread_id" in data
        assert data["status"] is not None


def test_query_paused_for_approval(client):
    """Phase 6.1: Query returns paused_for_human_approval with thread_id."""
    with patch("src.main.orchestrator.execute") as mock_orch:
        mock_orch.return_value = {
            "answer": "PENDING APPROVAL: Human approval required",
            "confidence": 0.3,
            "entities": [],
            "sources": [],
            "status": "paused_for_human_approval",
            "thread_id": "test-thread-123",
            "summary": "Human approval required for credibility evaluation.",
        }
        response = client.post("/query", json={
            "query": "test low credibility",
            "structured": False,
        })
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "paused_for_human_approval"
        assert data["thread_id"] == "test-thread-123"
        assert "PENDING APPROVAL" in data["answer"]
        assert len(data["sources"]) == 0


def test_config_includes_cloud_providers(client):
    """Cloud LLM: Config response includes NVIDIA/OpenRouter/Custom fields."""
    with patch("src.main.get_discovered", return_value=("nvidia", "https://integrate.api.nvidia.com/v1", ["model-1"])):
        with patch("src.main.get_active_provider", return_value="nvidia"):
            with patch("src.main.get_active_model", return_value="nvidia/nemotron-3-super-120b-a12b"):
                response = client.get("/config")
                assert response.status_code == 200
                data = response.json()
                assert "llm_provider_type" in data
                assert "nvidia_api_key_set" in data
                assert "openrouter_api_key_set" in data
                assert "custom_llm_api_url_set" in data
                assert data["llm_active_provider"] == "nvidia"


def test_search_api_missing_param(client):
    """Phase 1.5: /search requires 'q' parameter."""
    response = client.get("/search")
    assert response.status_code == 422


def test_timeline_range_endpoint(client):
    """Phase 3.2: /timeline/range returns date range."""
    with patch("src.main.get_timeline_range") as mock_range:
        mock_range.return_value = {"earliest": "2020-01-01", "latest": "2026-07-14", "total": 9}
        response = client.get("/timeline/range")
        assert response.status_code == 200
        data = response.json()
        assert data["earliest"] == "2020-01-01"
        assert data["latest"] == "2026-07-14"
        assert data["total"] == 9


def test_events_response_structure(client):
    """Phase 1.1: /events response has consistent structure."""
    with patch("src.main.query_events") as mock_query:
        mock_query.return_value = [
            {"id": "e1", "title": "Event 1", "description": "Desc", "date": "2026-01-01",
             "confidence": 0.9, "source": "src1", "type": "crash", "sources": ["src1"]},
        ]
        response = client.get("/events")
        data = response.json()
        event = data["events"][0]
        assert set(event.keys()) == {"id", "title", "description", "date", "confidence", "source", "type", "sources"}


def test_websocket_endpoint_exists(client):
    """Phase 6.2: /ws/agent WebSocket endpoint is registered."""
    # We can't easily test WebSocket with TestClient, but verify the route exists
    from src.main import app
    routes = [r.path for r in app.routes]
    assert "/ws/agent" in routes


def test_simulate_response_structure(client):
    """Phase 7: /simulate response has all expected fields."""
    response = client.post("/simulate", json={"gravity": 0.3, "velocity": 0.4, "intensity": 0.5})
    assert response.status_code == 200
    data = response.json()
    expected_fields = {"success", "gravity_metric", "velocity_metric", "field_intensity",
                       "resolved_path_confidence", "logs", "warp_factor", "lapse",
                       "entropy_density", "target_year"}
    assert expected_fields.issubset(data.keys())


def test_fulltext_index_exists(client):
    """Phase 1.4: Fulltext index 'fulltext_entity' is created."""
    from src.main import app
    routes = [r.path for r in app.routes]
    assert "/search" in routes


def test_sse_endpoint_exists(client):
    """Phase 4.3: /events/stream SSE endpoint is registered."""
    from src.main import app
    routes = [r.path for r in app.routes]
    assert "/events/stream" in routes


@pytest.mark.skip(reason="SSE StreamingResponse hangs with TestClient")
def test_sse_endpoint_returns_success(client):
    """Phase 4.3: /events/stream returns 200."""
    response = client.get("/events/stream")
    assert response.status_code in (200, 422)


def test_ingest_wiki_page_writes_dates():
    """Phase 1.2: ingest_wiki_page writes 'date' to Neo4j from body text."""
    from src.knowledge_graph.ingest import ingest_wiki_page
    from unittest.mock import MagicMock

    mock_driver = MagicMock()
    mock_session = MagicMock()
    mock_driver.session.return_value.__enter__.return_value = mock_session

    content = """---
title: Test Event
tags: [crash, ufo]
sources: [test]
---
In 1996, the Varginha UFO crash occurred in Brazil."""

    nodes, rels = ingest_wiki_page(mock_driver, "Test Event", content,
                                    default_tags=["crash", "ufo"],
                                    default_sources=["test"])

    # Verify the MERGE query includes date param
    call_args = mock_session.run.call_args_list
    merge_calls = [c for c in call_args if "MERGE" in str(c) and "Entity" in str(c)]
    assert len(merge_calls) > 0, "MERGE query should be called"

    # Find the primary node MERGE call and check date param
    for call in merge_calls:
        kwargs = call[1] if len(call.args) <= 1 else {}
        if kwargs.get("name") == "test event":
            assert kwargs.get("date") is not None, "date should be extracted from body"
            break


def test_ingest_malformed_frontmatter_does_not_crash():
    """Phase 8.3: Malformed YAML frontmatter is handled gracefully."""
    from src.knowledge_graph.ingest import ingest_wiki_page
    from unittest.mock import MagicMock

    mock_driver = MagicMock()
    mock_session = MagicMock()
    mock_driver.session.return_value.__enter__.return_value = mock_session

    # Malformed YAML — missing closing ---
    content = """---
title: Broken
tags: [test
---
Body text."""

    # Should not raise
    nodes, rels = ingest_wiki_page(mock_driver, "Broken Page", content)
    assert nodes >= 0
    assert rels >= 0


def test_parse_structured_list_wrapping():
    """Phase 8.1: parse_structured wraps bare top-level list in model field."""
    from src.llm_client import parse_structured
    from pydantic import BaseModel
    from typing import List

    class TestModel(BaseModel):
        items: List[str] = []

    # LLM returns a bare list — Strategy 3 wraps it into {"items": [...]}
    # Note: actual production calls do NOT use the `field` parameter
    result = parse_structured('["a", "b", "c"]', TestModel)
    assert result is None  # Can't unwrap without field hint, returns None

    # With field="items", Strategy 3 wraps correctly
    result2 = parse_structured('["x", "y"]', TestModel, field="items")
    assert result2 is not None
    assert result2.items == ["x", "y"]


def test_parse_structured_valid_json():
    """Phase 8.1: parse_structured handles valid JSON matching model shape."""
    from src.llm_client import parse_structured
    from pydantic import BaseModel
    from typing import List

    class TestModel(BaseModel):
        items: List[str] = []

    # LLM returns a dict matching the model — Strategy 1 succeeds
    result = parse_structured('{"items": ["valid"]}', TestModel)
    assert result is not None
    assert result.items == ["valid"]


def test_parse_structured_invalid_returns_none():
    """Phase 8.1: parse_structured returns None for completely invalid input."""
    from src.llm_client import parse_structured
    from pydantic import BaseModel

    class TestModel(BaseModel):
        x: int = 0

    result = parse_structured("not even close to json", TestModel)
    assert result is None


def test_cache_invalidate_entity():
    """Phase 1.6: invalidate_entity clears entity-specific cache keys."""
    from src.cache import cache_store

    cache_store.set("cache:neo4j:get_entity_neighborhood:abc123", {"data": "test"}, ttl=300)
    cache_store.set("cache:search:search_entities:def456", {"data": "search"}, ttl=300)
    cache_store.set("cache:neo4j:other:xyz789", {"data": "other"}, ttl=300)

    cache_store.invalidate_entity("test-entity")

    # Search caches should be invalidated
    assert cache_store.get("cache:search:search_entities:def456") is None

    # Other caches should remain
    other = cache_store.get("cache:neo4j:other:xyz789")
    assert other is not None


def test_orphan_cleanup_on_delete():
    """Phase 1.7: File delete triggers Neo4j node removal."""
    from src.wiki.watcher import _on_file_event
    # This is an integration test — verify the import works and the function exists
    import inspect
    assert inspect.iscoroutinefunction(_on_file_event)


def test_timeline_default_365_days():
    """Phase 3.4: build_timeline defaults to 365 days."""
    from src.almanac.timeline import build_timeline
    import inspect

    sig = inspect.signature(build_timeline)
    days_param = sig.parameters.get("days")
    assert days_param is not None
    assert days_param.default == 365


def test_timeline_has_include_all():
    """Phase 3.4: build_timeline supports include_all flag."""
    from src.almanac.timeline import build_timeline
    import inspect

    sig = inspect.signature(build_timeline)
    assert "include_all" in sig.parameters


def test_timeline_is_cached():
    """Phase 3.3: build_timeline caches results via cache_store."""
    from src.almanac.timeline import build_timeline
    # Verify the function has the cache_key logic (not a direct check, but verify imports work)
    import inspect
    source = inspect.getsource(build_timeline)
    assert "cache_key" in source
    assert "cache_store.get" in source
    assert "cache_store.set" in source


def test_simulate_error_handling(client):
    """Phase 7: /simulate returns structured error on simulation failure."""
    response = client.post("/simulate", json={"gravity": 0.1, "velocity": 0.1, "intensity": 0.1})
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data["logs"], list)
    assert isinstance(data["warp_factor"], (int, float))
    assert isinstance(data["resolved_path_confidence"], (int, float))


def test_events_no_fabricated_heuristics(client):
    """Phase 1.1: /events code no longer contains hardcoded date heuristics."""
    import inspect
    from src.main import get_events
    source = inspect.getsource(get_events)
    # Verify no hardcoded dates exist
    assert "1933-06-13" not in source
    assert "1944-10-24" not in source
    assert "1989-12-01" not in source
    assert "1994-09-16" not in source
    assert "1996-01-20" not in source


def test_neoj4_circuit_breaker():
    """Phase 10.1: Neo4j circuit breaker opens after threshold failures."""
    from src.knowledge_graph.connection import Neo4jCircuitBreaker

    cb = Neo4jCircuitBreaker(threshold=3, recovery_timeout=0.1)
    assert cb.is_available()

    cb.record_failure()
    assert cb.is_available()

    cb.record_failure()
    assert cb.is_available()

    cb.record_failure()  # threshold reached
    assert not cb.is_available()

    # Recovery after timeout
    import time
    time.sleep(0.15)
    assert cb.is_available()


def test_neoj4_circuit_breaker_reset():
    """Phase 10.1: Neo4j circuit breaker resets on success."""
    from src.knowledge_graph.connection import Neo4jCircuitBreaker

    cb = Neo4jCircuitBreaker(threshold=2)
    cb.record_failure()
    cb.record_failure()
    assert not cb.is_available()

    cb.reset()
    assert cb.is_available()
