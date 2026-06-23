---
title: "Local-First LLM"
tags: [llm, local, omx, ollama, lm-studio]
created: 2026-06-22
updated: 2026-06-22
sources: [omlx-2026, ollama-2026, lmstudio-2026]
related: [omlx, ollama, lm-studio, ai-alien-connection]
---

# Local-First LLM

The LLM layer of Project Chicken Soup is local-first, with auto-discovery of local LLM providers.

## Providers

1. **oMLX** (default for Mac) — `http://127.0.0.1:9000/v1`
2. **Ollama** — `http://localhost:11434/v1`
3. **LM Studio** — `http://localhost:1234/v1`

## Auto-Discovery

On startup, the system queries all three endpoints (`/v1/models` for each) and builds a model catalog.

## Fallback Chain

oMLX → Ollama → LM Studio

## Configuration

- `.env` file with explicit overrides
- Discovered models cached locally
- Model catalog updated on startup

## Benefits

- **Offline capable** — No cloud dependency
- **Fast** — Local inference, no network latency
- **Private** — Data stays local
- **Flexible** — Easy to add new providers

## See Also

- [[omlx]]
- [[ollama]]
- [[lm-studio]]
- [[ai-alien-connection]]
