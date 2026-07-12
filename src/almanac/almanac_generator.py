import hashlib
import html
import json
import logging
import os
from datetime import date, datetime, timezone
from pathlib import Path
from typing import List, Dict, Any, Optional

from src.config import settings
from src.models import ClaimEvidence, ClaimConfidence
from src.wiki.paths import ensure_almanac_dir, get_almanac_dir, get_pulse_dir
from src.wiki.writer import slugify

logger = logging.getLogger("chickensoup.almanac.generator")


class AlmanacResult:
    def __init__(
        self,
        status: str,
        date_str: str,
        html_path: Optional[str] = None,
        md_path: Optional[str] = None,
        entities_processed: int = 0,
        claims_moved: int = 0,
        claims_collapsed: int = 0,
        newly_contested: int = 0,
        entanglements: List[Dict[str, Any]] = None,
        elapsed_seconds: float = 0.0,
        error: Optional[str] = None,
        dry_run: bool = False,
        html_content: Optional[str] = None,
    ):
        self.status = status
        self.date_str = date_str
        self.html_path = html_path
        self.md_path = md_path
        self.entities_processed = entities_processed
        self.claims_moved = claims_moved
        self.claims_collapsed = claims_collapsed
        self.newly_contested = newly_contested
        self.entanglements = entanglements or []
        self.elapsed_seconds = elapsed_seconds
        self.error = error
        self.dry_run = dry_run
        self.html_content = html_content


def _today_str() -> str:
    return date.today().isoformat()


def _load_tier_entities() -> List[str]:
    # Load Tier-1 entities from wiki — pages with tier: 1 in frontmatter
    from src.wiki.writer import read_page
    from src.wiki.paths import get_entities_dir, get_concepts_dir
    import yaml as yaml_lib

    tier1 = []
    tier1_explicit = []

    # Check all wiki dirs
    for page_type in ("entities", "concepts", "projects"):
        wiki_dir = Path(__file__).resolve().parents[2] / "wiki" / page_type
        if not wiki_dir.exists():
            continue
        for fname in wiki_dir.glob("*.md"):
            try:
                with open(fname, "r", encoding="utf-8") as f:
                    content = f.read()
                import re
                yaml_match = re.match(r"^---\s*\n(.*?)\n---\s*\n", content, re.DOTALL)
                if yaml_match:
                    fm = yaml_lib.safe_load(yaml_match.group(1)) or {}
                    tier = fm.get("tier")
                    handles = fm.get("last30days_handles")
                    if tier == 1 or handles:
                        tier1_explicit.append({
                            "slug": fname.stem,
                            "title": fm.get("title", fname.stem),
                            "tier": tier,
                            "handles": handles,
                        })
            except Exception:
                continue

    if tier1_explicit:
        # Sort by tier
        tier1_explicit.sort(key=lambda x: (x.get("tier", 999), x["slug"]))
        return tier1_explicit

    # Fallback: use a small hardcoded set of high-interest entities if no tier field found
    return [
        {"slug": "bob-lazar", "title": "Bob Lazar", "tier": 1, "handles": None},
        {"slug": "element-115", "title": "Element 115", "tier": 1, "handles": None},
        {"slug": "roswell-crash", "title": "Roswell Crash", "tier": 1, "handles": None},
    ]


def _compute_almanac_hash(claim_confs: List[ClaimConfidence]) -> str:
    if not claim_confs:
        return "empty-no-evidence"
    payload = sorted([
        (c.claim_text or "", c.epistemic_confidence, c.state_label, c.collapsed)
        for c in claim_confs
    ])
    h = hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()
    return h[:16]


def _load_last_almanac_hash() -> Optional[str]:
    almanac_dir = get_almanac_dir()
    if not almanac_dir.exists():
        return None

    # Find most recent md file
    md_files = sorted(almanac_dir.glob("*.md"), reverse=True)
    for mf in md_files[:5]:
        try:
            with open(mf, "r", encoding="utf-8") as f:
                content = f.read()
            # Look for hash in meta comment
            import re
            m = re.search(r"<!-- hash: ([a-z0-9\-]+) -->", content)
            if m:
                return m.group(1)
        except Exception:
            continue
    return None


