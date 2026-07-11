---
title: "Credibility Scoring"
tags: [credibility, scoring, wavefunction, quantum]
created: 2026-06-22
updated: 2026-07-12
sources: [ufo-2026, living-almanac, vqe-runner, entanglement]
related: [knowledge-graph-schema, local-first-llm, ai-alien-connection, living-almanac, agent-architecture, field-geometry-tensor, api-design, quantum-state-representation]
---

# Credibility Scoring — Quantum Wavefunction Engine

Hardcoded confidence constants (`0.95` in TQL, `0.5` heuristic, `0.8` wiki-file fallback, `+0.1 Person, +0.15 Project` label heuristic) are now replaced by **quantum-scored wavefunctions** derived from real corroboration when `last30days` evidence exists. Falls back to existing heuristic when no recent pulse — graceful degrade, not hard dependency.

## The Wavefunction Model

Every claim is a state vector over three basis states: `CORROBORATED`, `CONTESTED`, `UNVERIFIED`.

### Inputs (all derived from real `ClaimEvidence`, never invented)

| Input | How Derived | Example |
|-------|-------------|---------|
| `source_diversity` | Distinct independent platforms (`len(platforms)/5`) | reddit + x + youtube + news = 0.8 |
| `engagement_magnitude` | `log1p(total_eng)/log1p(10000)` | 1200 engagement → ~0.3 |
| `polymarket_prior` | Mean of `polymarket_odds` when market exists, nullable | 0.91 → strong corroborated signal |
| `contradiction_signal` | Stddev of odds when multiple markets diverge; stub 0.0 if lint not built, logged as TODO | 0.15 vs 0.85 odds → high contradiction |
| `social_traction` | Raw engagement decayed with half-life `SOCIAL_TRACTION_HALF_LIFE_DAYS=7`, `log1p` scaled — computed separately, never folded as epistemic alone | 100k views → high traction but may be low epistemic |

### The Named Constant

`SOCIAL_TRACTION_WEIGHT_IN_EPISTEMIC = 0.15` — engagement contributes to epistemic confidence only via this explicitly named weight, not buried in a formula. This satisfies the non-negotiable: social traction and epistemic credibility are two separate numbers, never merged.

### Quantum Implementation

- Amplitudes computed from inputs → normalized → passed to `score_claim_state()` in `src/spacetime_engine/vqe_runner.py`
- `vqe_runner.py` builds a qubit circuit: `RY(theta)` encoding for 3-basis system, `AerEstimatorV2` pattern first, legacy Aer fallback, NumPy fallback
- `meyer_wallach()` entanglement scorer from `src/spacetime_engine/entanglement.py` — reusable (VQE rejection at <0.3 + entanglement correlation)
- Output: `(epistemic_confidence: float, state_label: str, collapsed: bool)` plus `evidence_count`, `last_pulse_at`, `scoring_inputs` dict for auditability

### Collapse

- `collapsed=True` when distribution sharply peaked on one basis (max prob > 0.75) **and** evidence strength gate passes (diversity > 0.3 or count >=3 or market present or eng_mag > 0.4). Single low-diversity claims don't collapse even if `p(unverified)` high — calibration check in `test_wavefunction.py`.

## Data Model

```python
class ClaimConfidence(BaseModel):
    epistemic_confidence: float = Field(..., ge=0.0, le=1.0)
    social_traction: float = Field(..., ge=0.0, le=1.0)
    state_label: str  # "corroborated" | "contested" | "unverified"
    collapsed: bool
    evidence_count: int
    last_pulse_at: Optional[str]
    scoring_version: str = "v1-wavefunction"
    scoring_inputs: Dict[str, Any]  # falsifiable + logged
    claim_text: Optional[str]
```

### Decoupling Proof

`tests/test_wavefunction.py` asserts:
- High engagement single-platform → high traction, low diversity, epistemic != traction
- Low engagement multi-platform + high market → low traction, high epistemic, still decoupled
- No fixture where they shouldn't be equal has equality

## Wiring

- `research_agent.py` `credibility_scoring_node`: tries `load_recent_pulse_evidence(entity, max_age_days=14)` for each found node; if evidence exists, `ClaimWavefunction.score_claim()` replaces heuristic. If not, fallback to existing `+0.1/+0.15` label heuristic.
- `main.py` `_build_query_response()` now actually populates `inferred_events` and `inferred_entities` from `wavefunction_scores` (dead since last audit — this is the fix).
- `GET /entities/{name}/divergence` extends `WikiPageDetailResponse` with `divergence: DivergenceResult` + `claim_confidences: List[ClaimConfidence]`

## Related Modules

- `src/quantum_credibility/wavefunction.py` — core scorer
- `src/spacetime_engine/vqe_runner.py` — AerEstimatorV2 wrapper + claim state circuits
- `src/spacetime_engine/entanglement.py` — `meyer_wallach()` reusable scorer
- `src/quantum_credibility/vectorizer.py` — `claims_to_vector()`, `canon_page_to_vector()`, `vector_to_field_geometry()` — factory for `FieldGeometryTensor` from claim evidence (avoids duplicating warp math)
- `src/quantum_credibility/divergence_engine.py` — repoints tensor machinery at real drift, calls `find_optimal_path` (grep-able shared function per spec)
- `src/quantum_credibility/entanglement_corr.py` — encodes co-occurrence across independent clusters as quantum state, runs Meyer-Wallach, independent platforms score higher than single cross-ref
- `src/almanac/timeline.py` — reconstructs from `wiki/raw/pulse/*.json` + `git log`, no new TSDB, chartable `{date, epistemic, social, divergence}`
- `src/agents/tribunal_agent.py` — Skeptic/Empiricist/Believer + referee LangGraph, gated on contested/divergence, uncontested never triggers (cost control)

## Calibration Fixtures

| Fixture | Expected State | Example |
|---------|---------------|---------|
| High diversity (5 platforms) + high market (0.90 avg) | corroborated, collapsed | "Bob Lazar S-4" with reddit+x+youtube+news+github + 0.91 odds |
| Single low-engagement source | unverified, not collapsed | 5 upvotes, 1 platform |
| Contradicted (odds variance high) | contested | 0.75 vs 0.15 market odds |

## See Also

- [[living-almanac]] — full 7-phase implementation plan
- [[agent-architecture]] — research agent + tribunal wiring
- [[field-geometry-tensor]] — contract between quantum layers
- [[api-design]] — new endpoints: `/pulse`, `/divergence`, `/timeline`, `/entanglement`, `/tribunal`, `/budget`, `/almanac`
- [[frontend-settings-menu]] — SwiftUI plan for exposing scores and controls
