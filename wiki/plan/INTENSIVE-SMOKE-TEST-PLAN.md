# Production Smoke Test Plan — Project Chicken Soup

> **Scope:** Full-stack, production-grade validation of every backend surface and its Swift frontend contract.
> **Goal:** Find gaps, breakages, and regressions before they reach production. No demo shortcuts.
> **Constraint:** The live server is already running. Tests must be runnable against a live instance without restarting it.

---

## 0. Test Harness Requirements

### 0.1 Environment Pre-Checks (run once, before any test)
| Check | Expected |
|---|---|
| `redis-cli ping` | `PONG` |
| `neo4j status` | Running, bolt port reachable |
| `LAST30DAYS_ENABLED` in `.env` | `true` or `false` (document which) |
| `LAST30DAYS_BINARY_PATH` in `.env` | Absolute path or empty |
| `.env` has `LLM_ACTIVE_PROVIDER` and `LLM_ACTIVE_MODEL` | Set |
| `lsof -i:8000` | uvicorn PID present |
| Disk write permissions on `wiki/`, `wiki/raw/`, `backups/` | Writable |
| `papers/` directory exists with at least one PDF | Present |
| `xcodebuild` for Swift frontend | BUILD SUCCEEDED |

### 0.2 Test Isolation Rules
- Tests that **write** to Redis must use unique keys (prefix with test run ID) or clean up after themselves.
- Tests that **write** to the wiki must use a temporary subdirectory or revert changes.
- Tests that **trigger LLM calls** must respect the configured budget ceiling.
- Tests that **invoke `last30days`** must require explicit opt-in env var `RUN_PULSE_INTEGRATION_TESTS=true`.
- Tests that **wipe Neo4j** must be gated behind `RUN_DESTRUCTIVE_TESTS=true`.
- No test may call `sys.exit()` or `os._exit()`.
- All HTTP tests use the `X-Api-Key: dev` header (dev mode bypasses auth; production uses real key).

### 0.3 Reporting Format
Every test case outputs:
```text
[PASS|FAIL|SKIP] <test_id>: <description>
  duration_ms: <ms>
  assertion: <key=value pairs>
  error: <if failed>
```

Final summary:
```text
=== Smoke Test Report ===
passed: N
failed: N
skipped: N
total: N
duration: Xs
```

---

## 1. API Contract Tests (End-to-End HTTP)

### 1.1 `GET /status` — System Health Probe
| Case | Assertions |
|---|---|
| `status-01` | `GET /status` returns 200; `status` in `["healthy","degraded"]`; `llm_connected` bool; `neo4j_connected` bool; `redis_connected` bool; `last30days_enabled` matches `.env`; `budget_remaining` float or null |
| `status-02` | Stop Redis; `GET /status` returns `redis_connected: false`; `status` still `"healthy"` or `"degraded"`; no 500 |
| `status-03` | Stop Neo4j; `GET /status` returns `neo4j_connected: false`; response is JSON; no crash |

### 1.2 `POST /query` — Main Query Pipeline
| Case | Input | Expected `task_id` | Assertions |
|---|---|---|---|
| `query-01` | `{"query":"What is the Philadelphia Experiment?","structured":false}` | `null` | 200; `answer` non-empty str; `entities` list; `source_tier=="local"`; `confidence` float `[0,1]`; response time < 5s |
| `query-02` | `{"query":"deep-research Bob Lazar","structured":false}` | non-null UUID | 200; `answer` contains "Started async enrichment"; `entities` contains "Bob Lazar"; `task_id` present |
| `query-03` | `{"query":"","structured":false}` | `null` | 200; `answer` non-empty; no crash |
| `query-04` | `{"query":"navigate to Earth-1947","structured":false}` | `null` | 200; response has answer containing navigation result or `success:true` |
| `query-05` | `{"query":"pulse Area 51","structured":false}` | non-null UUID | 200; `task_id` present; `entities` contains "Area 51" |
| `query-06` | Missing `query` field | error | 422 (Pydantic validation); no crash |
| `query-07` | `{"query":"research EntityThatDoesNotExist","structured":false}` | non-null UUID | 200; `task_id` present; no 500 |

### 1.3 `GET /tasks/{task_id}` — Background Task Status
| Case | Setup | Assertions |
|---|---|---|
| `task-01` | Submit `deep-research` query; capture `task_id` | Task exists; `status` in `["running","success","failed"]` |
| `task-02` | Poll every 4s for up to 60s | Transitions to `success`; `progress>=1.0`; `logs` count ≥ 3; `elapsed>0`; `result` non-null |
| `task-03` | `GET /tasks/00000000-0000-0000-0000-000000000000` | 404; `{"detail":"..."}` |
| `task-04` | Query task started 24h ago | Still registered if in-memory |

### 1.4 `GET /almanac/summary` — Almanac State
| Case | Assertions |
|---|---|
| `almanac-01` | `GET /almanac/summary` | 200; `date` null or ISO date; `contested_claims` list; `newly_contested` int; `entities_processed` list |
| `almanac-02` | Trigger `POST /almanac/generate?dry_run=true`; wait; `GET /almanac/summary` | 200; optional `date` populated; no crash |

### 1.5 `GET /pulse/history` — Pulse History
| Case | Assertions |
|---|---|
| `pulse-hist-01` | `GET /pulse/history?limit=5` | 200; `pulses` list; each item has `entity_name`, `date`, `evidence_count`, `evidence` |
| `pulse-hist-02` | `GET /pulse/history?limit=0` | 200; `pulses` list (possibly empty) |
| `pulse-hist-03` | `GET /pulse/history?entity_name=project-serpo&limit=5` | 200; results filtered to entity |

### 1.6 `POST /pulse/{entity_name}` — Pulse Trigger
| Case | Assertions |
|---|---|
| `pulse-trigger-01` | `POST /pulse/Area 51` with api key | 200/400/500; JSON body; no unhandled exception |
| `pulse-trigger-02` | `POST /pulse/"` (malformed) | 404 or 422; no crash |

### 1.7 `POST /pulse/purge-empty` — Pulse Maintenance
| Case | Assertions |
|---|---|
| `purge-01` | `POST /pulse/purge-empty` | 200; `purged_count` int ≥ 0 |
| `purge-02` | `POST /pulse/purge-empty?entity_name=project-serpo` | 200; body present |

### 1.8 `POST /research/{thread_id}/approve` — Human Approval Gate
| Case | Assertions |
|---|---|
| `approve-01` | Deep-research triggering `human_approval_required`; capture `thread_id`; wait; `POST /research/{thread_id}/approve` | 200 or 404 |
| `approve-02` | `POST /research/00000000-0000-0000-0000-000000000000/approve` | 404; `{"detail":"No paused research..."}` |

