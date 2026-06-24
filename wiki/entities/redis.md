---
title: "Redis"
tags: [cache, redis, infrastructure]
created: 2026-06-22
updated: 2026-06-23
sources: [redis-2026]
related: [cache-architecture, local-first-llm, api-design]
---

# Redis

Redis provides the caching layer for all LLM responses, quantum results, and graph queries. Implementation in `src/cache.py`.

## Cache Implementation (`src/cache.py`)

### RedisCache Class
- Async (`aredis`) and sync (`redis`) dual API
- MD5 key hashing for consistent key lengths
- `get(key)` / `set(key, value, ttl)` / `delete(key)` / `clear()`
- `exists(key)` check
- Pattern-based invalidation via `flush_namespace(namespace)`

### cache_decorator
A decorator that wraps any function with automatic caching:

```python
@cache_decorator(prefix="neo4j", ttl=300)
def get_entity_neighborhood(driver, entity_name): ...
```

Prefix namespaces:
- `cache:neo4j:*` — Graph query results (TTL 300s)
- `cache:llm:*` — LLM responses and classifications (TTL 300s)
- `cache:mcp:*` — MCP tool results (TTL 300s)

## Configuration

- **Docker:** `docker-compose up redis`
- **Port:** `6379`
- **Connection:** `redis://localhost:6379`
- **URL env var:** `REDIS_URL`

## Integration

Used throughout the backend: Neo4j queries, LLM classification, agent responses, MCP tool calls. Every external call goes through `cache_decorator` to minimize redundant work.

## See Also

- [[local-first-llm]]
- [[api-design]]
