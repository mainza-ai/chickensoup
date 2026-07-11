import logging
import math
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

import numpy as np

from src.config import settings
from src.models import ClaimEvidence, ClaimConfidence
from src.spacetime_engine.vqe_runner import score_claim_state
from src.observability import wavefunction_state_total

logger = logging.getLogger("chickensoup.quantum_credibility.wavefunction")

SOCIAL_TRACTION_WEIGHT_IN_EPISTEMIC = 0.15
COLLAPSE_THRESHOLD = 0.75
STATE_LABELS = ["corroborated", "contested", "unverified"]


def _source_diversity(evidence: List[ClaimEvidence]) -> float:
    if not evidence:
        return 0.0
    platforms = set(e.source_platform.lower() for e in evidence if e.source_platform)
    # 1 platform = 0.2, 5+ platforms = 1.0
    return min(1.0, len(platforms) / 5.0)


def _engagement_magnitude(evidence: List[ClaimEvidence]) -> float:
    if not evidence:
        return 0.0
    total = sum(e.engagement_count for e in evidence)
    # log1p scaled, cap at ~1.0 for 10k total engagement
    return min(1.0, math.log1p(total) / math.log1p(10000))


def _polymarket_prior(evidence: List[ClaimEvidence]) -> Optional[float]:
    odds = [e.polymarket_odds for e in evidence if e.polymarket_odds is not None]
    if not odds:
        return None
    return float(np.mean(odds))


def _contradiction_signal(evidence: List[ClaimEvidence]) -> float:
    # Stub: if we have divergent polymarket odds or mixed sentiment markers
    # For now: stddev of polymarket odds scaled
    odds = [e.polymarket_odds for e in evidence if e.polymarket_odds is not None]
    if len(odds) >= 2:
        std = float(np.std(odds))
        return min(1.0, std * 3.0)

    # Mixed platform signals — low diversity but high engagement could indicate contestation
    # Placeholder 0.0 if lint/contradiction agent not built
    return 0.0


def _social_traction(
    evidence: List[ClaimEvidence],
    half_life_days: float = None,
) -> float:
    if not evidence:
        return 0.0

    if half_life_days is None:
        half_life_days = settings.SOCIAL_TRACTION_HALF_LIFE_DAYS

    total_raw = sum(e.engagement_count for e in evidence)
    if total_raw <= 0:
        return 0.0

    # Decayed engagement if timestamps available
    decayed_total = 0.0
    has_decay = False
    now = datetime.now(timezone.utc)

    for e in evidence:
        eng = e.engagement_count
        if not settings.SOCIAL_TRACTION_DECAY_ENABLED:
            decayed_total += eng
            continue

        try:
            ts = datetime.fromisoformat(e.timestamp.replace("Z", "+00:00"))
            if ts.tzinfo is None:
                ts = ts.replace(tzinfo=timezone.utc)
            age_days = (now - ts).total_seconds() / 86400.0
            decay_factor = 0.5 ** (age_days / half_life_days) if half_life_days > 0 else 1.0
            decayed_total += eng * decay_factor
            has_decay = True
        except Exception:
            decayed_total += eng

    # Normalised to [0,1] via log scale
    # 100 engagement → 0.3, 1000 → 0.6, 10000 → 1.0
    traction = min(1.0, math.log1p(decayed_total) / math.log1p(10000))
    return traction


