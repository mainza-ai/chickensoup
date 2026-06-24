---
title: "Pydantic Settings"
tags: [pydantic, settings, configuration]
created: 2026-06-22
updated: 2026-06-23
sources: [pydantic-2026]
related: [pydantic-ai, pydantic-graph, api-design]
---

# Pydantic Settings

Type-safe configuration management using pydantic-settings. Implementation in `src/config.py`.

## Configuration Schema (19 fields)

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `PORT` | int | 8000 | API server port |
| `HOST` | str | "0.0.0.0" | API server host |
| `NEO4J_URI` | str | "bolt://localhost:7687" | Neo4j connection |
| `NEO4J_USER` | str | "neo4j" | Neo4j username |
| `NEO4J_PASSWORD` | str | "password" | Neo4j password |
| `REDIS_URL` | str | "redis://localhost:6379" | Redis connection |
| `LLM_FALLBACK_CHAIN` | str | "omlx,ollama,lmstudio" | Provider order |
| `OMLX_API_URL` | str | "http://localhost:8001" | oMLX endpoint |
| `OLLAMA_API_URL` | str | "http://localhost:11434" | Ollama endpoint |
| `LMSTUDIO_API_URL` | str | "http://localhost:1234" | LM Studio endpoint |
| `QUANTUM_SIMULATION_BACKEND` | str | "numpy" | Quantum backend |
| `IBM_API_TOKEN` | str | "" | IBM Quantum token |
| `DWAVE_API_TOKEN` | str | "" | D-Wave token |
| `IONQ_API_TOKEN` | str | "" | IonQ token |
| `QUANTUM_HARDWARE_ENABLED` | bool | False | Hardware flag |

## Computed Properties

`fallback_chain_list` — Parses `LLM_FALLBACK_CHAIN` comma-separated string into a list.

## Usage

- Loaded from `.env` file at startup
- Updated at runtime via `POST /config` endpoint (persisted back to `.env`)
- Used throughout the backend for connection strings and feature flags

## See Also

- [[pydantic-ai]]
- [[pydantic-graph]]
- [[api-design]]
