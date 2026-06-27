---
title: "Celery Tasks"
tags: [celery, async, tasks, background-jobs]
created: 2026-06-26
updated: 2026-06-26
sources: [celery-tasks]
related: [redis, api-design, technology-stack, knowledge-graph-ingestion]
---

# Celery Tasks

Async task definitions for background processing of wiki ingestion and spacetime navigation. Implementation in `src/tasks.py` (83 lines).

## Overview

Celery provides asynchronous task execution for operations that may take longer than ideal for a synchronous HTTP request. The Celery app uses Redis as both the broker (message queue) and backend (result store).

## Celery Configuration

```python
redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
celery_app = Celery("chickensoup", broker=redis_url, backend=redis_url)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
)
```

- **Broker:** Redis (default `redis://localhost:6379/0`)
- **Backend:** Redis (same instance)
- **Serializer:** JSON
- **Timezone:** UTC

## Tasks

### `async_ingest_page(title, content, tags, sources)`

Asynchronously ingests a single wiki page into Neo4j.

**Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `title` | str | Page title (becomes the node name) |
| `content` | str | Markdown content (with YAML frontmatter) |
| `tags` | List[str] | Page tags |
| `sources` | List[str] | Source attribution |

**Execution:**
1. Ensures Neo4j driver connection
2. Calls `ingest_wiki_page()` from `src.knowledge_graph.ingest`
3. Returns `{success, title, nodes_created, relationships_created, confidence_score}`

**Error handling:** Returns `{success: False, error: str, title}` on failure. Logged via `chickensoup.tasks` logger.

### `async_navigate(origin, destination, target_year, energy_level)`

Asynchronously calculates a spacetime trajectory between two points.

**Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `origin` | str | Starting location |
| `destination` | str | Target location |
| `target_year` | int | Target year |
| `energy_level` | float | Energy level (affects warp factor) |

**Execution:**
1. Creates a `FieldGeometryTensor` with the specified energy level
2. Submits a quantum job via `QuantumJobScheduler`
3. Waits 1 second for processing
4. Returns `{success, origin, destination, path, warp_factor, divergence_risk}`

**Error handling:** Returns `{success: False, error: str}` on failure.

## Task Names

Tasks are registered with explicit names for monitoring:
- `tasks.async_ingest_page`
- `tasks.async_navigate`

These names appear in Celery worker logs and monitoring dashboards.

## Running Workers

```bash
celery -A src.tasks.celery_app worker --loglevel=info
```

## Integration

- **API endpoints** — `POST /ingest` can dispatch to `async_ingest_page` via Celery (or run synchronously)
- **Redis dependency** — Requires a running Redis instance (started via `docker-compose up redis`)
- **Fallback** — If Redis is unavailable, the API falls back to synchronous execution

## See Also

- [[redis]] — Caching layer and message broker
- [[api-design]] — API endpoints that use async tasks
- [[knowledge-graph-ingestion]] — Neo4j ingestion pipeline
- [[technology-stack]] — Celery in the tech stack