def _compute_amplitudes(
    source_diversity: float,
    engagement_magnitude: float,
    polymarket_prior: Optional[float],
    contradiction_signal: float,
) -> List[float]:
    # Three basis states: CORROBORATED, CONTESTED, UNVERIFIED
    # We compute unnormalised amplitudes, then normalise

    # Corroborated amplitude: grows with diversity + magnitude + market prior
    # Polymarket is weighted heavily as market-priced belief
    market_term = 0.0
    if polymarket_prior is not None:
        # Map 0.5 → neutral, 0.9 → high corroborated, 0.1 → low
        market_term = (polymarket_prior - 0.5) * 1.5

    corroborated_raw = (
        source_diversity * 0.4
        + engagement_magnitude * SOCIAL_TRACTION_WEIGHT_IN_EPISTEMIC
        + max(0.0, market_term) * 0.6
        + 0.1  # bias
    )

    # Contested amplitude: grows with contradiction signal + moderate diversity but conflicting odds
    contested_raw = (
        contradiction_signal * 0.7
        + (0.3 if 0.2 < source_diversity < 0.6 and contradiction_signal > 0 else 0.0)
        + 0.05
    )

    # Unverified amplitude: high when evidence sparse
    # Inverse of diversity and engagement
    unverified_raw = (
        (1.0 - source_diversity) * 0.5
        + (1.0 - engagement_magnitude) * 0.3
        + (0.5 if polymarket_prior is None else 0.0)
        + 0.1
    )

    # Adjust: if market strongly contradicts (odds < 0.2) and diversity high, boost contested over corroborated
    if polymarket_prior is not None and polymarket_prior < 0.3 and source_diversity > 0.4:
        contested_raw += (0.3 - polymarket_prior) * 0.8

    # If market strongly corroborates and diversity high, suppress unverified
    if polymarket_prior is not None and polymarket_prior > 0.7 and source_diversity > 0.4:
        unverified_raw *= 0.3
        contested_raw *= 0.5

    amplitudes = [corroborated_raw, contested_raw, unverified_raw]
    # Ensure non-negative
    amplitudes = [max(0.01, a) for a in amplitudes]

    return amplitudes


