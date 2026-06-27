---
title: "API Design"
tags: [api, fastapi, endpoints]
created: 2026-06-22
updated: 2026-06-25
sources: [fastapi-2026]
related: [fastapi, local-first-llm, multi-llm-consensus, quantum-job-scheduler, mcp-server, agent-architecture, chat-to-wiki-pipeline, ingestion-pipeline]
---

# API Design

FastAPI server at `src/main.py` (1611 lines). All endpoints live in one file, organized by function.

## Endpoints

### Query
| Method | Path | Purpose | Models |
|--------|------|---------|--------|
| `POST` | `/query` | Submit query to orchestrator (supports `conversation_id` for multi-turn context) | `QueryRequest` → `QueryResponse` |
| `GET` | `/conversation/{id}` | Retrieve conversation history (last 20 turns, 7-day TTL) | → `{conversation_id, history[]}` |
| `GET` | `/conversations` | List all conversations with metadata (count, last_activity, ingested status) | → `{conversations[], total}` |
| `POST` | `/consensus/query` | Multi-LLM consensus | `QueryRequest` → `QueryResponse` |

### Graph
| Method | Path | Purpose |
|--------|------|---------|
| `GET` | `/graph/{entity}` | Entity + neighbor relationships with relationship types |
| `GET` | `/entities` | List all lore entities |
| `GET` | `/events` | List temporal events |

### Navigation & Quantum
| Method | Path | Purpose |
|--------|------|---------|
| `POST` | `/navigate` | Compute optimal spacetime path |
| `POST` | `/quantum/schedule` | Submit quantum simulation job |
| `GET` | `/quantum/job/{job_id}` | Poll job status and results |

### System
| Method | Path | Purpose |
|--------|------|---------|
| `GET` | `/status` | System health (LLM, Neo4j, Redis, quantum backend) |
| `GET` | `/config` | Current quantum + LLM settings (always probes fresh) |
| `POST` | `/config` | Update quantum backend, hardware toggle, tokens + LLM provider/model selection |
| `POST` | `/config/llm` | Update LLM provider/model, probes fresh, persists to `.env` |
| `POST` | `/config/llm/probe` | Probe a specific provider (omlx/ollama/lmstudio) and return its models without changing active config |
| `GET` | `/models` | List available LLM models |

### Ingestion
| Method | Path | Purpose | Models |
|--------|------|---------|--------|
| `POST` | `/ingest` | Ingest raw content by title/content (Celery or sync) | `IngestRequest` → `IngestResponse` |
| `POST` | `/ingest/bulk` | Clear Neo4j + re-ingest all wiki pages | → `{success, pages_ingested, nodes_created, rels_created}` |
| `POST` | `/ingest/analyze` | Analyze content → preview (no commit) | `AnalyzeRequest` → `AnalyzeResponse` |
| `POST` | `/ingest/file` | Upload single file → analyze + commit wiki + Neo4j | multipart → `FileIngestResponse` |
| `POST` | `/ingest/folder` | Upload zip → process all files through pipeline | zip → `FolderIngestResponse` |

### Chat-to-Wiki
| Method | Path | Purpose |
|--------|------|---------|
| `GET` | `/chat/ingest/status` | Scheduler status (last run, conversations checked/ingested, pages created) |
| `POST` | `/chat/ingest/now` | Trigger immediate scan (overrides interval) |
| `GET` | `/chat/ingest/history` | Recent ingest events parsed from wiki log |
| `GET` | `/chat/ingest/notifications` | Chat-specific ingest notifications with page count |
| `POST` | `/chat/name` | Set or rename user wiki entity |

### Debug
| Method | Path | Purpose |
|--------|------|---------|
| `GET` | `/debug/routing` | Run classification only and return routing decision (confidence, intent, wiki matches) without executing full pipeline |

### Streaming
| Type | Path | Purpose |
|------|------|---------|
| WebSocket | `/ws/agent` | Streaming agent responses with real-time status updates, chunked text |

## Request/Response Models

All models in `src/models.py` (~161 lines), typed with Pydantic:

| Model | Key Fields |
|-------|-----------|
| `QueryRequest` | `query: str`, `structured: bool`, `conversation_id?: str` |
| `QueryResponse` | `query, answer, confidence, entities, sources, inferred_events, inferred_entities, conversation_id?, history[]` |
| `NavigateRequest/Response` | Origin/destination/target_year/energy_level; success/path/warp_factor/divergence_risk/geometry_tensor |
| `IngestRequest/Response` | Title/content/tags/sources; success/nodes_created/relationships_created/confidence_score |
| `AnalyzeRequest/Response` | Content/filename; success/suggested_pages[]/confidence/raw_text_preview |
| `SuggestedPageModel` | `title, page_type (entities|concepts|projects), tags, sources, summary, body, related[], confidence` |
| `FileIngestResponse` | `success, pages_created[], pages_updated[], total_pages, nodes_created, relationships_created` |
| `FolderIngestResponse` | `success, total_files, total_pages_created/updated, total_nodes/relationships_created, file_results[]` |
| `ConversationMetaResponse` | `id, message_count, last_activity, ingested, ingested_at, pages_created[]` |
| `ChatIngestStatusResponse` | `enabled, last_run, conversations_checked, conversations_ingested, pages_created, pages_updated` |
| `SetUserNameRequest/Response` | `name`; `success, previous_name, current_name, slug` |
| `StatusResponse` | `status, llm_provider, llm_connected, neo4j_connected, redis_connected, quantum_backend` |
| `ConfigRequest/Response` | Quantum backend, tokens, hardware toggle, LLM provider/model + `LLMProviderStatus` per provider |
| `LLMConfigRequest/Response` | `llm_active_provider?`, `llm_active_model?` + success + available models |
| `LLMProbeRequest/Response` | `provider_name` (omlx/ollama/lmstudio); `provider, available, models[]` |
| `ModelsResponse` | `provider, models[]` |

## Middleware

- **CORS** — All origins allowed (development)
- **OpenTelemetry** — Tracing spans for HTTP requests and WebSocket
- **ObservabilityAndRateLimitMiddleware** — Custom metrics (4 counters/gauges)

## Lifecycle

- **Startup**: Connects Neo4j, initializes constraints/indexes, starts chat-to-wiki scheduler background task
- **Shutdown**: Gracefully cancels scheduler, closes Neo4j connection

## See Also

- [[fastapi]]
- [[local-first-llm]]
- [[multi-llm-consensus]]
- [[quantum-job-scheduler]]
- [[mcp-server]]
- [[ingestion-pipeline]]
- [[chat-to-wiki-pipeline]]
