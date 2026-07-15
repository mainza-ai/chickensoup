---
title: "Pydantic Settings"
tags: [pydantic, settings, configuration]
created: 2026-06-22
updated: 2026-07-15
sources: [pydantic-2026]
related: [pydantic-ai, pydantic-graph, api-design]
---

# Pydantic Settings

Type-safe configuration management using pydantic-settings. Implementation in `src/config.py` (138 lines).

## Configuration Schema (50+ fields)

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
| `NEO4J_PASSWORD` | str | "chickensoup_password" | Neo4j password |
| `REDIS_URL` | str | "redis://localhost:6379/0" | Redis connection |

### LLM Provider
| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `LLM_FALLBACK_CHAIN` | str | "omlx,ollama,lmstudio" | Provider fallback order |
| `OMLX_API_URL` | str | "http://127.0.0.1:9000/v1" | oMLX endpoint |
| `OLLAMA_API_URL` | str | "http://localhost:11434/v1" | Ollama endpoint |
| `LMSTUDIO_API_URL` | str | "http://localhost:1234/v1" | LM Studio endpoint |
| `NVIDIA_API_KEY` | str | "" | NVIDIA cloud API key |
| `NVIDIA_API_URL` | str | "https://integrate.api.nvidia.com/v1" | NVIDIA API endpoint |
| `OPENROUTER_API_KEY` | str | "" | OpenRouter API key |
| `OPENROUTER_API_URL` | str | "https://openrouter.ai/api/v1" | OpenRouter endpoint |
| `CUSTOM_LLM_API_KEY` | str | "" | Custom provider API key |
| `CUSTOM_LLM_API_URL` | str | "" | Custom provider URL |
| `CUSTOM_LLM_MODELS` | str | "" | Custom provider model list |
| `LLM_PROVIDER_TYPE` | str | "local" | "local" or "cloud" |
| `LLM_ACTIVE_PROVIDER` | str | "" | Override auto-discovered provider |
| `LLM_ACTIVE_MODEL` | str | "" | Override auto-discovered model |

### Quantum Backend
| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `QUANTUM_SIMULATION_BACKEND` | str | "numpy" | Backend (numpy/qiskit) |
| `IBM_API_TOKEN` | str | "" | IBM Quantum token |
| `DWAVE_API_TOKEN` | str | "" | D-Wave token |
| `IONQ_API_TOKEN` | str | "" | IonQ token |
| `QUANTUM_HARDWARE_ENABLED` | bool | False | Hardware flag |

### Wiki & Ingest
| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `WIKI_AUTO_CREATE` | bool | True | Auto-create pages on file ingest |
| `WIKI_MIN_CONFIDENCE` | float | 0.5 | Min confidence for page creation |
| `WIKI_DATA_DIR` | str | "wiki" | Wiki root directory |
| `WIKI_BACKUP_ENABLED` | bool | True | Enable automatic backups |
| `WIKI_BACKUP_DIR` | str | "backups" | Backup directory |
| `WIKI_BACKUP_RETENTION_DAYS` | int | 30 | Backup retention period |
| `WIKI_AUTO_COMMIT` | bool | False | Auto-commit backups to git |
| `WIKI_RECONCILE_ON_STARTUP` | bool | True | Reconcile pages at startup |

### Chat-to-Wiki
| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `CHAT_WIKI_CONVERSION_ENABLED` | bool | False | Master switch (opt-in) |
| `CHAT_WIKI_MIN_CONVERSATION_LENGTH` | int | 10 | Min messages for eligibility |
| `CHAT_WIKI_CHECK_INTERVAL_SECONDS` | int | 300 | Scheduler interval |
| `CHAT_WIKI_IDLE_TIMEOUT_MINUTES` | int | 30 | Idle timeout before extract |
| `CHAT_WIKI_USER_ENTITY_NAME` | str | "Primary Researcher" | User entity name |

