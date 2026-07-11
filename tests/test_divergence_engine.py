import pytest
from src.models import ClaimEvidence
from src.quantum_credibility.divergence_engine import compute_narrative_divergence
from datetime import datetime, timezone, timedelta


def _ev(text, platform="reddit", eng=100, odds=None, cluster="c1"):
    return ClaimEvidence(
        claim_text=text,
        source_platform=platform,
        engagement_count=eng,
        timestamp=datetime.now(timezone.utc).isoformat(),
        cluster_id=cluster,
        polymarket_odds=odds,
    )


def _wiki_page(title="Bob Lazar", tags=None, sources=None, related=None, body="Bob Lazar worked at S-4."):
    return {
        "name": title,
        "frontmatter": {
            "title": title,
            "tags": tags or ["person", "ufo"],
            "sources": sources or ["Grusch-2023"],
            "related": related or ["area-51", "element-115"],
        },
        "body": body,
    }


def test_divergence_identical_canon_and_fresh_near_zero():
    wiki_page = _wiki_page(
        title="Bob Lazar",
        sources=["Grusch-2023"],
        body="Bob Lazar worked at S-4 on exotic craft propulsion using Element 115."
    )

    # Fresh evidence identical to canon — same claim text
    fresh = [
        _ev("Bob Lazar worked at S-4 on exotic craft propulsion using Element 115.", platform="news", eng=10, cluster="c1"),
    ]

    result = compute_narrative_divergence("Bob Lazar", wiki_page, fresh)

    assert result.entity_name == "Bob Lazar"
    assert result.divergence_risk >= 0.0
    assert result.divergence_risk < 0.5  # near-zero for identical
    assert result.canon_vector_hash != ""
    assert result.live_vector_hash != ""
    assert result.canon_vector_hash != result.live_vector_hash  # vectors differ at least slightly due to construction


def test_divergence_contradicting_claim_high_score_with_driving_claim_named():
    wiki_page = _wiki_page(
        title="Element 115",
        tags=["element", "propulsion"],
        sources=["Lazar-1989"],
        body="Element 115 is claimed to power alien craft via antimatter reactor."
    )

    # Fresh evidence contradicting canon — different narrative
    fresh = [
        _ev("Element 115 does not exist as stable isotope, claim completely debunked by physics community", platform="reddit", eng=2000, cluster="c1"),
        _ev("Element 115 Moscovium half-life microseconds, cannot power craft", platform="news", eng=1500, cluster="c2"),
        _ev("Physicists reject Element 115 propulsion claims", platform="x", eng=800, odds=0.15, cluster="c3"),
    ]

    result = compute_narrative_divergence("Element 115", wiki_page, fresh)

    assert result.divergence_risk > 0.3
    assert len(result.driving_claims) >= 1
    # At least one driving claim should mention debunk or contradiction
    driving_texts = " ".join(dc.claim_text.lower() for dc in result.driving_claims)
    assert any(kw in driving_texts for kw in ["debunk", "reject", "not exist", "cannot", "microsecond"])


def test_divergence_calls_into_spacetime_engine():
    import inspect
    from src.quantum_credibility import divergence_engine as de_mod
    source = inspect.getsource(de_mod._compute_divergence_risk)

    # Must call find_optimal_path from ai_navigator or vector_to_field_geometry from spacetime_engine
    assert ("find_optimal_path" in source) or ("vector_to_field_geometry" in source) or ("FieldGeometryTensor" in source)

    # Also check module level imports for reuse
    module_source = inspect.getsource(de_mod)
    # Must import from spacetime_engine or ai_navigator
    assert "spacetime_engine" in module_source or "ai_navigator" in module_source
    # Must NOT reimplement warp-factor formula inline — should delegate
    # We allow small fallback, but primary path must delegate


def test_divergence_empty_fresh_evidence():
    wiki_page = _wiki_page(title="Area 51")
    result = compute_narrative_divergence("Area 51", wiki_page, [])

    assert result.entity_name == "Area 51"
    assert 0.0 <= result.divergence_risk <= 1.0
    assert result.canon_vector_hash != ""
