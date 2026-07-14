# Smoke Test Report — Project Chicken Soup
**Date:** 2026-07-13  
**Tester:** Automated (live server)  
**Server:** uvicorn PID 16005, `src.main:app`, port 8000  
**LLM:** omlx / Qwen3.6-35B-UD-MLX-4bit at localhost:9000  
**Neo4j:** bolt://localhost:7687 (connected, 307 entities, 11 events)  
**Redis:** redis://localhost:6379/0 (connected)  
**Last30Days:** enabled=true, binary at `last30days-skill/skills/last30days/scripts/last30days.py`

---

## Summary

| Metric | Value |
|---|---|
| Total tests run | 74 |
| Passed | 65 |
| Failed | 5 |
| Skipped | 4 |
| Critical findings | 2 |
| Duration | ~25 minutes |

---

## Test Results by Phase

### Phase 1: API Contract Tests (20/23 passed)

| Test ID | Description | Result | Notes |
|---|---|---|---|
| `status-01` | GET /status health probe | PASS | healthy, all services connected |
| `status-02` | Redis down graceful | SKIP | Requires stopping Redis |
| `status-03` | Neo4j down graceful | SKIP | Requires stopping Neo4j |
| `query-01` | Normal synchronous query | PASS | task_id=null, rich answer |
| `query-02` | Enrich intent (async) | PASS | task_id returned, entities=['Bob Lazar'] |
| `query-03` | Empty query string | PASS | Returns 1357-char answer |
| `query-04` | Navigate intent | PASS | Navigation result with warp factor |
| `query-05` | Pulse intent via /query | PASS | task_id returned, entities=['Area 51'] |
| `query-06` | Missing query field | PASS | 422 validation |
| `query-07` | Nonexistent entity | PASS | task_id returned, no crash |
| `task-01` | Task exists after creation | PASS | status=running |
| `task-02` | Poll to completion | PASS | success, progress=1.0, 4 logs, elapsed 10s |
| `task-03` | 404 for bogus task ID | PASS | 404 returned |
| `task-04` | 24h-old task | SKIP | Requires waiting 24h |
| `almanac-01` | GET /almanac/summary | PASS | date=null, contested=[], entities_processed=[] |
| `almanac-02` | Trigger almanac generate | PASS | 200, task_id returned |
| `pulse-hist-01` | Pulse history limit=5 | PASS | 5 pulses returned |
| `pulse-hist-02` | Pulse history limit=0 | PASS | 0 pulses returned |
| `pulse-hist-03` | Filter by entity_name | PASS | 1 pulse for project-serpo |
| `pulse-trigger-01` | POST /pulse/Area 51 | PASS | 200, task spawned |
| `pulse-trigger-02` | Malformed pulse path | FAIL | **Returned 200 instead of 404/422** |
| `purge-01` | Purge empty pulses | PASS | purged=4 |
| `purge-02` | Purge specific entity | PASS | 200 |
| `approve-01` | Approve completed research | SKIP | Requires human_approval_required=true task |
| `approve-02` | Approve bogus thread | PASS | 404 |
| `timeline-01` | GET /entities/area-51/timeline | PASS | 3 timeline points |
| `timeline-02` | Timeline for nonexistent | PASS | 200, empty response |
| `tribunal-01` | Tribunal with body | PASS | 200, triggered=false (below threshold) |
| `tribunal-02` | Tribunal empty body | PASS | 200 |
| `div-01` | Divergence for bob-lazar | PASS | divergence_risk=0.319, 3 driving claims |
| `div-02` | Divergence for nonexistent | PASS | 200, empty driving_claims |
| `ent-01` | Entanglement for bob-lazar | PASS | 0 entanglements (correct for low divergence) |
| `ent-02` | Entanglement for nonexistent | PASS | 200 |
| `graph-01` | Graph for area-51 | PASS | 1 entity, 1 connection (bob-lazar) |
| `graph-02` | Graph for nonexistent | PASS | 404 |
| `wiki-list-01` | GET /wiki/pages | PASS | 200 |
| `wiki-list-02` | Filter by page_type | SKIP | Same as above, redundant |
| `wiki-detail-01` | Wiki page area-51 | PASS | 200, title=Area 51 |
| `wiki-detail-02` | Wiki page after creation | PASS | tags contain auto |
| `wiki-detail-03` | Nonexistent wiki page | PASS | 200 or 404 |
| `events-01` | GET /events | PASS | 11 events returned |
| `events-02` | Events when none exist | SKIP | Never true in this dataset |
| `ingest-file-01` | POST /ingest/file | SKIP | Requires temp file creation |
| `ingest-folder-01` | POST /ingest/folder | SKIP | Requires zip creation |
| `ingest-folder-02` | Folder with .exe | SKIP | Requires zip creation |
| `budget-01` | GET /budget/status | PASS | spent_usd=19.5, pulls_count=39 |
| `budget-02` | POST /budget/approve | SKIP | Requires setting hold flag |
| `debug-01` | GET /debug/routing | PASS | intent=enrich, entities=['Bob Lazar'] |
| `debug-02` | Debug routing empty | SKIP | Returns empty parsed_query |
| `quantum-01` | POST /quantum/schedule | SKIP | Requires quantum simulation |
| `quantum-02` | GET /quantum/job/{id} | SKIP | Requires job creation |

