---
title: "Living Almanac — Troubleshooting"
tags: [living-almanac, troubleshooting, debug]
created: 2026-07-12
updated: 2026-07-12
sources: [chickensoup-living-almanac-implementation-spec, agent-architecture, integration-architecture]
related: [living-almanac, api-design, production-readiness, snapshot-feed-fixes]
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

---

## Snapshot Feed — Duplicate & 0-Evidence Issues

### Re-run produces duplicate rows in feed

**Cause (F1–F4)**: Every `POST /pulse/{entity}` invocation writes a new file to `wiki/raw/pulse/` with a unique counter suffix. The `/pulse/history` endpoint returns every matching file. SwiftUI treats each file path as a unique row identity. There is no "latest per entity" grouping on either the write path or the read path.

**Diagnosis**: `ls wiki/raw/pulse/` shows `project-serpo-2026-07-12.json`, `-2.json`, `-3.json`, `-4.json` for the same entity on the same day. `/pulse/history` returns all 4 entries.

---

### Re-run returns 0 evidence after adapter fix

**Cause (F9 — FIXED)**: Pre-existing semantic disambiguation filter in `src/agents/pulse_agent.py` used `entity_name.split()` which, for slug-form names like `project-serpo` or `bob-lazar`, produced a single giant token (`["project-serpo"]`). The filter then required that literal token to appear in every claim text or URL. No last30days claim contains `"project-serpo"` verbatim, so all claims were silently dropped.

**Fix**: Changed tokeniser to `re.split(r"[-_ ]+", entity_name)`, added STOP_WORDS filter, and changed threshold from 50% to **all-words-required** for multi-word entities.

---

### 0-evidence re-run creates empty snapshot spiral

**Cause (F1, F2)**: Before the 24h dedup guard was added, every 0-evidence re-run created a new empty snapshot file. The first empty write was never dedup'd (no prior empty snapshot to match), so a series of re-runs accumulated `-2.json`, `-3.json`, `-4.json`, etc.

**Current behaviour (post-fix)**: `_has_recent_empty_snapshot(slug)` in `pulse_writer.py` skips writing a new empty snapshot if one exists within the last 24h. Returns `{"json_path": "", ...}` silently.

**Residual issue (F6)**: The caller stores `json_path = ""` in `PulseResult.raw_snapshot_path`. The task console shows "Ingested 0 evidence items" — indistinguishable from a write error. Use server logs (`Filtering out`, `Skipping duplicate empty snapshot`) to tell dedup hits apart from genuine failures.

---

### Purge-empty removes all empty snapshots globally

**Cause (F7)**: `POST /pulse/purge-empty` iterates `pulse_dir.glob("*.json")` across all entities with no per-entity opt-out. Use the UI filter in `PulsesHistorySection` to review before purging.

---

### `st_mtime` discrepancy with snapshot `timestamp` field

**Cause (F5)**: `_has_recent_empty_snapshot` uses `snap_path.stat().st_mtime` for the 24h window. If files are restored from backup or `touch`-ed, `st_mtime` can diverge from the `timestamp` field inside the JSON. In normal operation these are near-identical.

---

### UI does not collapse same-entity re-runs

**Cause (F4)**: `ForEach(displayed.prefix(5), id: \.file)` in `PulsesHistorySection.swift:73` uses the full file path as row identity. Same-entity re-runs produce distinct rows with identical `entityName`, `date`, and `evidenceCount`. Users must tap each row and read `timestamp` inside `PulseSnapshotDetailsView` to distinguish them.

---

### Diagnostic commands

```bash
# List all snapshots for an entity, sorted newest first
ls -lt wiki/raw/pulse/project-serpo-*.json

# Count total snapshots
ls wiki/raw/pulse/*.json | wc -l

# Count empty snapshots
python3 -c "
import json, pathlib
d = pathlib.Path('wiki/raw/pulse')
empty = [f.name for f in d.glob('*.json') if json.load(open(f)).get('evidence_count',-1)==0]
print(f'Empty snapshots: {len(empty)}')
"

# Check dedup guard hit in server log
grep "Skipping duplicate empty snapshot" /tmp/chickensoup-server.log | tail -10

# Check filter drops in server log
grep "Filtering out cross-contamination" /tmp/chickensoup-server.log | tail -20
```
