---
created: 2026-06-22
protected: true
related:
- local-first-llm
- ai-alien-connection
sources:
- celery-2026
tags:
- batch
- celery
title: Celery
updated: '2026-06-25'
---

# Celery

Celery is a distributed task queue for processing batch jobs asynchronously. It is used for batch processing in Project Chicken Soup.

## Key Features

- **Distributed** — Run tasks on multiple workers
- **Asynchronous** — Process tasks asynchronously
- **Batches** — Process batches efficiently
- **Retry** — Automatic retry on failure
- **Monitoring** — Built-in monitoring

## Configuration

- **Broker:** Redis
- **Backend:** Redis
- **Workers:** Multiple workers
- **Tasks:** Defined in `src/`

## Use Cases

- **Graph ingestion** — Batch ingesting wiki pages
- **Quantum shots** — Batch quantum circuit execution
- **LLM batching** — Batch LLM calls
- **Background tasks** — Background processing

## Integration

- **Redis broker** — Uses Redis as broker
- **FastAPI** — Integrate with FastAPI
- **Task queues** — Define task queues
- **Workers** — Run workers in background

## See Also

- [[local-first-llm]]
- [[ai-alien-connection]]

