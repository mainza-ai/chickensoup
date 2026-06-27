import os
import pytest
import tempfile
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

from src.config import settings
from src.wiki.backup import create_snapshot
from src.wiki.cleanup import _should_preserve

def test_api_ingest_file_size_limit(client):
    # Simulate a file exceeding the 50MB limit
    large_payload = b"a" * (50 * 1024 * 1024 + 1)
    response = client.post(
        "/ingest/file",
        files={"file": ("large-file.md", large_payload, "text/markdown")}
    )
    assert response.status_code == 400
    assert "size exceeds" in response.json()["detail"]

def test_api_ingest_folder_size_limit(client):
    # Simulate a folder zip file exceeding the 50MB limit
    large_payload = b"a" * (50 * 1024 * 1024 + 1)
    response = client.post(
        "/ingest/folder",
        files={"file": ("large-folder.zip", large_payload, "application/zip")}
    )
    assert response.status_code == 400
    assert "size exceeds" in response.json()["detail"]

def test_clear_content_safeguard(client):
    # Call without confirm query parameter
    response = client.post("/wiki/clear-content")
    assert response.status_code == 400
    assert "destructive operation" in response.json()["detail"]

    # Call with confirm=true (we patch clear_content_pages and neo4j get_driver so it runs purely in-memory)
    mock_res = {
        "success": True,
        "dry_run": False,
        "preserved_count": 0,
        "deleted_count": 0,
        "protected_added_count": 0,
        "preserved_slugs": [],
        "deleted_slugs": []
    }
    with patch("src.wiki.cleanup.clear_content_pages", return_value=mock_res), \
         patch("src.knowledge_graph.ingest.ingest_wiki_page", return_value=(0, 0)):
        response = client.post("/wiki/clear-content?confirm=true")
        assert response.status_code == 200
        assert response.json()["success"] is True

def test_recursive_backup_exclusion():
    # Verify backup directories are excluded from os.walk during backups
    # Create a temporary directory structure
    with tempfile.TemporaryDirectory() as tmpdir:
        wiki_dir = os.path.join(tmpdir, "wiki")
        backup_dir = os.path.join(wiki_dir, "backups")
        
        os.makedirs(os.path.join(wiki_dir, "entities"), exist_ok=True)
        os.makedirs(os.path.join(backup_dir, "auto"), exist_ok=True)
        
        # Create a mock wiki page
        with open(os.path.join(wiki_dir, "entities", "alien.md"), "w") as f:
            f.write("Alien info")
            
        # Create an existing backup zip file (which should NOT be walked recursively)
        with open(os.path.join(backup_dir, "auto", "old-backup.zip"), "w") as f:
            f.write("mock-zip-bytes")
            
        with patch("src.wiki.backup.WIKI_DIR", wiki_dir), \
             patch("src.wiki.backup.BACKUP_DIR", backup_dir), \
             patch("src.wiki.backup.settings") as mock_settings:
            
            mock_settings.WIKI_BACKUP_ENABLED = True
            mock_settings.WIKI_BACKUP_DIR = "backups"
            
            zip_path = create_snapshot("auto")
            assert zip_path is not None
            assert os.path.exists(zip_path)
            
            # Check contents of the zip
            import zipfile
            with zipfile.ZipFile(zip_path, "r") as zf:
                namelist = zf.namelist()
                # Should contain the wiki page
                assert any("entities/alien.md" in name for name in namelist)
                # Should NOT contain the old backup file
                assert not any("old-backup.zip" in name for name in namelist)

def test_should_preserve_untagged():
    # If in entities or concepts and lacks tags, return False (do not preserve)
    fm_no_tags = {"title": "Alien"}
    assert _should_preserve(fm_no_tags, "entities", "alien.md") is False

    # If tagged with engineering tags, return True (preserve)
    fm_eng = {"title": "System Config", "tags": ["settings"]}
    assert _should_preserve(fm_eng, "entities", "config.md") is True

    # If tagged with content tags, return False (delete)
    fm_content = {"title": "UFO Roswell", "tags": ["ufo"]}
    assert _should_preserve(fm_content, "entities", "roswell.md") is False

