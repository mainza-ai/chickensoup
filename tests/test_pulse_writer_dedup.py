import json
import os
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path

import pytest
from unittest.mock import patch

from src.models import ClaimEvidence
from src.wiki.pulse_writer import write_pulse_snapshot, _get_latest_snapshot_meta, _evidence_fingerprint


def _write_snapshot(pulse_dir: Path, slug: str, evidence, timestamp: str):
    slug_safe = slug.lower().replace(" ", "-")
    base = f"{slug_safe}-{timestamp}"
    json_path = pulse_dir / f"{base}.json"
    payload = {
        "entity_name": slug,
        "slug": slug_safe,
        "date": timestamp,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "evidence_count": len(evidence),
        "evidence": [e.model_dump() for e in evidence],
        "raw_output_preview": "",
        "meta": {},
    }
    json_path.write_text(json.dumps(payload))
    return json_path


def test_exact_evidence_rerun_within_window_is_deduped(tmp_path: Path):
    pulse_dir = tmp_path / "pulse"
    pulse_dir.mkdir()
    slug = "project-serpo"

    ev = [ClaimEvidence(claim_text="claim alpha", source_platform="reddit", engagement_count=10, url="http://a")]
    fp = _evidence_fingerprint(ev)

    with patch("src.wiki.pulse_writer.get_pulse_dir", return_value=pulse_dir), \
         patch("src.wiki.pulse_writer.ensure_pulse_dir", return_value=pulse_dir):
        r1 = write_pulse_snapshot(slug, ev)
        assert r1["json_path"] != ""
        assert r1.get("deduped") is not True

        r2 = write_pulse_snapshot(slug, ev)
        assert r2.get("deduped") is True
        assert r2.get("matched_path") == r1["json_path"]
        assert r2["json_path"] == ""


def test_different_evidence_within_window_is_written(tmp_path: Path):
    pulse_dir = tmp_path / "pulse"
    pulse_dir.mkdir()
    slug = "project-serpo"

    ev1 = [ClaimEvidence(claim_text="claim alpha", source_platform="reddit", engagement_count=10, url="http://a")]
    ev2 = [ClaimEvidence(claim_text="claim beta", source_platform="youtube", engagement_count=20, url="http://b")]

    with patch("src.wiki.pulse_writer.get_pulse_dir", return_value=pulse_dir), \
         patch("src.wiki.pulse_writer.ensure_pulse_dir", return_value=pulse_dir):
        r1 = write_pulse_snapshot(slug, ev1)
        assert r1["json_path"] != ""

        r2 = write_pulse_snapshot(slug, ev2)
        assert r2.get("deduped") is not True
        assert r2["json_path"] != ""
        assert r2["json_path"] != r1["json_path"]


def test_evidence_after_window_expires_is_written(tmp_path: Path):
    pulse_dir = tmp_path / "pulse"
    pulse_dir.mkdir()
    slug = "project-serpo"

    ev = [ClaimEvidence(claim_text="claim alpha", source_platform="reddit", engagement_count=10, url="http://a")]

    with patch("src.wiki.pulse_writer.get_pulse_dir", return_value=pulse_dir), \
         patch("src.wiki.pulse_writer.ensure_pulse_dir", return_value=pulse_dir):
        r1 = write_pulse_snapshot(slug, ev)
        assert r1["json_path"] != ""

        os.utime(r1["json_path"], (time.time() - 30 * 3600, time.time() - 30 * 3600))

        r2 = write_pulse_snapshot(slug, ev)
        assert r2.get("deduped") is not True
        assert r2["json_path"] != ""


def test_empty_evidence_first_write_is_written(tmp_path: Path):
    pulse_dir = tmp_path / "pulse"
    pulse_dir.mkdir()
    slug = "empty-entity"

    with patch("src.wiki.pulse_writer.get_pulse_dir", return_value=pulse_dir), \
         patch("src.wiki.pulse_writer.ensure_pulse_dir", return_value=pulse_dir):
        r1 = write_pulse_snapshot(slug, [])
        assert r1["json_path"] != ""
        assert r1.get("deduped") is not True


def test_empty_evidence_second_write_within_window_is_deduped(tmp_path: Path):
    pulse_dir = tmp_path / "pulse"
    pulse_dir.mkdir()
    slug = "empty-entity"

    with patch("src.wiki.pulse_writer.get_pulse_dir", return_value=pulse_dir), \
         patch("src.wiki.pulse_writer.ensure_pulse_dir", return_value=pulse_dir):
        r1 = write_pulse_snapshot(slug, [])
        assert r1["json_path"] != ""

        r2 = write_pulse_snapshot(slug, [])
        assert r2.get("deduped") is True
        assert r2.get("matched_path") == r1["json_path"]
        assert r2["json_path"] == ""


def test_different_entities_do_not_dedup_against_each_other(tmp_path: Path):
    pulse_dir = tmp_path / "pulse"
    pulse_dir.mkdir()

    ev = [ClaimEvidence(claim_text="claim alpha", source_platform="reddit", engagement_count=10, url="http://a")]

    with patch("src.wiki.pulse_writer.get_pulse_dir", return_value=pulse_dir), \
         patch("src.wiki.pulse_writer.ensure_pulse_dir", return_value=pulse_dir):
        r1 = write_pulse_snapshot("entity-one", ev)
        r2 = write_pulse_snapshot("entity-two", ev)
        assert r1["json_path"] != ""
        assert r2["json_path"] != ""
        assert r1["json_path"] != r2["json_path"]


def test_evidence_fingerprint_order_independent():
    ev1 = [ClaimEvidence(claim_text="b claim", source_platform="x", engagement_count=5, url="http://b"),
           ClaimEvidence(claim_text="a claim", source_platform="reddit", engagement_count=10, url="http://a")]
    ev2 = [ClaimEvidence(claim_text="a claim", source_platform="reddit", engagement_count=10, url="http://a"),
           ClaimEvidence(claim_text="b claim", source_platform="x", engagement_count=5, url="http://b")]
    assert _evidence_fingerprint(ev1) == _evidence_fingerprint(ev2)


def test_get_latest_snapshot_meta_returns_newest_within_window(tmp_path: Path):
    pulse_dir = tmp_path / "pulse"
    pulse_dir.mkdir()
    slug = "project-serpo"

    old_ts = "2026-07-10"
    new_ts = "2026-07-12"

    _write_snapshot(pulse_dir, slug, [], old_ts)
    new_path = _write_snapshot(pulse_dir, slug, [ClaimEvidence(claim_text="fresh", source_platform="reddit", engagement_count=1, url="http://x")], new_ts)

    with patch("src.wiki.pulse_writer.get_pulse_dir", return_value=pulse_dir):
        meta = _get_latest_snapshot_meta(slug, max_age_hours=48)
        assert meta is not None
        assert meta["path"] == str(new_path)
        assert meta["evidence_count"] == 1


def test_get_latest_snapshot_meta_returns_none_when_no_recent(tmp_path: Path):
    pulse_dir = tmp_path / "pulse"
    pulse_dir.mkdir()
    slug = "project-serpo"

    old_ts = "2026-07-01"
    old_path = _write_snapshot(pulse_dir, slug, [], old_ts)
    os.utime(old_path, (time.time() - 48 * 3600, time.time() - 48 * 3600))

    with patch("src.wiki.pulse_writer.get_pulse_dir", return_value=pulse_dir):
        meta = _get_latest_snapshot_meta(slug, max_age_hours=24)
        assert meta is None
