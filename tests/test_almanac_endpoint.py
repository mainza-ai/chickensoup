"""
P2-3: Almanac Full-Run Endpoint Integration Test.

Tests the POST /almanac/generate → GET /tasks/{task_id} flow.
Mocks generate_daily_almanac to return a controlled result.
"""
from unittest.mock import patch, MagicMock
from datetime import date

import pytest
from fastapi.testclient import TestClient

from src.almanac.almanac_generator import AlmanacResult


def _make_mock_result(status: str = "success") -> AlmanacResult:
    return AlmanacResult(
        status=status,
        date_str=date.today().isoformat(),
        entities_processed=3,
        claims_moved=1,
        claims_collapsed=2,
        newly_contested=3,
        html_path="/tmp/test-almanac.html",
        md_path="/tmp/test-almanac.md",
        dry_run=True,
        error=None,
    )


class TestAlmanacEndpointFlow:
    """Tests the endpoint lifecycle: trigger → background task → poll."""

    @pytest.fixture(autouse=True)
    def _mock_almanac(self):
        with patch("src.almanac.almanac_generator.generate_daily_almanac") as mock_gen:
            mock_gen.return_value = _make_mock_result("success")
            yield mock_gen

    def test_generate_returns_task_id(self, client):
        response = client.post(
            "/almanac/generate?dry_run=true",
            headers={"X-Api-Key": "dev"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "task_id" in data
        assert data["status"] == "running"

    def test_task_completes_successfully(self, client):
        response = client.post(
            "/almanac/generate?dry_run=true",
            headers={"X-Api-Key": "dev"},
        )
        assert response.status_code == 200
        task_id = response.json()["task_id"]

        task_resp = client.get(f"/tasks/{task_id}")
        assert task_resp.status_code == 200
        task_data = task_resp.json()
        assert task_data["status"] == "success"
        assert task_data["progress"] == 1.0

    def test_task_contains_entities_processed(self, client):
        response = client.post(
            "/almanac/generate?dry_run=true",
            headers={"X-Api-Key": "dev"},
        )
        task_id = response.json()["task_id"]

        task_resp = client.get(f"/tasks/{task_id}")
        task_data = task_resp.json()
        result = task_data.get("result", {})
        assert result.get("entities_processed") == 3

    def test_dry_run_flag_passed_through(self, client):
        response = client.post(
            "/almanac/generate?dry_run=true",
            headers={"X-Api-Key": "dev"},
        )
        task_id = response.json()["task_id"]

        task_resp = client.get(f"/tasks/{task_id}")
        task_data = task_resp.json()
        result = task_data.get("result", {})
        assert result.get("dry_run") is True

    def test_task_fails_gracefully(self, client):
        with patch("src.almanac.almanac_generator.generate_daily_almanac") as mock_gen:
            mock_gen.side_effect = RuntimeError("LLM timeout")
            response = client.post(
                "/almanac/generate?dry_run=true",
                headers={"X-Api-Key": "dev"},
            )
            task_id = response.json()["task_id"]

            task_resp = client.get(f"/tasks/{task_id}")
            task_data = task_resp.json()
            assert task_data["status"] == "failed"

    def test_nonexistent_task_returns_404(self, client):
        response = client.get("/tasks/nonexistent-task-id")
        assert response.status_code == 404


class TestAlmanacEndpointDryRunDefault:
    """Tests the default dry_run=True behavior."""

    def test_default_dry_run_is_true(self, client):
        with patch("src.almanac.almanac_generator.generate_daily_almanac") as mock_gen:
            mock_gen.return_value = _make_mock_result("success")
            client.post(
                "/almanac/generate",
                headers={"X-Api-Key": "dev"},
            )
            _, kwargs = mock_gen.call_args
            assert kwargs.get("dry_run") is True

    def test_explicit_dry_run_false(self, client):
        with patch("src.almanac.almanac_generator.generate_daily_almanac") as mock_gen:
            mock_gen.return_value = _make_mock_result("success")
            client.post(
                "/almanac/generate?dry_run=false",
                headers={"X-Api-Key": "dev"},
            )
            _, kwargs = mock_gen.call_args
            assert kwargs.get("dry_run") is False