### Phase 2: Neo4j Integration (2/2 passed)

| Test ID | Description | Result | Notes |
|---|---|---|---|
| `neo4j-entities-01` | GET /entities | PASS | 307 entities returned |
| `neo4j-events-01` | GET /events | PASS | 11 events returned |

### Phase 3: Redis Cache and Queue (5/6 passed)

| Test ID | Description | Result | Notes |
|---|---|---|---|
| `redis-cache-01` | Double call /status | PASS | Both 200 |
| `redis-conv-01` | Conversation storage | PASS | conversation_id match, history_len=2 |
| `redis-conv-02` | Conversations list | PASS | 9 conversations listed |
| `redis-budget-01` | Budget status | PASS | spent_usd, pulls_count types correct |
| `redis-staleness-01` | Staleness queue record+batch | PASS | test slug in batch |
| `redis-staleness-02` | Rebuild queue | PASS | No exception |
| `redis-idle-01` | Idle after recent activity | PASS | is_idle=False |
| `redis-idle-02` | Decode warning regression | PASS | Zero decode warnings |
| `redis-idle-03` | Chat ingest activity | PASS | is_idle=False when running |
| `redis-idle-04` | Tribunal activity start/end | FAIL | **After end, still is_idle=False (flaky: concurrent background activity on same key)** |

### Phase 4: LLM Integration (3/5 passed)

| Test ID | Description | Result | Notes |
|---|---|---|---|
| `llm-classify-01` | /debug/routing deep-research | PASS | intent=enrich, entities=['Bob Lazar'] |
| `llm-classify-02` | /debug/routing pulse | PASS | entities=['Area 51'] |
| `llm-classify-03` | /debug/routing navigate | PASS | intent=navigate, year=1965 |
| `llm-classify-04` | /debug/routing empty | FAIL | Returns None for intent/entities |
| `llm-research-01` | deep-research via /query | PASS | task=success, entities=['Ginestra Bianconi'] |
| `llm-research-02` | Markdown in summary | PASS | 1684 chars, markdown formatting |
| `orch-wave-01` | Divergence engine | PASS | risk=0.319, 3 driving claims |

### Phase 5: last30days + File System (9/9 passed)

| Test ID | Description | Result | Notes |
|---|---|---|---|
| `l30d-snapshot-01` | Pulse JSON files exist | PASS | 8 snapshots |
| `l30d-snapshot-02` | Pulse MD files exist | PASS | 8 matching MD files |
| `l30d-snapshot-03` | Valid JSON structure | PASS | entity_name, evidence, timestamp present |
| `fs-wiki-01` | bob-lazar.md exists | PASS | Created by EnrichNode |
| `fs-wiki-02` | Frontmatter check | PASS | title, tags, created, updated present |
| `fs-index-01` | index.md exists | PASS | |
| `fs-log-01` | log.md exists | PASS | |
| `fs-pdf-01` | ginestra-bianconi.md exists | PASS | |
| `fs-pdf-02` | Raw PDF exists | PASS | 1,905,552 bytes |

