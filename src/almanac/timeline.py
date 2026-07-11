import json
import logging
import os
import subprocess
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import List, Optional, Dict, Any

from src.models import TimelinePoint, ClaimEvidence
from src.wiki.paths import get_pulse_dir, get_entities_dir, get_wiki_dir, get_project_root
from src.wiki.writer import slugify

logger = logging.getLogger("chickensoup.almanac.timeline")


class TimelineBuilderResult:
    def __init__(self, points: List[TimelinePoint], entity_name: str):
        self.points = points
        self.entity_name = entity_name


def _parse_pulse_snapshots(entity_name: str, days: int = 30) -> List[Dict[str, Any]]:
    pulse_dir = get_pulse_dir()
    if not pulse_dir.exists():
        return []

    slug = slugify(entity_name)
    pattern = f"{slug}-*.json"
    files = sorted(pulse_dir.glob(pattern))

    if not files:
        return []

    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    snapshots = []

    for f in files:
        try:
            with open(f, "r", encoding="utf-8") as fh:
                data = json.load(fh)
        except Exception as e:
            logger.debug(f"Failed to load pulse snapshot {f}: {e}")
            continue

        ts_str = data.get("timestamp", "")
        try:
            ts = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
            if ts.tzinfo is None:
                ts = ts.replace(tzinfo=timezone.utc)
            if ts < cutoff:
                continue
        except Exception:
            # Use file mtime fallback
            try:
                mtime = datetime.fromtimestamp(os.path.getmtime(f), tz=timezone.utc)
                if mtime < cutoff:
                    continue
                # Inject mtime as timestamp
                if not ts_str:
                    data["timestamp"] = mtime.isoformat()
            except Exception:
                pass

        data["_file_path"] = str(f)
        snapshots.append(data)

    snapshots.sort(key=lambda d: d.get("timestamp", ""))
    return snapshots


def _parse_git_history(entity_name: str, days: int = 30) -> List[Dict[str, str]]:
    slug = slugify(entity_name)
    wiki_root = get_wiki_dir()
    project_root = get_project_root()

    # Find the file relative to git root
    possible_paths = [
        wiki_root / "entities" / f"{slug}.md",
        wiki_root / "concepts" / f"{slug}.md",
        wiki_root / "projects" / f"{slug}.md",
    ]

    target_file: Optional[Path] = None
    for p in possible_paths:
        if p.exists():
            target_file = p
            break

    if not target_file:
        return []

    # Try git log
    try:
        # Compute path relative to project root for git
        rel_path = os.path.relpath(str(target_file), str(project_root))

        cmd = [
            "git", "log",
            f"--since={days} days ago",
            "--pretty=format:%H|%ad|%s",
            "--date=iso",
            "--follow",
            "--", rel_path
        ]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=10,
            cwd=str(project_root),
            shell=False,
        )

        if result.returncode != 0:
            logger.debug(f"git log failed for {rel_path}: {result.stderr[:200]}")
            return []

        commits = []
        for line in result.stdout.strip().splitlines():
            if not line.strip():
                continue
            parts = line.split("|", 2)
            if len(parts) >= 3:
                sha, date_str, msg = parts[0], parts[1], parts[2]
                commits.append({
                    "sha": sha[:8],
                    "date": date_str,
                    "message": msg,
                    "file": rel_path,
                })

        commits.sort(key=lambda c: c["date"])
        return commits

    except FileNotFoundError:
        logger.debug("git not found — skipping git history for timeline")
        return []
    except subprocess.TimeoutExpired:
        logger.warning("git log timed out for timeline")
        return []
    except Exception as e:
        logger.debug(f"git log error for timeline: {e}")
        return []


def _evidence_to_active_claims(evidence_list: List[Dict[str, Any]]) -> List[str]:
    claims = []
    for ev in evidence_list:
        text = ev.get("claim_text", "") if isinstance(ev, dict) else getattr(ev, "claim_text", "")
        if text:
            claims.append(text[:200])
    return claims


