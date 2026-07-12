import json
import logging
import re
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

from src.models import ClaimEvidence

logger = logging.getLogger("chickensoup.last30days_adapter")

PLATFORM_KEYWORDS = {
    "reddit": ["reddit", "subreddit", "r/", "upvote"],
    "x": ["twitter", "x.com", "t.co", "tweet", "@", "𝕏"],
    "youtube": ["youtube", "youtu.be", "video transcript"],
    "news": ["news", "article", "report", "hearing", "congress"],
    "github": ["github", "git", "commit", "pr", "issue"],
    "subreddit": ["subreddit", "r/"],
    "polymarket": ["polymarket", "market odds", "market-implied", "prediction market"],
    "perplexity": ["perplexity"],
    "brave": ["brave search"],
    "podcast": ["podcast", "episode", "transcript"],
}


def _infer_platform(text: str) -> str:
    lower = text.lower()
    for platform, keywords in PLATFORM_KEYWORDS.items():
        for kw in keywords:
            if kw in lower:
                return platform
    return "unknown"


def _extract_urls(text: str) -> List[str]:
    pattern = re.compile(r"https?://[^\s\)\]\>\"']+")
    urls = pattern.findall(text)
    # Trim trailing punctuation
    cleaned = []
    for u in urls:
        u = u.rstrip(".,;!?)")
        cleaned.append(u)
    return cleaned


def parse_json_output(raw: str, entity_name: str) -> Optional[List[ClaimEvidence]]:
    try:
        data = json.loads(raw)
    except (json.JSONDecodeError, ValueError):
        return None

    evidence_list: List[ClaimEvidence] = []

    # Support multiple shapes
    candidates = []
    if isinstance(data, dict):
        if "claims" in data and isinstance(data["claims"], list):
            candidates = data["claims"]
        elif "evidence" in data and isinstance(data["evidence"], list):
            candidates = data["evidence"]
        elif "results" in data and isinstance(data["results"], list):
            candidates = data["results"]
        elif "findings" in data and isinstance(data["findings"], list):
            candidates = data["findings"]
        else:
            # Treat whole dict as single claim if it has claim-ish keys
            if any(k in data for k in ("claim", "text", "title", "summary", "claim_text")):
                candidates = [data]
    elif isinstance(data, list):
        candidates = data

    for idx, item in enumerate(candidates):
        if not isinstance(item, dict):
            continue
        claim_text = (
            item.get("claim_text")
            or item.get("claim")
            or item.get("text")
            or item.get("title")
            or item.get("summary")
            or item.get("snippet")
            or ""
        )
        if not claim_text or len(claim_text.strip()) < 10:
            continue

        platform = item.get("source_platform") or item.get("platform") or _infer_platform(claim_text + " " + str(item.get("source", "")))
        url = item.get("url") or item.get("source") or ""
        if not url:
            urls = _extract_urls(claim_text)
            url = urls[0] if urls else ""

        engagement = item.get("engagement_count") or item.get("engagement") or item.get("upvotes") or 0
        try:
            engagement = int(engagement)
        except (ValueError, TypeError):
            engagement = 0

        polymarket = item.get("polymarket_odds")
        if polymarket is None:
            polymarket = item.get("market_odds")
        if polymarket is not None:
            try:
                polymarket = float(polymarket)
                if polymarket > 1.0:
                    polymarket = polymarket / 100.0
            except (ValueError, TypeError):
                polymarket = None

        timestamp = item.get("timestamp") or item.get("date") or datetime.now(timezone.utc).isoformat()
        cluster_id = str(item.get("cluster_id") or item.get("id") or f"{entity_name}:{idx}")

        try:
            ev = ClaimEvidence(
                claim_text=claim_text.strip()[:2000],
                source_platform=platform,
                engagement_count=engagement,
                url=url,
                timestamp=timestamp,
                cluster_id=cluster_id,
                polymarket_odds=polymarket,
                provenance_chain=[f"last30days:{entity_name}", f"cluster:{cluster_id}"],
            )
            evidence_list.append(ev)
        except Exception as e:
            logger.debug(f"Skipping invalid evidence item {idx}: {e}")
            continue

    return evidence_list if evidence_list else None


