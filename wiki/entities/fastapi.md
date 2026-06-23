---
title: "FastAPI"
tags: [api, fastapi]
created: 2026-06-22
updated: 2026-06-22
sources: [fastapi-2026]
related: [local-first-llm, ai-alien-connection]
---

# FastAPI

FastAPI is a modern, fast (high-performance) web framework for building APIs with Python 3.8+ based on standard Python type hints. It is the API layer for Project Chicken Soup.

## Key Features

- **Type-safe** — Uses Python type hints for automatic validation
- **Auto documentation** — OpenAPI/Swagger docs auto-generated
- **Async support** — Native async/await support
- **Fast** — One of the fastest Python frameworks
- **Pydantic integration** — Uses Pydantic for data validation
- **Middleware** — Easy to add middleware
- **Dependency injection** — Built-in dependency injection system

## Configuration

- **Port:** `8000` (default)
- **Host:** `0.0.0.0`
- **Auto docs:** `http://localhost:8000/docs`
- **Auto OpenAPI:** `http://localhost:8000/openapi.json`

## Endpoints

- `POST /query` — Submit a query, get AI interpretation
- `GET /graph/{entity}` — Retrieve entity and related data
- `POST /navigate` — Compute optimal time travel path
- `GET /status` — System health (LLM, Neo4j, quantum backends)
- `GET /models` — List available LLM models
- `POST /ingest` — Ingest new wiki content into knowledge graph

## Integration

- **Pydantic models** — All request/response schemas are Pydantic models
- **OpenAPI** — Auto-generated OpenAPI specification
- **Middleware** — CORS, auth, rate limiting
- **Error handling** — Custom error handlers

## See Also

- [[local-first-llm]]
- [[ai-alien-connection]]
