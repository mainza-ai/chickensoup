import hashlib
import logging
import math
import re
from typing import List, Dict, Any, Optional

import numpy as np

from src.models import ClaimEvidence
from src.spacetime_engine.tensor import FieldGeometryTensor

logger = logging.getLogger("chickensoup.quantum_credibility.vectorizer")

SOCIAL_TRACTION_WEIGHT_IN_EPISTEMIC = 0.15

N_DIM = 16  # claim vector dimension — must stay small for quantum circuit encoding


def _normalize_vec(v: np.ndarray) -> np.ndarray:
    norm = np.linalg.norm(v)
    if norm < 1e-12:
        return np.zeros_like(v)
    return v / norm


def claims_to_vector(evidence: List[ClaimEvidence]) -> np.ndarray:
    if not evidence:
        return np.zeros(N_DIM)

    platform_set = set(e.source_platform for e in evidence)
    n_platforms = len(platform_set)
    total_eng = sum(e.engagement_count for e in evidence)
    has_polymarket = sum(1 for e in evidence if e.polymarket_odds is not None)
    avg_odds = float(np.mean([e.polymarket_odds for e in evidence if e.polymarket_odds is not None])) if has_polymarket > 0 else 0.5

    # Log-scaled engagement magnitude
    eng_mag = math.log1p(total_eng) / 10.0 if total_eng > 0 else 0.0
    eng_mag = min(1.0, eng_mag)

    # Source diversity normalised
    diversity = min(1.0, n_platforms / 5.0)

    # Decay-weighted engagement (if present)
    decayed_avg = 0.0
    decayed_items = [e.engagement_decayed for e in evidence if e.engagement_decayed is not None]
    if decayed_items:
        decayed_avg = float(np.mean(decayed_items))

    # Build 16-dim vector — interpretable slots:
    # 0: diversity, 1: eng_mag, 2: decayed_avg, 3: avg_odds, 4: has_polymarket normalised, 5: evidence count norm
    # 6-9: platform one-hots (reddit, x, youtube, news) as binary
    # 10: contradiction proxy — variance in odds if multiple markets
    # 11: timestamp recency — avg age in days capped
    # 12: claim text char length diversity, 13: url presence ratio, 14: cluster diversity, 15: bias term 1.0

    vec = np.zeros(N_DIM)

    vec[0] = diversity
    vec[1] = eng_mag
    vec[2] = decayed_avg
    vec[3] = avg_odds
    vec[4] = min(1.0, has_polymarket / max(len(evidence), 1))
    vec[5] = min(1.0, len(evidence) / 10.0)

    platform_lower = set(p.lower() for p in platform_set)
    vec[6] = 1.0 if "reddit" in platform_lower or "subreddit" in platform_lower else 0.0
    vec[7] = 1.0 if "x" in platform_lower or "twitter" in platform_lower else 0.0
    vec[8] = 1.0 if "youtube" in platform_lower else 0.0
    vec[9] = 1.0 if "news" in platform_lower else 0.0

    # Variance in polymarket odds as contradiction proxy
    odds_list = [e.polymarket_odds for e in evidence if e.polymarket_odds is not None]
    if len(odds_list) >= 2:
        vec[10] = min(1.0, float(np.std(odds_list)) * 2.0)
    else:
        vec[10] = 0.0

    # Recency — if evidence timestamps parseable, compute avg days ago
    try:
        from datetime import datetime, timezone
        now = datetime.now(timezone.utc)
        ages = []
        for e in evidence:
            try:
                ts = datetime.fromisoformat(e.timestamp.replace("Z", "+00:00"))
                if ts.tzinfo is None:
                    ts = ts.replace(tzinfo=timezone.utc)
                age_days = (now - ts).total_seconds() / 86400.0
                ages.append(max(0.0, age_days))
            except Exception:
                continue
        if ages:
            avg_age = float(np.mean(ages))
            vec[11] = max(0.0, min(1.0, 1.0 - avg_age / 30.0))
        else:
            vec[11] = 0.5
    except Exception:
        vec[11] = 0.5

    # Text length diversity
    lengths = [len(e.claim_text) for e in evidence]
    if lengths:
        mean_len = float(np.mean(lengths))
        vec[12] = min(1.0, mean_len / 500.0)
        url_ratio = sum(1 for e in evidence if e.url) / len(evidence)
        vec[13] = url_ratio
        cluster_set = set(e.cluster_id for e in evidence if e.cluster_id)
        vec[14] = min(1.0, len(cluster_set) / max(len(evidence), 1))
    else:
        vec[12] = 0.0
        vec[13] = 0.0
        vec[14] = 0.0

    vec[15] = 1.0  # bias

    return _normalize_vec(vec)