def _render_html(tier_results: List[Dict[str, Any]], meta: Dict[str, Any]) -> str:
    date_str = meta.get("date", _today_str())
    total = meta.get("entities_processed", 0)
    moved = meta.get("claims_moved", 0)
    collapsed = meta.get("claims_collapsed", 0)
    contested = meta.get("newly_contested", 0)

    entanglements = meta.get("entanglements", [])

    html_parts = []
    html_parts.append(f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>State of the Anomaly — {date_str}</title>
<style>
  :root {{
    --bg: #FAFAF8;
    --fg: #1A1A1A;
    --muted: #6B6B6B;
    --border: #E5E5E0;
    --accent: #FF9500;
    --card-bg: #FFFFFF;
    --corroborated: #2D7D46;
    --contested: #C45D00;
    --unverified: #6B6B6B;
  }}
  @media (prefers-color-scheme: dark) {{
    :root {{
      --bg: #121212;
      --fg: #E8E8E8;
      --muted: #9A9A9A;
      --border: #2A2A2A;
      --card-bg: #1E1E1E;
      --accent: #FF9500;
    }}
  }}
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{
    font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Text', system-ui, sans-serif;
    background: var(--bg);
    color: var(--fg);
    line-height: 1.6;
    max-width: 800px;
    margin: 0 auto;
    padding: 2rem 1.5rem;
  }}
  h1 {{ font-size: 2rem; font-weight: 700; margin-bottom: 0.25rem; letter-spacing: -0.02em; }}
  h2 {{ font-size: 1.3rem; font-weight: 600; margin: 2rem 0 1rem; padding-bottom: 0.5rem; border-bottom: 2px solid var(--border); }}
  h3 {{ font-size: 1.05rem; font-weight: 600; margin: 1.5rem 0 0.5rem; }}
  .subtitle {{ color: var(--muted); font-size: 0.95rem; margin-bottom: 2rem; }}
  .stats {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); gap: 1rem; margin: 1.5rem 0; }}
  .stat-card {{ background: var(--card-bg); border: 1px solid var(--border); border-radius: 12px; padding: 1rem; text-align: center; }}
  .stat-value {{ font-size: 1.8rem; font-weight: 700; }}
  .stat-label {{ font-size: 0.8rem; color: var(--muted); text-transform: uppercase; letter-spacing: 0.05em; margin-top: 0.25rem; }}
  .entity-card {{ background: var(--card-bg); border: 1px solid var(--border); border-radius: 12px; padding: 1.25rem; margin: 1rem 0; }}
  .badge {{ display: inline-block; padding: 0.2em 0.6em; border-radius: 999px; font-size: 0.75rem; font-weight: 600; letter-spacing: 0.02em; }}
  .badge-collapsed {{ background: var(--corroborated); color: white; }}
  .badge-contested {{ background: var(--contested); color: white; }}
  .badge-unverified {{ background: var(--border); color: var(--muted); }}
  .badge-superposition {{ background: #8B5CF6; color: white; }}
  .evidence-item {{ padding: 0.5rem 0; border-bottom: 1px solid var(--border); font-size: 0.9rem; }}
  .evidence-item:last-child {{ border-bottom: none; }}
  .meta {{ font-size: 0.8rem; color: var(--muted); }}
  a {{ color: var(--accent); text-decoration: none; }}
  a:hover {{ text-decoration: underline; }}
  .tribunal {{ background: var(--card-bg); border-left: 3px solid var(--accent); padding: 1rem; margin: 1rem 0; border-radius: 0 8px 8px 0; }}
  .disagreement {{ margin: 0.75rem 0; padding: 0.5rem; background: var(--bg); border-radius: 8px; }}
  footer {{ margin-top: 3rem; padding-top: 1rem; border-top: 1px solid var(--border); font-size: 0.8rem; color: var(--muted); text-align: center; }}
  @media print {{
    body {{ background: white; color: black; max-width: 100%; padding: 1rem; }}
    .stat-card, .entity-card {{ border: 1px solid #CCC; break-inside: avoid; }}
    a {{ color: black; text-decoration: underline; }}
  }}
</style>
</head>
<body>
<header>
<h1>🌀 State of the Anomaly</h1>
<p class="subtitle">Daily briefing — {date_str} — {total} entities, {moved} moved, {collapsed} collapsed, {contested} newly contested</p>
</header>

<div class="stats">
  <div class="stat-card"><div class="stat-value">{total}</div><div class="stat-label">Entities</div></div>
  <div class="stat-card"><div class="stat-value">{moved}</div><div class="stat-label">Moved</div></div>
  <div class="stat-card"><div class="stat-value">{collapsed}</div><div class="stat-label">Collapsed</div></div>
  <div class="stat-card"><div class="stat-value">{contested}</div><div class="stat-label">Contested</div></div>
</div>
""")

    if not tier_results:
        html_parts.append("<p>No material changes since last briefing.</p>\n")
    else:
        for er in tier_results:
            entity_name = er.get("entity_name", "Unknown")
            confidences = er.get("confidences", [])
            divergence = er.get("divergence")
            pulse_status = er.get("pulse_status", "unknown")
            evidence_count = er.get("evidence_count", 0)

            html_parts.append(f'<div class="entity-card">\n')
            html_parts.append(f'<h3>{html.escape(entity_name)} <span class="meta">({html.escape(pulse_status)}, {evidence_count} evidence)</span></h3>\n')

            if confidences:
                for cc in confidences:
                    state = cc.get("state_label", "unverified")
                    epi = cc.get("epistemic_confidence", 0.5)
                    trac = cc.get("social_traction", 0.0)
                    coll = cc.get("collapsed", False)
                    claim_t = cc.get("claim_text", "")[:200]

                    badge_class = "badge-unverified"
                    if state == "corroborated":
                        badge_class = "badge-collapsed" if coll else "badge-superposition"
                    elif state == "contested":
                        badge_class = "badge-contested"

                    badge_text = f"{state}" + (" ✓ collapsed" if coll else " ◐ superposition")

                    html_parts.append(f'<div class="evidence-item">\n')
                    html_parts.append(f'  <span class="badge {badge_class}">{html.escape(badge_text)}</span>\n')
                    html_parts.append(f'  <span class="meta"> epi={epi:.2f} trac={trac:.2f}</span><br>\n')
                    if claim_t:
                        html_parts.append(f'  <em>{html.escape(claim_t)}</em>\n')
                    html_parts.append(f'</div>\n')

            if divergence:
                div_risk = divergence.get("divergence_risk", 0.0)
                html_parts.append(f'<p class="meta">Divergence risk: {div_risk:.1%} — ')
                driving = divergence.get("driving_claims", [])
                if driving:
                    html_parts.append(f'driven by {len(driving)} claim(s): ')
                    html_parts.append(", ".join(f"<em>{html.escape(dc.get('claim_text','')[:80])}</em>" for dc in driving[:3]))
                html_parts.append('</p>\n')

            tribunal = er.get("tribunal")
            if tribunal and tribunal.get("triggered"):
                html_parts.append(f'<div class="tribunal">\n')
                html_parts.append(f'<strong>⚖️ Tribunal — {html.escape(tribunal.get("final_state_label", "contested"))}</strong><br>\n')
                html_parts.append(f'<p>{html.escape(tribunal.get("referee_synthesis", "")[:1000])}</p>\n')
                for dis in tribunal.get("disagreements", [])[:3]:
                    html_parts.append(f'<div class="disagreement">\n')
                    html_parts.append(f'<strong>{html.escape(dis.get("topic","Disagreement"))}</strong><br>\n')
                    html_parts.append(f'<span class="meta">Skeptic: {html.escape(dis.get("skeptic","")[:200])}<br>\n')
                    html_parts.append(f'Empiricist: {html.escape(dis.get("empiricist","")[:200])}<br>\n')
                    html_parts.append(f'Believer: {html.escape(dis.get("believer","")[:200])}</span>\n')
                    html_parts.append(f'</div>\n')
                html_parts.append(f'</div>\n')

            html_parts.append('</div>\n')

    if entanglements:
        html_parts.append('<h2>🔗 Entanglement Discoveries</h2>\n')
        for ent in entanglements[:10]:
            html_parts.append(f'<div class="entity-card">\n')
            html_parts.append(f'  <strong>{html.escape(str(ent.get("entity_a")))} ↔ {html.escape(str(ent.get("entity_b")))}</strong> — '
                              f'score {ent.get("entanglement_score",0):.2f} '
                              f'({ent.get("independent_clusters",0)} clusters, '
                              f'{len(ent.get("independent_platforms",[]))} platforms)<br>\n')
            html_parts.append(f'  <span class="meta">{ent.get("co_occurrence_count",0)} co-mentions</span>\n')
            html_parts.append(f'</div>\n')

    html_parts.append(f"""
<footer>
  <p>Generated by Project Chicken Soup — The Living Almanac Engine — {date_str}</p>
  <p class="meta">Epistemic confidence and social traction are separate numbers, never merged into one. Market odds shown as probability priors when available.</p>
  <p class="meta">Source tier: network_opt_in (last30days) + local (wiki canon)</p>
</footer>
</body>
</html>
""")

    return "".join(html_parts)


def _render_markdown(tier_results: List[Dict[str, Any]], meta: Dict[str, Any]) -> str:
    date_str = meta.get("date", _today_str())
    hash_val = meta.get("hash", "unknown")

    lines = [f"<!-- hash: {hash_val} -->\n\n"]
    lines.append(f"# State of the Anomaly — {date_str}\n\n")
    lines.append(f"**Entities:** {meta.get('entities_processed',0)} | "
                 f"**Moved:** {meta.get('claims_moved',0)} | "
                 f"**Collapsed:** {meta.get('claims_collapsed',0)} | "
                 f"**Contested:** {meta.get('newly_contested',0)}\n\n")

    lines.append(f"Generated: {datetime.now(timezone.utc).isoformat()}\n\n")
    lines.append("---\n\n")

    for er in tier_results:
        lines.append(f"## {er.get('entity_name','Unknown')}\n\n")
        lines.append(f"Pulse: {er.get('pulse_status','unknown')} | Evidence: {er.get('evidence_count',0)}\n\n")

        for cc in er.get("confidences", []):
            state = cc.get("state_label","unverified")
            epi = cc.get("epistemic_confidence",0.5)
            trac = cc.get("social_traction",0.0)
            coll = "collapsed" if cc.get("collapsed") else "superposition"
            claim_t = cc.get("claim_text","")[:300]
            lines.append(f"- **{state}** ({coll}) epi={epi:.2f} trac={trac:.2f}: {claim_t}\n")

        div = er.get("divergence")
        if div:
            lines.append(f"\nDivergence: {div.get('divergence_risk',0):.1%}\n")
            for dc in div.get("driving_claims", [])[:3]:
                lines.append(f"  - Driving: {dc.get('claim_text','')[:150]} ({dc.get('platform','')})\n")

        tribunal = er.get("tribunal")
        if tribunal and tribunal.get("triggered"):
            lines.append(f"\n### Tribunal — {tribunal.get('final_state_label','contested')}\n\n")
            lines.append(f"{tribunal.get('referee_synthesis','')[:2000]}\n\n")

        lines.append("\n")

    if meta.get("entanglements"):
        lines.append("## Entanglement Discoveries\n\n")
        for ent in meta["entanglements"][:10]:
            lines.append(f"- **{ent.get('entity_a')} ↔ {ent.get('entity_b')}** — "
                         f"{ent.get('entanglement_score',0):.2f} "
                         f"({ent.get('independent_clusters',0)} clusters)\n")

    lines.append(f"\n---\n\n*Generated by Project Chicken Soup — {date_str}*\n")

    return "".join(lines)


async def generate_daily_almanac(dry_run: bool = False) -> AlmanacResult:
    import time
    t0 = time.perf_counter()

    today = _today_str()
    logger.info(f"Generating daily almanac for {today} (dry_run={dry_run})")

    tier_entities = _load_tier_entities()
    if not tier_entities:
        logger.info("No Tier-1 entities found for almanac generation")
        return AlmanacResult(
            status="no_material_change",
            date_str=today,
            entities_processed=0,
            dry_run=dry_run,
            elapsed_seconds=time.perf_counter() - t0,
        )

    tier_results: List[Dict[str, Any]] = []
    all_confidences: List[ClaimConfidence] = []
    all_evidence: List[ClaimEvidence] = []
    claims_moved = 0
    claims_collapsed = 0
    newly_contested = 0

    # Phase: pulse → wavefunction → divergence for each Tier-1 entity
    for ent in tier_entities:
        entity_name = ent.get("title") or ent.get("slug", "").replace("-", " ").title()
        handles = ent.get("handles")

        result_entry: Dict[str, Any] = {
            "entity_name": entity_name,
            "slug": ent.get("slug"),
            "pulse_status": "unknown",
            "evidence_count": 0,
            "confidences": [],
            "divergence": None,
            "tribunal": None,
        }

        # 1. Pulse
        try:
            from src.agents.pulse_agent import PulseAgent
            pulse_agent = PulseAgent()
            pulse_result = pulse_agent.run_pulse(entity_name, handles=handles)
            result_entry["pulse_status"] = pulse_result.status
            result_entry["evidence_count"] = len(pulse_result.evidence)
            all_evidence.extend(pulse_result.evidence)
        except Exception as pulse_err:
            logger.warning(f"Pulse failed for '{entity_name}': {pulse_err}")
            result_entry["pulse_status"] = f"error: {pulse_err}"
            result_entry["evidence"] = []
            tier_results.append(result_entry)
            continue

        evidence_list = pulse_result.evidence if pulse_result.status in ("success", "no_data") else []

        if not evidence_list:
            # Try to load recent pulse evidence from disk as fallback
            try:
                from src.wiki.pulse_writer import load_recent_pulse_evidence
                evidence_list = load_recent_pulse_evidence(entity_name, max_age_days=14)
                result_entry["evidence_count"] = len(evidence_list)
            except Exception:
                pass

        if not evidence_list:
            tier_results.append(result_entry)
            continue

        # 2. Wavefunction scoring
        try:
            from src.quantum_credibility.wavefunction import ClaimWavefunction
            wf = ClaimWavefunction()

            # Group evidence by claim_text for per-claim scoring
            claim_groups: Dict[str, List[ClaimEvidence]] = {}
            for ev in evidence_list:
                key = ev.claim_text[:300]
                claim_groups.setdefault(key, []).append(ev)

            confs = []
            for claim_t, evs in list(claim_groups.items())[:10]:
                cc_obj = wf.score_claim(claim_t, evs)
                confs.append(cc_obj)
                all_confidences.append(cc_obj)

                if cc_obj.state_label == "contested":
                    newly_contested += 1
                if cc_obj.collapsed:
                    claims_collapsed += 1
                # Moved = divergence or state change — counted via divergence below

            # Convert to dicts for template
            result_entry["confidences"] = [c.model_dump() for c in confs]

        except Exception as wf_err:
            logger.warning(f"Wavefunction scoring failed for '{entity_name}': {wf_err}")

        # 3. Divergence check
        try:
            from src.wiki.writer import read_page
            from src.quantum_credibility.divergence_engine import compute_narrative_divergence

            slug = slugify(entity_name)
            wiki_page = None
            for ptype in ("entities", "concepts", "projects"):
                pg = read_page(slug, ptype)
                if pg:
                    wiki_page = pg
                    break

            if wiki_page and evidence_list:
                div_res = compute_narrative_divergence(entity_name, wiki_page, evidence_list)
                result_entry["divergence"] = div_res.model_dump()
                if div_res.divergence_risk > settings.DIVERGENCE_SPIKE_THRESHOLD:
                    claims_moved += 1
        except Exception as div_err:
            logger.debug(f"Divergence check failed for '{entity_name}': {div_err}")

        # 4. Tribunal for contested or high divergence
        try:
            should_tribunal = False
            div_risk = result_entry.get("divergence", {}).get("divergence_risk", 0.0) if result_entry.get("divergence") else 0.0

            for conf_dict in result_entry.get("confidences", []):
                if conf_dict.get("state_label") == "contested":
                    should_tribunal = True
                    break
            if div_risk >= settings.DIVERGENCE_SPIKE_THRESHOLD:
                should_tribunal = True

            if should_tribunal:
                from src.agents.tribunal_agent import TribunalAgent

                tribunal_agent = TribunalAgent()

                # Pick most contested or highest divergence claim for tribunal
                target_claim = ""
                target_wf = {}
                max_contested = None
                for cd in result_entry.get("confidences", []):
                    if cd.get("state_label") == "contested":
                        if max_contested is None or cd.get("epistemic_confidence", 0) < max_contested.get("epistemic_confidence", 1):
                            max_contested = cd

                if max_contested:
                    target_claim = max_contested.get("claim_text", entity_name)
                    target_wf = max_contested
                elif result_entry.get("confidences"):
                    # Highest divergence proxy
                    target_claim = result_entry["confidences"][0].get("claim_text", entity_name)
                    target_wf = result_entry["confidences"][0]
                else:
                    target_claim = entity_name
                    target_wf = {"state_label": "contested", "epistemic_confidence": 0.5}

                trib_result = tribunal_agent.run_tribunal(
                    claim_text=target_claim,
                    evidence=evidence_list[:20],
                    wavefunction=target_wf,
                    divergence_risk=div_risk,
                )
                result_entry["tribunal"] = trib_result

        except Exception as trib_err:
            logger.warning(f"Tribunal failed for '{entity_name}': {trib_err}")

        tier_results.append(result_entry)

    # Entanglement discoveries across all evidence
    entanglements = []
    if all_evidence:
        try:
            from src.quantum_credibility.entanglement_corr import compute_all_entanglements
            # Use first tier entity as anchor, or try pairs
            if tier_results:
                anchor = tier_results[0].get("entity_name", "")
                if anchor:
                    entanglements = compute_all_entanglements(anchor, all_evidence)[:5]
        except Exception as ent_err:
            logger.debug(f"Entanglement computation failed: {ent_err}")

    # Compute hash for idempotency check
    current_hash = _compute_almanac_hash(all_confidences)

    last_hash = _load_last_almanac_hash()

    if last_hash and current_hash == last_hash and not dry_run:
        # No material change
        elapsed = time.perf_counter() - t0
        logger.info(f"Almanac no material change — hash {current_hash} unchanged since last run")

        try:
            from src.wiki.writer import append_to_log
            append_to_log(f"almanac | {today} | no material change | hash={current_hash} | {len(tier_results)} entities checked")
        except Exception:
            pass

        return AlmanacResult(
            status="no_material_change",
            date_str=today,
            entities_processed=len(tier_results),
            claims_moved=0,
            claims_collapsed=0,
            newly_contested=0,
            entanglements=[],
            elapsed_seconds=elapsed,
            dry_run=dry_run,
        )

    # Render
    meta = {
        "date": today,
        "entities_processed": len(tier_results),
        "claims_moved": claims_moved,
        "claims_collapsed": claims_collapsed,
        "newly_contested": newly_contested,
        "entanglements": entanglements,
        "hash": current_hash,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }

    html_content = _render_html(tier_results, meta)
    md_content = _render_markdown(tier_results, meta)

    if dry_run:
        elapsed = time.perf_counter() - t0
        logger.info(f"Almanac dry-run complete for {today}: {len(tier_results)} entities, hash={current_hash}")
        return AlmanacResult(
            status="success",
            date_str=today,
            entities_processed=len(tier_results),
            claims_moved=claims_moved,
            claims_collapsed=claims_collapsed,
            newly_contested=newly_contested,
            entanglements=entanglements,
            elapsed_seconds=elapsed,
            dry_run=True,
            html_content=html_content,
        )

    # Write to wiki/raw/almanac/
    try:
        almanac_dir = ensure_almanac_dir()
        html_path = almanac_dir / f"{today}.html"
        md_path = almanac_dir / f"{today}.md"

        with open(html_path, "w", encoding="utf-8") as f:
            f.write(html_content)

        with open(md_path, "w", encoding="utf-8") as f:
            f.write(md_content)

        logger.info(f"Almanac written: {html_path} + {md_path}")

        # Append to log.md
        try:
            from src.wiki.writer import append_to_log
            append_to_log(
                f"almanac | {today} | {len(tier_results)} entities | "
                f"moved={claims_moved} collapsed={claims_collapsed} contested={newly_contested} | "
                f"hash={current_hash} | {html_path.name}"
            )
        except Exception as log_err:
            logger.warning(f"Failed to append almanac to log: {log_err}")

        elapsed = time.perf_counter() - t0

        return AlmanacResult(
            status="success",
            date_str=today,
            html_path=str(html_path),
            md_path=str(md_path),
            entities_processed=len(tier_results),
            claims_moved=claims_moved,
            claims_collapsed=claims_collapsed,
            newly_contested=newly_contested,
            entanglements=entanglements,
            elapsed_seconds=elapsed,
            dry_run=False,
            html_content=html_content,
        )

    except Exception as e:
        logger.error(f"Almanac write failed: {e}", exc_info=True)
        elapsed = time.perf_counter() - t0
        return AlmanacResult(
            status="error",
            date_str=today,
            entities_processed=len(tier_results),
            elapsed_seconds=elapsed,
            error=str(e),
            dry_run=dry_run,
        )
