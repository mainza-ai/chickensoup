---
title: "Pydantic Settings"
tags: [pydantic, settings, configuration]
created: 2026-06-22
updated: 2026-06-25
sources: [pydantic-2026]
related: [pydantic-ai, pydantic-graph, api-design, chat-to-wiki-pipeline]
---

# Pydantic Settings

Type-safe configuration management using pydantic-settings. Implementation in `src/config.py` (52 lines).

## Configuration Schema (24+ fields)

### Server
| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `PORT` | int | 8000 | API server port |
| `HOST` | str | "0.0.0.0" | API server host |

### Database Connections
| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `NEO4J_URI` | str | "bolt://localhost:7687" | Neo4j connection |
| `NEO4J_USER` | str | "neo4j" | Neo4j username |
| `NEO4J_PASSWORD` | str | "password" | Neo4j password |
| `REDIS_URL` | str | "redis://localhost:6379/0" | Redis connection |

### LLM Provider URLs
| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `LLM_FALLBACK_CHAIN` | str | "omlx,ollama,lmstudio" | Provider order |
| `OMLX_API_URL` | str | "http://127.0.0.1:9000/v1" | oMLX endpoint |
| `OLLAMA_API_URL` | str | "http://localhost:11434/v1" | Ollama endpoint |
| `LMSTUDIO_API_URL` | str | "http://localhost:1234/v1" | LM Studio endpoint |
| `LLM_ACTIVE_PROVIDER` | str | "" | Override auto-discovered provider |
| `LLM_ACTIVE_MODEL` | str | "" | Override auto-discovered model |

### Quantum Backend
| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `QUANTUM_SIMULATION_BACKEND` | str | "numpy" | Quantum backend (numpy/qiskit/pennylane) |
| `IBM_API_TOKEN` | str | "" | IBM Quantum token |
| `DWAVE_API_TOKEN` | str | "" | D-Wave token |
| `IONQ_API_TOKEN` | str | "" | IonQ token |
| `QUANTUM_HARDWARE_ENABLED` | bool | False | Hardware flag |

### Wiki Ingest
| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `WIKI_AUTO_CREATE` | bool | True | Auto-create wiki pages on file ingest |
| `WIKI_MIN_CONFIDENCE` | float | 0.5 | Minimum confidence for page creation |
| `WIKI_DATA_DIR` | str | "wiki" | Wiki root directory |

### Chat-to-Wiki Conversion
| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `CHAT_WIKI_CONVERSION_ENABLED` | bool | False | Master switch (opt-in) |
| `CHAT_WIKI_MIN_CONVERSATION_LENGTH` | int | 10 | Min messages for eligibility |
| `CHAT_WIKI_CHECK_INTERVAL_SECONDS` | int | 300 | Scheduler check interval (seconds) |
| `CHAT_WIKI_IDLE_TIMEOUT_MINUTES` | int | 30 | Idle timeout before extraction |
| `CHAT_WIKI_USER_ENTITY_NAME` | str | "Primary Researcher" | Initial user wiki entity name |

## Computed Properties

`fallback_chain_list` — Parses `LLM_FALLBACK_CHAIN` comma-separated string into a list of provider names.

## Runtime Model Selection

When `LLM_ACTIVE_MODEL` is set, all consumers (QueryAgent, ResearchAgent, MultiLLMConsensus, ChatIngestAgent) use it instead of the first available model. When `LLM_ACTIVE_PROVIDER` is set, discovery probes only that provider. Both can be updated at runtime via `POST /config` — no server restart needed.

## Usage

- Loaded from `.env` file at startup
- Updated at runtime via `POST /config` endpoint (persisted back to `.env`)
- Used throughout the backend for connection strings and feature flags

## See Also

- [[pydantic-ai]]
- [[pydantic-graph]]
- [[api-design]]
- [[chat-to-wiki-pipeline]]
