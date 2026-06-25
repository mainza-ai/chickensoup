---
created: 2026-06-22
protected: true
related:
- omlx
- lm-studio
- local-first-llm
- ai-alien-connection
sources:
- ollama-2026
tags:
- llm
- local
- ollama
title: Ollama
updated: '2026-06-25'
---

# Ollama

Ollama is a tool that allows you to easily run and manage large language models on your local machine, providing a quick way to get started with AI. It is the second LLM provider in the fallback chain.

## Key Features

- **OpenAI-compatible API** — Drop-in replacement for OpenAI API
- **Model library** — Large library of pre-trained models
- **Simple model management** — `ollama pull`, `ollama run`, `ollama list`
- **Cross-platform** — Works on macOS, Linux, Windows
- **LLM and embeddings** — Supports both chat and embedding models
- **Tool calling** — Supports function calling and tool use

## Configuration

- **Endpoint:** `http://localhost:11434/v1`
- **API key:** `ollama` (required but ignored)
- **Model discovery:** `GET /v1/models`
- **Admin UI:** `http://localhost:11434`

## Models

Ollama supports a wide range of models, including:

- `qwen3:8b` — Qwen3 small model
- `llama3` — Meta's Llama 3
- `claude-3-5-sonnet` — Claude model via API
- And many more from the Ollama library

## Benefits

- **Universal** — Works on any platform
- **Simple** — Easy to install and use
- **Flexible** — Supports many models
- **Fast** — Local inference, no network latency

## See Also

- [[omlx]]
- [[lm-studio]]
- [[local-first-llm]]
- [[ai-alien-connection]]

