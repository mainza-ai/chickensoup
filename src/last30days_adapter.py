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


def _extract_claims_from_json(data: Any, entity_name: str) -> List[ClaimEvidence]:
    evidence_list: List[ClaimEvidence] = []

    # Support multiple shapes
    candidates = []
    if isinstance(data, dict):
        if "ranked_candidates" in data and isinstance(data["ranked_candidates"], list):
            candidates = data["ranked_candidates"]
        elif "claims" in data and isinstance(data["claims"], list):
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
            item.get("snippet")
            or item.get("title")
            or item.get("body")
            or item.get("claim_text")
            or item.get("claim")
            or item.get("text")
            or item.get("summary")
            or item.get("explanation")
            or ""
        )
        if not claim_text:
            continue

        claim_text = claim_text.strip()
        # Clean JSON key-value pattern formatting if present
        m = re.match(r'^["\']?(?:title|url|claim_text|claim|text|summary|snippet)["\']?\s*:\s*["\']?(.*?)["\']?$', claim_text)
        if m:
            claim_text = m.group(1).strip()
        if claim_text.startswith('"') and claim_text.endswith('"'):
            claim_text = claim_text[1:-1].strip()
        if claim_text.startswith("'") and claim_text.endswith("'"):
            claim_text = claim_text[1:-1].strip()

        # Data-quality filter: skip claims that are just raw URLs
        if claim_text.startswith("http://") or claim_text.startswith("https://") or len(claim_text) < 10:
            continue

        platform = item.get("source_platform") or item.get("source") or item.get("platform")
        if isinstance(platform, dict):
             platform = platform.get("source") or "unknown"
        if not platform or not isinstance(platform, str):
             platform = _infer_platform(claim_text + " " + str(item.get("url", "")))

        url = item.get("url") or item.get("source") or ""
        if isinstance(url, dict):
             url = url.get("url") or ""
        if not url or not isinstance(url, str):
            urls = _extract_urls(claim_text)
            url = urls[0] if urls else ""

        engagement = item.get("engagement_count") or item.get("engagement") or item.get("upvotes")
        
        # Check inside source_items list if not found or 0
        if not engagement and "source_items" in item and isinstance(item["source_items"], list) and item["source_items"]:
            for s_item in item["source_items"]:
                if isinstance(s_item, dict):
                    s_eng = s_item.get("engagement")
                    if s_eng:
                        engagement = s_eng
                        break

        if not engagement:
            engagement = 0

        if isinstance(engagement, dict):
             engagement = sum(float(v) for v in engagement.values() if isinstance(v, (int, float)))
        try:
            engagement = int(float(engagement))
        except (ValueError, TypeError):
            engagement = 0

        polymarket = item.get("polymarket_odds")
        if polymarket is None:
            polymarket = item.get("market_odds")
        if polymarket is None and "metadata" in item and isinstance(item["metadata"], dict):
            polymarket = item["metadata"].get("polymarket_odds") or item["metadata"].get("market_odds")
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
        except Exception:
            pass

    return evidence_list


def parse_json_output(raw: str, entity_name: str) -> Optional[List[ClaimEvidence]]:
    if not raw or not raw.strip():
        return None
    try:
        data = json.loads(raw)
        return _extract_claims_from_json(data, entity_name)
    except (json.JSONDecodeError, ValueError):
        pass

    # Substring extraction search
    first_brace = raw.find('{')
    first_bracket = raw.find('[')
    
    start_idx = -1
    if first_brace != -1 and first_bracket != -1:
        start_idx = min(first_brace, first_bracket)
    elif first_brace != -1:
        start_idx = first_brace
    elif first_bracket != -1:
        start_idx = first_bracket
        
    if start_idx == -1:
        return None
        
    last_brace = raw.rfind('}')
    last_bracket = raw.rfind(']')
    
    end_idx = -1
    if last_brace != -1 and last_bracket != -1:
        end_idx = max(last_brace, last_bracket)
    elif last_brace != -1:
        end_idx = last_brace
    elif last_bracket != -1:
        end_idx = last_bracket
        
    if end_idx == -1 or end_idx <= start_idx:
        return None
        
    json_str = raw[start_idx:end_idx+1]
    try:
        data = json.loads(json_str)
        return _extract_claims_from_json(data, entity_name)
    except (json.JSONDecodeError, ValueError):
        return None


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