class ClaimWavefunction:
    def __init__(self):
        self.scoring_version = settings.WAVEFUNCTION_SCORING_VERSION

    def score_claim(self, claim_text: str, evidence: List[ClaimEvidence]) -> ClaimConfidence:
        if not evidence:
            # No evidence → unverified with low epistemic, zero traction
            return ClaimConfidence(
                epistemic_confidence=0.35,
                social_traction=0.0,
                state_label="unverified",
                collapsed=False,
                evidence_count=0,
                last_pulse_at=None,
                scoring_version=self.scoring_version,
                scoring_inputs={
                    "source_diversity": 0.0,
                    "engagement_magnitude": 0.0,
                    "polymarket_prior": None,
                    "contradiction_signal": 0.0,
                    "social_traction": 0.0,
                    "note": "no evidence — fallback heuristic",
                },
                claim_text=claim_text[:500] if claim_text else None,
            )

        diversity = _source_diversity(evidence)
        eng_mag = _engagement_magnitude(evidence)
        market_prior = _polymarket_prior(evidence)
        contra_sig = _contradiction_signal(evidence)
        traction = _social_traction(evidence)

        if contra_sig == 0.0:
            logger.debug("Contradiction signal stub 0.0 — lint/contradiction agent not yet built (TODO)")

        amplitudes = _compute_amplitudes(diversity, eng_mag, market_prior, contra_sig)

        # Route through quantum VQE scorer
        try:
            quantum_result = score_claim_state(amplitudes)
            probs = quantum_result.get("probabilities", [])
            if len(probs) >= 3:
                probs_arr = np.array(probs)
            else:
                amps_arr = np.array(amplitudes)
                probs_arr = (amps_arr ** 2)
                probs_arr = probs_arr / probs_arr.sum() if probs_arr.sum() > 1e-12 else np.array([0.33, 0.33, 0.34])

            collapsed = quantum_result.get("collapsed", False)
            vqe_backend = quantum_result.get("vqe", {}).get("backend", "unknown")
            entanglement_score = quantum_result.get("vqe", {}).get("entanglement_score", 0.0)
        except Exception as e:
            logger.warning(f"Quantum scoring failed, using classical fallback: {e}")
            amps_arr = np.array(amplitudes)
            probs_arr = (amps_arr ** 2)
            probs_arr = probs_arr / probs_arr.sum() if probs_arr.sum() > 1e-12 else np.array([0.33, 0.33, 0.34])
            collapsed = bool(probs_arr.max() > COLLAPSE_THRESHOLD)
            vqe_backend = f"classical-fallback: {e}"
            entanglement_score = 0.0

        # Probabilities: [corroborated, contested, unverified]
        max_idx = int(probs_arr.argmax())
        state_label = STATE_LABELS[max_idx] if max_idx < len(STATE_LABELS) else "unverified"

        # Epistemic confidence: weighted combination
        # Corroborated prob is primary, but contested reduces effective confidence
        p_corr = float(probs_arr[0]) if len(probs_arr) > 0 else 0.33
        p_cont = float(probs_arr[1]) if len(probs_arr) > 1 else 0.33
        p_unver = float(probs_arr[2]) if len(probs_arr) > 2 else 0.33

        # Epistemic: high when corroborated dominates, reduced by contested, low when unverified dominates
        # Formula: epistemic = p_corr * 0.7 + (1 - p_unver) * 0.2 + (1 - p_cont) * 0.1
        # But also incorporate raw signals: diversity weights into epistemic (not social)
        epistemic = (
            p_corr * 0.6
            + (1.0 - p_unver) * 0.15
            + (1.0 - p_cont) * 0.1
            + diversity * 0.1
            + (market_prior if market_prior is not None else 0.5) * 0.05
        )
        epistemic = max(0.0, min(1.0, epistemic))

        # Refine: if contested state, epistemic is pulled toward 0.5 (uncertainty)
        if state_label == "contested":
            epistemic = 0.5 + (epistemic - 0.5) * 0.5

        max_prob = float(probs_arr.max()) if len(probs_arr) > 0 else 0.0

        if not collapsed:
            collapsed = bool(max_prob > COLLAPSE_THRESHOLD)

        # Evidence-strength gate for collapse: single low-diversity low-engagement
        # claims should not be considered collapsed even if p(unverified) is high.
        # Collapsed requires either sufficient diversity, count, or market signal.
        if collapsed:
            has_strength = (
                diversity > 0.3
                or len(evidence) >= 3
                or (market_prior is not None)
                or eng_mag > 0.4
            )
            if state_label == "unverified" and not has_strength:
                collapsed = False
            elif state_label in ("corroborated", "contested") and max_prob > 0.9:
                # Strong peaks always collapsed even with minimal evidence if market-backed
                pass
            elif not has_strength and max_prob < 0.92:
                collapsed = False

        # Last pulse timestamp — most recent evidence
        last_pulse = None
        try:
            from datetime import datetime
            latest = None
            for ev in evidence:
                try:
                    ts = datetime.fromisoformat(ev.timestamp.replace("Z", "+00:00"))
                    if latest is None or ts > latest:
                        latest = ts
                except Exception:
                    continue
            if latest:
                last_pulse = latest.isoformat()
        except Exception:
            pass

        scoring_inputs = {
            "source_diversity": diversity,
            "engagement_magnitude": eng_mag,
            "polymarket_prior": market_prior,
            "contradiction_signal": contra_sig,
            "social_traction": traction,
            "social_traction_weight": SOCIAL_TRACTION_WEIGHT_IN_EPISTEMIC,
            "amplitudes": amplitudes,
            "probabilities": probs_arr.tolist() if hasattr(probs_arr, 'tolist') else list(probs_arr),
            "vqe_backend": vqe_backend,
            "entanglement_score": entanglement_score,
            "evidence_platforms": list(set(e.source_platform for e in evidence)),
            "evidence_count": len(evidence),
        }

        try:
            wavefunction_state_total.add(1, {"state": state_label, "collapsed": str(collapsed).lower()})
        except Exception:
            pass

        logger.info(
            f"Wavefunction scored claim '{claim_text[:80]}': "
            f"{state_label} (epistemic={epistemic:.3f}, traction={traction:.3f}, "
            f"collapsed={collapsed}, diversity={diversity:.2f}, backend={vqe_backend})"
        )

        return ClaimConfidence(
            epistemic_confidence=epistemic,
            social_traction=traction,
            state_label=state_label,
            collapsed=collapsed,
            evidence_count=len(evidence),
            last_pulse_at=last_pulse,
            scoring_version=self.scoring_version,
            scoring_inputs=scoring_inputs,
            claim_text=claim_text[:500] if claim_text else None,
        )

    def score_claims(self, claims_with_evidence: List[tuple[str, List[ClaimEvidence]]]) -> List[ClaimConfidence]:
        results = []
        for claim_text, ev_list in claims_with_evidence:
            try:
                results.append(self.score_claim(claim_text, ev_list))
            except Exception as e:
                logger.warning(f"Failed to score claim '{claim_text[:50]}': {e}")
                results.append(ClaimConfidence(
                    epistemic_confidence=0.5,
                    social_traction=0.0,
                    state_label="unverified",
                    collapsed=False,
                    evidence_count=len(ev_list),
                    scoring_version=self.scoring_version,
                    scoring_inputs={"error": str(e)},
                    claim_text=claim_text[:500],
                ))
        return results
