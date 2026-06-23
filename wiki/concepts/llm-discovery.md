---
title: "LLM Auto-Discovery"
tags: [llm, discovery, local]
created: 2026-06-22
updated: 2026-06-22
sources: [omlx-2026, ollama-2026, lmstudio-2026]
related: [local-first-llm, omlx, ollama, lm-studio]
---

# LLM Auto-Discovery

The LLM auto-discovery mechanism allows agents to find and use local LLM providers without manual configuration.

## How It Works

1. On startup, query all configured endpoints (`/v1/models`)
2. Build a model catalog with metadata (name, type, size, etc.)
3. Cache the catalog locally
4. Update the catalog on subsequent queries

## Endpoints

- **oMLX:** `GET /v1/models`
- **Ollama:** `GET /v1/models`
- **LM Studio:** `GET /api/v0/models`

## Features

- **Auto-detection** — Automatically discovers available models
- **Caching** — Cached catalog for fast access
- **Fallback** — Falls back to next provider if one is unavailable
- **Configuration** — Explicit overrides in `.env`

## See Also

- [[local-first-llm]]
- [[omlx]]
- [[ollama]]
- [[lm-studio]]
