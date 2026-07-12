---
title: "Living Almanac — Troubleshooting"
tags: [living-almanac, troubleshooting, debug]
created: 2026-07-12
updated: 2026-07-12
sources: [chickensoup-living-almanac-implementation-spec, agent-architecture, integration-architecture]
related: [living-almanac, api-design, production-readiness]
---

# Living Almanac — Troubleshooting

Quick-reference guide for common failure modes in the evidence pipeline.

## Symptoms & Fixes

### All entities show `(error, 0 evidence)` in almanac

1. Check `LAST30DAYS_ENABLED=true` is set in `.env`.
2. Check `LAST30DAYS_BINARY_PATH` points to an executable `last30days` script (e.g. `last30days-skill/skills/last30days/scripts/last30days.py`).
3. Check the script has execute permission: `chmod +x /path/to/last30days.py`.
4. Check `LAST30DAYS_PULSE_TIMEOUT_SECONDS` ≥ 90 (script takes ~58s on cold start).
5. Check `wiki/raw/pulse/` is writable and not empty: `ls wiki/raw/pulse/`.
6. If `npx last30days` is being invoked instead of the cloned script, the workspace root in `pulse_agent.py` is wrong — it must be 3 dirname hops from `src/agents/pulse_agent.py` to reach the project root where `last30days-skill/` lives.

### `CLI exit 1: npm error code E404` from last30days

Caused by `LAST30DAYS_BINARY_PATH` being empty AND the cloned workspace script check failing (wrong workspace root). Fix:
1. Set `LAST30DAYS_BINARY_PATH` to the absolute path of the cloned script in `.env`.
2. Or fix `workspace_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))` (3 hops, not 2).

### `/entities/{name}/divergence` returns 404 or empty data

1. Confirm `name` does NOT contain percent-encoded characters. Swift `AlmanacService` should pass raw names — any `.addingPercentEncoding` before `appendingPathComponent` will double-encode (`%20` → `%2520`).
2. If 404 persists, check FastAPI route decoding matches entity slug (lowercase, spaces → hyphens). The slugify in the backend should produce the same slug as the frontend uses in the path.

### Pulse task status shows `failed` with `Permission denied`

The `last30days.py` script is not executable. Run: `chmod +x last30days-skill/skills/last30days/scripts/last30days.py`.

### Pulse times out after 60s

Script needs ~58s on cold start with no cached cookies. Increase `LAST30DAYS_PULSE_TIMEOUT_SECONDS` to 120. Subsequent runs use warm cache and complete faster.

### Entanglement shows "no data" despite evidence

Ensure at least 2 independent platforms co-mention both entities in recent pulse snapshots. Entanglement requires `independent_clusters ≥ 2` and `independent_platforms ≥ 2` before an entanglement is recorded.

### Budget hold / spend stuck

Check `GET /budget/status`. If `on_hold=true`, call `POST /budget/approve`. Verify budget ceiling in `.env` (`LAST30DAYS_MONTHLY_BUDGET_USD`). Budget is tracked in Redis hash `budget:YYYY-MM`.
