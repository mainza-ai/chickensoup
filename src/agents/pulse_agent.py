import json
import logging
import os
import shlex
import shutil
import subprocess
import time
from datetime import datetime, timezone
from typing import Optional, Dict, List

from src.config import settings
from src.models import ClaimEvidence, PulseResult
from src.budget import budget_tracker
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

        # Prefer JSON output
        is_python_script = any("last30days.py" in p for p in binary_parts)
        if is_python_script:
            cmd.extend(["--emit", "json"])
        else:
            if "--json" not in cmd:
                cmd.append("--json")

        return cmd

    def run_pulse(self, entity_name: str, handles: dict | None = None) -> PulseResult:
        t_start = time.perf_counter()
        entity_name = _sanitize_entity_name(entity_name)
        slug = slugify(entity_name)

        budget_status = budget_tracker.get_status()

        # Disabled gate — clean no-op
        if not settings.LAST30DAYS_ENABLED:
            logger.info(f"Pulse disabled (LAST30DAYS_ENABLED=false) for '{entity_name}' — returning no-op")
            return PulseResult(
                entity_name=entity_name,
                status="disabled",
                evidence=[],
                raw_snapshot_path=None,
                budget_remaining=budget_status.remaining_usd,
            )

        # Budget check before any network call
        cost = settings.LAST30DAYS_COST_PER_PULL_USD
        allowed, remaining, reason = budget_tracker.check_budget(cost)
        if not allowed:
            logger.warning(f"Pulse refused for '{entity_name}': budget exceeded — {reason} (remaining ${remaining:.2f})")
            try:
                from src.wiki.writer import append_to_log
                safe_name = entity_name.replace("\n", " ").replace("\r", " ")[:100]
                append_to_log(f"pulse | {safe_name} | budget_exceeded | {reason} | remaining=${remaining:.2f}")
            except Exception as log_err:
                logger.debug(f"Failed to append budget refusal to log: {log_err}")

            return PulseResult(
                entity_name=entity_name,
                status="budget_exceeded",
                evidence=[],
                raw_snapshot_path=None,
                budget_remaining=remaining,
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
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=settings.LAST30DAYS_PULSE_TIMEOUT_SECONDS,
                shell=False,
                env={**os.environ, "NO_COLOR": "1"},
            )
            raw_output = result.stdout or ""

            if result.returncode != 0:
                logger.warning(f"last30days CLI exited {result.returncode} for '{entity_name}': stderr={result.stderr[:500]}")
                if not raw_output.strip():
                    return PulseResult(
                        entity_name=entity_name,
                        status="error",
                        evidence=[],
                        raw_snapshot_path=None,
                        budget_remaining=remaining,
                        error=f"CLI exit {result.returncode}: {result.stderr[:500]}",
                    )

        except subprocess.TimeoutExpired:
            msg = f"last30days pulse timed out after {settings.LAST30DAYS_PULSE_TIMEOUT_SECONDS}s for '{entity_name}'"
            logger.warning(msg)
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
            evidence = self.adapter.normalize_engagement(evidence)
        except Exception as e:
            logger.error(f"Failed to parse last30days output for '{entity_name}': {e}")
            evidence = []

        if not evidence:
            logger.info(f"No evidence parsed for '{entity_name}' — returning no_data")
            # Still record spend (API was hit) and write raw snapshot for audit
            try:
                budget_tracker.record_spend(cost, f"pulse:{entity_name}:no_data")
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
                budget_remaining=budget_tracker.get_status().remaining_usd,
            )

        # Cap claims per pulse
        max_claims = settings.LAST30DAYS_MAX_CLAIMS_PER_PULSE
        if len(evidence) > max_claims:
            evidence = evidence[:max_claims]

        # Write immutable snapshot to wiki/raw/pulse — never touches entities/concepts
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
            budget_tracker.record_spend(cost, f"pulse:{entity_name}:{len(evidence)}")
        except Exception as rec_err:
            logger.debug(f"Failed to record spend after success: {rec_err}")

        final_remaining = budget_tracker.get_status().remaining_usd

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
