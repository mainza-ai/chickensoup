---
title: "Pulse Agent"
tags: [agent, living-almanac, last30days, pulse, budget]
created: 2026-07-12
updated: 2026-07-12
sources: [living-almanac]
related: [agent-architecture, budget-tracking, credibility-scoring, api-design, frontend-settings-menu]
---

# Pulse Agent

Entity-scoped ingestion that pulls fresh evidence for a wiki entity via the `last30days` engine, normalizes into `ClaimEvidence`, and hands off to quantum credibility layer. Never writes directly to entity/concept pages — `wiki/raw/pulse/` only.

## Class Shape

Follows `chat_ingest_agent.py` — class with periodic entry point, not request-handler:

```python
class PulseAgent:
    def run_pulse(self, entity_name: str, handles: dict | None = None) -> PulseResult:
        # 1. Sanitize entity name (reject null bytes, newlines, cap 200)
        # 2. Check LAST30DAYS_ENABLED — disabled returns clean no-op, not error
        # 3. Budget check via budget_tracker (Lua atomic) — refusal logged, not throttled
        # 4. Resolve binary: LAST30DAYS_BINARY_PATH → npx last30days → last30days
        # 5. Build command list (never shell=True) + timeout 60s + catch degrade
        # 6. Parse via last30days_adapter.py (JSON first, markdown fallback)
        # 7. Normalize engagement (log-scaled, decayed with half-life 7d)
        # 8. Write immutable dated snapshot to wiki/raw/pulse/{slug}-{date}.json+.md
        # 9. Record spend, append to log.md, return structured evidence
```

## Security

- `shell=False` always — `run_pulse("Bob Lazar; rm -rf /")` passes malicious string as single arg, not executed
- `_sanitize_entity_name`: rejects `\x00`, `\n`, `\r`, caps 200 chars
- Subprocess timeout `LAST30DAYS_PULSE_TIMEOUT_SECONDS=60`
- Config `LAST30DAYS_BINARY_PATH` + `shutil.which` resolution

## Budget Guardrails

- `src/budget.py: BudgetTracker` with Redis Lua `BUDGET_LUA_CHECK` (atomic check+incr) + `BUDGET_HOLD_LUA`
- `budget:YYYY-MM` hash {spent, pulls, last_pull, last_description}
- HOLD when remaining < 2× cost (`BUDGET_HOLD_THRESHOLD_REMAINING=2.0`)
- `POST /budget/approve` to clear HOLD — same shape as MilimoClaw SpendApprovalHandler
- `PulseResult(status=budget_exceeded)` with reason, log.md entry — never silently throttled

## Adapter

`src/last30days_adapter.py: Last30daysAdapter`:

- `parse_output(raw, entity_name) -> List[ClaimEvidence]`: tries `parse_json_output` (claims|evidence|results arrays, or single dict with claim-ish keys) first, then `parse_markdown_output` (## Claims/evidence bullet extraction, URL regex, engagement hints, polymarket % detection)
- `normalize_engagement()`: `log1p(count)/log1p(max)` decayed
- `_infer_platform()`: keyword map reddit/x/youtube/news/github/polymarket/perplexity/brave/podcast
- Last resort: whole raw as single claim if >100 chars

## Snapshot Format

- `wiki/raw/pulse/{slug}-{date}.json`: `{entity_name, slug, date, timestamp, evidence_count, evidence: [ClaimEvidence], raw_output_preview, meta: {handles, budget_remaining_before, binary, cost_usd}}`
- `wiki/raw/pulse/{slug}-{date}.md`: human-readable per-claim sections with platform, engagement, decayed, market odds, url, cluster, quote
- Collision handling: if file exists today, append `-2`, `-3`, etc.
- Never touches index.md (pulse files are raw snapshots, not wiki pages)

## Endpoints

- `POST /pulse/{entity_name}` with `{"handles": {"x": "@handle", "subreddit": "r/ufos"}}` → `PulseResult`
- `GET /pulse/history?entity_name=&limit=50` → pulse history with evidence counts
- `GET /budget/status` → BudgetStatus
- `POST /budget/approve` → clear HOLD

## Acceptance

- `run_pulse("Bob Lazar")` with `ENABLED=false` returns no-op, not error, no file, 0 evidence
- With enabled, writes exactly one new immutable file to `wiki/raw/pulse/`, never touches `wiki/entities/` or `concepts/`
- Budget ceiling checked before pull; refusal logged, not silently throttled; subprocess never called when budget exceeded (tested `mock_run.called` false)
- `shell=False` always (tested `test_pulse_never_shell_true`)
- Adapter handles both JSON and markdown output shapes

## See Also

- [[budget-tracking]]
- [[credibility-scoring]]
- [[agent-architecture]]
- [[api-design]]
- [[frontend-settings-menu]]