### 1.9 `GET /entities/{name}/timeline` — Timeline Builder
| Case | Assertions |
|---|---|
| `timeline-01` | `GET /entities/area-51/timeline?days=30` | 200; `timeline` list; items have `date`, `epistemic_confidence`, `divergence_risk` |
| `timeline-02` | `GET /entities/NonExistentEntity/timeline?days=30` | 200 or 404; no crash |

### 1.10 `POST /entities/{name}/tribunal` — Tribunal Agent
| Case | Assertions |
|---|---|
| `tribunal-01` | `POST /entities/Bob Lazar/tribunal` with body | 200/500; JSON; no unhandled exception; 4 LLM calls in logs |
| `tribunal-02` | Empty body | 422 or graceful JSON error |

### 1.11 `GET /entities/{name}/divergence` — Divergence Engine
| Case | Assertions |
|---|---|
| `div-01` | `GET /entities/bob-lazar/divergence` | 200; `divergence_risk` float; `driving_claims` list |
| `div-02` | `GET /entities/nonexistent/divergence` | 200 or 404; no crash |

### 1.12 `GET /entities/{name}/entanglement` — Entanglement Engine
| Case | Assertions |
|---|---|
| `ent-01` | `GET /entities/bob-lazar/entanglement?limit=5` | 200; `entanglements` list; items have `entity_name`, `entanglement_score`; count ≤ 5 |
| `ent-02` | `GET /entities/nonexistent/entanglement` | 200 or 404; no crash |

### 1.13 `GET /graph/{entity}` — Graph Neighborhood
| Case | Assertions |
|---|---|
| `graph-01` | `GET /graph/area-51` | 200; has `nodes` or `relationships` |
| `graph-02` | `GET /graph/nonexistent` | 404 |

### 1.14 `GET /wiki/pages` — Wiki Page Listing
| Case | Assertions |
|---|---|
| `wiki-list-01` | `GET /wiki/pages` | 200; `pages` list; `total` int ≥ 0 |
| `wiki-list-02` | `GET /wiki/pages?page_type=entities` | 200; filtered correctly |

### 1.15 `GET /wiki/page/{slug}` — Wiki Page Detail
| Case | Assertions |
|---|---|
| `wiki-detail-01` | `GET /wiki/page/area-51` | 200; `success:true`; `title=="Area 51"`; body non-empty |
| `wiki-detail-02` | `GET /wiki/page/smoke-test-entity1` after creation | 200; `tags` contains `"auto"` |
| `wiki-detail-03` | `GET /wiki/page/nonexistent?page_type=entities` | 200 or 404; no crash |

### 1.16 `GET /events` — Event Detection
| Case | Assertions |
|---|---|
| `events-01` | `GET /events` | 200; JSON list; items have name/date/tags |
| `events-02` | No entities with event-like tags | `[]`; no crash |

### 1.17 `POST /ingest/file` and `/ingest/folder`
| Case | Setup | Assertions |
|---|---|---|
| `ingest-file-01` | Create temp `.md`; `POST /ingest/file` | 200; `pages_created:1`; file in wiki |
| `ingest-folder-01` | Zip of 3 `.md`; `POST /ingest/folder` | 200; `total_files:3`; `failed_files` empty or documented |
| `ingest-folder-02` | Zip with `.exe` | `.exe` filtered; `failed_files` has entry; no crash |

### 1.18 `GET /budget/status` and `POST /budget/approve`
| Case | Assertions |
|---|---|
| `budget-01` | `GET /budget/status` | 200; `spent_usd` float; `pulls_count` int; `remaining_usd` float or null |
| `budget-02` | Set hold; `POST /budget/approve` | 200; hold cleared |

### 1.19 `GET /debug/routing`
| Case | Assertions |
|---|---|
| `debug-01` | `GET /debug/routing?query=deep-research+Bob+Lazar` | 200; has `intent`, `entities`, `confidence` |
| `debug-02` | `GET /debug/routing?query=` (empty) | 200; no crash |

### 1.20 Quantum Schedule
| Case | Assertions |
|---|---|
| `quantum-01` | `POST /quantum/schedule` with simulated hardware | 200; has `job_id` |
| `quantum-02` | `GET /quantum/job/{job_id}` | 200; `status` in `["pending","running","completed","failed"]` |

---

## 2. Neo4j Knowledge Graph Integration Tests

### 2.1 Schema Initialization
| Case | Assertions |
|---|---|
| `neo4j-schema-01` | All 10 uniqueness constraints exist: `Person`, `Place`, `Concept`, `QuantumPlatform`, `Algorithm`, `Event`, `Object`, `Project`, `Entity`, `Paper` |
| `neo4j-schema-02` | Range indexes exist on `:Entity(type)` and `:Event(date)` |
| `neo4j-schema-03` | Re-running `CREATE CONSTRAINT IF NOT EXISTS` is idempotent (no error) |

### 2.2 Entity CRUD via `/ingest`
| Case | Setup | Assertions |
|---|---|---|
| `neo4j-ingest-01` | `POST /ingest` with `{"title":"TestIngestEntity","content":"Test content","tags":[],"sources":[]}` | 200; `nodes_created: 1`; `relationships_created: 0` |
| `neo4j-ingest-02` | Re-submit same title | 200; `nodes_created: 0`; `relationships_created: 0` (idempotent MERGE) |
| `neo4j-ingest-03` | Submit with `related: ["Bob Lazar"]` | 200; target node exists; relationship created |
| `neo4j-ingest-04` | Submit with invalid related target | 200; entity created; related target either created as stub or silently ignored (document behavior) |

### 2.3 Entity Query via `/graph/{entity}`
| Case | Assertions |
|---|---|
| `neo4j-graph-01` | `GET /graph/area-51` | 200; returns at least the `area-51` node + ≥ 1 neighbor or empty relationships |
| `neo4j-graph-02` | `GET /graph/TestIngestEntity` | 200; returns the test entity with its neighborhood |
| `neo4j-graph-03` | `GET /graph/` (empty name) | 404 or 422; no crash |

### 2.4 Reconciliation (`reconcile_neo4j_with_wiki`)
| Case | Assertions |
|---|---|
| `neo4j-reconcile-01` | Delete a wiki file; call any endpoint that triggers reconcile | Orphan Neo4j node for deleted file is pruned |
| `neo4j-reconcile-02` | Add a new wiki file; call reconcile | New node appeared in Neo4j with correct tags/sources |

### 2.5 Bulk Ingress `/ingest/bulk`
| Case | Gate | Assertions |
|---|---|---|
| `neo4j-bulk-01` | `RUN_DESTRUCTIVE_TESTS=true` | Wipes all Neo4j; re-ingests all wiki markdown files; `nodes_created` equals number of wiki files + stub relations |
| `neo4j-bulk-02` | `RUN_DESTRUCTIVE_TESTS=true` | After bulk, querying `/graph/area-51` still returns `area-51` node |

---

## 3. Redis Cache and Queue Tests

