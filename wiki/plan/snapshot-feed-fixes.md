---
title: "Snapshot Feed Fixes — Implementation Plan"
tags: [project, living-almanac, snapshot-feed, dedup, implementation-plan]
created: 2026-07-12
updated: 2026-07-12
sources: [living-almanac, living-almanac-troubleshooting, api-design, project-structure]
related: [living-almanac, living-almanac-troubleshooting, master-implementation-plan, api-design]
---

# Snapshot Feed Fixes — Implementation Plan

Addresses findings F1–F9 from the [[living-almanac]] Section 16 audit (2026-07-12).

## Scope

Three workstreams: write-path dedup, read-path grouping, UI grouping. Each is independently deployable.

---

## Workstream A — Write-Path Dedup (findings F1, F2, F6)

### A1. Replace 24h empty-only dedup with time-window latest-per-entity dedup

**Current**: `_has_recent_empty_snapshot(slug)` only skips writes when `evidence_count == 0` within 24h.

**New**: `_get_latest_snapshot_meta(slug)` returns the most recent snapshot's `evidence_count` and `timestamp` for a given slug. The write path skips if:
- A snapshot for the same entity was written within the configurable window (`LAST30DAYS_DEDUP_WINDOW_HOURS`, default 24h), **AND**
- The new evidence list is byte-equivalent to the existing snapshot's evidence (same count + same claim texts, ignoring timestamps), **OR** both are empty (`evidence_count == 0`).

Why byte-equivalence and not just "any write": non-empty re-runs **should** create new snapshots when fresh evidence arrives. We only want to suppress exact duplicates (same CLI output re-parsed to identical claims).

**Files changed**:
- `src/wiki/pulse_writer.py` — replace `_has_recent_empty_snapshot` with `_get_latest_snapshot_meta`, add `_evidence_fingerprint(evidence)` helper
- `src/config.py` — add `LAST30DAYS_DEDUP_WINDOW_HOURS: int = 24`

**Behaviour**:
| Scenario | Result |
|---|---|
| First pulse, 5 evidence | Written as `{slug}-{date}.json` |
| Re-run same entity, same 5 evidence, within 24h | Skipped (dedup) — `PulseResult.status="deduped"` |
| Re-run same entity, 5 evidence but 1 new claim, within 24h | Written as `{slug}-{date}-N.json` |
| Re-run same entity, 0 evidence, within 24h | Skipped (dedup) — `PulseResult.status="deduped"` |
| Re-run same entity, >0 evidence, after 24h window | Written (window expired) |
| Re-run new entity, any evidence | Written (different slug) |

### A2. Truthful dedup status in PulseResult

**Current**: dedup'd writes return `raw_snapshot_path=""`, `status="no_data"` from the caller. The UI shows "Ingested 0 evidence items" — looks like a failure.

**New**: Add `status="deduped"` to `PulseResult` status enum. Log the dedup reason with the matched snapshot path so operators can audit.

**Files changed**:
- `src/models.py` — add `"deduped"` to `PulseResult.status` Literal
- `src/agents/pulse_agent.py` — set `result.status = "deduped"` when `write_pulse_snapshot` returns empty path due to dedup; include `matched_snapshot` in result for logging
- `src/wiki/pulse_writer.py` — return `{"json_path": "", "md_path": "", "base_name": "", "deduped": True, "matched_path": str(existing_path)}`

---

## Workstream B — Read-Path Grouping (findings F3, F8)

### B1. Add `latest=true` query param to `/pulse/history`

**Current**: endpoint returns all files matching the glob, newest-first, capped at `limit=50`.

**New**: when `?latest=true` is passed, group snapshots by `entity_name` and return only the most recent entry per entity. The full history is still available without the flag.

**Rationale**: The `PulsesHistorySection` feed should default to "latest per entity" view. Users can expand or filter to see full history.

**Files changed**:
- `src/main.py:2137` — add `latest: bool = False` query param; when true, group by `entity_name` and keep max-timestamp entry per group

