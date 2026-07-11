import logging
import math
from collections import defaultdict
from typing import List, Dict, Tuple, Set

import numpy as np

from src.models import ClaimEvidence
from src.spacetime_engine.entanglement import meyer_wallach

logger = logging.getLogger("chickensoup.quantum_credibility.entanglement_corr")


def _cluster_evidence_by_id(evidence: List[ClaimEvidence]) -> Dict[str, List[ClaimEvidence]]:
    clusters: Dict[str, List[ClaimEvidence]] = defaultdict(list)
    for ev in evidence:
        clusters[ev.cluster_id or f"auto:{ev.claim_text[:20]}"].append(ev)
    return clusters


def _extract_entity_mentions(evidence: List[ClaimEvidence], entity_names: Set[str]) -> Dict[str, Set[str]]:
    # Map cluster_id -> set of entity names mentioned
    mentions: Dict[str, Set[str]] = defaultdict(set)
    lower_names = {name.lower(): name for name in entity_names}

    for ev in evidence:
        text_lower = ev.claim_text.lower()
        for lower_name, original_name in lower_names.items():
            if lower_name in text_lower:
                mentions[ev.cluster_id].add(original_name)

    return mentions


def compute_entanglement_correlation(
    entity_a: str,
    entity_b: str,
    evidence: List[ClaimEvidence],
) -> Dict[str, any]:
    if not evidence:
        return {
            "entity_a": entity_a,
            "entity_b": entity_b,
            "entanglement_score": 0.0,
            "co_occurrence_count": 0,
            "independent_platforms": [],
            "independent_clusters": 0,
            "is_strong": False,
        }

    # Find evidence mentioning both entities
    lower_a = entity_a.lower()
    lower_b = entity_b.lower()

    co_evidence: List[ClaimEvidence] = []
    for ev in evidence:
        text_lower = ev.claim_text.lower()
        if lower_a in text_lower and lower_b in text_lower:
            co_evidence.append(ev)

    if not co_evidence:
        return {
            "entity_a": entity_a,
            "entity_b": entity_b,
            "entanglement_score": 0.0,
            "co_occurrence_count": 0,
            "independent_platforms": [],
            "independent_clusters": 0,
            "is_strong": False,
        }

    # Independent platforms and clusters
    platforms = set(ev.source_platform for ev in co_evidence)
    clusters = set(ev.cluster_id for ev in co_evidence)

    # Encode co-occurrence pattern as quantum state
    # Each independent cluster = basis contribution; more clusters + more platforms = higher entanglement
    n_platforms = len(platforms)
    n_clusters = len(clusters)

    # Build a statevector where each qubit represents a platform's participation
    # For simplicity: map platforms to qubits, clusters to superposition basis
    # |psi> = sum_{cluster} (1/sqrt(N)) |platform_bitstring_cluster>
    n_qubits = max(1, min(4, n_platforms))  # cap at 4 qubits (16 states) for tractability

    # Map platform to qubit index
    plat_list = sorted(platforms)
    plat_to_qubit = {p: i % n_qubits for i, p in enumerate(plat_list)}

    dim = 2 ** n_qubits
    state = np.zeros(dim, dtype=complex)

    # Group evidence by cluster and build bitstring per cluster
    cluster_platforms: Dict[str, Set[str]] = defaultdict(set)
    for ev in co_evidence:
        cluster_platforms[ev.cluster_id].add(ev.source_platform)

    for cluster_id, plats in cluster_platforms.items():
        bitstring = 0
        for p in plats:
            q = plat_to_qubit.get(p, 0)
            bitstring |= (1 << q)
        # Add to superposition (with equal weight for now — independent source = genuine entanglement)
        state[bitstring % dim] += 1.0

    # Normalise
    norm = np.linalg.norm(state)
    if norm < 1e-12:
        return {
            "entity_a": entity_a,
            "entity_b": entity_b,
            "entanglement_score": 0.0,
            "co_occurrence_count": len(co_evidence),
            "independent_platforms": list(platforms),
            "independent_clusters": n_clusters,
            "is_strong": False,
        }

    state = state / norm

    # Meyer-Wallach entanglement score
    try:
        q_score = meyer_wallach(state)
    except Exception as e:
        logger.debug(f"Meyer-Wallach scoring failed: {e}")
        q_score = 0.0

    # Adjust score: boost when platforms are truly independent (from different clusters)
    # vs single wiki-editor cross-ref (single cluster, single platform)
    if n_clusters == 1 and n_platforms == 1:
        # Single co-mention — not entangled
        effective_score = q_score * 0.2
    elif n_clusters >= 3 and n_platforms >= 3:
        # Strong independent binding
        effective_score = min(1.0, q_score * 1.5)
    else:
        effective_score = q_score

    # Factor in raw counts
    count_factor = min(1.0, (n_clusters + n_platforms) / 6.0)
    final_score = effective_score * 0.7 + count_factor * 0.3
    final_score = max(0.0, min(1.0, final_score))

    return {
        "entity_a": entity_a,
        "entity_b": entity_b,
        "entanglement_score": float(final_score),
        "co_occurrence_count": len(co_evidence),
        "independent_platforms": sorted(platforms),
        "independent_clusters": n_clusters,
        "is_strong": final_score > 0.5,
        "meyer_wallach_raw": float(q_score),
        "co_evidence": [e.model_dump() for e in co_evidence[:5]],
    }


def compute_all_entanglements(
    target_entity: str,
    evidence: List[ClaimEvidence],
    candidate_entities: List[str] = None,
) -> List[Dict[str, any]]:
    if candidate_entities is None:
        # Extract entities from evidence claim_text via simple capitalised phrase detection
        import re
        entity_counter: Dict[str, int] = defaultdict(int)
        for ev in evidence:
            # Capitalised phrases of 2+ words
            caps = re.findall(r"\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)", ev.claim_text)
            for c in caps:
                if c.lower() != target_entity.lower() and len(c) > 3:
                    entity_counter[c] += 1

        # Top candidates with >=2 mentions
        candidate_entities = [name for name, cnt in sorted(entity_counter.items(), key=lambda x: -x[1]) if cnt >= 2][:20]

    results = []
    for cand in candidate_entities:
        if cand.lower() == target_entity.lower():
            continue
        res = compute_entanglement_correlation(target_entity, cand, evidence)
        if res["co_occurrence_count"] > 0:
            results.append(res)

    results.sort(key=lambda r: -r["entanglement_score"])
    return results
