---
title: "API Design"
tags: [api, fastapi, endpoints]
created: 2026-06-22
updated: 2026-07-12
sources: [fastapi-2026]
related: [fastapi, local-first-llm, multi-llm-consensus, quantum-job-scheduler, mcp-server, agent-architecture, chat-to-wiki-pipeline, ingestion-pipeline, credibility-scoring, living-almanac, frontend-settings-menu]
---

# API Design

FastAPI server at `src/main.py` (~2100 lines after Living Almanac). All endpoints live in one file, organized by function. OpenTelemetry middleware + custom Observability+RateLimit middleware with 11 custom metrics.

## Endpoints

### Query (Core AI)

| Method | Path | Purpose | Models |
|--------|------|---------|--------|
| `POST` | `/query` | Submit query to orchestrator (supports `conversation_id` for multi-turn). Now populates `inferred_events`/`inferred_entities` + `claim_confidences` from wavefunction scoring. `source_tier: local | network_opt_in`. | `QueryRequest` → `QueryResponse` |
| `GET` | `/conversation/{id}` | Retrieve conversation history (last 20 turns, 7-day TTL) | → `{conversation_id, history[]}` |
| `GET` | `/conversations` | List all conversations with metadata | → `{conversations[], total}` |
| `POST` | `/consensus/query` | Multi-LLM consensus via Jaccard | → `{consensus_response, agreement_score, individual_responses}` |

### Graph

| Method | Path | Purpose |
|--------|------|---------|
| `GET` | `/graph/{entity}` | Entity + neighbor relationships with relationship types |
| `GET` | `/entities` | List all lore entities (reconciles Neo4j vs wiki filesystem orphans) |
| `GET` | `/events` | List temporal events (filtered — engineering tags excluded unless serpo/rainbow/looking glass/pegasus/paperclip) |

### Living Almanac — Quantum Credibility (NEW)

| Method | Path | Auth | Purpose |
|--------|------|------|---------|
| `POST` | `/pulse/{entity_name}` | Yes | Trigger pulse for entity: subprocess to last30days CLI (`shell=False`), budget check via Lua atomic, writes immutable dated snapshot to `wiki/raw/pulse/{slug}-{date}.json+.md`, never touches entities/concepts. Returns `PulseResult` with evidence list. Disabled gate returns no-op not error. |
| `GET` | `/pulse/history?entity_name=&limit=50` | No | List pulse snapshots with evidence counts |
| `GET` | `/entities/{name}/divergence` | No | Narrative divergence: builds `FieldGeometryTensor` from canon vector (wiki frontmatter+body) vs live vector (fresh `ClaimEvidence`), runs same divergence-risk math via `find_optimal_path` (grep-able shared call), returns `divergence_risk` + `driving_claims`. |
| `GET` | `/entities/{name}/timeline?days=30` | No | Time-slider: reconstructs from `wiki/raw/pulse/{slug}-*.json` + `git log --follow` on entity md, chartable `[{date, epistemic_confidence, social_traction, divergence_risk, active_claims, pulse_file, wiki_commit}]`. No new TSDB. |
| `GET` | `/entities/{name}/entanglement?candidate=&limit=10` | No | Entanglement correlation: encodes co-occurrence across independent clusters as quantum state, Meyer-Wallach scorer, independent platforms score higher than single cross-ref. `candidate` filters to single pair. |
| `POST` | `/entities/{name}/tribunal` | No | Tribunal: 3 roles (Skeptic, Empiricist, Believer) + referee LangGraph, gated on `state_label==contested` or `divergence_risk>=0.7`. Uncontested never triggers (cost control, 0 LLM calls). Returns 3 positions + citations + referee synthesis + disagreements preserved. |
| `GET` | `/budget/status` | No | Monthly budget: spent, pulls, remaining, ceiling, HOLD flag |
| `POST` | `/budget/approve` | Yes | Clear HOLD flag (review→HOLD→approve pattern, same shape as MilimoClaw SpendApprovalHandler) |
| `POST` | `/almanac/generate?dry_run=true` | No | Generate daily almanac: Tier-1 entities → pulse → wavefunction → divergence → tribunal → self-contained HTML (inline CSS, no JS, dark mode `@media (prefers-color-scheme: dark)`, print-friendly) + md. `wiki/raw/almanac/{date}.html`, `log.md` append. `dry_run=true` returns HTML content, no file writes, no budget spend. Idempotency: same hash → `no_material_change` logged, no redundant brief. |
| `GET` | `/almanac/history?limit=20` | No | List published HTML briefs |