**Response shape unchanged** — still `[APIPulseHistoryEntry]`. Default behaviour (no flag) unchanged.

### B2. Add `total` breakdown to `/pulse/history` response

Return `{"pulses": [...], "total": N, "unique_entities": M, "empty_count": K}` so the UI can show "12 snapshots across 5 entities (3 empty)" without recomputing.

**Files changed**:
- `src/main.py:2162` — include counts in response dict
- `APIPulseHistoryResponse.swift` — add `uniqueEntities`, `emptyCount` (optional, default 0 for backward compat)

---

## Workstream C — UI Grouping (finding F4)

### C1. Add expandable re-run history row

**Current**: each row shows entity name + date + claim count + re-run button. Re-runs appear as separate rows.

**New**: when `displayed` contains multiple entries with the same `entityName`, render a single collapsed row for the latest entry. Tapping reveals prior runs for that entity beneath it. The re-run button operates on whichever row's entity name is tapped.

**Files changed**:
- `PulsesHistorySection.swift` — introduce a `groupedPulses` computed property that clusters by `entityName`, newest first within each group; pivot `ForEach` to iterate groups with an `@State private var expandedGroups: Set<String>` for disclosure

**Visual**:
```
▼ Project Serpo   2 claims    ⟳  (latest, expanded)
  ├─ 2026-07-12-4   2 claims
  ├─ 2026-07-12-2   2 claims
  └─ 2026-07-12     4 claims
▼ Roswell Crash   50 claims   ⟳
▼ Enoch           0 claims    ⟳
```

### C2. Add "Purge Empty Logs" per-entity option

**Current**: purge-empty button deletes all empty snapshots across ALL entities.

**New**: in the expanded group view, add a per-entity "Purge my empty logs" action. Calls existing `POST /pulse/purge-empty` but scoped to that entity's files in a follow-up endpoint, or filters client-side by re-fetching history after a per-entity server endpoint.

**Files changed**:
- `src/main.py` — add `POST /pulse/purge-empty?entity_name=project-serpo` (optional scope param; omit = current global behaviour)
- `PulsesHistorySection.swift` — append per-entity purge button when group contains empty entries

---

## Priority order

| Priority | Workstream | Effort | Impact |
|---|---|---|---|
| P0 | A1 latest-per-entity dedup on write | Medium | High — stops file proliferation at source |
| P0 | A2 truthful `deduped` status | Small | High — eliminates UI confusion |
| P1 | B1 `latest=true` grouping on read | Small | Medium — feed shows clean "one row per entity" view |
| P1 | C1 expandable re-run rows in SwiftUI | Medium | Medium — surfaces existing history without proliferation |
| P2 | B2 response counts enrichment | Small | Low — diagnostic value only |
| P2 | C2 per-entity purge | Small | Low — quality of life |

## Tests

| Test | What it asserts |
|---|---|
| `tests/test_pulse_writer_dedup.py` [NEW] | exact-evidence re-run within window → skipped; different evidence → written; after window → written; empty-first-write → written; empty-second-write-within-24h → skipped |
| `tests/test_pulse_history_grouping.py` [NEW] | `GET /pulse/history?latest=true` returns one entry per entity; `latest=false` (default) returns all entries; counts in response correct |
| Update `tests/test_adapter_real_schema.py` | adapter tests unaffected (dedup is post-adapter) |
| All existing tests | must stay green |

## Rollout

1. Merge A1 + A2 together (write-path contract change — `PulseResult.status` gains new enum value, must be coordinated).
2. Merge B1 independently — read-path only, no writer changes.
3. Merge C1 + B1 together to validate grouping end-to-end (SwiftUI groups against grouped API response).
4. Merge B2 + C2 last — purely additive enrichment.

All changes are additive. No existing call sites break: `deduped` is a new `PulseResult.status` value, `latest` defaults to `False`, and `APIPulseHistoryResponse` new fields default to `0`/`[]`.
