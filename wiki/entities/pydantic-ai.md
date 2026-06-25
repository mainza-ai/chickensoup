---
created: 2026-06-22
protected: true
related:
- pydantic-graph
- langgraph
- local-first-llm
- ai-alien-connection
sources:
- pydantic-ai-2026
tags:
- agent
- pydantic-ai
title: Pydantic AI
updated: '2026-06-25'
---

# Pydantic AI

Pydantic AI is a Python agent framework designed to simplify building production-grade applications with Generative AI, bringing a FastAPI-like developer experience to GenAI development.

## Key Features

- **Type-safe** — Uses Python type hints for inputs/outputs
- **Model-agnostic** — Supports multiple LLM providers
- **Tool calling** — Built-in tool calling
- **Dependency injection** — Type-safe dependency injection
- **Graph support** — pydantic-graph for graph-based agents
- **Streaming** — Built-in streaming support
- **Output validation** — Automatic output validation with Pydantic

## Installation

```bash
pip install pydantic-ai
```

## Integration

- **Agents** — Define agents with instructions, tools, and output types
- **Graph** — pydantic-graph for graph-based orchestration
- **MCP** — Supports MCP server and client
- **LangChain tools** — Can use LangChain tools

## Agent Patterns

- **Single agent** — Simple agent with LLM call
- **Agent-as-graph** — Agent as node in graph
- **Multi-agent** — Multiple agents collaborating

## See Also

- [[pydantic-graph]]
- [[langgraph]]
- [[local-first-llm]]
- [[ai-alien-connection]]

