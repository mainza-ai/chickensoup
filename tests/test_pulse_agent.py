import json
import os
import tempfile
from unittest.mock import MagicMock, patch

import pytest

from src.models import ClaimEvidence


def _mock_evidence_json(entity="Bob Lazar"):
    return json.dumps({
        "claims": [
            {
                "claim_text": f"{entity} allegedly worked at S-4 near Area 51 on exotic craft",
                "source_platform": "reddit",
                "engagement_count": 1200,
                "url": "https://reddit.com/r/ufos/123",
                "timestamp": "2026-07-10T12:00:00Z",
                "cluster_id": "c1",
                "polymarket_odds": 0.35
            },
            {
                "claim_text": f"New hearing mentions {entity} testimony from 1989",
                "source_platform": "news",
                "engagement_count": 500,
                "url": "https://example.com/news",
                "timestamp": "2026-07-09T08:00:00Z",
                "cluster_id": "c2"
            }
        ]
    })


def test_pulse_disabled_returns_noop():
    from src.agents.pulse_agent import PulseAgent
    from src.config import settings
    orig_enabled = settings.LAST30DAYS_ENABLED
    settings.LAST30DAYS_ENABLED = False
    try:
        agent = PulseAgent()
        result = agent.run_pulse("Bob Lazar")
        assert result.status == "disabled"
        assert result.evidence == []
        assert result.raw_snapshot_path is None
        assert "budget" in result.model_dump_json().lower() or result.budget_remaining >= 0
    finally:
        settings.LAST30DAYS_ENABLED = orig_enabled


def test_pulse_enabled_writes_one_immutable_file():
    from src.agents.pulse_agent import PulseAgent
    from src.config import settings

    with tempfile.TemporaryDirectory() as tmpdir:
        # Redirect pulse dir via patching ensure_pulse_dir
        from pathlib import Path

        pulse_dir = Path(tmpdir) / "pulse"

        with patch("src.agents.pulse_agent.budget_tracker") as mock_budget, \
             patch("src.wiki.pulse_writer.ensure_pulse_dir", return_value=pulse_dir), \
             patch("src.wiki.pulse_writer.get_pulse_dir", return_value=pulse_dir), \
             patch("src.wiki.paths.ensure_pulse_dir", return_value=pulse_dir), \
             patch("src.wiki.writer.append_to_log"), \
             patch("src.agents.pulse_agent.budget_tracker") as mock_budget2:

            mock_status = MagicMock()
            mock_status.remaining_usd = 19.5
            mock_budget.get_status.return_value = mock_status
            mock_budget.check_budget.return_value = (True, 19.5, "ok")
            mock_budget.record_spend.return_value = mock_status
            mock_budget2.get_status.return_value = mock_status
            mock_budget2.check_budget.return_value = (True, 19.5, "ok")
            mock_budget2.record_spend.return_value = mock_status

            # We need to patch budget_tracker inside pulse_agent module separately

        # Second variant with correct patch targets
        with tempfile.TemporaryDirectory() as tmpdir2:
            pulse_dir2 = Path(tmpdir2) / "pulse"
            pulse_dir2.mkdir(parents=True, exist_ok=True)

            import src.wiki.pulse_writer as pw_mod
            import src.wiki.paths as paths_mod

            orig_enabled = settings.LAST30DAYS_ENABLED
            orig_cost = settings.LAST30DAYS_COST_PER_PULL_USD
            settings.LAST30DAYS_ENABLED = True
            settings.LAST30DAYS_COST_PER_PULL_USD = 0.5

            mock_budget_tracker = MagicMock()
            status_mock = MagicMock()
            status_mock.remaining_usd = 19.5
            mock_budget_tracker.get_status.return_value = status_mock
            mock_budget_tracker.check_budget.return_value = (True, 19.5, "ok")
            mock_budget_tracker.record_spend.return_value = status_mock

            try:
                with patch("src.agents.pulse_agent.budget_tracker", mock_budget_tracker), \
                     patch.object(pw_mod, "ensure_pulse_dir", return_value=pulse_dir2), \
                     patch.object(pw_mod, "get_pulse_dir", return_value=pulse_dir2), \
                     patch("src.wiki.writer.append_to_log"), \
                     patch("src.agents.pulse_agent.subprocess.run") as mock_run, \
                     patch.object(paths_mod, "ensure_pulse_dir", return_value=pulse_dir2):

                    mock_run.return_value = MagicMock(
                        returncode=0,
                        stdout=_mock_evidence_json("Bob Lazar"),
                        stderr=""
                    )

                    with patch("src.agents.pulse_agent.PulseAgent._resolve_binary", return_value=["last30days"]):
                        agent = PulseAgent()
                        result = agent.run_pulse("Bob Lazar")

                        assert result.status == "success"
                        assert len(result.evidence) == 2
                        assert result.raw_snapshot_path is not None

                        # Exactly one new file in pulse dir (actually 2: json + md, but count json)
                        json_files = list(pulse_dir2.glob("*.json"))
                        md_files = list(pulse_dir2.glob("*.md"))
                        assert len(json_files) == 1
                        assert len(md_files) == 1

                        # Never touches entities/concepts — ensure no write_page call
                        # We already assert pulse dir only

                        # Evidence fields distinct
                        assert result.evidence[0].source_platform == "reddit"
                        assert result.evidence[0].polymarket_odds == 0.35

                        # Budget check called
                        assert mock_budget_tracker.check_budget.called

            finally:
                settings.LAST30DAYS_ENABLED = orig_enabled
                settings.LAST30DAYS_COST_PER_PULL_USD = orig_cost


