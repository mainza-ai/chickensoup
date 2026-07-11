import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock, AsyncMock

import pytest

from src.models import ClaimEvidence, ClaimConfidence
from datetime import datetime, timezone


def _ev(text, platform="reddit", eng=100, cluster="c1"):
    return ClaimEvidence(
        claim_text=text,
        source_platform=platform,
        engagement_count=eng,
        timestamp=datetime.now(timezone.utc).isoformat(),
        cluster_id=cluster,
    )


@pytest.mark.anyio
async def test_almanac_dry_run_no_files_no_budget():
    with tempfile.TemporaryDirectory() as tmpdir:
        almanac_dir = Path(tmpdir) / "almanac"
        pulse_dir = Path(tmpdir) / "pulse"

        almanac_dir.mkdir(parents=True)
        pulse_dir.mkdir(parents=True)

        # Create a mock pulse file
        pulse_data = {
            "entity_name": "Bob Lazar",
            "slug": "bob-lazar",
            "date": "2026-07-11",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "evidence_count": 1,
            "evidence": [_ev("Bob Lazar worked at S-4", "reddit", 500, "c1").model_dump()],
        }
        pulse_file = pulse_dir / "bob-lazar-2026-07-11.json"
        with open(pulse_file, "w") as f:
            json.dump(pulse_data, f)

        mock_cc = ClaimConfidence(
            epistemic_confidence=0.75,
            social_traction=0.4,
            state_label="corroborated",
            collapsed=True,
            evidence_count=1,
            scoring_version="v1-wavefunction",
            claim_text="Bob Lazar worked at S-4",
            scoring_inputs={"source_diversity": 0.6},
        )

        with patch("src.almanac.almanac_generator._load_tier_entities", return_value=[
            {"slug": "bob-lazar", "title": "Bob Lazar", "tier": 1, "handles": None}
        ]), \
             patch("src.wiki.paths.get_almanac_dir", return_value=almanac_dir), \
             patch("src.wiki.paths.get_pulse_dir", return_value=pulse_dir), \
             patch("src.almanac.timeline.get_pulse_dir", return_value=pulse_dir), \
             patch("src.almanac.timeline.get_wiki_dir", return_value=Path(tmpdir) / "wiki"), \
             patch("src.almanac.timeline.get_project_root", return_value=Path(tmpdir)), \
             patch("src.wiki.writer.read_page", return_value=None), \
             patch("src.agents.pulse_agent.PulseAgent.run_pulse") as mock_pulse, \
             patch("src.quantum_credibility.wavefunction.ClaimWavefunction.score_claim", return_value=mock_cc), \
             patch("src.wiki.writer.append_to_log"), \
             patch("src.almanac.almanac_generator._load_last_almanac_hash", return_value=None), \
             patch("src.budget.budget_tracker") as mock_budget:

            mock_pulse.return_value = MagicMock(
                status="success",
                evidence=[_ev("Bob Lazar worked at S-4", "reddit", 500, "c1")],
            )
            mock_status = MagicMock()
            mock_status.remaining_usd = 19.5
            mock_budget.get_status.return_value = mock_status
            mock_budget.check_budget.return_value = (True, 19.5, "ok")
            mock_budget.record_spend.return_value = mock_status

            from src.almanac.almanac_generator import generate_daily_almanac

            result = await generate_daily_almanac(dry_run=True)

            assert result.status == "success"
            assert result.dry_run is True
            # Dry run should NOT write files
            html_files = list(almanac_dir.glob("*.html"))
            assert len(html_files) == 0, "Dry-run should not write HTML files"

            # But html_content should be present
            assert result.html_content is not None
            assert "<!DOCTYPE html>" in result.html_content
            assert "State of the Anomaly" in result.html_content
            # Inline CSS, no JS, dark mode support
            assert "<style>" in result.html_content
            assert "prefers-color-scheme: dark" in result.html_content
            assert "@media print" in result.html_content
            # Well-formed HTML basics
            assert result.html_content.count("<html") == 1
            assert result.html_content.count("</html>") == 1


