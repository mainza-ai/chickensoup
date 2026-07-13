import json
import pytest
from pathlib import Path
from unittest.mock import patch


def test_pulse_history_latest_per_entity_and_purge(client, tmp_path: Path):
    pulse_dir = tmp_path / "pulse"
    pulse_dir.mkdir()

    file_serpo = pulse_dir / "project-serpo-2026-07-12.json"
    file_roswell = pulse_dir / "roswell-crash-2026-07-12.json"
    file_empty = pulse_dir / "empty-entity-2026-07-12.json"

    file_serpo.write_text(json.dumps({
        "entity_name": "Project Serpo",
        "slug": "project-serpo",
        "date": "2026-07-12",
        "timestamp": "2026-07-12T12:00:00+00:00",
        "evidence_count": 5,
        "evidence": [{"claim_text": "c"}] * 5,
    }))
    file_roswell.write_text(json.dumps({
        "entity_name": "Roswell Crash",
        "slug": "roswell-crash",
        "date": "2026-07-12",
        "timestamp": "2026-07-12T11:00:00+00:00",
        "evidence_count": 0,
        "evidence": [],
    }))
    file_empty.write_text(json.dumps({
        "entity_name": "Empty Entity",
        "slug": "empty-entity",
        "date": "2026-07-12",
        "timestamp": "2026-07-12T10:00:00+00:00",
        "evidence_count": 0,
        "evidence": [],
    }))

    with patch("src.wiki.paths.get_pulse_dir", return_value=pulse_dir), \
         patch("src.wiki.pulse_writer.get_pulse_dir", return_value=pulse_dir):
        response = client.get("/pulse/history?limit=50")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 3
        assert data["unique_entities"] == 3
        assert data["empty_count"] == 2

        purge_response = client.post("/pulse/purge-empty")
        assert purge_response.status_code == 200
        purge_data = purge_response.json()
        assert purge_data["purged_count"] == 2
        assert purge_data["status"] == "success"

        assert file_serpo.exists()
        assert not file_roswell.exists()
        assert not file_empty.exists()

        history_response = client.get("/pulse/history")
        assert history_response.status_code == 200
        history_data = history_response.json()
        assert history_data["total"] == 1
