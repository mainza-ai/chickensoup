---
title: "Budget Tracking"
tags: [budget, living-almanac, pulse, almanac, redis]
created: 2026-07-12
updated: 2026-07-12
sources: [living-almanac]
related: [pulse-agent, credibility-scoring, api-design, frontend-settings-menu, key-decisions]
---

# Budget Tracking

Monthly spend ceiling for `last30days` paid APIs (ScrapeCreators, Perplexity, Brave). Mandatory per spec non-negotiable #4 — not a follow-up.

## Model

- Redis hash `budget:YYYY-MM` {spent, pulls, last_pull, last_description}
- Lua atomic: `BUDGET_LUA_CHECK` — if spent+cost > ceiling return 0 (refuse) else incr spent+pulls and return 1 (allowed) with new spent
- HOLD Lua: `BUDGET_HOLD_LUA` — when remaining < threshold*cost (default 2.0x = need <$1 left when cost $0.50), SET `budget:YYYY-MM:hold` with 24h TTL
- Fallback: non-atomic hget/hset when Lua eval fails (single worker safe)
- Optimistic allowance when Redis unavailable (warning logged) — needed for tests with mock Redis

## Config

- `LAST30DAYS_MONTHLY_BUDGET_USD=20.0`
- `LAST30DAYS_COST_PER_PULL_USD=0.50`
- `BUDGET_REDIS_KEY_PREFIX=budget`
- `BUDGET_HOLD_THRESHOLD_REMAINING=2.0`

## API

- `GET /budget/status` → `BudgetStatus{month_key, spent_usd, pulls_count, remaining_usd, ceiling_usd, on_hold}`
- `POST /budget/approve` (auth) → clears HOLD flag, returns updated status
- `BudgetTracker.reset_month(month_key?)` — admin helper

## Flow

1. `PulseAgent.run_pulse()` → `budget_tracker.get_status()` for remaining in disabled/no-op return
2. `budget_tracker.check_budget(cost)` → atomic Lua: allowed, remaining, reason
3. If not allowed: log `pulse | {entity} | budget_exceeded | {reason} | remaining=${remaining}` to `wiki/log.md`, return `PulseResult(status=budget_exceeded)` with reason, never shell out (`test_pulse_budget_exceeded_refused_and_logged` asserts `mock_run.called` false)
4. If allowed: shell out to last30days, parse, write snapshot
5. `budget_tracker.record_spend(cost, description)` updates metadata {last_pull, last_description} + expire 35 days
6. Observability: `pulse_runs_total{status,entity}`, `pulse_latency_seconds`, `budget_spent_usd` counters/histogram

## HOLD Pattern

Reuses MilimoClaw SpendApprovalHandler shape (config gate + explicit confirm step per spec):

- Config gate: `LAST30DAYS_ENABLED` default false
- Confirm step: `POST /budget/approve` clears HOLD
- HOLD triggers when remaining budget < threshold×cost → next pulse gets `status=budget_exceeded` with HOLD reason
- Frontend shows red banner + approve button when `on_hold=true`

## See Also

- [[pulse-agent]]
- [[api-design]]
- [[frontend-settings-menu]]
- [[key-decisions]]
