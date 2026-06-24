---
title: "API Design"
tags: [api, fastapi, endpoints]
created: 2026-06-22
updated: 2026-06-23
sources: [fastapi-2026]
related: [fastapi, local-first-llm, multi-llm-consensus, quantum-job-scheduler, mcp-server, agent-architecture]
---

# API Design

FastAPI server at `src/main.py` (~706 lines). All endpoints live in one file, organized by function.

## Endpoints

### Query
| Method | Path | Purpose | Models |
|--------|------|---------|--------|
| POST | `/query` | Submit query to orchestrator | `QueryRequest` → `QueryResponse` |
| POST | `/consensus/query` | Multi-LLM consensus | `QueryRequest` → `QueryResponse` |

### Graph
| Method | Path | Purpose |
|--------|------|---------|
| GET | `/graph/{entity}` | Entity + neighbor relationships |
| GET | `/entities` | List all lore entities |
| GET | `/events` | List temporal events |

### Navigation & Quantum
| Method | Path | Purpose |
|--------|------|---------|
| POST | `/navigate` | Compute optimal spacetime path |
| POST | `/quantum/schedule` | Submit quantum simulation job |
| GET | `/quantum/job/{job_id}` | Poll job status and results |

### System
| Method | Path | Purpose |
|--------|------|---------|
| GET | `/status` | System health (LLM, Neo4j, Redis, quantum) |
| GET | `/config` | Current quantum + LLM settings (always probes fresh) |
| POST | `/config` | Update quantum backend, hardware toggle, tokens + LLM provider/model selection |
| POST | `/config/llm` | Update LLM provider/model, probes fresh, persists to `.env` |
| GET | `/models` | List available LLM models |

### Ingestion
| Method | Path | Purpose |
|--------|------|---------|
| POST | `/ingest` | Ingest single wiki page |
| POST | `/ingest/bulk` | Clear + bulk ingest all wiki pages |

### Streaming
| Type | Path | Purpose |
|------|------|---------|
| WebSocket | `/ws/agent` | Streaming agent responses with real-time status updates, chunked text |

## Request/Response Models

All models in `src/models.py` (~67 lines), typed with Pydantic:

| Model | Key Fields |
|-------|-----------|
| `QueryRequest` | `query: str`, `structured: bool` |
| `QueryResponse` | `query, answer, confidence, entities, sources, inferred_events, inferred_entities` |
| `NavigateRequest` | `origin, destination, target_year, energy_level` |
| `NavigateResponse` | `success, path, warp_factor, divergence_risk, geometry_tensor` |
| `IngestRequest` | `title, content, tags, sources` |
| `IngestResponse` | `success, nodes_created, relationships_created, confidence_score` |
| `StatusResponse` | `status, llm_provider, llm_connected, neo4j_connected, redis_connected, quantum_backend` |
| `ConfigRequest` | `quantum_backend, ibm_api_token?, dwave_api_token?, ionq_api_token?, hardware_enabled, llm_active_provider?, llm_active_model?` |
| `ConfigResponse` | `quantum_backend, hardware_enabled, ibm/dwave/ionq token_set, llm_active_provider, llm_active_model, llm_available_models` |
| `LLMConfigRequest` | `llm_active_provider?, llm_active_model?` |
| `LLMConfigResponse` | `success, llm_active_provider, llm_active_model, llm_available_models` |

## Middleware

- **CORS** — All origins allowed (development)
- **OpenTelemetry** — Tracing spans for HTTP requests and WebSocket
- **ObservabilityAndRateLimitMiddleware** — Custom metrics (4 counters/gauges)

## Lifecycle

- **Startup**: Connects Neo4j, initializes constraints/indexes, logs status
- **Shutdown**: Gracefully closes Neo4j connection

## See Also

- [[fastapi]]
- [[local-first-llm]]
- [[multi-llm-consensus]]
- [[quantum-job-scheduler]]
- [[mcp-server]]