### 3.1 Cache Decorator Behavior
| Case | Assertions |
|---|---|
| `redis-cache-01` | Call cached endpoint twice with Redis up | Second call hits cache (observe via log or timing) |
| `redis-cache-02` | Stop Redis; call cached endpoint | No exception; returns fallback data |
| `redis-cache-03` | `POST /config/llm` (invalidates cache); immediately call cached function | Cache miss observed |

### 3.2 Conversation Storage
| Case | Input | Assertions |
|---|---|---|
| `redis-conv-01` | `POST /query` with `conversation_id: "test-abc-123"` | Response has `conversation_id`; `GET /conversation/test-abc-123` returns the message |
| `redis-conv-02` | Second `POST /query` with same `conversation_id` | `GET /conversations` lists it; `message_count: 2` |
| `redis-conv-03` | Wait beyond 7-day TTL | Entry expired; `GET /conversation/test-abc-123` returns empty |

### 3.3 Staleness Queue
| Case | Gate | Assertions |
|---|---|---|
| `redis-staleness-01` | `RUN_PULSE_INTEGRATION_TESTS=true` | `record_pulse_completed("test-slug")`; `ZRANGE staleness:queue 0 -1 WITHSCORES` contains `test-slug` |
| `redis-staleness-02` | `RUN_PULSE_INTEGRATION_TESTS=true` | `get_next_batch(1)` after recording returns list with `test-slug` |
| `redis-staleness-03` | `RUN_PULSE_INTEGRATION_TESTS=true` | `rebuild_queue()` size equals count of all `.md` files in `entities/`, `concepts/`, `projects/` |

### 3.4 Budget Hold Circuit Breaker
| Case | Gate | Assertions |
|---|---|---|
| `redis-budget-01` | `RUN_DESTRUCTIVE_TESTS=true` | Set `budget:YYYY-MM:hold`; call billable endpoint; response indicates `budget_exceeded` or hold state |
| `redis-budget-02` | — | `GET /budget/status` returns `BudgetStatus` with correct types |

### 3.5 Idle Sentinel State
| Case | Assertions |
|---|---|
| `redis-idle-01` | No activity; wait 10 minutes | `is_idle()` returns `True` |
| `redis-idle-02` | `update_activity("query")` | `is_idle()` returns `False` |
| `redis-idle-03` | `update_activity("tribunal","start")` | `is_idle()` returns `False` |
| `redis-idle-04` | After `update_activity("tribunal","end")` | `is_idle()` returns `True` |
| `redis-idle-05` | Set `chat_ingest` key to `"running"` | `is_idle()` returns `False` |
| `redis-idle-06` | Redis down | `is_idle()` returns `True`; no exception |
| `redis-idle-07` | Run `is_idle()` 100 times | Zero `WARNING:chickensoup.idle_sentinel:Error checking idle status` log lines |

---

## 4. LLM Integration Tests (Real, Non-Mock)

> Gate: `LLM_ACTIVE_PROVIDER` set to a real provider (not `simulated`). Timeout 30s per LLM test.

### 4.1 `QueryAgent.classify_and_parse()`
| Case | Input | Assertions |
|---|---|---|
| `llm-classify-01` | `"deep-research Bob Lazar"` | `intent` in `["enrich","query"]`; `entities: ["Bob Lazar"]`; `confidence: ≥ 0.5` |
| `llm-classify-02` | `"pulse Area 51"` | `entities: ["Area 51"]` |
| `llm-classify-03` | `"navigate from Earth to Alpha Centauri in 1965"` | `intent: "navigate"`; `structured_filters` contains `{"year": 1965}` |
| `llm-classify-04` | `""` (empty) | Non-empty `entities` or `intent` from TQL fallback; no crash |
| `llm-classify-05` | Gibberish | `intent: "query"`; `confidence: 0.5`; no timeout crash |

### 4.2 `ResearchAgent.run_research()` via `/query`
| Case | Assertions |
|---|---|
| `llm-research-01` | `deep-research Bob Lazar`; poll to success | `result.summary` non-empty; `result.entities` contains Bob Lazar; `result.credibility_scores` contains `bob-lazar` |
| `llm-research-02` | Summary contains markdown | Has `##` headers, `|` tables, or `**bold**` |
| `llm-research-03` | `result.research_details.assembled_context` | Non-empty block containing Neo4j entity data |
| `llm-research-04` | Multi-entity query | `result.entities` contains both; summary addresses both |
| `llm-research-05` | `LAST30DAYS_ENABLED=false` | Background task returns success; no pulse integration invoked |

### 4.3 `IngestAgent.analyze_content()` via `/ingest/analyze`
| Case | Assertions |
|---|---|
| `llm-ingest-01` | Submit `bob-lazar.md` body | `success: true`; `suggested_pages` list; at least 1 item with `confidence ≥ 0.5` |
| `llm-ingest-02` | Submit gibberish | `success: true` or graceful; `confidence ≤ 0.5` |
| `llm-ingest-03` | Submit empty string | 200 or 422; no crash |

### 4.4 `TribunalAgent.run_tribunal()` via `/entities/{name}/tribunal`
| Case | Assertions |
|---|---|
| `llm-tribunal-01` | `POST /entities/Bob Lazar/tribunal` with body | 200/500; JSON; no unhandled exception |
| `llm-tribunal-02` | Verify 4 LLM calls in logs | Exactly 4 LLM calls emitted |
| `llm-tribunal-03` | LLM returns inconsistent JSON | `state_label` and `disagreement_score` present; fallback state used |

### 4.5 LLM Failure Fallbacks
| Case | Simulation | Assertions |
|---|---|---|
| `llm-fallback-01` | Stop LLM provider; call `/query` | 200; non-empty `answer` (heuristic); no 500 |
| `llm-fallback-02` | Stop LLM; call `/ingest/analyze` | `success: true`; `confidence ≤ 0.5`; fallback stub suggested |
| `llm-fallback-03` | LLM returns 500 | All agents recover gracefully; no unhandled exception |

---

## 5. `last30days` CLI Integration Tests

> Gate: `RUN_PULSE_INTEGRATION_TESTS=true`. Binary must be reachable.

### 5.1 Binary Resolution
| Case | Setup | Assertions |
|---|---|---|
| `l30d-binary-01` | `LAST30DAYS_BINARY_PATH` set correctly | `PulseAgent._resolve_binary()` returns path |
| `l30d-binary-02` | `LAST30DAYS_BINARY_PATH` wrong; fallback chain | Returns path in `last30days-skill/` then `npx`; warns but no crash |
| `l30d-binary-03` | All resolution paths fail | Returns `None` or raises; subsequent pulse returns `status: "error"` |