### Navigation & Quantum

| Method | Path | Purpose |
|--------|------|---------|
| `POST` | `/navigate` | Compute optimal spacetime path (Celery async with sync fallback) |
| `POST` | `/quantum/schedule` | Submit quantum simulation job to QPU backend |
| `GET` | `/quantum/job/{job_id}` | Poll job status and results |

### System

| Method | Path | Purpose |
|--------|------|---------|
| `GET` | `/status` | System health: LLM provider, Neo4j, Redis, quantum backend, now also `last30days_enabled` + `budget_remaining` |
| `GET` | `/config` | Current quantum + LLM settings (probes fresh) + provider map |
| `POST` | `/config` | Update quantum backend, hardware toggle, tokens + LLM provider/model |
| `POST` | `/config/llm` | Update LLM provider/model, fresh probe, persists to `.env`, invalidates `cache:llm:*` |
| `POST` | `/config/llm/probe` | Probe specific provider without changing active config |
| `GET` | `/models` | List available LLM models from active provider |

### Ingestion

| Method | Path | Purpose | Models |
|--------|------|---------|--------|
| `POST` | `/ingest` | Ingest raw content by title/content (Celery or sync) | `IngestRequest` → `IngestResponse` |
| `POST` | `/ingest/bulk` | Clear Neo4j + re-ingest all wiki pages | → `{success, pages_ingested, nodes_created, rels_created}` |
| `POST` | `/ingest/analyze` | Analyze content → preview (no commit) | `AnalyzeRequest` → `AnalyzeResponse` |
| `POST` | `/ingest/file` | Upload single file → analyze + commit wiki + Neo4j | multipart → `FileIngestResponse` |
| `POST` | `/ingest/folder` | Upload zip → process all files through pipeline | zip → `FolderIngestResponse` |
| `POST` | `/ingest/pdf-folder` | Scan PDFs folder, pypdf extract, IngestAgent, wiki pages + Neo4j bulk rebuild | `PdfFolderIngestRequest` → `PdfFolderIngestResponse` |

### Chat-to-Wiki

| Method | Path | Purpose |
|--------|------|---------|
| `GET` | `/chat/ingest/status` | Scheduler status |
| `POST` | `/chat/ingest/now` | Trigger immediate scan |
| `GET` | `/chat/ingest/history` | Recent ingest events from wiki log |
| `GET` | `/chat/ingest/notifications` | Chat-specific notifications |
| `POST` | `/chat/name` | Set or rename user wiki entity |

### Wiki CRUD

| Method | Path | Purpose |
|--------|------|---------|
| `GET` | `/wiki/pages?page_type=` | List all wiki pages with frontmatter |
| `GET` | `/wiki/page/{slug}?page_type=` | Full detail for a wiki page (now includes `divergence` + `claim_confidences`) |
| `DELETE` | `/wiki/page/{slug}?page_type=&hard=&force=` | Delete page with backup snapshot + Neo4j cleanup + Obsidian link cleaning |
| `GET` | `/wiki/export` | Export entire wiki as zip |
| `POST` | `/wiki/import` | Import wiki zip and re-ingest Neo4j |
| `POST` | `/wiki/clear-content?confirm=` | Delete CONTENT pages, preserve ENGINEERING, tag-based |

### Debug

| Method | Path | Purpose |
|--------|------|---------|
| `GET` | `/debug/routing?query=` | Classification only, returns routing decision without executing pipeline |

### Streaming

| Type | Path | Purpose |
|------|------|---------|
| WebSocket | `/ws/agent` | Streaming agent responses with status + chunked text |

## Request/Response Models

All models in `src/models.py` (~310 lines), Pydantic v2:

