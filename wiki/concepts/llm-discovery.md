---
title: "LLM Auto-Discovery"
tags: [llm, discovery, local]
created: 2026-06-22
updated: 2026-06-22
sources: [omlx-2026, ollama-2026, lmstudio-2026]
related: [local-first-llm, omlx, ollama, lm-studio, llm-fallback-chain]
---

# LLM Auto-Discovery

The LLM auto-discovery mechanism allows agents to find and use local LLM providers without manual configuration. On startup, the system probes all known endpoints, builds a model catalog, and selects the best provider.

## How It Works

1. **Startup discovery** — Query all configured provider endpoints
2. **Catalog build** — Parse responses into a `ModelCatalog` with metadata
3. **Selection** — Choose the best provider (highest priority with available models)
4. **Health monitoring** — Periodic checks to detect provider changes

## Endpoints

| Provider | Endpoint | Expected Response |
|----------|----------|-------------------|
| **oMLX** | `GET http://127.0.0.1:9000/v1/models` | `{ "data": [{ "id": "mlx-model", "object": "model" }] }` |
| **Ollama** | `GET http://localhost:11434/v1/models` | `{ "data": [{ "id": "llama3:70b", "object": "model" }] }` |
| **LM Studio** | `GET http://localhost:1234/v1/models` | `{ "data": [{ "id": "lm-studio-model", "object": "model" }] }` |

### Response Format Example (oMLX)

```json
GET /v1/models
{
  "data": [
    { "id": "mlx-qwen2.5-32b", "object": "model", "created": 1735689600 },
    { "id": "mlx-llama3.1-8b", "object": "model", "created": 1735689600 }
  ]
}
```

The system parses model names to extract model family, parameter count, and quantization info (e.g., "32b" = 32 billion parameters).

## Error States

| Error | Cause | Handling |
|-------|-------|----------|
| Connection refused | Provider not running | Skip provider, log warning |
| Timeout | Provider busy or hung | Retry once after 5s, then skip |
| Authentication | Provider requires API key | Check .env for key, skip if missing |
| Model not found | Provider running but no models loaded | Provider available but unusable |
| Invalid response | Provider returned malformed data | Skip provider, log error |

## Discovery Timing

| Event | Action | Frequency |
|-------|--------|-----------|
| Application startup | Full discovery against all endpoints | Once |
| Provider health check | Lightweight ping (HEAD /) | Every 30s |
| Provider failure | Full rediscovery against remaining endpoints | On demand |
| Model catalog refresh | Re-query available models | Every 5 min |
| User request | Check cached catalog (not re-query) | Per request |

## Caching

The model catalog is cached in-memory with a 5-minute TTL:
- Within TTL: no network request, instant response from cache
- Expired: re-query the provider endpoints (asynchronous background refresh)
- Cache miss: synchronous re-query

## Configuration

```yaml
# config/default.yaml
llm:
  providers:
    - name: omlx
      endpoint: http://127.0.0.1:9000/v1
      priority: 1
    - name: ollama
      endpoint: http://localhost:11434/v1
      priority: 2
    - name: lm_studio
      endpoint: http://localhost:1234/v1
      priority: 3
  discovery:
    startup: true
    health_check_interval: 30
    catalog_ttl: 300
```

## Provider Selection

The Settings UI provides a **provider picker** that lets users switch between providers at runtime:

1. **Auto-detect** (default) — Probes fallback chain in order, uses first responsive provider
2. **oMLX** — Explicitly probes oMLX endpoint, shows its models
3. **Ollama** — Explicitly probes Ollama endpoint, shows its models
4. **LM Studio** — Explicitly probes LM Studio endpoint, shows its models

When a provider is selected, `POST /config/llm/probe` probes that specific provider and returns its available models. The user then picks a model and hits Apply, which calls `POST /config/llm` with both `llm_active_provider` and `llm_active_model` to persist the selection.

## See Also

- [[local-first-llm]] — LLM strategy overview
- [[llm-fallback-chain]] — Fallback behavior when providers fail
- [[omlx]] — oMLX provider
- [[ollama]] — Ollama provider
- [[lm-studio]] — LM Studio provider