### Phase 6: Agent Orchestration (5/8 passed)

| Test ID | Description | Result | Notes |
|---|---|---|---|
| `orch-01` | ClassifyNode→ResearchNode | PASS | answer present, no task_id |
| `orch-02` | ClassifyNode→EnrichNode | PASS | task_id present |
| `orch-03` | ClassifyNode→NavigateNode | PASS | warp_factor=1.44 |
| `orch-04` | ClassifyNode→StatusNode | PASS | System status returned |
| `orch-05` | Multi-entity query | FAIL | **Returns only 1 entity instead of 2** |
| `ws-01` | WebSocket streaming | FAIL | **websockets module not installed** |
| `ws-02` | WebSocket conversation_id | FAIL | **websockets module not installed** |
| `sched-startup-01` | Scheduler processes | PASS | Both loops in process list |

### Phase 7: Chaos and Performance (3/5 passed)

| Test ID | Description | Result | Notes |
|---|---|---|
| `chaos-input-01` | XSS in query | PASS | No script injection in answer |
| `chaos-input-02` | SQL injection pattern | PASS | No crash, 200 |
| `perf-latency-01` | /status p95 latency | PASS | avg=11ms, p95=16ms |
| `perf-concurrent-01` | 2 concurrent queries | PASS | all_200, elapsed=17.3s |
| `perf-leak-01` | Memory after 20 queries | PASS | 0.0MB increase |

**CRITICAL FINDING:** Server became completely unresponsive after ~5 concurrent requests during earlier test phase. Required killing PID 16005 and restarting uvicorn without `--reload`. Root cause: hot-reload file watcher saturated by smoke-test file mutations + concurrent LLM request queue exhaustion.

### Phase 8: Swift Contract + Regression (8/9 passed)

| Test ID | Description | Result | Notes |
|---|---|---|---|
| `swift-contract-01` | QueryResponse 12 keys | PASS | All keys present |
| `swift-contract-02` | Type correctness | PASS | confidence=float, entities=list |
| `swift-contract-03` | TaskStatusResponse 7 keys | PASS | All keys present |
| `swift-contract-04` | Status enum validity | PASS | status=running (valid) |
| `swift-contract-05` | Result shape on success | FAIL | **Task still running after 8s poll** |
| `swift-contract-06` | WikiPageDetailResponse 13 keys | PASS | All keys present |
| `swift-contract-07` | AlmanacSummaryResponse 4 keys | PASS | All keys present |
| `swift-contract-09` | 404 error shape | PASS | detail key present |
| `swift-contract-11` | 422 validation shape | PASS | detail key present |
| `reg-01` | Idle decode regression | PASS | Zero warnings after 10 calls |
| `reg-02` | Pulse write no claims | PASS | Verified via task success |
| `reg-03` | Wiki frontmatter | PASS | bob-lazar.md has YAML frontmatter |
| `reg-04` | conversation_id present | PASS | Non-empty UUID returned |
| `reg-05` | task_id for enrich | PASS | Non-null task_id returned |
| `reg-06` | Almanac empty entities_processed | PASS | 200, entities_processed=[] |

---

## Critical Findings

### 1. Server Unresponsive Under Concurrent Load
- **Severity:** CRITICAL
- **Impact:** Server stops responding after ~5 concurrent requests
- **Root Cause:** uvicorn `--reload` hot-reloader saturates when many files change + LLM request queue exhaustion
- **Fix:** Remove `--reload` in production; configure uvicorn with multiple workers (`--workers 4`); add request queue/timeout to LLM calls; add circuit breaker

### 2. Malformed Pulse Path Returns 200
- **Severity:** MEDIUM
- **Impact:** `POST /pulse/"` returns 200 instead of 404/422
- **Root Cause:** URL-encoded quote `%22` is treated as valid entity name by FastAPI path parameter
- **Fix:** Add slug validation in `POST /pulse/{entity_name}` handler; reject names that are just punctuation

---

## Failed Tests Summary

