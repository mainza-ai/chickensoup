---
title: "API Design"
tags: [api, fastapi, endpoints]
created: 2026-06-22
updated: 2026-07-15
sources: [fastapi-2026]
related: [fastapi, local-first-llm, multi-llm-consensus, quantum-job-scheduler, mcp-server, agent-architecture, chat-to-wiki-pipeline, ingestion-pipeline, credibility-scoring, living-almanac, frontend-settings-menu]
---

# API Design

FastAPI server at `src/main.py` (~2878 lines). All 59 endpoints live in one file, organized by function. Custom ObservabilityAndRateLimitMiddleware with 12 OpenTelemetry metrics.

## Endpoints

### System & Health

| Method | Path | Purpose |
|--------|------|---------|
| `GET` | `/health` | Health check — Redis, Neo4j, LLM, disk latency probes |
| `GET` | `/status` | High-level system status: provider, connections, budget_remaining |
| `GET` | `/config` | Current quantum + LLM settings (fresh probe) + provider map |
| `POST` | `/config` | Update quantum backend, hardware toggle, tokens + LLM provider/model |
| `POST` | `/config/llm` | Update LLM provider/model, fresh probe, persists to `.env` |
| `POST` | `/config/llm/probe` | Probe a specific provider without changing active config |
| `GET` | `/models` | List available LLM models from active provider |
| `GET` | `/status/time` | Server time in CDT timezone |
| `GET` | `/status/progress` | Redis-backed progress for all background systems (
- reconciliation, idle ingestion, wiki watcher, LLM client, Neo4j |

### Query & Conversation

| Method | Path | Purpose |
|--------|------|---------|
| `POST` | `/query` | Submit query to orchestrator (supports `conversation_id`) |
| `GET` | `/conversation/{id}` | Retrieve conversation history (last 20 turns) |
| `GET` | `/conversations` | List all conversations with metadata |
| `POST` | `/research/{thread_id}/approve` | Approve research after human-in-the-loop pause |

### Graph & Knowledge

| Method | Path | Purpose |
|--------|------|---------|
| `GET` | `/graph/{entity}` | Entity + neighbor relationships with types |
| `GET` | `/entities` | List all lore entities (Neo4j vs wiki filesystem) |
| `GET` | `/entities/{name}` | Delete entity from Neo4j |
| `DELETE` | `/events` | List temporal events (engineering tags excluded) |
| `GET` | `/search` | Fulltext BM25 search across all entities |
| `GET` | `/events/stream` | SSE stream for real-time entity updates |

### Navigation, Simulation & Quantum

| Method | Path | Purpose |
|--------|------|---------|
| `POST` | `/navigate` | Compute optimal spacetime path |
| `POST` | `/simulate` | Run spacetime simulation with warp/gravity/velocity/intensity params |
| `POST` | `/temporal/causality` | Build PRECEDED_BY + CAUSED temporal chains |
| `POST` | `/consensus/query` | Multi-LLM consensus via Jaccard word overlap |
| `POST` | `/quantum/schedule` | Submit quantum simulation job |
| `GET` | `/quantum/job/{job_id}` | Poll job status and results |

### Ingestion

| Method | Path | Purpose |
|--------|------|---------|
| `POST` | `/ingest` | Ingest raw content by title/content |
| `POST` | `/ingest/analyze` | Analyze content → preview (no commit) |
| `POST` | `/ingest/file` | Upload single file → analyze + commit wiki + Neo4j |
| `POST` | `/ingest/folder` | Upload zip → process all files |
| `POST` | `/ingest/pdf-folder` | Scan PDFs folder, extract, ingest |
| `POST` | `/ingest/bulk` | Clear Neo4j + re-ingest all wiki pages |

### Chat-to-Wiki

| Method | Path | Purpose |
|--------|------|---------|
| `GET` | `/chat/ingest/status` | Scheduler status |
| `POST` | `/chat/ingest/now` | Trigger immediate scan |
| `GET` | `/chat/ingest/history` | Recent ingest events |
| `GET` | `/chat/ingest/notifications` | Chat-specific notifications |
| `POST` | `/chat/name` | Set or rename user wiki entity |

### Wiki CRUD

| Method | Path | Purpose |
|--------|------|---------|
| `GET` | `/wiki/pages` | List all wiki pages with frontmatter |
| `GET` | `/wiki/page/{slug}` | Full detail for a wiki page |
| `DELETE` | `/wiki/page/{slug}` | Delete page with backup snapshot + Neo4j cleanup |
| `GET` | `/wiki/export` | Export entire wiki as zip |
| `POST` | `/wiki/import` | Import wiki zip and re-ingest Neo4j |
| `POST` | `/wiki/clear-content` | Delete CONTENT pages, preserve ENGINEERING |
| `GET` | `/wiki/backups` | List available backup snapshots |
| `POST` | `/wiki/backup/now` | Trigger immediate backup |
| `POST` | `/wiki/reconcile` | Trigger reconciliation of all pages |
| `POST` | `/wiki/reconcile-stop` | Signal reconciliation to stop |

### Timeline & Events

| Method | Path | Purpose |
|--------|------|---------|
| `GET` | `/timeline` | All dated events ordered chronologically |
| `GET` | `/timeline/range` | Timeline events within a date range |
| `GET` | `/entities/{name}/temporal-context` | Events scoped to a specific entity |

### Almanac & Pulse

| Method | Path | Purpose |
|--------|------|---------|
| `POST` | `/almanac/generate` | Generate daily almanac brief |
| `GET` | `/almanac/history` | List published briefs |
| `GET` | `/almanac/summary` | Latest almanac summary |
| `GET` | `/almanac/file/{date}` | Almanac for a specific date |
| `POST` | `/pulse/{entity_name}` | Trigger pulse for entity |
| `GET` | `/pulse/history` | List pulse snapshots |
| `POST` | `/pulse/purge-empty` | Remove pulse entries with no evidence |
| `GET` | `/pulse/snapshot` | Get a specific pulse snapshot |
| `GET` | `/entities/{name}/divergence` | Narrative divergence score |
| `GET` | `/entities/{name}/timeline` | Entity timeline from pulses + git |
| `GET` | `/entities/{name}/entanglement` | Entanglement correlation between entities |
| `POST` | `/entities/{name}/tribunal` | Adversarial claim tribunal |
| `GET` | `/budget/status` | Monthly budget status |
| `POST` | `/budget/approve` | Clear HOLD flag |

### Entity Drafts

| Method | Path | Purpose |
|--------|------|---------|
| `GET` | `/entities/drafts` | List pages pending LLM extraction |
| `POST` | `/entities/{slug}/promote` | Promote draft to full entity |
| `GET` | `/system/ingestion/status` | Idle-driven ingestion status |

### Debug

| Method | Path | Purpose |
|--------|------|---------|
| `GET` | `/debug/routing` | Classification-only, returns routing decision |

### Streaming

| Type | Path | Purpose |
|------|------|---------|
| WebSocket | `/ws/agent` | Streaming agent responses with status + chunked text |
| SSE | `/events/stream` | Server-sent events for real-time entity/index changes |

## Request/Response Models

All models in `src/models.py` (383 lines), Pydantic v2:

| Model | Key Fields |
|-------|-----------|
| `ClaimEvidence` | `claim_text, source_platform, engagement_count, url, timestamp, cluster_id, polymarket_odds?, engagement_decayed?, provenance_chain[]` |
| `ClaimConfidence` | `epistemic_confidence, social_traction, state_label, collapsed, evidence_count, last_pulse_at?, scoring_version, scoring_inputs{}, claim_text?` |
| `DrivingClaim` | `claim_text, platform, old_confidence?, new_confidence, delta` |
| `DivergenceResult` | `entity_name, divergence_risk, canon_vector_hash, live_vector_hash, driving_claims[], computed_at` |
| `PulseResult` | `entity_name, status, evidence[], raw_snapshot_path?, budget_remaining, error?` |
| `TimelinePoint` | `date, epistemic_confidence, social_traction, divergence_risk, active_claims[], pulse_file?, wiki_commit?` |
| `BudgetStatus` | `month_key, spent_usd, pulls_count, remaining_usd, ceiling_usd, on_hold` |
| `QueryRequest` | `query: str, structured: bool, conversation_id?: str` |
| `QueryResponse` | `query, answer, confidence, entities, sources, inferred_events[], inferred_entities[], conversation_id?, history[], claim_confidences[], source_tier` |
| `NavigateRequest/Response` | Origin/destination/target_year/energy_level; success/path/warp_factor/divergence_risk |
| `IngestRequest/Response` | Title/content/tags/sources; success/nodes_created/relationships_created/confidence_score |
| `FileIngestResponse` | `success, pages_created[], pages_updated[], total_pages, nodes_created, relationships_created` |
| `SimulateRequest/Response` | gravity/velocity/intensity → warp_factor/confidence/target_year/logs |
| `StatusResponse` | `status, llm_provider, llm_connected, neo4j_connected, redis_connected, quantum_backend, budget_remaining?` |
| `ConfigRequest/Response` | Quantum backend, tokens, hardware toggle, LLM provider/model + provider map |
| `APIStatusProgress` | 7 sections: reconciliation, idle_ingestion, chat_ingest, fallback_retry, wiki_watcher, llm_client, neo4j |

## Middleware

- **CORS** — Configurable via `CORS_ORIGINS` env var
- **ObservabilityAndRateLimitMiddleware** — Rate limits per-category (search 60/m, read 30/m, write 10/m, general 20/m). 12 OTel metrics: agent_loop, quantum_simulation, cache_hits/misses, pulse, budget, wavefunction, divergence, tribunal, almanac, LLM calls/failures
- **OpenTelemetry** — Tracing + metrics (no console exporter, kept in-memory)

## Lifecycle

- **Startup**: Neo4j connection + constraints/indexes → background loops (chat ingest scheduler, idle ingestion, wiki watcher, queue rebuild, fallback retry) → reconcile existing pages → rebuild staleness queue → build temporal causality chains → clear stale idle sentinel keys
- **Shutdown**: Cancels all background tasks, closes Neo4j

## See Also

- [[project-structure]] — full source tree
- [[fastapi]]
- [[agent-architecture]]
- [[ingestion-pipeline]]
- [[chat-to-wiki-pipeline]]
- [[living-almanac-project]]