### 5.2 Pulse Execution
| Case | Input | Assertions |
|---|---|---|
| `l30d-pulse-01` | `POST /pulse/Area 51` with correct binary | 200; `result.status` in `["success","no_data","budget_exceeded","disabled","error"]` |
| `l30d-pulse-02` | `LAST30DAYS_ENABLED=false`; `POST /pulse/Area 51` | 200; `result.status: "disabled"` |
| `l30d-pulse-03` | `LAST30DAYS_ENABLED=true` but binary missing | `result.status: "error"`; `error` field present |
| `l30d-pulse-04` | Binary hangs (exceeds timeout) | Process killed; `result.status: "error"`; no zombie process |

### 5.3 Evidence Parsing
| Case | Assertions |
|---|---|
| `l30d-evidence-01` | Check pulse with evidence | `evidence_count ≥ 1`; each has `claim_text`, `source_platform`, `engagement_count` |
| `l30d-evidence-02` | Check `source_platform` values | In known set: `reddit`, `x`, `youtube`, `news`, `github`, `polymarket` |
| `l30d-evidence-03` | Cross-contamination filter | No evidence references different entity |
| `l30d-evidence-04` | Hiring signal filter | Non-org entity has no hiring-related claims |

### 5.4 Pulse Snapshot Write
| Case | Assertions |
|---|---|
| `l30d-snapshot-01` | After successful pulse | `wiki/raw/pulse/{slug}-{date}.json` and `.md` exist; JSON has correct `evidence_count` |
| `l30d-snapshot-02` | Re-run pulse same day | JSON overwritten; MD regenerated; no `-1` suffix |
| `l30d-snapshot-03` | Calendar rollover | New filename uses new date; old file untouched |

---

## 6. File System Write Path Tests

### 6.1 Wiki Page Write (`write_page`)
| Case | Setup | Assertions |
|---|---|---|
| `fs-wiki-01` | Ingest new entity `SmokeTestEntity1` | `wiki/entities/smoke-test-entity1.md` exists; has YAML frontmatter with `title`, `tags`, `sources`, `created`, `updated` |
| `fs-wiki-02` | Ingest with `tags=["a","b"]`, `sources=["src1"]` | Frontmatter `tags` contains both; `sources` contains `src1` |
| `fs-wiki-03` | Ingest same entity twice | Second write overwrites first; `updated` changes; `created` stays original |
| `fs-wiki-04` | Delete entity with `hard=true` | File moved to `backups/auto/wiki-{ts}.zip` or deleted; `GET /wiki/page/slug` returns empty or 404 |
| `fs-wiki-05` | Frontmatter `protected: true`; attempt delete without `force=true` | 403; file not deleted |
| `fs-wiki-06` | Tag page with `eng-*`; attempt delete | 403; never-deleted |

### 6.2 Pulse Snapshot Write
| Case | Assertions |
|---|---|
| `fs-pulse-01` | Write pulse for `SmokeTestEntity1` | `wiki/raw/pulse/smoke-test-entity1-{today}.json` and `.md` exist; MD has `# Pulse: {entity_name}` header |
| `fs-pulse-02` | Calendar rollover test | New filename uses new date; old file untouched |

### 6.3 Index and Log Updates
| Case | Assertions |
|---|---|
| `fs-index-01` | After creating entity | `wiki/index.md` contains `[[smoke-test-entity1]]` |
| `fs-log-01` | After pulse | `wiki/log.md` contains entry with date and entity name |
| `fs-log-02` | Log entry | Includes `sources:` list and `related:` `[[wikilinks]]` |

### 6.4 Backup Export/Import
| Case | Assertions |
|---|---|
| `fs-backup-01` | `GET /wiki/export` | Returns zip; file size > 0; contains `entities/`, `concepts/`, `projects/` |
| `fs-backup-02` | `POST /wiki/clear-content?confirm=true`; `POST /wiki/import` with exported zip | Entity count restored to original value |

### 6.5 PDF Ingest
| Case | Gate | Assertions |
|---|---|---|
| `fs-pdf-01` | `papers/2408.14391v7.pdf` exists | `POST /ingest/pdf-folder` processes file; `pdfs_processed: 1` |
| `fs-pdf-02` | After PDF ingest | `wiki/entities/ginestra-bianconi.md` exists; `wiki/raw/2408.14391v7.pdf` exists |
| `fs-pdf-03` | Non-PDF file via `/ingest/pdf-folder` | File skipped or `pdfs_processed` not incremented; no crash |

---

## 7. Agent Behavior and Orchestration Tests

### 7.1 Orchestrator Graph Transitions
| Case | Input | Assertions |
|---|---|---|
| `orch-01` | `POST /query` "What is entropic gravity?" | `ClassifyNode` → `ResearchNode`; response has `answer`; no `task_id` |
| `orch-02` | `POST /query` "deep-research Bob Lazar" | `ClassifyNode` → `EnrichNode`; response has `task_id`; task completes |
| `orch-03` | `POST /query` "navigate to Area 51 and back" | `ClassifyNode` → `NavigateNode`; response has `success:true` |
| `orch-04` | `POST /query` "What is your status?" | `ClassifyNode` → `StatusNode`; response has `status` field |
| `orch-05` | Multi-entity query | Both entities in `entities` list |
| `orch-06` | Ambiguous query with `confidence < 0.6` | Falls back to `ResearchNode`; response still has `answer` |

### 7.2 LangGraph Checkpoint and Threading
| Case | Assertions |
|---|---|
| `orch-langgraph-01` | `EnrichNode` task thread_id matches `conversation_id` from `/query` | Same UUID |
| `orch-langgraph-02` | If `human_approval_required=true`; call `POST /research/{thread_id}/approve` | Graph resumes; task transitions to `success` |
| `orch-langgraph-03` | `POST /research/{thread_id}/approve` on completed task | 404 with `"No paused research..."` |

### 7.3 ResearchAgent Wavefunction Scoring
| Case | Assertions |
|---|---|
| `orch-wave-01` | Entity with pulse evidence | `credibility_scores[slug]` float `[0,1]`; not exactly `0.5` |
| `orch-wave-02` | Entity with no pulse evidence | `wavefunction_scores: {}` |
| `orch-wave-03` | `state_label` in result | One of `["corroborated","contested","unverified"]` |

### 7.4 WebSocket Streaming
| Case | Setup | Assertions |
|---|---|---|
| `ws-01` | Connect `/ws/agent`; send plain text | First message is `processing`; last message is `completed` |
| `ws-02` | Stream contains `conversation_id` | Last message has non-empty `conversation_id` |
| `ws-03` | Stream contains word chunks | At least one message has `chunk` field before `completed` |
| `ws-04` | Disconnect mid-stream | Server handles `WebSocketDisconnect`; no unhandled exception |

---

## 8. Idle Sentinel and Background Ingestion Loop Tests

### 8.1 Scheduler Startup
| Case | Assertions |
|---|---|
| `sched-startup-01` | Server log on startup | `periodic_chat_ingest_loop started` and `idle_ingestion_loop started` present |
| `sched-startup-02` | With `LAST30DAYS_ENABLED=false` | `idle_ingestion_loop` starts but skips work |

