import json
import logging
import os
import re
import shlex
import shutil
import subprocess
import time
from datetime import datetime, timezone
from typing import Optional, Dict, List

from src.config import settings
from src.models import ClaimEvidence, PulseResult
from src.resource_ledger import ResourceLedger
from src.last30days_adapter import Last30daysAdapter
from src.wiki.pulse_writer import write_pulse_snapshot
from src.wiki.writer import slugify
from src.observability import pulse_runs_total, pulse_latency_seconds, budget_spent_usd

logger = logging.getLogger("chickensoup.agents.pulse_agent")


def _sanitize_entity_name(name: str) -> str:
    if not name or not name.strip():
        raise ValueError("Entity name must be non-empty")
    # Disallow control chars and shell metacharacters if someone mistakenly passes raw shell
    cleaned = name.strip()
    # Reject if contains null bytes or newlines
    if "\x00" in cleaned or "\n" in cleaned or "\r" in cleaned:
        raise ValueError("Entity name contains invalid characters")
    # Length cap
    if len(cleaned) > 200:
        cleaned = cleaned[:200]
    return cleaned


class PulseAgent:
    def __init__(self):
        self.adapter = Last30daysAdapter()

    def _resolve_binary(self) -> Optional[List[str]]:
        # Explicit binary path takes precedence
        if settings.LAST30DAYS_BINARY_PATH:
            path = settings.LAST30DAYS_BINARY_PATH.strip()
            if os.path.isfile(path) and os.access(path, os.X_OK):
                return [path]
            if os.path.isfile(path):
                return [path]
            logger.warning(f"LAST30DAYS_BINARY_PATH set but not found/executable: {path}")

        # Check for cloned workspace repository last30days.py
        import sys
        workspace_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        cloned_script = os.path.join(workspace_root, "last30days-skill", "skills", "last30days", "scripts", "last30days.py")
        if os.path.exists(cloned_script):
            return [sys.executable, cloned_script]

        # Try npx last30days
        npx_path = shutil.which("npx")
        if npx_path:
            return [npx_path, "last30days"]

        # Try last30days direct
        direct = shutil.which("last30days")
        if direct:
            return [direct]

        return None

    def _build_command(self, binary_parts: List[str], entity_name: str, handles: Optional[Dict] = None) -> List[str]:
        # Never use shell=True — list args only
        cmd = list(binary_parts)

        # If binary is npx last30days, we add -- separator handling
        # We pass entity as topic arg; if handles provided, we pass as flags if supported
        # The last30days skill spec says it accepts topic as positional or --topic
        # We use --json for structured output if available

        cmd.append(entity_name)

        # If handles provided, append as search modifiers if the CLI supports them
        # We include them as additional query context rather than inventing flags
        if handles:
            # e.g., x handle: pass as additional search terms
            for key, val in handles.items():
                if val and isinstance(val, str):
                    cmd.append(val)

        # Prefer JSON output with quick mode
        is_python_script = any("last30days.py" in p for p in binary_parts)
        if is_python_script:
            cmd.extend(["--emit", "json", "--quick"])
        else:
            if "--json" not in cmd:
                cmd.append("--json")

        return cmd

    def run_pulse(self, entity_name: str, handles: dict | None = None) -> PulseResult:
        t_start = time.perf_counter()
        entity_name = _sanitize_entity_name(entity_name)
        slug = slugify(entity_name)

        # Check wiki page frontmatter for handles or tags
        from src.wiki.writer import read_page
        is_org = False
        wiki_handles = None
        try:
            page_data = read_page(slug)
            if page_data and "frontmatter" in page_data:
                fm = page_data["frontmatter"]
                # 1. Extract handles
                wiki_handles = fm.get("last30days_handles")
                # 2. Check if organization
                tags = [str(t).lower() for t in fm.get("tags", [])]
                if any(org_tag in tags for org_tag in ("organization", "company", "business", "corp")):
                    is_org = True
        except Exception as e:
            logger.debug(f"Failed to read wiki page frontmatter for handles/tags: {e}")

        if not handles and wiki_handles:
            handles = wiki_handles

        # Determine if paid or free based on presence of API keys
        is_paid = bool(os.environ.get("PERPLEXITY_API_KEY") or os.environ.get("BRAVE_API_KEY") or os.environ.get("XAI_API_KEY"))
        cost = settings.LAST30DAYS_COST_PER_PULL_USD if is_paid else 0.0
        
        # Disabled gate — clean no-op
        if not settings.LAST30DAYS_ENABLED:
            logger.info(f"Pulse disabled (LAST30DAYS_ENABLED=false) for '{entity_name}' — returning no-op")
            return PulseResult(
                entity_name=entity_name,
                status="disabled",
                evidence=[],
                raw_snapshot_path=None,
                budget_remaining=ResourceLedger.get_status().paid_remaining,
            )

        # Budget check before any network call
        allowed, remaining, reason = ResourceLedger.check_budget(is_paid=is_paid)
        if not allowed and is_paid:
            logger.info("Paid budget limit reached/blocked, attempting free fallback...")
            is_paid = False
            allowed, remaining, reason = ResourceLedger.check_budget(is_paid=False)

        if not allowed:
            logger.warning(f"Pulse refused for '{entity_name}': budget/rate limit exceeded — {reason}")
            try:
                from src.wiki.writer import append_to_log
                safe_name = entity_name.replace("\n", " ").replace("\r", " ")[:100]
                append_to_log(f"pulse | {safe_name} | budget_exceeded | {reason}")
            except Exception as log_err:
                logger.debug(f"Failed to append budget refusal to log: {log_err}")

            return PulseResult(
                entity_name=entity_name,
                status="budget_exceeded",
                evidence=[],
                raw_snapshot_path=None,
                budget_remaining=ResourceLedger.get_status().paid_remaining,
                error=reason,
            )

        # Resolve binary
        binary_parts = self._resolve_binary()
        if not binary_parts:
            msg = "last30days binary not found — install via npm (npx last30days) or set LAST30DAYS_BINARY_PATH"
            logger.error(msg)
            return PulseResult(
                entity_name=entity_name,
                status="error",
                evidence=[],
                raw_snapshot_path=None,
                budget_remaining=remaining,
                error=msg,
            )

        cmd = self._build_command(binary_parts, entity_name, handles)
        logger.info(f"Running last30days pulse for '{entity_name}': {' '.join(shlex.quote(c) for c in cmd[:5])} ...")

        raw_output = ""
        timeout = settings.LAST30DAYS_PULSE_TIMEOUT_SECONDS
        try:
            proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                env={**os.environ, "TERM": "dumb"},
            )
            # Wait for process to finish (with timeout). Using proc.wait() avoids the
            # pipe-buffer deadlock that can occur with repeated proc.communicate() calls.
            # proc.communicate() can only be called once per process — calling it in a
            # loop with timeout=1 would corrupt internal state on the second call.
            proc.wait(timeout=timeout)
            stdout, stderr = proc.communicate()
            raw_output = stdout or ""

            # Check for preemption after the subprocess finishes (during the 300s window,
            # the system might have become non-idle; we accept this minor gap rather than
            # risking the pipe-buffer deadlock that the 1s-polling pattern introduced).
            from src.idle_sentinel import IdleSentinel
            if not IdleSentinel.is_idle():
                logger.info(f"Pulse preempted (post-hoc) for '{entity_name}'")
                return PulseResult(
                    entity_name=entity_name,
                    status="preempted",
                    evidence=[],
                    raw_snapshot_path=None,
                    budget_remaining=remaining,
                    error="Preempted by user activity",
                )

            if proc.returncode != 0:
                logger.warning(f"last30days CLI exited {proc.returncode} for '{entity_name}': stderr={stderr[:500] if stderr else ''}")
                if not raw_output.strip():
                    return PulseResult(
                        entity_name=entity_name,
                        status="error",
                        evidence=[],
                        raw_snapshot_path=None,
                        budget_remaining=remaining,
                        error=f"CLI exit {proc.returncode}: {stderr[:500] if stderr else ''}",
                    )

        except subprocess.TimeoutExpired:
            msg = f"last30days pulse timed out after {settings.LAST30DAYS_PULSE_TIMEOUT_SECONDS}s for '{entity_name}'"
            logger.warning(msg)
            # Kill zombie process to prevent resource leak
            try:
                proc.kill()
                proc.wait(timeout=5)
            except Exception:
                pass
            # Mark the pulse as completed so the staleness queue doesn't re-queue infinitely
            try:
                from src.staleness_queue import record_pulse_completed as _rpc
                _rpc(slug, divergence_risk=0.0, state_label="unverified")
            except Exception:
                pass
            return PulseResult(
                entity_name=entity_name,
                status="error",
                evidence=[],
                raw_snapshot_path=None,
                budget_remaining=remaining,
                error=msg,
            )
        except FileNotFoundError:
            msg = f"last30days binary not found at: {binary_parts[0]}"
            logger.error(msg)
            return PulseResult(
                entity_name=entity_name,
                status="error",
                evidence=[],
                raw_snapshot_path=None,
                budget_remaining=remaining,
                error=msg,
            )
        except Exception as e:
            msg = f"Unexpected error running last30days for '{entity_name}': {e}"
            logger.error(msg, exc_info=True)
            return PulseResult(
                entity_name=entity_name,
                status="error",
                evidence=[],
                raw_snapshot_path=None,
                budget_remaining=remaining,
                error=msg,
            )

        # Parse output into ClaimEvidence
        try:
            evidence = self.adapter.parse_output(raw_output, entity_name)
            filtered_evidence = []
            for ev in evidence:
                url_lower = ev.url.lower() if ev.url else ""
                claim_lower = ev.claim_text.lower() if ev.claim_text else ""
                platform_lower = ev.source_platform.lower() if ev.source_platform else ""
                
                # 1. Semantic Disambiguation check
                ent_lower = entity_name.lower()
                ent_words = [w for w in re.split(r"[-_ ]+", ent_lower) if len(w) > 2]
                if ent_words:
                    STOP_WORDS = {"the", "and", "for", "from", "with", "that", "this", "were", "was", "his", "her", "their"}
                    ent_words = [w for w in ent_words if w not in STOP_WORDS]
                if not ent_words:
                    ent_words = [ent_lower]
                # Use word-boundary token matching to avoid false positives (e.g., "element" in "elemental")
                claim_tokens = set(re.findall(r"\b[a-z0-9]+\b", claim_lower))
                url_tokens = set(re.findall(r"\b[a-z0-9]+\b", url_lower))
                all_tokens = claim_tokens | url_tokens
                match_count = sum(1 for w in ent_words if w in all_tokens)
                # Fractional threshold: at least ceil(60%) of entity words must match
                import math as _math
                min_required = max(1, _math.ceil(len(ent_words) * 0.6))
                if match_count < min_required:
                        logger.info(f"Filtering out cross-contamination candidate for '{entity_name}': {ev.claim_text}")
                        continue

                # 1b. Noise floor for single-word entities: require minimum engagement
                if len(ent_words) <= 1:
                    noise_floor = 5
                    eng = getattr(ev, "engagement_count", 0) or 0
                    if eng < noise_floor:
                        logger.debug(f"Filtering low-engagement noise for single-word entity '{entity_name}': eng={eng}")
                        continue

                # 2. Hiring/jobs check for non-organizations
                if not is_org:
                    hiring_domains = ("greenhouse.io", "ashbyhq.com", "lever.co", "workable.com", "apply.workable.com")
                    hiring_keywords = ("hiring", "careers", "database engineer", "business development executive", "job openings", "current openings")
                    if (platform_lower in ("jobs-web", "jobs", "careers") or
                        any(dom in url_lower for dom in hiring_domains) or
                        any(kw in claim_lower for kw in hiring_keywords)):
                        logger.debug(f"Filtering out hiring-signal/jobs evidence from non-org '{entity_name}': {ev.claim_text}")
                        continue
                        
                filtered_evidence.append(ev)
            evidence = filtered_evidence
            evidence = self.adapter.normalize_engagement(evidence)
        except Exception as e:
            logger.error(f"Failed to parse last30days output for '{entity_name}': {e}")
            evidence = []

        if not evidence:
            logger.info(f"No evidence parsed for '{entity_name}' — trying DDGS fallback")
            # Fallback: try direct DuckDuckGo search via ddgs package when CLI returns nothing
            try:
                from ddgs import DDGS
                with DDGS() as ddgs:
                    ddg_results = list(ddgs.text(f'\"{entity_name}\" {" ".join(ent_words[:3]) if ent_words else ""}', max_results=10))
                if ddg_results:
                    from src.models import ClaimEvidence as _CE
                    from datetime import datetime as _dt, timezone as _tz
                    ddg_evidence = []
                    for r in ddg_results:
                        title = (r.get("title") or "").strip()
                        body = (r.get("body") or r.get("snippet") or "").strip()
                        url = (r.get("href") or r.get("url") or "").strip()
                        claim = f"{title}: {body}" if title and body else (title or body)
                        if claim:
                            ddg_evidence.append(_CE(
                                claim_text=claim[:2000],
                                source_platform="web",
                                engagement_count=10,
                                url=url,
                                timestamp=_dt.now(_tz.utc).isoformat(),
                                cluster_id=f"ddgs:{slug}:{len(ddg_evidence)}",
                            ))
                    if ddg_evidence:
                        evidence = ddg_evidence
                        logger.info(f"DDGS fallback found {len(evidence)} items for '{entity_name}'")
            except Exception as ddgs_err:
                logger.debug(f"DDGS fallback failed for '{entity_name}': {ddgs_err}")

        if not evidence:
            logger.info(f"No evidence parsed for '{entity_name}' — returning no_data")
            # Still record spend (API was hit) and write raw snapshot for audit
            try:
                ResourceLedger.record_spend(is_paid, f"pulse:{entity_name}:no_data")
            except Exception as rec_err:
                logger.debug(f"Failed to record spend for no_data pulse: {rec_err}")

            try:
                paths = write_pulse_snapshot(
                    entity_name=entity_name,
                    evidence=[],
                    raw_output=raw_output,
                    extra_meta={
                        "handles": handles or {},
                        "budget_remaining_before": remaining,
                        "status": "no_data",
                    },
                )
                json_path = paths["json_path"]
            except Exception as write_err:
                logger.warning(f"Failed to write no_data pulse snapshot: {write_err}")
                json_path = None

            return PulseResult(
                entity_name=entity_name,
                status="no_data",
                evidence=[],
                raw_snapshot_path=json_path,
                budget_remaining=ResourceLedger.get_status().paid_remaining,
            )

        max_claims = settings.LAST30DAYS_MAX_CLAIMS_PER_PULSE
        if len(evidence) > max_claims:
            evidence = evidence[:max_claims]

        try:
            paths = write_pulse_snapshot(
                entity_name=entity_name,
                evidence=evidence,
                raw_output=raw_output,
                extra_meta={
                    "handles": handles or {},
                    "budget_remaining_before": remaining,
                    "binary": binary_parts[0],
                    "cost_usd": cost,
                },
            )
            json_path = paths["json_path"]
            logger.info(f"Pulse snapshot for '{entity_name}': {json_path} with {len(evidence)} evidence")
        except Exception as e:
            logger.error(f"Failed to write pulse snapshot for '{entity_name}': {e}")
            return PulseResult(
                entity_name=entity_name,
                status="error",
                evidence=evidence,
                raw_snapshot_path=None,
                budget_remaining=remaining,
                error=f"Failed to write snapshot: {e}",
            )

        # Record spend
        try:
            ResourceLedger.record_spend(is_paid, f"pulse:{entity_name}:{len(evidence)}")
        except Exception as rec_err:
            logger.debug(f"Failed to record spend after success: {rec_err}")

        final_remaining = ResourceLedger.get_status().paid_remaining

        # Append to log.md — provenance, not pytest temp paths
        try:
            from src.wiki.writer import append_to_log
            safe_name = entity_name.replace("\n", " ").replace("\r", " ")[:100]
            append_to_log(
                f"pulse | {safe_name} | {len(evidence)} evidence | "
                f"${cost:.2f} | remaining=${final_remaining:.2f} | {slug}"
            )
        except Exception as log_err:
            logger.debug(f"Failed to append pulse to log: {log_err}")

        elapsed = time.perf_counter() - t_start
        try:
            pulse_runs_total.add(1, {"status": "success", "entity": slug[:20]})
            pulse_latency_seconds.record(elapsed)
            budget_spent_usd.add(cost)
        except Exception:
            pass

        return PulseResult(
            entity_name=entity_name,
            status="success",
            evidence=evidence,
            raw_snapshot_path=json_path,
            budget_remaining=final_remaining,
        )
