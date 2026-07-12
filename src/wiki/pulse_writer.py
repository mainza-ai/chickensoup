import json
import logging
from datetime import date, datetime, timezone
from pathlib import Path
from typing import List, Optional, Dict, Any

from src.models import ClaimEvidence
from src.wiki.paths import ensure_pulse_dir, get_pulse_dir
from src.wiki.writer import slugify

logger = logging.getLogger("chickensoup.wiki.pulse_writer")


def _today_str() -> str:
    return date.today().isoformat()


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _has_recent_empty_snapshot(slug: str, max_age_hours: int = 24) -> bool:
    pulse_dir = get_pulse_dir()
    if not pulse_dir.exists():
        return False

    cutoff = datetime.now(timezone.utc).timestamp() - (max_age_hours * 3600)
    pattern = f"{slug}-*.json"
    for snap_path in pulse_dir.glob(pattern):
        try:
            if snap_path.stat().st_mtime < cutoff:
                continue
            data = load_pulse_snapshot(snap_path)
            if data and data.get("evidence_count", -1) == 0:
                return True
        except Exception:
            continue
    return False


def write_pulse_snapshot(
    entity_name: str,
    evidence: List[ClaimEvidence],
    raw_output: str = "",
    extra_meta: Optional[Dict[str, Any]] = None,
) -> Dict[str, str]:
    slug = slugify(entity_name)

    if not evidence:
        if _has_recent_empty_snapshot(slug):
            logger.info(f"Skipping duplicate empty snapshot for '{entity_name}' — empty snapshot written within last 24h")
            return {"json_path": "", "md_path": "", "base_name": ""}

    pulse_dir = ensure_pulse_dir()
    today = _today_str()
    now_iso = _now_iso()

    base_name = f"{slug}-{today}"

    json_path = pulse_dir / f"{base_name}.json"
    md_path = pulse_dir / f"{base_name}.md"

    # Avoid collision — if file exists today, append counter
    counter = 1
    while json_path.exists() or md_path.exists():
        counter += 1
        base_name = f"{slug}-{today}-{counter}"
        json_path = pulse_dir / f"{base_name}.json"
        md_path = pulse_dir / f"{base_name}.md"

    # JSON snapshot — immutable evidence records
    payload = {
        "entity_name": entity_name,
        "slug": slug,
        "date": today,
        "timestamp": now_iso,
        "evidence_count": len(evidence),
        "evidence": [e.model_dump() for e in evidence],
        "raw_output_preview": raw_output[:5000] if raw_output else "",
        "meta": extra_meta or {},
    }

    try:
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, ensure_ascii=False)
        logger.info(f"Pulse JSON snapshot written: {json_path} ({len(evidence)} evidence)")
    except Exception as e:
        logger.error(f"Failed to write pulse JSON {json_path}: {e}")
        raise

    # Markdown snapshot — human-readable
    md_lines = [
        f"# Pulse: {entity_name}\n\n",
        f"**Date:** {today}\n",
        f"**Timestamp:** {now_iso}\n",
        f"**Evidence count:** {len(evidence)}\n",
        f"**Slug:** `{slug}`\n\n",
        f"---\n\n",
        f"## Evidence\n\n",
    ]

    platforms = {}
    for ev in evidence:
        platforms[ev.source_platform] = platforms.get(ev.source_platform, 0) + 1

    if platforms:
        md_lines.append("### By platform\n\n")
        for plat, count in sorted(platforms.items(), key=lambda x: -x[1]):
            md_lines.append(f"- **{plat}**: {count}\n")
        md_lines.append("\n")

    for idx, ev in enumerate(evidence, 1):
        md_lines.append(f"### {idx}. {ev.claim_text[:120]}\n\n")
        md_lines.append(f"- **Platform:** {ev.source_platform}\n")
        md_lines.append(f"- **Engagement:** {ev.engagement_count}\n")
        if ev.engagement_decayed is not None:
            md_lines.append(f"- **Engagement decayed:** {ev.engagement_decayed:.3f}\n")
        if ev.polymarket_odds is not None:
            md_lines.append(f"- **Polymarket odds:** {ev.polymarket_odds:.2%}\n")
        if ev.url:
            md_lines.append(f"- **URL:** {ev.url}\n")
        md_lines.append(f"- **Cluster:** `{ev.cluster_id}`\n")
        md_lines.append(f"- **Timestamp:** {ev.timestamp}\n\n")
        md_lines.append(f"> {ev.claim_text}\n\n")

    if extra_meta:
        md_lines.append("---\n\n## Meta\n\n```json\n")
        md_lines.append(json.dumps(extra_meta, indent=2))
        md_lines.append("\n```\n")

    try:
        with open(md_path, "w", encoding="utf-8") as f:
            f.write("".join(md_lines))
        logger.info(f"Pulse MD snapshot written: {md_path}")
    except Exception as e:
        logger.error(f"Failed to write pulse MD {md_path}: {e}")
        # JSON already written — don't fail entirely, but log

    return {
        "json_path": str(json_path),
        "md_path": str(md_path),
        "base_name": base_name,
    }


def list_pulse_snapshots(entity_name: Optional[str] = None) -> List[Path]:
    pulse_dir = get_pulse_dir()
    if not pulse_dir.exists():
        return []

    if entity_name:
        slug = slugify(entity_name)
        pattern = f"{slug}-*.json"
        return sorted(pulse_dir.glob(pattern))

    return sorted(pulse_dir.glob("*.json"))


def load_pulse_snapshot(json_path: Path) -> Optional[Dict[str, Any]]:
    if not json_path.exists():
        return None
    try:
        with open(json_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.warning(f"Failed to load pulse snapshot {json_path}: {e}")
        return None


def load_recent_pulse_evidence(entity_name: str, max_age_days: int = 7) -> List[ClaimEvidence]:
    import os
    from datetime import timedelta

    snapshots = list_pulse_snapshots(entity_name)
    if not snapshots:
        return []

    cutoff = datetime.now(timezone.utc) - timedelta(days=max_age_days)
    recent_evidence: List[ClaimEvidence] = []

    for snap_path in sorted(snapshots, reverse=True):
        data = load_pulse_snapshot(snap_path)
        if not data:
            continue
        ts_str = data.get("timestamp", "")
        try:
            ts = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
            if ts.tzinfo is None:
                ts = ts.replace(tzinfo=timezone.utc)
            if ts < cutoff:
                continue
        except Exception:
            # If timestamp unparsable, include if file is recent by mtime
            try:
                mtime = datetime.fromtimestamp(os.path.getmtime(snap_path), tz=timezone.utc)
                if mtime < cutoff:
                    continue
            except Exception:
                pass

        for ev_dict in data.get("evidence", []):
            try:
                recent_evidence.append(ClaimEvidence(**ev_dict))
            except Exception as e:
                logger.debug(f"Skipping invalid evidence in {snap_path}: {e}")
                continue

    return recent_evidence
