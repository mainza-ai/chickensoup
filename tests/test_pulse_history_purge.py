import json
import pytest
from pathlib import Path
from unittest.mock import patch

def test_pulse_history_ordering_and_purge(client, tmp_path):
    # Setup mock pulse directory with test json and markdown files
    pulse_dir = tmp_path / "pulse"
    pulse_dir.mkdir()

    # Write files:
    # 1. entity-1 oldest (no claims)
    # 2. entity-1 newest (5 claims)
    # 3. entity-2 (0 claims)
    
    file_old = pulse_dir / "entity-one-2026-07-12-1.json"
    file_new = pulse_dir / "entity-one-2026-07-12-2.json"
    file_other = pulse_dir / "entity-two-2026-07-12-1.json"
    
    md_old = pulse_dir / "entity-one-2026-07-12-1.md"
    md_new = pulse_dir / "entity-one-2026-07-12-2.md"
    md_other = pulse_dir / "entity-two-2026-07-12-1.md"

    # Write contents
    for f in [md_old, md_new, md_other]:
        f.write_text("Markdown content")

    file_old.write_text(json.dumps({
        "entity_name": "Entity One",
        "slug": "entity-one",
        "date": "2026-07-12",
        "timestamp": "2026-07-12T10:00:00Z",
        "evidence_count": 0,
        "evidence": []
    }))

    file_new.write_text(json.dumps({
        "entity_name": "Entity One",
        "slug": "entity-one",
        "date": "2026-07-12",
        "timestamp": "2026-07-12T11:00:00Z",
        "evidence_count": 5,
        "evidence": [{"claim_text": "Sample claim"}] * 5
    }))

    file_other.write_text(json.dumps({
        "entity_name": "Entity Two",
        "slug": "entity-two",
        "date": "2026-07-12",
        "timestamp": "2026-07-12T12:00:00Z",
        "evidence_count": 0,
        "evidence": []
    }))

    # Patch get_pulse_dir to return our temporary path
    with patch("src.wiki.paths.get_pulse_dir", return_value=pulse_dir), \
         patch("src.wiki.pulse_writer.get_pulse_dir", return_value=pulse_dir):
        # 1. Test GET /pulse/history with entity_name returns newest first
        response = client.get("/pulse/history?entity_name=Entity+One")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2
        # Check ordering: first entry should be the newest one (entity-one-2026-07-12-2.json)
        assert data["pulses"][0]["file"] == str(file_new)
        assert data["pulses"][0]["evidence_count"] == 5
        assert data["pulses"][1]["file"] == str(file_old)
        assert data["pulses"][1]["evidence_count"] == 0

        # 2. Test POST /pulse/purge-empty deletes files with 0 evidence
        purge_response = client.post("/pulse/purge-empty")
        assert purge_response.status_code == 200
        purge_data = purge_response.json()
        assert purge_data["purged_count"] == 2
        assert purge_data["status"] == "success"

        # Verify filesystem changes
        assert file_new.exists()
        assert md_new.exists()
        assert not file_old.exists()
        assert not md_old.exists()
        assert not file_other.exists()
        assert not md_other.exists()
        
        # Verify history endpoint now returns only the remaining active pulse
        history_response = client.get("/pulse/history")
        assert history_response.status_code == 200
        history_data = history_response.json()
        assert history_data["total"] == 1
        assert history_data["pulses"][0]["file"] == str(file_new)