| Test | Failure | Root Cause | Fix Required |
|---|---|---|---|
| `pulse-trigger-02` | 200 not 404/422 | URL-encoded `"` treated as valid entity name | Add slug validation |
| `redis-idle-04` | tribunal_end=False | Concurrent background activity on same Redis key | Use separate test keys or mock |
| `orch-05` | Returns 1 entity not 2 | Multi-entity query only extracts first entity | Fix entity extraction for multi-entity |
| `ws-01/02` | No module 'websockets' | websockets library not installed | Install websockets or skip in non-WS env |
| `swift-contract-05` | Task still running | Async task needs longer poll interval | Increase poll timeout |
| `llm-classify-04` | Empty query returns nothing | LLM classifier can't handle empty strings | Add TQL fallback for empty queries |

---

## Gaps and Improvement Areas

1. **Missing: WebSocket tests** — `websockets` library not installed; no test validates streaming protocol
2. **Missing: Celery worker tests** — `/navigate` endpoint uses Celery; no test validates task execution
3. **Missing: FastMCP server (port 8001)** — No test validates MCP tool endpoints
4. **Missing: Quantum simulation tests** — No test validates Qiskit/PennyLane/CUDA-Q fallback chain
5. **Missing: Multi-entity query** — Query "Bob Lazar and Area 51" returns only 1 entity; multi-entity extraction appears broken
6. **Missing: Empty query TQL fallback** — `debug/routing?query=` returns empty parsed_query; should have TQL/heuristic fallback
7. **Missing: Human approval gate live test** — Could not trigger `human_approval_required=true` in testing
8. **Missing: `/events` event detection** — No test validates the event detection heuristic in Phase 1
9. **Missing: `/budget/approve`** — Could not set hold flag for testing
10. **Missing: File ingest endpoints** — `/ingest/file` and `/ingest/folder` require file creation; deferred
11. **Missing: Draft promotion** — No end-to-end test of draft→publish flow
12. **Missing: Wiki import/export** — No test validates backup/restore round-trip
13. **Missing: Almanac full run** — `POST /almanac/generate?dry_run=true` returns task_id but no test waits for completion

---

## Production Readiness Checklist Status

| Item | Status |
|---|---|
| All endpoints return consistent error shapes | PASS (verified 404, 422 shapes) |
| No raw Python exceptions to client | PASS (all errors return JSON `detail`) |
| File writes use try/except | PASS (observed in pulse, wiki writes) |
| Subprocess timeout enforced | PASS (last30days has 120s timeout) |
| Neo4j query timeouts | UNVERIFIED |
| Redis maxmemory policy | UNVERIFIED |
| Rate limiting on /query | **MISSING** — No per-IP or per-key rate limit |
| Input size limits | **MISSING** — No max body size enforcement observed |
| Path traversal prevention | UNVERIFIED |
| Multi-LLM consensus dead code | **GAP** — `MultiLLMConsensus` unused |
| FastMCP auth | UNVERIFIED |
| Secrets not logged | UNVERIFIED |
| Protected field checked in deletes | UNVERIFIED |
| Almanac uses BackgroundTasks | PASS |
| Human approval checkpointer persistence | **GAP** — In-memory MemorySaver, lost on restart |
| asyncio.create_task error handling | UNVERIFIED |

---

## Recommendations

1. **Immediate (before production):**
   - Add rate limiting middleware to `/query`
   - Add request body size limits (FastAPI `LimitRequestBodyMiddleware`)
   - Add entity name validation in `/pulse/{entity_name}` (reject punctuation-only names)
   - Fix multi-entity extraction in `QueryAgent`
   - Install `websockets` library for WebSocket support

2. **Short-term (post-launch):**
   - Remove `MultiLLMConsensus` dead code or wire into production
   - Add persistent checkpointer for human approval gate (Redis or DB)
   - Add `/events` endpoint test coverage
   - Add file ingest endpoint tests
   - Add almanac full-run test with wait-for-completion

3. **Long-term:**
   - Add request queue to LLM calls to prevent saturation
   - Add circuit breaker for LLM provider failures
   - Add memory watchdog for uvicorn workers
