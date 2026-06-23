from unittest.mock import patch, MagicMock

def test_api_status_healthy(client):
    # Mock Neo4j check_health to return True, Redis ping to return True
    with patch("src.main.discover_active_provider", return_value=("omlx", "http://127.0.0.1:9000/v1", ["model-1"])):
        response = client.get("/status")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["llm_provider"] == "omlx"
        assert data["llm_connected"] is True
        assert data["neo4j_connected"] is True
        assert data["redis_connected"] is True

def test_api_status_degraded(client, mock_neo4j, mock_redis):
    # Mock Neo4j check_health to return False, discovery returns "simulated" (so llm_connected is False)
    mock_neo4j.check_health.return_value = False
    
    with patch("src.main.discover_active_provider", return_value=("simulated", "http://localhost:8000/mock/v1", [])):
        response = client.get("/status")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "degraded"
        assert data["llm_connected"] is False
        assert data["neo4j_connected"] is False

def test_api_models_endpoint(client):
    with patch("src.main.discover_active_provider", return_value=("omlx", "http://127.0.0.1:9000/v1", ["omlx-m1"])):
        response = client.get("/models")
        assert response.status_code == 200
        data = response.json()
        assert data["provider"] == "omlx"
        assert data["models"] == ["omlx-m1"]

def test_api_navigate_endpoint(client):
    # Test navigating through spacetime using mock spacetime calculations
    payload = {
        "origin": "Earth-2026",
        "destination": "Earth-1947",
        "target_year": 1947,
        "energy_level": 2.5
    }
    response = client.post("/navigate", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "success" in data
    assert "path" in data
    assert "warp_factor" in data
    assert "divergence_risk" in data
    assert "geometry_tensor" in data
    assert len(data["path"]) > 0

def test_api_query_endpoint(client, mock_neo4j):
    mock_driver = MagicMock()
    mock_neo4j.get_driver.return_value = mock_driver
    
    orchestrator_mock_res = {
        "status": "completed",
        "answer": "Found relevant connections in the lore: Roswell Craft.",
        "confidence": 0.95,
        "entities": ["Roswell Craft"],
        "sources": ["Local Wiki Knowledge Graph"]
    }
    
    with patch("src.main.orchestrator.execute", return_value=orchestrator_mock_res):
        response = client.post("/query", json={"query": "Roswell", "structured": False})
        assert response.status_code == 200
        data = response.json()
        assert "Roswell Craft" in data["answer"]
        assert data["confidence"] == 0.95
        assert data["entities"] == ["Roswell Craft"]