def canon_page_to_vector(wiki_page: Dict[str, Any]) -> np.ndarray:
    if not wiki_page:
        return np.zeros(N_DIM)

    frontmatter = wiki_page.get("frontmatter", {}) if isinstance(wiki_page, dict) else {}
    body = wiki_page.get("body", "") if isinstance(wiki_page, dict) else str(wiki_page)

    tags = frontmatter.get("tags", []) if isinstance(frontmatter, dict) else []
    sources = frontmatter.get("sources", []) if isinstance(frontmatter, dict) else []
    related = frontmatter.get("related", []) if isinstance(frontmatter, dict) else []

    vec = np.zeros(N_DIM)

    # Slots mirroring live vector but derived from canon
    vec[0] = min(1.0, len(set(sources)) / 5.0) if sources else 0.0  # diversity proxy
    vec[1] = 0.5  # canon engagement placeholder (neutral)
    vec[2] = 0.5
    vec[3] = 0.5  # no market odds in canon — neutral
    vec[4] = 0.0
    vec[5] = min(1.0, len(related) / 10.0) if related else 0.0

    vec[6] = 1.0 if any("reddit" in str(s).lower() for s in sources) else 0.0
    vec[7] = 0.0
    vec[8] = 1.0 if any("youtube" in str(s).lower() or "video" in str(s).lower() for s in sources) else 0.0
    vec[9] = 1.0 if any("news" in str(s).lower() or "hearing" in str(s).lower() for s in sources) else 0.0

    vec[10] = 0.0  # no contradiction signal in canon alone

    # Tag-based heuristics
    tag_str = " ".join(tags).lower() if tags else ""
    body_lower = body.lower() if isinstance(body, str) else ""

    vec[11] = 0.8  # canon assumed established
    vec[12] = min(1.0, len(body) / 5000.0) if body else 0.0
    vec[13] = min(1.0, body.count("http") / 10.0) if body else 0.0
    vec[14] = min(1.0, body.count("[[") / 20.0) if body else 0.0
    vec[15] = 1.0

    return _normalize_vec(vec)


def vector_to_field_geometry(canon_vec: np.ndarray, live_vec: np.ndarray) -> FieldGeometryTensor:
    diff = live_vec - canon_vec
    diff_norm = float(np.linalg.norm(diff))

    # Map divergence magnitude to warp and lapse perturbations
    warp = 1.0 + diff_norm * 0.5
    lapse = max(0.1, 1.0 - diff_norm * 0.2)

    # Entropy density correlated with divergence
    entropy = diff_norm * 0.5

    # Extrinsic curvature seeded by diff components
    k_scale = diff_norm * 0.05

    spatial_metric = [
        [warp, k_scale, 0.0],
        [k_scale, 1.0, k_scale * 0.5],
        [0.0, k_scale * 0.5, 1.0],
    ]

    extrinsic_curvature = [
        [k_scale, 0.0, 0.0],
        [0.0, k_scale * 0.5, 0.0],
        [0.0, 0.0, k_scale * 0.3],
    ]

    return FieldGeometryTensor(
        lapse=lapse,
        shift=[float(diff[0] * 0.1) if len(diff) > 0 else 0.0, 0.0, 0.0],
        spatial_metric=spatial_metric,
        extrinsic_curvature=extrinsic_curvature,
        entropy_density=entropy,
        warp_factor=warp,
    )


def hash_vector(vec: np.ndarray) -> str:
    h = hashlib.sha256(vec.tobytes()).hexdigest()
    return h[:12]
