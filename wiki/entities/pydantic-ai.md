---
title: "Pydantic AI"
tags: [agent, pydantic-ai]
created: 2026-06-22
updated: 2026-06-22
sources: [pydantic-ai-2026]
related: [pydantic-graph, langgraph, local-first-llm, ai-alien-connection]
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
