---
title: "API Design"
tags: [api, fastapi]
created: 2026-06-22
updated: 2026-06-22
sources: [fastapi-2026]
related: [fastapi, local-first-llm, ai-alien-connection]
---

# API Design

The API design for Project Chicken Soup uses FastAPI with Pydantic models for request/response schemas.

## Endpoints

### POST /query
Submit a query, get AI interpretation.

### GET /graph/{entity}
Retrieve entity and related data.

### POST /navigate
Compute optimal time travel path.

### GET /status
System health (LLM, Neo4j, quantum backends).

### GET /models
List available LLM models.

### POST /ingest
Ingest new wiki content into knowledge graph.

## Request/Response

### All Pydantic, Typed

All request/response schemas are Pydantic models with Python type hints. Auto-validation with Pydantic.

## Authentication

- **Local auth** — API key authentication
- **Rate limiting** — Per-client, per-endpoint rate limiting

## Error Handling

- **Error taxonomy** — Custom error types
- **Error propagation** — Errors propagate through layers
- **Retry logic** — Automatic retry on failure

## Versioning

- **API versioning** — Versioned endpoints (/v1/)
- **Backward compatible** — Backward compatible changes

## Documentation

- **OpenAPI/Swagger** — Auto-generated OpenAPI specification
- **Developer docs** — Architecture and design decisions
- **User docs** — How to use the system

## See Also

- [[fastapi]]
- [[local-first-llm]]
- [[ai-alien-connection]]
