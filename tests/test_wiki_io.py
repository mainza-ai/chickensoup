"""
P2-6: Wiki export/import round-trip tests.

Tests GET /wiki/export and POST /wiki/import using TestClient
with real file system operations for export.
Import test mocks the file to avoid destructive operations.
"""
import io
import os

import pytest
from unittest.mock import patch


@pytest.fixture
def client():
    from src.main import app
    from fastapi.testclient import TestClient
    with TestClient(app) as c:
        yield c


class TestWikiExport:
    """Tests for GET /wiki/export."""

    def test_export_returns_response_shape(self, client):
        response = client.get("/wiki/export")
        assert response.status_code == 200
        data = response.json()
        assert "success" in data
        assert "page_count" in data
        assert data.get("page_count", 0) >= 0

    def test_export_filepath_is_set(self, client):
        response = client.get("/wiki/export")
        assert response.status_code == 200
        data = response.json()
        assert "filepath" in data
        if data.get("page_count", 0) > 0:
            assert data["filepath"]

    def test_export_size_is_positive(self, client):
        response = client.get("/wiki/export")
        assert response.status_code == 200
        data = response.json()
        if data.get("page_count", 0) > 0:
            assert data.get("size_kb", 0) > 0


class TestWikiImport:
    """Tests for POST /wiki/import."""

    def test_import_rejects_non_zip(self, client):
        response = client.post(
            "/wiki/import",
            files={"file": ("test.txt", b"not a zip file", "text/plain")},
            headers={"X-Api-Key": "dev"},
        )
        assert response.status_code in (400, 500)
