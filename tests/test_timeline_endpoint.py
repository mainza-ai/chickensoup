import json
import os
import tempfile
from datetime import datetime, timezone, timedelta
from pathlib import Path
from unittest.mock import patch

from src.models import ClaimEvidence


def _make_snapshot_file(pulse_dir: Path, entity_slug: str, date_str: str, claims):
    ts = datetime.fromisoformat(date_str).replace(tzinfo=timezone.utc).isoformat() if "T" not in date_str else date_str
    data = {
        "entity_name": entity_slug.replace("-", " ").title(),
        "slug": entity_slug,
        "date": date_str[:10],
        "timestamp": ts,
        "evidence_count": len(claims),
        "evidence": [
            {
                "claim_text": c,
                "source_platform": "reddit",
                "engagement_count": 100,
                "url": "",
                "timestamp": ts,
                "cluster_id": f"c{i}",
            }
            for i, c in enumerate(claims)
        ],
    }
    fname = f"{entity_slug}-{date_str[:10]}.json"
    fpath = pulse_dir / fname
    with open(fpath, "w") as f:
        json.dump(data, f)
    return fpath


def test_timeline_three_dated_pulls_returns_ordered_series():
    with tempfile.TemporaryDirectory() as tmpdir:
        pulse_dir = Path(tmpdir) / "pulse"
        pulse_dir.mkdir(parents=True)

        entity_slug = "bob-lazar"

        # Create 3 dated pulls
        _make_snapshot_file(pulse_dir, entity_slug, "2026-07-08", ["Claim A"])
        _make_snapshot_file(pulse_dir, entity_slug, "2026-07-09", ["Claim B", "Claim C"])
        _make_snapshot_file(pulse_dir, entity_slug, "2026-07-10", ["Claim D"])

        with patch("src.almanac.timeline.get_pulse_dir", return_value=pulse_dir), \
             patch("src.almanac.timeline.get_wiki_dir", return_value=Path(tmpdir) / "wiki"), \
             patch("src.almanac.timeline.get_project_root", return_value=Path(tmpdir)), \
             patch("src.wiki.writer.read_page", return_value=None), \
             patch("src.quantum_credibility.wavefunction.ClaimWavefunction.score_claim") as mock_score:

            from src.models import ClaimConfidence

            def fake_score(claim_text, evidence):
                return ClaimConfidence(
                    epistemic_confidence=0.6,
                    social_traction=0.3,
                    state_label="unverified",
                    collapsed=False,
                    evidence_count=len(evidence),
                    scoring_version="v1-wavefunction",
                    claim_text=claim_text[:100],
                )

            mock_score.side_effect = fake_score

            from src.almanac.timeline import build_timeline

            result = build_timeline("Bob Lazar", days=30)

            assert len(result.points) == 3
            # Chronological order
            dates = [p.date for p in result.points]
            assert dates == sorted(dates)

            # Chartable shape: each point has date, epistemic_confidence, social_traction, divergence_risk
            for pt in result.points:
                assert pt.date != ""
                assert 0.0 <= pt.epistemic_confidence <= 1.0
                assert 0.0 <= pt.social_traction <= 1.0
                assert 0.0 <= pt.divergence_risk <= 1.0
                assert isinstance(pt.active_claims, list)


def test_timeline_empty_entity_returns_empty():
    with tempfile.TemporaryDirectory() as tmpdir:
        pulse_dir = Path(tmpdir) / "pulse"
        pulse_dir.mkdir(parents=True)

        with patch("src.almanac.timeline.get_pulse_dir", return_value=pulse_dir), \
             patch("src.almanac.timeline.get_wiki_dir", return_value=Path(tmpdir) / "wiki"), \
             patch("src.almanac.timeline.get_project_root", return_value=Path(tmpdir)):

            from src.almanac.timeline import build_timeline
            result = build_timeline("NonExistent Entity XYZ", days=30)
            assert len(result.points) == 0


def test_timeline_git_fallback_no_crash():
    with tempfile.TemporaryDirectory() as tmpdir:
        pulse_dir = Path(tmpdir) / "pulse"
        pulse_dir.mkdir(parents=True)

        with patch("src.almanac.timeline.get_pulse_dir", return_value=pulse_dir), \
             patch("src.almanac.timeline.get_wiki_dir", return_value=Path(tmpdir) / "wiki"), \
             patch("src.almanac.timeline.get_project_root", return_value=Path(tmpdir) / "nonexistent"):

            from src.almanac.timeline import build_timeline
            # Should not crash even if git not available
            result = build_timeline("Bob Lazar", days=30)
            assert isinstance(result.points, list)
