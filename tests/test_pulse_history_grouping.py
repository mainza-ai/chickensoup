import json
import pytest
from pathlib import Path
from unittest.mock import patch


def test_history_latest_true_returns_one_per_entity(client, tmp_path: Path):
    pulse_dir = tmp_path / "pulse"
    pulse_dir.mkdir()

    latest = pulse_dir / "project-serpo-2026-07-12-2.json"
    older = pulse_dir / "project-serpo-2026-07-12-1.json"
    other = pulse_dir / "roswell-crash-2026-07-12-1.json"

    for p, entity_name, evidence_count in [
        (latest, "Project Serpo", 5),
        (older, "Project Serpo", 0),
        (other, "Roswell Crash", 0),
    ]:
        p.write_text(json.dumps({
            "entity_name": entity_name,
            "slug": entity_name.lower().replace(" ", "-"),
            "date": "2026-07-12",
            "timestamp": "2026-07-12T12:00:00+00:00",
            "evidence_count": evidence_count,
            "evidence": [{"claim_text": "c"}] * evidence_count,
        }))

    with patch("src.wiki.paths.get_pulse_dir", return_value=pulse_dir), \
         patch("src.wiki.pulse_writer.get_pulse_dir", return_value=pulse_dir):
        response = client.get("/pulse/history?latest=true&limit=50")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2
        assert data["unique_entities"] == 2
        entities = {p["entity_name"] for p in data["pulses"]}
        assert entities == {"Project Serpo", "Roswell Crash"}


def test_history_latest_false_returns_all_entries(client, tmp_path: Path):
    pulse_dir = tmp_path / "pulse"
    pulse_dir.mkdir()

    for name in ["entity-one-2026-07-12-1.json", "entity-one-2026-07-12-2.json"]:
        p = pulse_dir / name
        p.write_text(json.dumps({
            "entity_name": "Entity One",
            "slug": "entity-one",
            "date": "2026-07-12",
            "timestamp": "2026-07-12T12:00:00+00:00",
            "evidence_count": 1,
            "evidence": [{"claim_text": "c"}],
        }))

    with patch("src.wiki.paths.get_pulse_dir", return_value=pulse_dir), \
         patch("src.wiki.pulse_writer.get_pulse_dir", return_value=pulse_dir):
        response = client.get("/pulse/history?latest=false&limit=50")
        assert response.status_code == 200
        data = response.json()
        # default is latest=false; both files returned (limit=2)
        assert data["total"] == 2


def test_history_counts_are_correct(client, tmp_path: Path):
    pulse_dir = tmp_path / "pulse"
    pulse_dir.mkdir()

    entries = [
        ("alpha", 5),
        ("beta", 0),
        ("gamma", 3),
        ("alpha", 2),
    ]
    for i, (entity, count) in enumerate(entries):
        p = pulse_dir / f"{entity}-2026-07-12-{i+1}.json"
        p.write_text(json.dumps({
            "entity_name": entity,
            "slug": entity,
            "date": "2026-07-12",
            "timestamp": f"2026-07-12T{10+i}:00:00+00:00",
            "evidence_count": count,
            "evidence": [{"claim_text": f"c{i}"}] * count,
        }))

    with patch("src.wiki.paths.get_pulse_dir", return_value=pulse_dir), \
         patch("src.wiki.pulse_writer.get_pulse_dir", return_value=pulse_dir):
        response = client.get("/pulse/history?limit=50")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 4
        assert data["unique_entities"] == 3
        assert data["empty_count"] == 1


def test_history_with_latest_true_counts_reflect_grouped_set(client, tmp_path: Path):
    pulse_dir = tmp_path / "pulse"
    pulse_dir.mkdir()

    for name in ["alpha-2026-07-12-1.json", "beta-2026-07-12-1.json"]:
        p = pulse_dir / name
        entity_name = name.split("-2026")[0].replace("-", " ").title()
        p.write_text(json.dumps({
            "entity_name": entity_name,
            "slug": entity_name.lower().replace(" ", "-"),
            "date": "2026-07-12",
            "timestamp": "2026-07-12T12:00:00+00:00",
            "evidence_count": 0,
            "evidence": [],
        }))

    with patch("src.wiki.paths.get_pulse_dir", return_value=pulse_dir), \
         patch("src.wiki.pulse_writer.get_pulse_dir", return_value=pulse_dir):
        response = client.get("/pulse/history?latest=true")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2
        assert data["unique_entities"] == 2
        assert data["empty_count"] == 2