### 8.2 Idle Sentinel Accuracy
| Case | Setup | Assertions |
|---|---|---|
| `idle-01` | No activity; wait 10 minutes | `is_idle()` returns `True` |
| `idle-02` | `update_activity("query")` | `is_idle()` returns `False` within 1s |
| `idle-03` | `update_activity("query")` then wait 6 minutes | `is_idle()` returns `True` (default threshold 5 min) |
| `idle-04` | Activity from 4 minutes ago | `is_idle()` returns `False` |
| `idle-05` | `update_activity("tribunal","start")` | `is_idle()` returns `False` |
| `idle-06` | Then `update_activity("tribunal","end")` | `is_idle()` returns `True` |
| `idle-07` | Set `chat_ingest` key to `"running"` | `is_idle()` returns `False` |
| `idle-08` | Redis down | `is_idle()` returns `True`; no exception |

### 8.3 Chat Ingest Loop
| Case | Assertions |
|---|---|
| `chat-ingest-01` | Generate ≥ 10 messages in conversation; wait 5 min | Loop processes conversation; wiki page or log entry created |
| `chat-ingest-02` | Trigger `/chat/ingest/now` | Returns process result; `GET /chat/ingest/status` shows non-zero stats |
| `chat-ingest-03` | `GET /chat/ingest/status` | Returns all stats fields |

### 8.4 Idle-Driven Ingestion Loop
| Case | Gate | Assertions |
|---|---|---|
| `idle-ingest-01` | `RUN_PULSE_INTEGRATION_TESTS=true`; system idle 20s | Logs "Processing batch"; ≥ 1 pulse triggered |
| `idle-ingest-02` | Trigger any query during idle loop | Loop detects `!is_idle()` and yields |

### 8.5 Idle Sentinel `.decode()` Regression
| Case | Assertions |
|---|---|
| `idle-decode-01` | `redis.from_url(..., decode_responses=True)` | All `.get()` return `str`; `.decode()` raises `AttributeError` |
| `idle-decode-02` | Run `is_idle()` 100 times | Zero `WARNING:chickensoup.idle_sentinel:Error checking idle status` lines |

---

## 9. Error Injection and Chaos Tests

### 9.1 Neo4j Unavailable
| Case | Setup | Assertions |
|---|---|---|
| `chaos-neo4j-01` | Stop Neo4j; `POST /query` | 200 or 500; graceful JSON; no unhandled exception |
| `chaos-neo4j-02` | Stop Neo4j; `GET /graph/area-51` | Returns error JSON or empty; no 500 with traceback |

### 9.2 Redis Unavailable
| Case | Assertions |
|---|---|
| `chaos-redis-01` | Stop Redis; `POST /query` | 200; `answer` non-empty; no crash |
| `chaos-redis-02` | Stop Redis; `POST /query` with `conversation_id` | 200; conversation not stored (Redis unavailable) |
| `chaos-redis-03` | Stop Redis; restart; `GET /conversation/{stale_id}` | Returns empty (expired) |

### 9.3 LLM Provider Unavailable
| Case | Assertions |
|---|---|
| `chaos-llm-01` | Stop LLM provider; `POST /query` | 200; non-empty `answer` (heuristic fallback); no 500 |
| `chaos-llm-02` | Stop LLM; `/ingest/analyze` | `success: true`; `confidence ≤ 0.5`; fallback stub |
| `chaos-llm-03` | LLM returns 500 | All agents recover; no unhandled exception |

### 9.4 `last30days` Binary Failure
| Case | Setup | Assertions |
|---|---|---|
| `chaos-l30d-01` | `LAST30DAYS_BINARY_PATH` non-existent; pulse | `result.status: "error"`; `error` field present; wiki updated with `no_data`/`error` |
| `chaos-l30d-02` | Binary hangs | Process killed after timeout; `result.status: "error"`; no zombie |

### 9.5 Disk Full / Write Permission Denied
| Case | Setup | Assertions |
|---|---|---|
| `chaos-disk-01` | Make `wiki/` read-only; enrich via `/query` | 500 or graceful error; exception logged; no zombie task |
| `chaos-disk-02` | Make `wiki/raw/pulse/` read-only; pulse | `result.status: "error"` or `"no_data"`; error logged |

### 9.6 Malformed Input / Injection
| Case | Input | Assertions |
|---|---|---|
| `chaos-input-01` | `{"query":"<script>alert(1)</script>"}` | 200; JSON response; no XSS; `answer` contains safe escaped string |
| `chaos-input-02` | `{"query":"'; DROP TABLE entities; --"}` | 200; Neo4j safe (parameter binding); no data loss |
| `chaos-input-03` | `{"title":"../../etc/passwd","content":"x","tags":[],"sources":[]}` | Path sanitized or safely namespaced; no `/etc/passwd` write |
| `chaos-input-04` | `GET /wiki/page/../admin/delete` | 404 or slug sanitized; no files outside `wiki/` touched |

---

## 10. Performance and Throughput Benchmarks

### 10.1 Single-Request Latency (p95)
| Endpoint | Expected p95 |
|---|---|
| `GET /status` | 200ms |
| `POST /query` (normal, cached) | 1s |
| `POST /query` (LLM miss, heuristic) | 500ms |
| `POST /query` (enrich task creation) | 500ms |
| `GET /tasks/{recent_id}` | 100ms |
| `GET /almanac/summary` | 500ms |
| `GET /pulse/history` | 300ms |
| `GET /wiki/pages` | 500ms |

### 10.2 Concurrent Requests
| Case | Setup | Assertions |
|---|---|---|
| `perf-concurrent-01` | Fire 20 concurrent `POST /query` normal | All return 200; no deadlocks; no worker crash |
| `perf-concurrent-02` | Fire 5 concurrent `POST /query` enrich | All return with distinct `task_id`; no task collision |
| `perf-concurrent-03` | Fire 10 concurrent `GET /status` while Neo4j busy | All return 200; `neo4j_connected` reflects true state |

### 10.3 Cache Effectiveness
| Case | Assertions |
|---|---|
| `perf-cache-01` | Call `/config/llm/probe` 100 times with Redis up | Response time drops after first call; 100% success |
| `perf-cache-02` | Call `/config/llm/probe` 100 times with Redis down | All return 200; consistent response time |

### 10.4 Memory and Resource Leaks
| Case | Assertions |
|---|---|
| `perf-leak-01` | Run 100 `POST /query` requests; monitor memory | No unbounded growth (≤ 50MB increase) |
| `perf-leak-02` | Run 50 pulse tasks | No zombie `last30days` processes after timeout |

---

## 11. Swift ↔ Backend API Contract Tests

> Gate: Verify JSON shapes match `APIModels.swift` and `BackendService.swift`.