def _compute_confidences_for_snapshot(snapshot: Dict[str, Any]) -> tuple[float, float, float]:
    from src.quantum_credibility.wavefunction import ClaimWavefunction
    from src.quantum_credibility.divergence_engine import compute_narrative_divergence

    evidence_raw = snapshot.get("evidence", [])
    entity_name = snapshot.get("entity_name", "")

    # Parse ClaimEvidence objects
    evidence_objs: List[ClaimEvidence] = []
    for ev_dict in evidence_raw:
        try:
            if isinstance(ev_dict, dict):
                evidence_objs.append(ClaimEvidence(**ev_dict))
            else:
                evidence_objs.append(ev_dict)
        except Exception:
            continue

    if not evidence_objs:
        return 0.5, 0.0, 0.0

    # Wavefunction scoring
    try:
        wf = ClaimWavefunction()
        # Score as single aggregate claim
        aggregate_claim = " ".join(e.get("claim_text", "") if isinstance(e, dict) else getattr(e, "claim_text", "") for e in evidence_raw[:3])[:500]
        cc = wf.score_claim(aggregate_claim or entity_name, evidence_objs)
        epistemic = cc.epistemic_confidence
        traction = cc.social_traction
    except Exception as e:
        logger.debug(f"Wavefunction scoring in timeline failed: {e}")
        epistemic = 0.5
        traction = 0.0

    # Divergence — if wiki page exists
    divergence = 0.0
    try:
        from src.wiki.writer import read_page
        slug = slugify(entity_name)
        wiki_page = None
        for ptype in ("entities", "concepts", "projects"):
            pg = read_page(slug, ptype)
            if pg:
                wiki_page = pg
                break
        if wiki_page and evidence_objs:
            div_result = compute_narrative_divergence(entity_name, wiki_page, evidence_objs)
            divergence = div_result.divergence_risk
    except Exception as e:
        logger.debug(f"Divergence compute in timeline failed: {e}")

    return epistemic, traction, divergence


def build_timeline(entity_name: str, days: int = 30) -> TimelineBuilderResult:
    snapshots = _parse_pulse_snapshots(entity_name, days=days)
    git_commits = _parse_git_history(entity_name, days=days)

    # Build points from pulse snapshots
    points: List[TimelinePoint] = []
    points_by_date: Dict[str, TimelinePoint] = {}

    for snap in snapshots:
        ts_str = snap.get("timestamp", "")
        date_part = ts_str[:10] if len(ts_str) >= 10 else "unknown"
        file_path = snap.get("_file_path", "")

        try:
            epistemic, traction, divergence = _compute_confidences_for_snapshot(snap)
        except Exception:
            epistemic, traction, divergence = 0.5, 0.0, 0.0

        active_claims = _evidence_to_active_claims(snap.get("evidence", []))

        point = TimelinePoint(
            date=date_part,
            epistemic_confidence=epistemic,
            social_traction=traction,
            divergence_risk=divergence,
            active_claims=active_claims[:10],
            pulse_file=file_path,
            wiki_commit=None,
        )

        # Deduplicate by date — keep latest if multiple per day
        existing = points_by_date.get(date_part)
        if existing is None or snap.get("timestamp", "") > points_by_date[date_part].date:
            points_by_date[date_part] = point

    # Merge git commits as additional points where no pulse exists for that date
    commit_map: Dict[str, str] = {}  # date -> sha
    for commit in git_commits:
        date_str = commit["date"]
        date_part = date_str[:10] if len(date_str) >= 10 else "unknown"
        commit_map[date_part] = commit["sha"]
        if date_part not in points_by_date:
            # Create a wiki-only point
            points_by_date[date_part] = TimelinePoint(
                date=date_part,
                epistemic_confidence=0.5,
                social_traction=0.0,
                divergence_risk=0.0,
                active_claims=[],
                pulse_file=None,
                wiki_commit=commit["sha"],
            )

    # Attach commit shas to pulse points where dates match
    for date_part, point in points_by_date.items():
        if date_part in commit_map and point.wiki_commit is None:
            point.wiki_commit = commit_map[date_part]

    # Sort chronologically
    sorted_points = sorted(points_by_date.values(), key=lambda p: p.date)

    return TimelineBuilderResult(points=sorted_points, entity_name=entity_name)
