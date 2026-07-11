import pytest
from datetime import datetime, timezone, timedelta

from src.models import ClaimEvidence
from src.quantum_credibility.wavefunction import ClaimWavefunction


def _ev(claim_text, platform, eng=100, url="", odds=None, days_ago=0, cluster="c1"):
    ts = (datetime.now(timezone.utc) - timedelta(days=days_ago)).isoformat()
    return ClaimEvidence(
        claim_text=claim_text,
        source_platform=platform,
        engagement_count=eng,
        url=url,
        timestamp=ts,
        cluster_id=cluster,
        polymarket_odds=odds,
    )


def test_wavefunction_high_diversity_high_market_collapses_corroborated():
    wf = ClaimWavefunction()
    evidence = [
        _ev("Bob Lazar worked at S-4", "reddit", eng=1200, odds=0.91, cluster="c1"),
        _ev("Bob Lazar S-4 confirmation", "x", eng=800, odds=0.89, cluster="c2"),
        _ev("Bob Lazar documentary", "youtube", eng=5000, odds=0.85, cluster="c3"),
        _ev("Bob Lazar hearing mention", "news", eng=300, odds=0.80, cluster="c4"),
        _ev("Bob Lazar GitHub archive", "github", eng=50, cluster="c5"),
    ]

    result = wf.score_claim("Bob Lazar worked at S-4", evidence)

    assert result.state_label == "corroborated"
    assert result.collapsed is True
    assert result.epistemic_confidence > 0.6
    assert result.evidence_count == 5
    assert result.scoring_inputs["source_diversity"] >= 0.8
    assert result.scoring_inputs["polymarket_prior"] is not None
    assert result.scoring_inputs["polymarket_prior"] > 0.8
    # Social traction should be non-zero but NOT equal to epistemic in this profile
    assert result.social_traction > 0.0


def test_wavefunction_single_low_engagement_unverified():
    wf = ClaimWavefunction()
    evidence = [
        _ev("Mysterious craft seen over desert", "reddit", eng=5, cluster="c1"),
    ]

    result = wf.score_claim("Mysterious craft", evidence)

    assert result.state_label == "unverified"
    assert result.collapsed is False
    assert result.epistemic_confidence < 0.6
    assert result.evidence_count == 1
    assert result.scoring_inputs["source_diversity"] < 0.5
    assert result.scoring_inputs["engagement_magnitude"] < 0.5


def test_wavefunction_contradicted_claim_contested():
    wf = ClaimWavefunction()
    evidence = [
        _ev("Element 115 powers craft", "reddit", eng=1000, odds=0.75, cluster="c1"),
        _ev("Element 115 claim debunked", "x", eng=900, odds=0.15, cluster="c2"),
        _ev("Element 115 analysis", "youtube", eng=500, odds=0.25, cluster="c3"),
    ]

    result = wf.score_claim("Element 115 powers craft", evidence)

    # When odds highly diverge, contradiction signal should be high
    assert result.scoring_inputs["contradiction_signal"] > 0.0
    # Should be contested or at least not strongly corroborated
    assert result.state_label in ("contested", "unverified")
    # Epistemic should be around mid-range due to conflict
    assert result.epistemic_confidence < 0.7


def test_wavefunction_decoupled_traction_and_epistemic():
    wf = ClaimWavefunction()

    # High engagement, low diversity, no market → high traction, low epistemic
    high_traction_evidence = [
        _ev("Viral UFO clip", "reddit", eng=100000, cluster=f"c{i}")
        for i in range(10)
    ]

    result = wf.score_claim("Viral UFO clip", high_traction_evidence)

    # Traction should be high due to massive engagement
    assert result.social_traction > 0.7
    # But epistemic should NOT be equally high (single platform, no market, low diversity proxy still single platform)
    # Our _source_diversity only counts distinct platforms, so 10 reddit posts = 1 platform = low diversity
    assert result.scoring_inputs["source_diversity"] == pytest.approx(0.2, abs=0.05)
    # Epistemic and traction must be different numbers
    assert result.epistemic_confidence != result.social_traction

    # Now low engagement but high diversity + high market odds → low traction, high epistemic
    low_traction_high_diversity = [
        _ev("Congressional UAP hearing confirms retrieval", "reddit", eng=10, odds=0.92, cluster="c1"),
        _ev("UAP hearing confirmation", "news", eng=15, odds=0.90, cluster="c2"),
        _ev("UAP hearing briefing", "youtube", eng=20, odds=0.88, cluster="c3"),
    ]

    result2 = wf.score_claim("Congressional UAP hearing confirms retrieval", low_traction_high_diversity)

    assert result2.epistemic_confidence > 0.5
    # Traction low due to low engagement counts
    assert result2.social_traction < result.social_traction
    # Still decoupled
    assert result2.epistemic_confidence != result2.social_traction


def test_wavefunction_no_evidence_fallback():
    wf = ClaimWavefunction()
    result = wf.score_claim("Unknown claim with no evidence", [])

    assert result.state_label == "unverified"
    assert result.collapsed is False
    assert result.evidence_count == 0
    assert result.social_traction == 0.0
    assert result.scoring_inputs.get("note") is not None


def test_wavefunction_scoring_version_and_inputs_logged():
    wf = ClaimWavefunction()
    evidence = [
        _ev("Test claim", "reddit", eng=100, odds=0.6, cluster="c1"),
        _ev("Test claim corroboration", "news", eng=200, odds=0.7, cluster="c2"),
    ]

    result = wf.score_claim("Test claim", evidence)

    assert result.scoring_version == "v1-wavefunction"
    assert "source_diversity" in result.scoring_inputs
    assert "engagement_magnitude" in result.scoring_inputs
    assert "polymarket_prior" in result.scoring_inputs
    assert "contradiction_signal" in result.scoring_inputs
    assert "social_traction" in result.scoring_inputs
    assert "social_traction_weight" in result.scoring_inputs
    assert result.scoring_inputs["social_traction_weight"] == 0.15
    assert "amplitudes" in result.scoring_inputs
    assert "probabilities" in result.scoring_inputs
    assert "evidence_platforms" in result.scoring_inputs
    assert len(result.scoring_inputs["probabilities"]) == 3


def test_wavefunction_batch_scoring():
    wf = ClaimWavefunction()
    batch = [
        ("Claim A", [_ev("Claim A evidence", "reddit", eng=100, odds=0.8, cluster="c1")]),
        ("Claim B", [_ev("Claim B evidence", "x", eng=5, cluster="c2")]),
    ]

    results = wf.score_claims(batch)
    assert len(results) == 2
    assert results[0].claim_text is not None
    assert results[1].claim_text is not None