### 11.1 `QueryResponse` Shape
| Case | Assertions |
|---|---|
| `swift-contract-01` | `POST /query` response | Keys: `query`, `answer`, `confidence`, `entities`, `sources`, `inferred_events`, `inferred_entities`, `conversation_id`, `history`, `claim_confidences`, `source_tier`, `task_id` |
| `swift-contract-02` | Types correct | `confidence` is number (not string); `entities` is array of strings; `conversation_id` is non-empty string |

### 11.2 `TaskStatusResponse` Shape
| Case | Assertions |
|---|---|
| `swift-contract-03` | `GET /tasks/{id}` response | Keys: `id`, `name`, `status`, `progress`, `logs`, `result`, `elapsed` |
| `swift-contract-04` | `status` is one of `["running","success","failed","paused","cancelled"]` |
| `swift-contract-05` | `result` when success | Has `status: "completed"`, `answer`, `entities`, `confidence`, `sources` |

### 11.3 `WikiPageDetailResponse` Shape
| Case | Assertions |
|---|---|
| `swift-contract-06` | `GET /wiki/page/area-51` response | Keys: `success`, `slug`, `title`, `page_type`, `tags`, `sources`, `related`, `body`, `created`, `updated`, `protected`, `divergence`, `claim_confidences` |

### 11.4 `AlmanacSummaryResponse` Shape
| Case | Assertions |
|---|---|
| `swift-contract-07` | `GET /almanac/summary` response | Keys: `date`, `contested_claims`, `newly_contested`, `entities_processed` |

### 11.5 WebSocket Message Shape
| Case | Assertions |
|---|---|
| `swift-contract-08` | Connect `/ws/agent` | First message has `status` key; chunk messages have `chunk`; final message has `status: "completed"` plus `answer`, `confidence`, `entities`, `conversation_id`, `history` |

### 11.6 Error Response Shape
| Case | Assertions |
|---|---|
| `swift-contract-09` | 404 response | `{"detail":"..."}` |
| `swift-contract-10` | 500 response | JSON with `detail` or `error`; no HTML error page |
| `swift-contract-11` | 422 validation error | JSON with `detail`; field-level errors in standard FastAPI format |

---

## 12. Regression Tests for Known Fixed Bugs

| Case | Description | Assertions |
|---|---|---|
| `reg-01` | **idle decode bug** | Zero `'str' object has no attribute 'decode'` warnings in logs after 10 `is_idle()` calls |
| `reg-02` | **pulse write bug** | `write_pulse_snapshot()` does not raise "unexpected keyword argument 'claims'"; JSON and MD files written; task returns `success` |
| `reg-03` | **wiki frontmatter bug** | EnrichNode writes proper wiki page via `write_page()` with YAML frontmatter, not raw `Path.write_text()` |
| `reg-04` | **conversation_id missing** | `POST /query` and WS return non-empty `conversation_id` |
| `reg-05` | **missing task_id** | Enrich query returns non-null `task_id` |
| `reg-06` | **almanac empty entities_processed** | `GET /almanac/summary` when no almanac files: 200; `entities_processed: []` |
| `reg-07` | **semantic disambiguation** | `pulse_agent.py` semantic filter matches tokenized fields; no cross-contamination |
| `reg-08` | **semantic hiring filter** | Pulse for `Area 51` does not return hiring-related claims |
| `reg-09` | **iOS ditto Process** | `DataStoreBackupService` does not reference unavailable `Process` on iOS; Swift build succeeds |
| `reg-10` | **staleness queue scan** | `rebuild_queue()` scans `entities/`, `concepts/`, `projects/`; queue size matches total `.md` count |

---

## 13. Data Integrity and Edge Cases

### 13.1 Unicode and Special Characters
| Case | Input | Assertions |
|---|---|---|
| `unicode-01` | `POST /query` with `"deep-research 北京"` | 200; no crash; `entities` contains `"北京"` or transliterated |
| `unicode-02` | `POST /ingest` with `title: "Café Résumé"` | File `cafe-resume.md` created; frontmatter preserves title |
| `unicode-03` | `POST /query` with `"navigate to 🌍 in 3000"` | 200; no crash; `year: 3000` extracted |

### 13.2 Very Long Inputs
| Case | Input | Assertions |
|---|---|---|
| `long-01` | `POST /query` with 10,000 chars | 200 or 422; no worker crash; response time < 30s |
| `long-02` | `POST /ingest` with 1 MB `content` | 200 or 413; no worker crash |

### 13.3 Concurrent Modification
| Case | Setup | Assertions |
|---|---|---|
| `concMod-01` | Two concurrent `POST /ingest` with same title | Both return 200; final file has content from one of them; no corruption |

### 13.4 Timezone Handling
| Case | Assertions |
|---|---|
| `tz-01` | All timestamps in API responses | ISO 8601 with timezone (`+00:00` or `Z`) |
| `tz-02` | Pulse snapshot `timestamp` field | ISO 8601 with timezone; parseable by `datetime.fromisoformat()` |
| `tz-03` | `/entities/{name}/timeline` dates | ISO 8601; ordering is chronological |

---

## 14. Authentication and Authorization

### 14.1 Dev Mode (no API key)
| Case | Assertions |
|---|---|
| `auth-01` | Server with `API_KEY=""` | All endpoints return 200 without `X-Api-Key` |
| `auth-02` | Server with `API_KEY="secret123"` | `POST /query` without key → 401 |
| `auth-03` | Server with `API_KEY="secret123"` | `POST /query` with wrong key → 401 |
| `auth-04` | Server with `API_KEY="secret123"` | `POST /query` with correct key → 200 |
| `auth-05` | GET endpoints with `API_KEY="secret123"` | Accessible without key (read-only open by design) |

---


## 15. New Feature Smoke Tests (added 2026-07-14)

### 15.1 Fulltext Search (Phase 1)
| Test | Endpoint | Expected |
|---|---|---|
| `search-01` | `GET /search?q=bob+lazar&limit=3` | 200, `total > 0`, results sorted by `score` descending |
| `search-02` | `GET /search?q=a` | 422 (min length 2) |
| `search-03` | `GET /search?q=xyznonexistent` | 200, `total == 0`, `results == []` |
| `search-04` | `GET /search` (no q param) | 422 |

### 15.2 Events (Phase 1)
| Test | Endpoint | Expected |
|---|---|---|
| `events-01` | `GET /events` | 200, each event has `id`, `title`, `description`, `date`, `confidence`, `source`, `type`, `sources` |
| `events-02` | `GET /events` | No hardcoded fabricated timestamps in response |

### 15.3 Timeline (Phase 3)
| Test | Endpoint | Expected |
|---|---|---|
| `timeline-01` | `GET /timeline` | 200, `events` array sorted by `date` ascending |
| `timeline-02` | `GET /timeline?start_date=2020-01-01&end_date=2025-01-01` | 200, respects date range |
| `timeline-03` | `GET /timeline/range` | 200, has `earliest`, `latest`, `total` |
| `timeline-04` | `GET /entities/{name}/temporal-context` | 200, events connected to entity |