def test_delete_protected_override_rules(client):
    # Test deleting a protected engineering/projects page
    fm_project = {"title": "Engine", "protected": True, "tags": ["architecture"]}
    pdata_project = {"frontmatter": fm_project, "body": "content", "path": "path"}
    
    with patch("src.main.read_page", return_value=pdata_project):
        response = client.delete("/wiki/page/engine?page_type=projects")
        assert response.status_code == 403
        assert "core engineering/project file" in response.json()["detail"]
        
        # Even with force=true, core engineering file deletion is blocked
        response_force = client.delete("/wiki/page/engine?page_type=projects&force=true")
        assert response_force.status_code == 403
        
    # Test deleting a protected content page without force parameter
    fm_content = {"title": "UFO Lazar", "protected": True, "tags": ["ufo"]}
    pdata_content = {"frontmatter": fm_content, "body": "content", "path": "path"}
    
    with patch("src.main.read_page", return_value=pdata_content):
        response = client.delete("/wiki/page/lazar?page_type=entities")
        assert response.status_code == 403
        assert "is protected. Use the 'force=true' parameter" in response.json()["detail"]
        
        # Deleting with force=true should bypass if we mock delete_page, create_snapshot and get_driver
        with patch("src.main.delete_page", return_value=True), \
             patch("src.wiki.backup.create_snapshot", return_value="zip"), \
             patch("src.knowledge_graph.connection.neo4j_conn.get_driver", return_value=None):
            response_force = client.delete("/wiki/page/lazar?page_type=entities&force=true")
            assert response_force.status_code == 200
            assert response_force.json()["success"] is True

def test_delete_wiki_page_obsidian_integrity(client):
    # Test referential integrity Obsidian link cleaning
    fm_deleted = {"title": "Roswell Crash", "tags": ["ufo"]}
    pdata_deleted = {"frontmatter": fm_deleted, "body": "body", "path": "path"}
    
    # Target page referencing deleted page
    fm_ref = {"title": "Alien Interview", "tags": ["alien"]}
    body_ref = "See [[Roswell Crash]] and [[Roswell Crash|Roswell Crash Site]] for more info."
    pdata_ref = {"frontmatter": fm_ref, "body": body_ref, "path": "ref_path"}
    
    with tempfile.TemporaryDirectory() as tmpdir:
        wiki_root = tmpdir
        os.makedirs(os.path.join(wiki_root, "entities"), exist_ok=True)
        
        # Mock settings and read_page / write_page filesystem interactions
        with patch("src.main.settings") as mock_settings, \
             patch("src.main.read_page") as mock_read, \
             patch("src.main.write_page") as mock_write, \
             patch("src.main.delete_page", return_value=True), \
             patch("src.wiki.backup.create_snapshot", return_value="zip"), \
             patch("src.knowledge_graph.connection.neo4j_conn.get_driver", return_value=None), \
             patch("os.path.isdir", return_value=True), \
             patch("os.listdir", return_value=["alien-interview.md"]):
             
            mock_settings.WIKI_DATA_DIR = wiki_root
            
            # Mock read_page side effect
            def side_effect(slug, page_type):
                if slug == "roswell-crash":
                    return pdata_deleted
                if slug == "alien-interview":
                    return pdata_ref
                return None
                
            mock_read.side_effect = side_effect
            
            response = client.delete("/wiki/page/roswell-crash?page_type=entities&hard=true")
            assert response.status_code == 200
            
            # Verify write_page was called to update reference
            assert mock_write.called
            write_args = mock_write.call_args[1]
            # Link wrappers [[...]] should be stripped and replaced with text/alias
            assert "See Roswell Crash and Roswell Crash Site for more info." in write_args["body"]