### Security & Rate Limiting
| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `API_KEY` | str | "" | Auth key (empty = dev mode) |
| `CORS_ORIGINS` | str | "http://127.0.0.1:8000,http://localhost:8000" | Allowed origins |
| `MAX_CONCURRENT_LLM_REQUESTS` | int | 4 | Total LLM concurrency (2 high + 2 low) |
| `REQUEST_RATE_LIMIT_PER_MINUTE` | int | 20 | Global rate limit |
| `REQUEST_RATE_LIMIT_BURST` | int | 5 | Rate limit burst |
| `REQUEST_MAX_BODY_BYTES` | int | 1_048_576 | Max request body size |
| `RATE_LIMITING_ENABLED` | bool | True | Rate limiting master switch |

### LLM Client & Circuit Breaker
| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `LLM_CIRCUIT_BREAKER_THRESHOLD` | int | 5 | Failures before breaker opens |
| `LLM_CIRCUIT_BREAKER_RECOVERY_TIMEOUT` | int | 120 | Cooldown seconds |
| `LLM_CLIENT_TIMEOUT` | float | 30.0 | Default request timeout (cloud) |
| `LLM_CLIENT_CLOUD_TIMEOUT` | float | 30.0 | Cloud provider timeout |
| `LLM_CLIENT_LOCAL_TIMEOUT` | float | 120.0 | Local provider timeout |
| `LLM_CLIENT_MAX_TOKENS` | int | 2048 | Max response tokens |
| `LLM_CLIENT_HIGH_PRIORITY_CONCURRENCY` | int | 2 | High priority semaphore slots |
| `LLM_CLIENT_LOW_PRIORITY_CONCURRENCY` | int | 2 | Low priority semaphore slots |

### Last30days / Almanac / Budget
| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `LAST30DAYS_ENABLED` | bool | False | Master switch |
| `LAST30DAYS_BINARY_PATH` | str | "" | last30days CLI path |
| `LAST30DAYS_MONTHLY_BUDGET_USD` | float | 20.0 | Monthly budget ceiling |
| `LAST30DAYS_COST_PER_PULL_USD` | float | 0.50 | Cost per pulse |
| `FREE_TIER_REQUESTS_PER_HOUR` | int | 60 | Free tier request cap |
| `FREE_TIER_ENABLED` | bool | True | Free tier flag |
| `IDLE_THRESHOLD_MINUTES` | int | 5 | Sentinal idle timeout |
| `LAST30DAYS_PULSE_TIMEOUT_SECONDS` | int | 60 | Pulse timeout |
| `LAST30DAYS_MAX_CLAIMS_PER_PULSE` | int | 50 | Max evidence per pulse |
| `LAST30DAYS_PULSE_ENABLED` | bool | False | Pulse loop switch |
| `BUDGET_REDIS_KEY_PREFIX` | str | "budget" | Budget Redis key prefix |
| `BUDGET_HOLD_THRESHOLD_REMAINING` | float | 2.0 | Multiples of cost_per_pull for HOLD |

### Wavefunction / Social Traction
| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `CLAIM_WAVEFUNCTION_SOCIAL_TRACTION_WEIGHT` | float | 0.15 | Traction decay weight |
| `SOCIAL_TRACTION_HALF_LIFE_DAYS` | float | 7.0 | Traction half-life |
| `SOCIAL_TRACTION_DECAY_ENABLED` | bool | True | Traction decay flag |
| `WAVEFUNCTION_SCORING_VERSION` | str | "v1-wavefunction" | Scoring version tag |
| `DIVERGENCE_SPIKE_THRESHOLD` | float | 0.7 | Divergence alert threshold |

### Almanac
| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `ALMANAC_GENERATION_INTERVAL_HOURS` | int | 24 | Brief generation interval |
| `ALMANAC_DRY_RUN_DEFAULT` | bool | True | Dry-run mode default |
| `ALMANAC_MIN_ENTITIES` | int | 2 | Min entities for almanac |

### Misc
| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `REQUEST_ID_HEADER` | str | "X-Request-ID" | Request tracing header |
| `CHECKPOINT_BACKEND` | str | "redis" | LangGraph checkpoint backend |
| `ORCHESTRATOR_TIMEOUT_SECONDS` | int | 120 | Graph execution timeout |

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