### 15.4 Rate Limiting (Phase 5)
| Test | Endpoint | Expected |
|---|---|---|
| `ratelimit-01` | 61x `GET /search?q=test` | Requests 61+ return 429 with `search` in message |
| `ratelimit-02` | 11x `POST /ingest/bulk` | Requests 11+ return 429 with `write` in message |

### 15.5 Approval Flow (Phase 6)
| Test | Endpoint | Expected |
|---|---|---|
| `approve-01` | `POST /query` (low credibility) | `status == "paused_for_human_approval"`, `thread_id` present |
| `approve-02` | Response from approve-01 | Has `status` and `thread_id` fields |
| `approve-03` | `POST /research/nonexistent/approve` | 404 |
| `approve-04` | `POST /research/default_thread/approve` | 400 (not paused) |

### 15.6 Streaming WebSocket (Phase 6)
| Test | Endpoint | Expected |
|---|---|---|
| `ws-01` | `ws://host:8000/ws/agent` | Accepts connection, returns processing status |
| `ws-02` | Send query via ws-01 | Receives `processing`, `streaming` chunks, `completed` |
| `ws-03` | Send invalid data to ws-01 | Returns `error` status |

### 15.7 Space-Time Simulator (Phase 7)
| Test | Endpoint | Expected |
|---|---|---|
| `sim-01` | `POST /simulate` with all params | 200, `success == true`, `logs` non-empty |
| `sim-02` | `POST /simulate` with empty body | 200, uses defaults |
| `sim-03` | `POST /simulate` with `gravity: 99` | 422 |
| `sim-04` | `POST /simulate` | Response has all 10 expected fields |

### 15.8 Server Time (Phase 0)
| Test | Endpoint | Expected |
|---|---|---|
| `time-01` | `GET /status/time` | Has `iso8601`, `unix`, `datetime`, `timezone`, `utc_offset`, `utc_iso8601` |
| `time-02` | `GET /status/time` | `unix > 1700000000` |
| `time-03` | `GET /status/time` | `timezone` non-empty |

### 15.9 SSE Notifications (Phase 4)
| Test | Endpoint | Expected |
|---|---|---|
| `sse-01` | `GET /events/stream` | 200, `content-type: text/event-stream` |
| `sse-02` | Trigger ingest while connected to sse-01 | Receives `entity_updated` event |
| `sse-03` | Wait 30s on sse-01 stream | Receives `heartbeat` event |

### 15.10 Neo4j Resilience (Phase 10)
| Test | Endpoint | Expected |
|---|---|---|
| `neo4j-01` | `GET /health` | `checks.neo4j.ok == true` |
| `neo4j-02` | Kill Neo4j, make 3 failing requests | Health shows Neo4j degraded |
| `neo4j-03` | Restart Neo4j, wait 30s | Health recovers |

### 15.11 Cloud LLM Provider (Cloud)
| Test | Endpoint | Expected |
|---|---|---|
| `cloud-01` | `GET /config` | Has `llm_provider_type`, `nvidia_api_key_set`, `openrouter_api_key_set`, `custom_llm_api_url_set` |
| `cloud-02` | `POST /config/llm/probe` with `{"provider_name": "nvidia"}` | `available: true`, models non-empty |

---

## 16. Observability and Logging

### 16.1 OpenTelemetry Spans
## 15. Observability and Logging

### 15.1 OpenTelemetry Spans
| Case | Assertions |
|---|---|
| `otel-01` | Each HTTP request | Span named `http_request_{METHOD}_{path}` exists |
| `otel-02` | LLM call span | Named `llm_chat_completion`; has `model` attribute |

### 15.2 Log Integrity
| Case | Assertions |
|---|---|
| `log-01` | After pulse | `wiki/log.md` contains new entry with correct date format |
| `log-02` | `/events` endpoint | Returns JSON list; no crash on empty dataset |
| `log-03` | Server error (malformed request) | Error logged with stack trace; no raw exception in response |

---

## 16. Gap Analysis and Improvement Areas

### 16.1 Missing Test Coverage (gaps found during execution)
| Surface | Gap |
|---|---|
| `WebSocket binary frames` | WS tests only cover text frames |
| `Celery worker` | No test validates Celery task execution (`async_navigate.delay`) |
| `FastMCP server (port 8001)` | No test validates MCP tool endpoints |
| `Quantum simulation` | No test validates Qiskit/PennyLane/CUDA-Q fallback chain |
| `Multi-LLM consensus` | `MultiLLMConsensus` is dead code; no test confirms removal or wiring |
| `Budget ledger` | No test validates free-tier hourly rollover (`resource_ledger`) |
| `Draft promotion flow` | No end-to-end test writes draft → promotes → verifies frontmatter |
| `Wiki backup/restore` | No test validates backup restore on different server instance |
| `Swift UI BackendService` | No test validates Swift `AlmanacService.fetchPulseHistory` poll loop |
| `Conversation snapshot export` | `_save_conversation_snapshot` not tested end-to-end |
| `Almanac generator full run` | No test validates HTML output contains contested/entanglement data |
| `Wavefunction scoring edge cases` | No test for exactly `0.0` or `1.0` credibility scores |
| `Idle sentinel preemption during pulse` | No test validates `idle_ingestion_loop` stops mid-pulse when activity occurs |

### 16.2 Known Brittle Code
| Location | Issue |
|---|---|
| `src/agents/orchestrator.py:229` | Fixed in this session: `write_pulse_snapshot()` called with obsolete kwargs. Verify no other call sites are stale. |
| `src/idle_sentinel.py:88` | `except Exception` catches all errors including `TypeError` from `.decode()`; broad swallow. Should narrow exception type. |
| `src/staleness_queue.py:97` | `el.decode() if isinstance(el, bytes) else el` — defensive but correct; verify no regression if Redis version changes |
| `src/main.py:924` | `content_bytes.decode("utf-8")` on `urllib.request` response — safe because `read()` returns bytes |
| `src/scheduler.py:59,83` | Same defensive decode pattern as staleness_queue |
| `/tasks/{task_id}` | In-memory registry; tasks lost on server restart. No persistence. Consider Redis or DB backing. |

