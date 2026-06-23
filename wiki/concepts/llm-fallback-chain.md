---
title: "LLM Fallback Chain"
tags: [llm, fallback, discovery]
created: 2026-06-22
updated: 2026-06-22
sources: [omlx-2026, ollama-2026, lmstudio-2026]
related: [local-first-llm, llm-discovery, omlx, ollama, lm-studio]
---

# LLM Fallback Chain

The LLM fallback chain defines the order of preference for LLM providers in Project Chicken Soup.

## Fallback Order

1. **oMLX** (default for Mac)
2. **Ollama** (universal)
3. **LM Studio** (alternative)

## How It Works

When an LLM call fails:
1. Try the current provider
2. If it fails, try the next provider in the chain
3. If all providers fail, return an error

## Configuration

- **Default provider** — oMLX (Mac), Ollama (universal)
- **Explicit override** — Set in `.env`
- **Fallback chain** — Configurable in `.env`

## Benefits

- **Resilient** — If one provider fails, the system continues
- **Flexible** — Easy to add new providers
- **Configurable** — Explicit override for specific providers

## See Also

- [[local-first-llm]]
- [[llm-discovery]]
- [[omlx]]
- [[ollama]]
- [[lm-studio]]
