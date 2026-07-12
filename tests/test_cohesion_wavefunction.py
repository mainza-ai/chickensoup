import pytest
from src.models import ClaimEvidence
from src.quantum_credibility.wavefunction import ClaimWavefunction
from datetime import datetime, timezone

def test_wavefunction_cohesion_with_reinforcement():
    wf = ClaimWavefunction()
    
    # Minimal evidence that would ordinarily be unverified
    evidence = [
        ClaimEvidence(
            claim_text="Alien craft S-4 sighting",
            source_platform="reddit",
            engagement_count=10,
            url="https://reddit.com/r/ufos/comments/1",
            timestamp=datetime.now(timezone.utc).isoformat(),
            cluster_id="c1"
        )
    ]
    
    # 1. Baseline: no reinforcement
    baseline_result = wf.score_claim("Alien craft S-4 sighting", evidence, reinforcement_count=0)
    
    # 2. Reinforced: count = 5
    reinforced_result = wf.score_claim("Alien craft S-4 sighting", evidence, reinforcement_count=5)
    
    # The reinforced result should have higher epistemic confidence
    assert reinforced_result.epistemic_confidence > baseline_result.epistemic_confidence
    assert reinforced_result.scoring_inputs["reinforcement_count"] == 5
    
    # The probability of corroborated should be higher
    p_corr_baseline = baseline_result.scoring_inputs["probabilities"][0]
    p_corr_reinforced = reinforced_result.scoring_inputs["probabilities"][0]
    assert p_corr_reinforced > p_corr_baseline
    
    # The probability of unverified should be lower
    p_unver_baseline = baseline_result.scoring_inputs["probabilities"][2]
    p_unver_reinforced = reinforced_result.scoring_inputs["probabilities"][2]
    assert p_unver_reinforced < p_unver_baseline