### 16.3 Production Readiness Checklist
- [ ] All 56 endpoints return consistent error shapes (`{"detail": "..."}`)
- [ ] No endpoint leaks raw Python exceptions to client
- [ ] All file writes use `try/except` with proper rollback or error logging
- [ ] `LAST30DAYS_PULSE_TIMEOUT_SECONDS` enforced by subprocess
- [ ] Worker pool size configured for concurrent `last30days` processes
- [ ] Neo4j query timeouts configured
- [ ] Redis maxmemory policy configured
- [ ] Rate limiting on `/query` (per-IP or per-API-key)
- [ ] Input size limits enforced on all body fields
- [ ] Path traversal prevention on `/wiki/page/{slug}` (slug sanitization)
- [ ] `multi_llm_consensus` either removed or wired into production path
- [ ] FastMCP server has same auth as main API
- [ ] `.env` secrets not logged or returned in API responses
- [ ] Wiki frontmatter `protected` field checked in all delete/mutation paths
- [ ] Almanac generation does not block request (`BackgroundTasks`)
- [ ] `Human approval gate` checkpointer persists across restarts (currently in-memory `MemorySaver`)
- [ ] All `asyncio.create_task` calls have error handling

---

## 17. Test Execution Checklist

Run in order. Mark each as complete.

```
PHASE 1: Environment & Contract
  [ ] 0.1 Environment pre-checks
  [ ] 1.1–1.20 API contract tests

PHASE 2: Data Layer
  [ ] 2.1–2.5 Neo4j integration tests
  [ ] 3.1–3.5 Redis cache/queue tests

PHASE 3: Intelligence Layer
  [ ] 4.1–4.5 LLM integration tests (real, non-mock)
  [ ] 5.1–5.4 last30days CLI tests

PHASE 4: Pipeline & Agents
  [ ] 6.1–6.5 File system tests
  [ ] 7.1–7.4 Agent behavior tests
  [ ] 8.1–8.5 Idle sentinel and background loop tests

PHASE 5: Resilience
  [ ] 9.1–9.6 Chaos and error injection tests
  [ ] 10.1–10.4 Performance benchmarks

PHASE 6: Contract & Regression
  [ ] 11.1–11.6 Swift ↔ Backend API contract tests
  [ ] 12.1–12.10 Regression tests for known bugs
  [ ] 13.1–13.4 Data integrity and edge cases

PHASE 7: Security & Ops
  [ ] 14.1–14.5 Auth and authorization tests
  [ ] 15.1–15.3 Observability and logging tests

PHASE 8: Report
  [ ] Compile gap analysis (16.1)
  [ ] Document brittle code (16.2)
  [ ] Run production readiness checklist (16.3)
  [ ] Write final report with `passed`, `failed`, `skipped`, `duration`
```

---

## 18. Test Execution Script Interface

### 18.1 Environment Variables
```bash
# Required
CHICKENSOUP_BASE_URL=http://localhost:8000
CHICKENSOUP_API_KEY=dev

# Gated (opt-in)
RUN_DESTRUCTIVE_TESTS=true          # Allows wipes, deletes, bulk re-ingest
RUN_PULSE_INTEGRATION_TESTS=true    # Allows last30days binary invocation
LLM_REAL_PROVIDER=true              # Skips tests that require live LLM

# Test identifiers
TEST_RUN_ID=smoke-2026-07-13-001    # Prefixes all Redis keys and file writes
```

### 18.2 Orchestration Script (`scripts/run_smoke_tests.py`)
- Reads `TEST_RUN_ID`; prepends to all Redis keys.
- Creates temp directory under `/tmp/chickensoup-smoke-test-{TEST_RUN_ID}/` for any write artifacts.
- Captures server logs to `logs/smoke-test-{TEST_RUN_ID}.log`.
- Outputs JUnit XML to `reports/smoke-test-{TEST_RUN_ID}.xml`.
- Exits 0 if all pass, 1 if any fail, 2 if any SKIP blocks production readiness.

### 18.3 Halting Conditions
- If `CHICKENSOUP_API_KEY` is not `"dev"`, halt and prompt for confirmation.
- If `LAST30DAYS_COST_PER_PULL_USD > 0.50` and `RUN_PULSE_INTEGRATION_TESTS=true`, prompt for cost confirmation.
- If any endpoint returns 500 three times in a row, halt and report.
- If disk usage on `wiki/` exceeds 90% of available, halt before write tests.

---

## Appendix A: Quick Reference — Key Config Variables

| Variable | Default | Effect on Tests |
|---|---|---|
| `LAST30DAYS_ENABLED` | `false` | Set `true` for pulse integration tests |
| `LAST30DAYS_BINARY_PATH` | auto | Must point to runnable `last30days.py` |
| `LAST30DAYS_PULSE_TIMEOUT_SECONDS` | `120` | Pulse subprocess timeout |
| `IDLE_THRESHOLD_MINUTES` | `5` | Idle sentinel threshold |
| `CHAT_WIKI_CHECK_INTERVAL_SECONDS` | `300` | Chat ingest loop interval |
| `API_KEY` | `""` | Empty = dev mode (no auth required) |
| `REDIS_URL` | `redis://localhost:6379/0` | Redis connection |
| `NEO4J_URI` | `bolt://localhost:7687` | Neo4j connection |
| `LLM_ACTIVE_PROVIDER` | `omlx` | Must be reachable for LLM tests |
| `LLM_FALLBACK_CHAIN` | `omlx,ollama,lmstudio` | Fallback order |
| `BUDGET_HOLD_THRESHOLD_REMAINING` | `5.0` USD | Triggers hold |
| `ORCHESTRATOR_TIMEOUT_SECONDS` | `120` | Orchestrator graph timeout |
| `LAST30DAYS_MAX_CLAIMS_PER_PULSE` | `50` | Claim truncation limit |
| `DIVERGENCE_SPIKE_THRESHOLD` | `0.7` | Tribunal trigger threshold |
| `PERPLEXITY_API_KEY` | `""` | Enables paid last30days tier |
| `BRAVE_API_KEY` | `""` | Enables paid last30days tier |
| `XAI_API_KEY` | `""` | Enables paid last30days tier |

---

## Appendix B: Quick Reference — Known Response Shapes

### Successful `POST /query` (normal)
```json
{
  "query": "...",
  "answer": "markdown string",
  "confidence": 0.95,
  "entities": ["Entity Name"],
  "sources": ["Local Wiki Knowledge Graph"],
  "inferred_events": [],
  "inferred_entities": [],
  "conversation_id": "uuid",
  "history": [],
  "claim_confidences": [],
  "source_tier": "local",
  "task_id": null
}
```

### Successful `POST /query` (enrich)
```json
{
  "answer": "Started async enrichment for X...",
  ...same as above...,
  "task_id": "uuid"
}
```

### Successful `GET /tasks/{id}`
```json
{
  "id": "uuid",
  "name": "enrich:EntityName",
  "status": "success",
  "progress": 1.0,
  "logs": ["[HH:MM:SS] log entry"],
  "result": {
    "status": "completed",
    "answer": "markdown",
    "entities": [...],
    "confidence": 0.95,
    "sources": [...],
    "research_details": {
      "assembled_context": "...",
      "credibility_scores": {...},
      "wavefunction_scores": {},
      "summary": "..."
    }
  },
  "elapsed": 43.86
}
```

### Error Response (generic)
```json
{
  "detail": "Human-readable error message"
}
```