import pytest
from unittest.mock import patch, MagicMock

from src.models import ClaimEvidence
from datetime import datetime, timezone


def _ev(text, platform="reddit", cluster="c1"):
    return ClaimEvidence(
        claim_text=text,
        source_platform=platform,
        engagement_count=100,
        timestamp=datetime.now(timezone.utc).isoformat(),
        cluster_id=cluster,
        url=f"https://example.com/{cluster}",
    )


def test_tribunal_uncontested_never_triggers():
    from src.agents.tribunal_agent import TribunalAgent

    agent = TribunalAgent()

    # Uncontested should never trigger
    assert agent.should_trigger_tribunal("corroborated", divergence_risk=0.1) is False
    assert agent.should_trigger_tribunal("unverified", divergence_risk=0.1) is False
    assert agent.should_trigger_tribunal("unverified", divergence_risk=0.0) is False

    # Mock LLM to count calls — should be 0 for uncontested
    evidence = [_ev("Bob Lazar worked at S-4", "reddit", "c1")]

    wavefunction = {
        "state_label": "corroborated",
        "epistemic_confidence": 0.85,
        "social_traction": 0.3,
        "collapsed": True,
        "evidence_count": 1,
    }

    with patch.object(agent, "_query_llm") as mock_llm:
        result = agent.run_tribunal(
            claim_text="Bob Lazar worked at S-4",
            evidence=evidence,
            wavefunction=wavefunction,
            divergence_risk=0.1,
        )

        assert result["triggered"] is False
        assert "uncontested" in result["reason"].lower() or "below threshold" in result["reason"].lower()
        assert not mock_llm.called


def test_tribunal_contested_triggers_with_three_positions():
    from src.agents.tribunal_agent import TribunalAgent

    agent = TribunalAgent()

    evidence = [
        _ev("Bob Lazar S-4 claims corroborated by witness", "reddit", "c1"),
        _ev("Bob Lazar S-4 claims debunked by officials", "news", "c2"),
        _ev("Element 115 propulsion contested", "x", "c3"),
    ]

    wavefunction = {
        "state_label": "contested",
        "epistemic_confidence": 0.55,
        "social_traction": 0.6,
        "collapsed": False,
        "evidence_count": 3,
        "scoring_inputs": {
            "source_diversity": 0.6,
            "evidence_platforms": ["reddit", "news", "x"],
        },
    }

    def fake_llm(system_prompt, user_prompt, role_label):
        return f"{role_label} analysis: based on evidence with citations https://example.com/{role_label.lower()}", [f"https://example.com/{role_label.lower()}"]

    with patch.object(agent, "_query_llm", side_effect=fake_llm):
        result = agent.run_tribunal(
            claim_text="Bob Lazar worked at S-4 on Element 115",
            evidence=evidence,
            wavefunction=wavefunction,
            divergence_risk=0.2,
        )

        assert result["triggered"] is True
        assert "skeptic_position" in result
        assert "empiricist_position" in result
        assert "believer_position" in result
        assert "referee_synthesis" in result
        assert "all_citations" in result
        assert len(result["all_citations"]) >= 1
        # Disagreement preserved
        assert "disagreements" in result


def test_tribunal_divergence_spike_triggers():
    from src.agents.tribunal_agent import TribunalAgent

    agent = TribunalAgent()

    # Even unverified but high divergence should trigger
    assert agent.should_trigger_tribunal("unverified", divergence_risk=0.8) is True
    assert agent.should_trigger_tribunal("corroborated", divergence_risk=0.8) is True
    assert agent.should_trigger_tribunal("contested", divergence_risk=0.0) is True  # contested always triggers


def test_tribunal_output_includes_citations_not_just_referee():
    from src.agents.tribunal_agent import TribunalAgent

    agent = TribunalAgent()

    evidence = [
        _ev("Roswell crash confirmed", "reddit", "c1"),
        _ev("Roswell debris recovery", "news", "c2"),
    ]

    wavefunction = {
        "state_label": "contested",
        "epistemic_confidence": 0.52,
        "social_traction": 0.7,
        "collapsed": False,
        "evidence_count": 2,
    }

    def fake_llm(system_prompt, user_prompt, role_label):
        return (
            f"{role_label} position with citation https://example.com/{role_label.lower()}/claim",
            [f"https://example.com/{role_label.lower()}/claim"]
        )

    with patch.object(agent, "_query_llm", side_effect=fake_llm):
        result = agent.run_tribunal(
            claim_text="Roswell crash was alien craft",
            evidence=evidence,
            wavefunction=wavefunction,
            divergence_risk=0.1,
        )

        assert result["triggered"] is True
        # All three positions' citations preserved
        assert "skeptic_citations" in result
        assert "empiricist_citations" in result
        assert "believer_citations" in result
        assert "all_citations" in result
        # all_citations should have entries from all three
        assert len(result["all_citations"]) >= 3
