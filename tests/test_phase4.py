import pytest
import asyncio
from unittest.mock import patch, MagicMock
from src.multi_llm import MultiLLMConsensus
from src.quantum_scheduler import QuantumJobScheduler
from src.spacetime_engine.tensor import FieldGeometryTensor

import time

@patch("src.multi_llm.get_discovered")
def test_consensus_mock_matching(mock_discover):
    mock_discover.return_value = ("simulated", "http://localhost:8000/mock/v1", ["mock-gpt-4", "mock-llama-3"])
    consensus = MultiLLMConsensus()
    res = asyncio.run(consensus.generate_consensus("What is the speed of gravity?"))
    assert "consensus_response" in res
    assert res["agreement_score"] == 0.95
    assert "mock-gpt-4" in res["individual_responses"]

@patch("src.multi_llm.get_active_model", return_value="model-a")
@patch("src.multi_llm.get_discovered")
def test_consensus_active_provider(mock_discover, mock_get_active_model):
    # Mocking active provider discovery with multiple models
    mock_discover.return_value = ("omlx", "http://127.0.0.1:9000/v1", ["model-a", "model-b"])
    consensus = MultiLLMConsensus()

    # Mock sync query method to simulate responses
    with patch.object(consensus, "_query_model_sync") as mock_query:
        mock_query.side_effect = [
            ("model-a", "The quick brown fox jumps over the lazy dog"),
            ("model-b", "The quick brown fox jumps over the lazy cat")
        ]
        
        res = asyncio.run(consensus.generate_consensus("Test prompt"))
        assert res["agreement_score"] > 0.0
        assert "model-a" in res["individual_responses"]
        assert "model-b" in res["individual_responses"]

def test_quantum_scheduler_submission():
    scheduler = QuantumJobScheduler()
    geom = FieldGeometryTensor.create_flat()
    
    # Test submitting to IBM
    job_ibm = scheduler.submit_job("ibm_quantum", geom)
    assert job_ibm["job_id"] is not None
    assert job_ibm["provider"] == "IBM Quantum Runtime"
    assert job_ibm["status"] == "queued"

    # Test submitting to D-Wave
    job_dwave = scheduler.submit_job("dwave", geom)
    assert job_dwave["job_id"] is not None
    assert job_dwave["provider"] == "D-Wave Ocean"
    assert job_dwave["status"] == "completed"

    # Test retrieving job status
    status_ibm = scheduler.get_job_status(job_ibm["job_id"])
    assert status_ibm["status"] in ["queued", "running", "completed"]

def test_api_consensus_endpoint(client):
    time.sleep(0.005)
    payload = {
        "prompt": "Test query consensus",
        "system_instruction": "Be concise"
    }
    response = client.post("/consensus/query", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "consensus_response" in data
    assert "agreement_score" in data

def test_api_quantum_endpoints(client):
    time.sleep(0.005)
    payload = {
        "hardware": "ibm_quantum",
        "target_year": 1947,
        "energy_level": 1.5
    }
    # Submit job
    response = client.post("/quantum/schedule", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "job_id" in data
    job_id = data["job_id"]

    # Check status
    time.sleep(0.005)
    response_status = client.get(f"/quantum/job/{job_id}")
    assert response_status.status_code == 200
    status_data = response_status.json()
    assert status_data["job_id"] == job_id
    assert "status" in status_data

    # Check invalid job
    time.sleep(0.005)
    response_invalid = client.get("/quantum/job/non-existent-job-id")
    assert response_invalid.status_code == 404
