import json
from datetime import date
from pathlib import Path
from unittest.mock import patch


FIXED_TODAY = "2026-07-12"


def test_history_returns_latest_per_entity(tmp_path: Path):
    pulse_dir = tmp_path / "pulse"
    pulse_dir.mkdir()

    older = pulse_dir / "project-serpo-2026-07-10.json"
    latest = pulse_dir / "project-serpo-2026-07-12.json"
    other = pulse_dir / "roswell-crash-2026-07-12.json"

    older.write_text(json.dumps({
        "entity_name": "Project Serpo",
        "slug": "project-serpo",
        "date": "2026-07-10",
        "timestamp": "2026-07-10T10:00:00+00:00",
        "evidence_count": 0,
        "evidence": [],
    }))
    latest.write_text(json.dumps({
        "entity_name": "Project Serpo",
        "slug": "project-serpo",
        "date": "2026-07-12",
        "timestamp": "2026-07-12T12:00:00+00:00",
        "evidence_count": 5,
        "evidence": [{"claim_text": "c"}] * 5,
    }))
    other.write_text(json.dumps({
        "entity_name": "Roswell Crash",
        "slug": "roswell-crash",
        "date": "2026-07-12",
        "timestamp": "2026-07-12T12:00:00+00:00",
        "evidence_count": 3,
        "evidence": [{"claim_text": "c"}] * 3,
    }))

    with patch("src.wiki.paths.get_pulse_dir", return_value=pulse_dir), \
         patch("src.wiki.pulse_writer.get_pulse_dir", return_value=pulse_dir):
        from src.main import app
        from fastapi.testclient import TestClient
        client = TestClient(app)
        response = client.get("/pulse/history?limit=50")
        assert response.status_code == 200
        data = response.json()

        serpo = next(p for p in data["pulses"] if p["entity_name"] == "Project Serpo")
        assert serpo["evidence_count"] == 5
        assert data["unique_entities"] == 2
        assert data["total"] == 2


def test_history_counts_are_correct(tmp_path: Path):
    pulse_dir = tmp_path / "pulse"
    pulse_dir.mkdir()

    for entity, count in [("alpha", 5), ("beta", 0), ("gamma", 3)]:
        p = pulse_dir / f"{entity}-{FIXED_TODAY}.json"
        p.write_text(json.dumps({
            "entity_name": entity,
            "slug": entity,
            "date": FIXED_TODAY,
            "timestamp": "2026-07-12T12:00:00+00:00",
            "evidence_count": count,
            "evidence": [{"claim_text": f"c{count}"}] * count,
        }))

    with patch("src.wiki.paths.get_pulse_dir", return_value=pulse_dir), \
         patch("src.wiki.pulse_writer.get_pulse_dir", return_value=pulse_dir), \
         patch("src.wiki.pulse_writer.date") as mock_date:
        mock_date.today.return_value = date.fromisoformat(FIXED_TODAY)
        mock_date.isoformat = date.isoformat
        from src.main import app
        from fastapi.testclient import TestClient
        client = TestClient(app)
        response = client.get("/pulse/history?limit=50")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 3
        assert data["unique_entities"] == 3
        assert data["empty_count"] == 1


def test_history_filtered_by_entity_name(tmp_path: Path):
    pulse_dir = tmp_path / "pulse"
    pulse_dir.mkdir()

    (pulse_dir / f"project-serpo-{FIXED_TODAY}.json").write_text(json.dumps({
        "entity_name": "Project Serpo",
        "slug": "project-serpo",
        "date": FIXED_TODAY,
        "timestamp": "2026-07-12T12:00:00+00:00",
        "evidence_count": 5,
        "evidence": [{"claim_text": "c"}] * 5,
    }))
    (pulse_dir / f"roswell-crash-{FIXED_TODAY}.json").write_text(json.dumps({
        "entity_name": "Roswell Crash",
        "slug": "roswell-crash",
        "date": FIXED_TODAY,
        "timestamp": "2026-07-12T12:00:00+00:00",
        "evidence_count": 3,
        "evidence": [{"claim_text": "c"}] * 3,
    }))

    with patch("src.wiki.paths.get_pulse_dir", return_value=pulse_dir), \
         patch("src.wiki.pulse_writer.get_pulse_dir", return_value=pulse_dir), \
         patch("src.wiki.pulse_writer.date") as mock_date:
        mock_date.today.return_value = date.fromisoformat(FIXED_TODAY)
        mock_date.isoformat = date.isoformat
        from src.main import app
        from fastapi.testclient import TestClient
        client = TestClient(app)
        response = client.get("/pulse/history?entity_name=project-serpo&limit=50")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["pulses"][0]["entity_name"] == "Project Serpo"
        assert data["pulses"][0]["evidence_count"] == 5
