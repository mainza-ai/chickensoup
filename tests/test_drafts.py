"""
P2-5: Draft promotion flow tests.

Tests GET /entities/drafts and POST /entities/{slug}/promote
using TestClient with real file system operations.
"""
import os
import shutil
import tempfile

import pytest

from src.config import settings
from src.wiki.writer import slugify


@pytest.fixture
def client():
    from src.main import app
    from fastapi.testclient import TestClient
    with TestClient(app) as c:
        yield c


def _drafts_dir():
    return os.path.join(settings.WIKI_DATA_DIR, "raw", "drafts")


def _create_draft_file(slug: str, title: str = None):
    drafts_dir = _drafts_dir()
    os.makedirs(drafts_dir, exist_ok=True)
    path = os.path.join(drafts_dir, f"{slug}.md")
    title = title or slug.replace("-", " ").title()
    with open(path, "w") as f:
        f.write(f"---\ntitle: \"{title}\"\ntags: [test]\n---\n\n# {title}\n\nTest draft content.")
    return path


def _remove_draft(slug: str):
    path = os.path.join(_drafts_dir(), f"{slug}.md")
    if os.path.exists(path):
        os.remove(path)


def _remove_published(slug: str):
    path = os.path.join(settings.WIKI_DATA_DIR, "entities", f"{slug}.md")
    if os.path.exists(path):
        os.remove(path)


class TestDraftsEndpoint:
    """Tests for GET /entities/drafts."""

    def test_list_drafts_returns_list(self, client):
        slug = slugify("Draft List Test")
        _create_draft_file(slug)
        try:
            response = client.get("/entities/drafts", headers={"X-Api-Key": "dev"})
            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, list)
        finally:
            _remove_draft(slug)

    def test_list_drafts_includes_created_draft(self, client):
        slug = slugify("Draft Inclusion Test")
        _create_draft_file(slug, title="Draft Inclusion Test")
        try:
            response = client.get("/entities/drafts", headers={"X-Api-Key": "dev"})
            data = response.json()
            slugs = [d.get("slug") or os.path.splitext(os.path.basename(d.get("file", "")))[0] for d in data]
            assert slug in slugs
        finally:
            _remove_draft(slug)


class TestPromoteEndpoint:
    """Tests for POST /entities/{slug}/promote."""

    def test_promote_existing_draft(self, client):
        slug = slugify("Promote Test Entity")
        _create_draft_file(slug, title="Promote Test Entity")
        try:
            response = client.post(f"/entities/{slug}/promote", headers={"X-Api-Key": "dev"})
            assert response.status_code == 200
            data = response.json()
            assert data.get("success") is True
            assert data.get("slug") == slug

            published_path = os.path.join(settings.WIKI_DATA_DIR, "entities", f"{slug}.md")
            assert os.path.exists(published_path)
        finally:
            _remove_draft(slug)
            _remove_published(slug)

    def test_promote_nonexistent_draft(self, client):
        response = client.post("/entities/nonexistent-slug-12345/promote", headers={"X-Api-Key": "dev"})
        assert response.status_code == 404

    def test_promote_creates_frontmatter(self, client):
        slug = slugify("Promote Frontmatter Test")
        _create_draft_file(slug, title="Promote Frontmatter Test")
        try:
            response = client.post(f"/entities/{slug}/promote", headers={"X-Api-Key": "dev"})
            assert response.status_code == 200

            published_path = os.path.join(settings.WIKI_DATA_DIR, "entities", f"{slug}.md")
            with open(published_path) as f:
                content = f.read()
            assert content.startswith("---")
            assert "title:" in content
        finally:
            _remove_draft(slug)
            _remove_published(slug)
