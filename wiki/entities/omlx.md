---
title: "oMLX"
tags: [llm, local, mac, omx]
created: 2026-06-22
updated: 2026-06-22
sources: [omlx-2026]
related: [ollama, lm-studio, ai-alien-connection]
---

# oMLX

oMLX is an optimized LLM inference server for Apple Silicon Macs featuring continuous batching and tiered KV caching. It is the default LLM provider for Project Chicken Soup on Mac.

## Key Features

- **Continuous batching** — Efficient inference with continuous batching
- **Tiered KV caching** — Optimized memory for long contexts
- **Auto-discovery** — Automatically discovers models from the model directory
- **OpenAI-compatible API** — Drop-in replacement for OpenAI API
- **Model types** — LLM, VLM, OCR, Embedding, Reranker
- **Model directory** — Two-level directory structure (e.g., `mlx-community/model-name/`)
- **Menu bar app** — macOS app with admin dashboard
- **CLI management** — `omlx start`, `omlx stop`, `omlx restart`

## Configuration

- **Endpoint:** `http://127.0.0.1:9000/v1` (configurable via `OMLX_PORT`)
- **Model directory:** `~/.omlx/models` (default, configurable via `OMLX_MODEL_DIR`)
- **Admin UI:** `http://localhost:8000/admin/chat`
- **Model discovery:** `GET /v1/models`

## Models

Models are auto-detected by type (LLM, VLM, OCR, Embedding, Reranker) and support models from mlx-lm and mlx-vlm.

## Models Served

- `Huihui-Qwen3.6-35B-A3B-Claude-4.7-Opus-abliterated-mlx-8bit` — Primary model
- Other mlx-community models
- Custom models in the model directory

## See Also

- [[ollama]]
- [[lm-studio]]
- [[ai-alien-connection]]
