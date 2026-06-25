---
created: 2026-06-22
protected: true
related:
- omlx
- ollama
- local-first-llm
- ai-alien-connection
sources:
- lmstudio-2026
tags:
- llm
- local
- lm-studio
title: LM Studio
updated: '2026-06-25'
---

# LM Studio

LM Studio is a desktop application for running and experimenting with large language models (LLMs) locally on your computer, featuring a chat interface, model management, and an OpenAI-compatible local server.

## Key Features

- **OpenAI-compatible API** — Drop-in replacement for OpenAI API
- **REST API** — Native REST API for model management
- **Model library** — Large library of GGUF and MLX models
- **Chat interface** — Built-in chat UI
- **Offline RAG** — Offline retrieval-augmented generation
- **Tool calling** — Supports function calling and tool use

## Configuration

- **Endpoint:** `http://localhost:1234/v1`
- **Native API:** `GET /api/v0/models`
- **Model discovery:** `GET /v1/models` (OpenAI) or `GET /api/v0/models` (native)
- **Admin UI:** `http://localhost:1234`

## Models

LM Studio supports:

- **GGUF models** — Meta Llama, Qwen, Mistral, and more
- **MLX models** — Apple Silicon optimized models
- **VLM models** — Vision-language models
- **Embedding models** — For semantic search

## Benefits

- **Universal** — Works on any platform
- **Rich UI** — Built-in chat and model management
- **Flexible** — Supports many model formats
- **Fast** — Local inference, no network latency

## See Also

- [[omlx]]
- [[ollama]]
- [[local-first-llm]]
- [[ai-alien-connection]]