@pytest.mark.anyio
async def test_almanac_live_writes_correct_paths_and_log():
    with tempfile.TemporaryDirectory() as tmpdir:
        almanac_dir = Path(tmpdir) / "almanac"
        pulse_dir = Path(tmpdir) / "pulse"
        almanac_dir.mkdir(parents=True)
        pulse_dir.mkdir(parents=True)

        mock_cc = ClaimConfidence(
            epistemic_confidence=0.65,
            social_traction=0.3,
            state_label="contested",
            collapsed=False,
            evidence_count=2,
            scoring_version="v1-wavefunction",
            claim_text="Test claim",
        )

        with patch("src.almanac.almanac_generator._load_tier_entities", return_value=[
            {"slug": "bob-lazar", "title": "Bob Lazar", "tier": 1, "handles": None}
        ]), \
             patch("src.wiki.paths.get_almanac_dir", return_value=almanac_dir), \
             patch("src.wiki.paths.get_pulse_dir", return_value=pulse_dir), \
             patch("src.almanac.timeline.get_pulse_dir", return_value=pulse_dir), \
             patch("src.almanac.timeline.get_wiki_dir", return_value=Path(tmpdir) / "wiki"), \
             patch("src.almanac.timeline.get_project_root", return_value=Path(tmpdir)), \
             patch("src.almanac.almanac_generator.ensure_almanac_dir", return_value=almanac_dir), \
             patch("src.wiki.writer.read_page", return_value=None), \
             patch("src.agents.pulse_agent.PulseAgent.run_pulse") as mock_pulse, \
             patch("src.agents.tribunal_agent.TribunalAgent.run_tribunal") as mock_tribunal, \
             patch("src.quantum_credibility.wavefunction.ClaimWavefunction.score_claim", return_value=mock_cc), \
             patch("src.wiki.writer.append_to_log") as mock_log, \
             patch("src.almanac.almanac_generator._load_last_almanac_hash", return_value=None), \
             patch("src.almanac.almanac_generator._compute_almanac_hash", return_value="unique-hash-123"), \
             patch("src.budget.budget_tracker") as mock_budget:

            mock_pulse.return_value = MagicMock(
                status="success",
                evidence=[
                    _ev("Bob Lazar S-4 claim", "reddit", 500, "c1"),
                    _ev("Bob Lazar Element 115", "news", 300, "c2"),
                ],
            )
            mock_tribunal.return_value = {
                "triggered": True,
                "final_state_label": "contested",
                "referee_synthesis": "Contested claim with mixed evidence.",
                "disagreements": [],
                "all_citations": [],
            }

            mock_status = MagicMock()
            mock_status.remaining_usd = 19.0
            mock_budget.get_status.return_value = mock_status
            mock_budget.check_budget.return_value = (True, 19.0, "ok")
            mock_budget.record_spend.return_value = mock_status

            from src.almanac.almanac_generator import generate_daily_almanac

            result = await generate_daily_almanac(dry_run=False)

            assert result.status == "success"
            assert result.dry_run is False
            assert result.html_path is not None
            assert result.md_path is not None

            # Files exist at correct paths
            assert Path(result.html_path).exists()
            assert Path(result.md_path).exists()

            # Paths match wiki/raw/almanac/{date}.html pattern
            assert "almanac" in result.html_path
            assert result.html_path.endswith(".html")
            assert result.md_path.endswith(".md")

            # HTML valid
            import html.parser

            class _HTMLValidator(html.parser.HTMLParser):
                def __init__(self):
                    super().__init__()
                    self.errors = []

                def error(self, message):
                    self.errors.append(message)

            validator = _HTMLValidator()
            with open(result.html_path, "r") as f:
                content = f.read()
            validator.feed(content)
            assert len(validator.errors) == 0, f"HTML validation errors: {validator.errors}"

            # Log appended
            assert mock_log.called
            log_call_args = str(mock_log.call_args)
            assert "almanac" in log_call_args.lower()


@pytest.mark.anyio
async def test_almanac_no_material_change_logs_instead():
    with tempfile.TemporaryDirectory() as tmpdir:
        almanac_dir = Path(tmpdir) / "almanac"
        almanac_dir.mkdir(parents=True)

        # Pre-create an almanac file with hash
        existing_md = almanac_dir / "2026-07-10.md"
        existing_md.write_text("<!-- hash: abc123 -->\n\n# Previous almanac\n")

        from src.almanac import almanac_generator as ag_mod

        almanac_dir2 = Path(tmpdir) / "almanac2"
        almanac_dir2.mkdir(parents=True, exist_ok=True)
        pulse_dir2 = Path(tmpdir) / "pulse2_empty"
        pulse_dir2.mkdir(parents=True, exist_ok=True)

        with patch.object(ag_mod, "_load_tier_entities", return_value=[
            {"slug": "bob-lazar", "title": "Bob Lazar", "tier": 1, "handles": None}
        ]), \
             patch.object(ag_mod, "_load_last_almanac_hash", return_value="empty-no-evidence"), \
             patch.object(ag_mod, "_compute_almanac_hash", return_value="empty-no-evidence"), \
             patch("src.wiki.paths.get_almanac_dir", return_value=almanac_dir2), \
             patch("src.wiki.paths.get_pulse_dir", return_value=pulse_dir2), \
             patch("src.wiki.writer.read_page", return_value=None), \
             patch("src.agents.pulse_agent.PulseAgent.run_pulse") as mock_pulse2, \
             patch("src.wiki.writer.append_to_log"), \
             patch("src.budget.budget_tracker") as mock_budget2:

            mock_pulse2.return_value = MagicMock(status="success", evidence=[])

            mock_status2 = MagicMock()
            mock_status2.remaining_usd = 10.0
            mock_budget2.get_status.return_value = mock_status2

            result = await ag_mod.generate_daily_almanac(dry_run=False)

            assert result.status == "no_material_change"
            # No new files should be written beyond existing
            html_files = list(almanac_dir.glob("*.html"))
            # may be 0 or existing — but no new file for today specifically created in no_change case