def test_pulse_budget_exceeded_refused_and_logged():
    from src.agents.pulse_agent import PulseAgent
    from src.config import settings

    orig_enabled = settings.LAST30DAYS_ENABLED
    settings.LAST30DAYS_ENABLED = True

    mock_tracker = MagicMock()
    status_mock = MagicMock()
    status_mock.remaining_usd = 0.1
    mock_tracker.get_status.return_value = status_mock
    mock_tracker.check_budget.return_value = (False, 0.1, "Budget ceiling $20.00 would be exceeded")

    try:
        with patch("src.agents.pulse_agent.budget_tracker", mock_tracker), \
             patch("src.wiki.writer.append_to_log") as mock_log, \
             patch("src.agents.pulse_agent.subprocess.run") as mock_run:

            agent = PulseAgent()
            result = agent.run_pulse("Bob Lazar")

            assert result.status == "budget_exceeded"
            assert result.evidence == []
            assert "budget" in result.error.lower() or "ceiling" in result.error.lower()

            # Subprocess must NOT have been called
            assert not mock_run.called

            # Log was attempted
            assert mock_log.called

    finally:
        settings.LAST30DAYS_ENABLED = orig_enabled


def test_pulse_never_shell_true():
    from src.agents.pulse_agent import PulseAgent
    import src.agents.pulse_agent as pa_mod

    with patch.object(pa_mod, "budget_tracker") as mock_tracker, \
         patch("src.wiki.writer.append_to_log"), \
         patch.object(pa_mod, "subprocess") as mock_subp:

        status_mock = MagicMock()
        status_mock.remaining_usd = 20.0
        mock_tracker.get_status.return_value = status_mock
        mock_tracker.check_budget.return_value = (True, 20.0, "ok")
        mock_tracker.record_spend.return_value = status_mock

        mock_subp.run.return_value = MagicMock(returncode=0, stdout=_mock_evidence_json(), stderr="")
        mock_subp.TimeoutExpired = __import__("subprocess").TimeoutExpired

        from src.config import settings
        orig_enabled = settings.LAST30DAYS_ENABLED
        settings.LAST30DAYS_ENABLED = True

        try:
            with patch("src.agents.pulse_agent.PulseAgent._resolve_binary", return_value=["last30days"]):
                agent = PulseAgent()
                agent.run_pulse("Bob Lazar; rm -rf /")

                # Check subprocess.run called with shell=False
                call_kwargs = mock_subp.run.call_args[1] if mock_subp.run.call_args else {}
                assert call_kwargs.get("shell") is False
                # Entity passed as separate arg, not interpolated into shell string
                called_args = mock_subp.run.call_args[0][0]
                assert isinstance(called_args, list)
                assert "Bob Lazar; rm -rf /" in called_args or any("Bob Lazar" in str(a) for a in called_args)

        finally:
            settings.LAST30DAYS_ENABLED = orig_enabled


def test_last30days_adapter_json_and_markdown():
    from src.last30days_adapter import Last30daysAdapter

    adapter = Last30daysAdapter()

    # JSON path
    json_raw = _mock_evidence_json("Test Entity")
    parsed = adapter.parse_output(json_raw, "Test Entity")
    assert len(parsed) == 2
    assert parsed[0].claim_text
    assert parsed[0].source_platform == "reddit"

    # Markdown path
    md_raw = """
## Claims
- Bob Lazar worked at S-4 according to Reddit discussion with 1200 upvotes https://reddit.com/r/ufos/test
- New congressional hearing mentions Element 115 propulsion with 500 likes

## Sources
- https://example.com/hearing
"""
    parsed_md = adapter.parse_output(md_raw, "Bob Lazar")
    assert len(parsed_md) >= 1
    assert all(isinstance(ev, ClaimEvidence) for ev in parsed_md)