def parse_markdown_output(raw: str, entity_name: str) -> List[ClaimEvidence]:
    evidence_list: List[ClaimEvidence] = []
    timestamp_now = datetime.now(timezone.utc).isoformat()

    # Strategy 1: Look for ## Claims or ## Evidence or ### sections
    claims_section_pattern = re.compile(
        r"^#{2,3}\s*(claims|evidence|findings|key claims|notable claims)[^\n]*\n(.*?)(?=^#{1,3}\s|\Z)",
        re.MULTILINE | re.DOTALL | re.IGNORECASE,
    )
    matches = claims_section_pattern.findall(raw)

    lines_to_parse: List[str] = []

    if matches:
        for _, section_body in matches:
            for line in section_body.splitlines():
                stripped = line.strip()
                if not stripped:
                    continue
                # Bullet points or numbered lists
                bullet_match = re.match(r"^[-*]\s+(.*)", stripped) or re.match(r"^\d+\.\s+(.*)", stripped)
                if bullet_match:
                    lines_to_parse.append(bullet_match.group(1).strip())
                elif len(stripped) > 30:
                    lines_to_parse.append(stripped)
    else:
        # Fallback: treat non-empty bullet lines across entire doc as claims
        for line in raw.splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith("#") or stripped.startswith("```"):
                continue
            bullet_match = re.match(r"^[-*]\s+(.*)", stripped) or re.match(r"^\d+\.\s+(.*)", stripped)
            candidate = bullet_match.group(1).strip() if bullet_match else stripped
            if len(candidate) > 40:
                lines_to_parse.append(candidate)

    for idx, line in enumerate(lines_to_parse):
        urls = _extract_urls(line)
        url = urls[0] if urls else ""

        # Try to extract engagement hints
        engagement = 0
        eng_match = re.search(r"(\d+)\s*(upvotes?|likes?|views?|shares?|comments?|retweets?)", line, re.IGNORECASE)
        if eng_match:
            try:
                engagement = int(eng_match.group(1))
            except ValueError:
                pass

        polymarket_odds: Optional[float] = None
        poly_match = re.search(r"(\d{1,3}(?:\.\d+)?)\s*%\s*(?:chance|odds|probability)?", line, re.IGNORECASE)
        if "polymarket" in line.lower() or "market" in line.lower():
            if poly_match:
                try:
                    polymarket_odds = float(poly_match.group(1)) / 100.0
                except ValueError:
                    pass

        platform = _infer_platform(line)
        cluster_id = f"{entity_name}:md:{idx}"

        try:
            ev = ClaimEvidence(
                claim_text=line[:2000],
                source_platform=platform,
                engagement_count=engagement,
                url=url,
                timestamp=timestamp_now,
                cluster_id=cluster_id,
                polymarket_odds=polymarket_odds,
                provenance_chain=[f"last30days:{entity_name}:md", f"cluster:{cluster_id}"],
            )
            evidence_list.append(ev)
        except Exception as e:
            logger.debug(f"Skipping md evidence line {idx}: {e}")
            continue

    # Last resort: if we parsed nothing but raw is substantial, create a single synthetic evidence
    if not evidence_list and len(raw.strip()) > 100:
        try:
            ev = ClaimEvidence(
                claim_text=raw.strip()[:2000],
                source_platform="unknown",
                engagement_count=0,
                url="",
                timestamp=timestamp_now,
                cluster_id=f"{entity_name}:raw:0",
                provenance_chain=[f"last30days:{entity_name}:raw"],
            )
            evidence_list.append(ev)
        except Exception:
            pass

    return evidence_list


class Last30daysAdapter:
    def parse_output(self, raw: str, entity_name: str) -> List[ClaimEvidence]:
        if not raw or not raw.strip():
            logger.info(f"Empty output for entity '{entity_name}' — no evidence")
            return []

        # Try JSON first
        json_result = parse_json_output(raw, entity_name)
        if json_result is not None:
            logger.info(f"Parsed {len(json_result)} evidence items as JSON for '{entity_name}'")
            return json_result

        # Fall back to markdown
        md_result = parse_markdown_output(raw, entity_name)
        logger.info(f"Parsed {len(md_result)} evidence items as markdown for '{entity_name}'")
        return md_result

    def normalize_engagement(self, evidence: List[ClaimEvidence]) -> List[ClaimEvidence]:
        if not evidence:
            return evidence

        max_eng = max((e.engagement_count for e in evidence), default=0)
        if max_eng <= 0:
            return evidence

        import math
        for ev in evidence:
            if ev.engagement_count > 0:
                # Log-scaled normalized engagement
                try:
                    ev.engagement_decayed = math.log1p(ev.engagement_count) / math.log1p(max_eng)
                except ValueError:
                    ev.engagement_decayed = 0.0
            else:
                ev.engagement_decayed = 0.0

        return evidence
