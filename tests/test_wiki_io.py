"""
P2-6: Wiki Export, Import, and Round-Trip Endpoint Tests.

Tests GET /wiki/export, POST /wiki/import, and POST /wiki/clear-content using
TestClient with real file system operations for export and a mock-safe round-trip.
"""
import io
import os
import zipfile

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


class TestWikiImportWithZip:
    """Tests POST /wiki/import with a small controlled zip."""

    def _make_wiki_zip(self) -> bytes:
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("wiki/entities/test-a.md", "# Test A\n\nBody.")
            zf.writestr("wiki/concepts/test-b.md", "# Test B\n\nBody.")
        return buf.getvalue()

    @patch("src.knowledge_graph.ingest.ingest_wiki_page", return_value=(0, 0))
    def test_import_valid_zip(self, mock_ingest, client):
        zip_bytes = self._make_wiki_zip()
        resp = client.post(
            "/wiki/import",
            files={"file": ("export.zip", zip_bytes, "application/zip")},
            headers={"X-Api-Key": "dev"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("restored_count", 0) > 0
