import pytest
from src.models import ClaimEvidence
from src.quantum_credibility.entanglement_corr import compute_entanglement_correlation
from datetime import datetime, timezone


def _ev(text, platform, cluster):
    return ClaimEvidence(
        claim_text=text,
        source_platform=platform,
        engagement_count=100,
        timestamp=datetime.now(timezone.utc).isoformat(),
        cluster_id=cluster,
    )


def test_entanglement_single_mention_low_score():
    evidence = [
        _ev("Element 115 and Bob Lazar were mentioned together at conference", "reddit", "c1"),
    ]

    result = compute_entanglement_correlation("Element 115", "Bob Lazar", evidence)

    assert result["co_occurrence_count"] == 1
    assert result["entanglement_score"] < 0.5
    assert result["is_strong"] is False


def test_entanglement_multi_platform_high_score():
    evidence = [
        _ev("Element 115 and Bob Lazar linked in Reddit discussion about S-4", "reddit", "c1"),
        _ev("Element 115 with Bob Lazar confirmed by X user", "x", "c2"),
        _ev("YouTube: Element 115 and Bob Lazar deep dive", "youtube", "c3"),
        _ev("News: Element 115 propulsion claimed by Bob Lazar associate", "news", "c4"),
        _ev("Podcast: Element 115 and Bob Lazar witness testimony", "podcast", "c5"),
    ]

    result = compute_entanglement_correlation("Element 115", "Bob Lazar", evidence)

    assert result["co_occurrence_count"] == 5
    assert len(result["independent_platforms"]) == 5
    assert result["independent_clusters"] == 5
    assert result["entanglement_score"] > result["meyer_wallach_raw"] * 0.1  # some positive entanglement
    # Multi-platform should score higher than single
    single = compute_entanglement_correlation("Element 115", "Bob Lazar", evidence[:1])
    assert result["entanglement_score"] > single["entanglement_score"]


def test_entanglement_no_cooccurrence_zero():
    evidence = [
        _ev("Roswell crash details", "reddit", "c1"),
        _ev("Area 51 secrets", "news", "c2"),
    ]

    result = compute_entanglement_correlation("Element 115", "Bob Lazar", evidence)
    assert result["co_occurrence_count"] == 0
    assert result["entanglement_score"] == 0.0


def test_entanglement_three_platforms_distinctly_higher_than_single():
    single_evidence = [
        _ev("Element 115 and Bob Lazar together in one Reddit post", "reddit", "c1"),
    ]

    triple_evidence = [
        _ev("Element 115 and Bob Lazar on Reddit", "reddit", "c1"),
        _ev("Element 115 and Bob Lazar on X", "x", "c2"),
        _ev("Element 115 and Bob Lazar on YouTube", "youtube", "c3"),
    ]

    single_res = compute_entanglement_correlation("Element 115", "Bob Lazar", single_evidence)
    triple_res = compute_entanglement_correlation("Element 115", "Bob Lazar", triple_evidence)

    assert triple_res["entanglement_score"] > single_res["entanglement_score"]
    assert triple_res["independent_clusters"] == 3