| Model | Key Fields |
|-------|-----------|
| `ClaimEvidence` | `claim_text, source_platform, engagement_count, url, timestamp, cluster_id, polymarket_odds?, engagement_decayed?, provenance_chain[]` |
| `ClaimConfidence` | `epistemic_confidence, social_traction, state_label (corroborated|contested|unverified), collapsed, evidence_count, last_pulse_at?, scoring_version, scoring_inputs{}, claim_text?` |
| `DrivingClaim` | `claim_text, platform, old_confidence?, new_confidence, delta` |
| `DivergenceResult` | `entity_name, divergence_risk, canon_vector_hash, live_vector_hash, driving_claims[], computed_at` |
| `PulseResult` | `entity_name, status (success|disabled|budget_exceeded|error|no_data), evidence[], raw_snapshot_path?, budget_remaining, error?` |
| `TimelinePoint` | `date, epistemic_confidence, social_traction, divergence_risk, active_claims[], pulse_file?, wiki_commit?` |
| `BudgetStatus` | `month_key, spent_usd, pulls_count, remaining_usd, ceiling_usd, on_hold` |
| `QueryRequest` | `query: str, structured: bool, conversation_id?: str` |
| `QueryResponse` | `query, answer, confidence, entities, sources, inferred_events[], inferred_entities[], conversation_id?, history[], claim_confidences[], source_tier (local|network_opt_in)` |
| `NavigateRequest/Response` | Origin/destination/target_year/energy_level; success/path/warp_factor/divergence_risk/geometry_tensor |
| `IngestRequest/Response` | Title/content/tags/sources; success/nodes_created/relationships_created/confidence_score |
| `AnalyzeRequest/Response` | Content/filename; success/suggested_pages[]/confidence/raw_text_preview |
| `SuggestedPageModel` | `title, page_type (entities|concepts|projects), tags, sources, summary, body, related[], confidence` |
| `FileIngestResponse` | `success, pages_created[], pages_updated[], total_pages, nodes_created, relationships_created` |
| `ConversationMetaResponse` | `id, message_count, last_activity, ingested, ingested_at, pages_created[]` |
| `ChatIngestStatusResponse` | `enabled, last_run, conversations_checked, conversations_ingested, pages_created, pages_updated` |
| `SetUserNameRequest/Response` | `name`; `success, previous_name, current_name, slug` |
| `StatusResponse` | `status, llm_provider, llm_connected, neo4j_connected, redis_connected, quantum_backend, last30days_enabled, budget_remaining?` |
| `ConfigRequest/Response` | Quantum backend, tokens, hardware toggle, LLM provider/model + per-provider status |
| `LLMProbeRequest/Response` | `provider_name`; `provider, available, models[]` |

## Middleware

- **CORS** — Configurable via `CORS_ORIGINS` env var
- **OpenTelemetry** — Tracing spans for HTTP requests and WebSocket, periodic metrics export
- **ObservabilityAndRateLimitMiddleware** — Custom metrics with attributes: `agent_loop_executions`, `quantum_simulation_duration_seconds`, `cache_hits/misses`, `pulse_runs_total{status,entity}`, `pulse_latency_seconds`, `budget_spent_usd`, `wavefunction_state_total{state,collapsed}`, `divergence_risk`, `tribunal_runs_total{trigger}`, `almanac_generated_total{status}`, `almanac_generation_duration_seconds`

## Lifecycle

- **Startup**: Connects Neo4j, initializes constraints/indexes, starts chat-to-wiki scheduler + almanac scheduler (hourly check, respects `ALMANAC_GENERATION_INTERVAL_HOURS`) background tasks
- **Shutdown**: Gracefully cancels both schedulers, closes Neo4j

## Source Tier Labeling

New endpoints explicitly label `source_tier` in responses:
- `local` — data from wiki canon, Neo4j, local LLM reasoning
- `network_opt_in` — data involving last30days evidence (requires `LAST30DAYS_ENABLED=true`)

This satisfies spec non-negotiable #2: local-first boundary stays explicit, network tier is clearly labeled opt-in.

## See Also

- [[fastapi]]
- [[local-first-llm]]
- [[multi-llm-consensus]]
- [[quantum-job-scheduler]]
- [[mcp-server]]
- [[ingestion-pipeline]]
- [[chat-to-wiki-pipeline]]
- [[credibility-scoring]]
- [[living-almanac]]
- [[frontend-settings-menu]]
- [[project-structure]] — full source tree
