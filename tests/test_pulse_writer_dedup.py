import json
from datetime import date
from pathlib import Path

import pytest
from unittest.mock import patch

from src.models import ClaimEvidence
from src.wiki.pulse_writer import write_pulse_snapshot, list_pulse_snapshots


FIXED_TODAY = "2026-07-12"


def test_same_entity_same_day_overwrites(tmp_path: Path):
    pulse_dir = tmp_path / "pulse"
    pulse_dir.mkdir()

    with patch("src.wiki.pulse_writer.get_pulse_dir", return_value=pulse_dir), \
         patch("src.wiki.pulse_writer.ensure_pulse_dir", return_value=pulse_dir):
        ev1 = [ClaimEvidence(claim_text="first", source_platform="reddit", engagement_count=1, url="http://a")]
        ev2 = [ClaimEvidence(claim_text="second", source_platform="youtube", engagement_count=2, url="http://b")]

        r1 = write_pulse_snapshot("project-serpo", ev1)
        r2 = write_pulse_snapshot("project-serpo", ev2)

        assert r1["json_path"] == r2["json_path"]
        assert Path(r2["json_path"]).exists()

        data = json.loads(Path(r2["json_path"]).read_text())
        assert data["evidence_count"] == 1
        assert data["evidence"][0]["claim_text"] == "second"


def test_different_entities_get_separate_files(tmp_path: Path):
    pulse_dir = tmp_path / "pulse"
    pulse_dir.mkdir()

    with patch("src.wiki.pulse_writer.get_pulse_dir", return_value=pulse_dir), \
         patch("src.wiki.pulse_writer.ensure_pulse_dir", return_value=pulse_dir):
        ev = [ClaimEvidence(claim_text="claim", source_platform="reddit", engagement_count=1, url="http://a")]
        r1 = write_pulse_snapshot("entity-one", ev)
        r2 = write_pulse_snapshot("entity-two", ev)

        assert r1["json_path"] != r2["json_path"]
        assert "entity-one" in r1["json_path"]
        assert "entity-two" in r2["json_path"]


def test_list_snapshots_returns_only_today_for_entity(tmp_path: Path):
    pulse_dir = tmp_path / "pulse"
    pulse_dir.mkdir()

    snap = pulse_dir / f"project-serpo-{FIXED_TODAY}.json"
    snap.write_text("{}")

    old_snap = pulse_dir / "project-serpo-2026-07-01.json"
    old_snap.write_text("{}")

    with patch("src.wiki.pulse_writer.get_pulse_dir", return_value=pulse_dir), \
         patch("src.wiki.pulse_writer.ensure_pulse_dir", return_value=pulse_dir), \
         patch("src.wiki.pulse_writer.date") as mock_date:
        mock_date.today.return_value = date.fromisoformat(FIXED_TODAY)
        mock_date.isoformat = date.isoformat
        results = list_pulse_snapshots("project-serpo")
        assert len(results) == 1
        assert FIXED_TODAY in results[0].name


def test_list_all_snapshots_returns_everything(tmp_path: Path):
    pulse_dir = tmp_path / "pulse"
    pulse_dir.mkdir()

    (pulse_dir / "entity-a-2026-07-12.json").write_text("{}")
    (pulse_dir / "entity-b-2026-07-10.json").write_text("{}")

    with patch("src.wiki.pulse_writer.get_pulse_dir", return_value=pulse_dir), \
         patch("src.wiki.pulse_writer.ensure_pulse_dir", return_value=pulse_dir):
        results = list_pulse_snapshots()
        assert len(results) == 2


def test_empty_evidence_snapshot_is_written(tmp_path: Path):
    pulse_dir = tmp_path / "pulse"
    pulse_dir.mkdir()

    with patch("src.wiki.pulse_writer.get_pulse_dir", return_value=pulse_dir), \
         patch("src.wiki.pulse_writer.ensure_pulse_dir", return_value=pulse_dir):
        r = write_pulse_snapshot("no-data-entity", [])
        assert Path(r["json_path"]).exists()
        data = json.loads(Path(r["json_path"]).read_text())
        assert data["evidence_count"] == 0
