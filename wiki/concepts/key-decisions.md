---
title: "Key Decisions"
tags: [project, decisions, architecture]
created: 2026-06-22
updated: 2026-06-22
sources: [PROJECT_SPEC-2026]
related: [agent-architecture, local-first-llm, api-design, mcp-server, knowledge-graph-schema, technology-stack]
---

# Key Decisions

## Decision Table

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Agent framework | pydantic-graph + LangGraph | Type-safety (pydantic-graph) + features (LangGraph) |
| Knowledge graph | Neo4j | Natural fit for entity-relationship data |
| LLM | oMLX (Mac default), Ollama, LM Studio | Local-first, auto-discovery, fallback chain |
| API | FastAPI + OpenAPI | Modern, type-safe, auto-generated docs |
| MCP | FastMCP | Standard protocol, simple integration |
| Cache | Redis | Industry standard, fast, scalable |
| Container | Docker | Simple, portable, reproducible |
| CI/CD | GitHub Actions | Simple, integrated, free for open source |

## Agent Framework

**Decision:** pydantic-graph + LangGraph

**Rationale:** pydantic-graph provides type-safety for core agent orchestration. LangGraph provides advanced features (checkpointing, streaming, human-in-the-loop) for complex sub-workflows. The two-framework approach adds complexity but provides the best of both worlds.

## Knowledge Graph

**Decision:** Neo4j

**Rationale:** Neo4j is a natural fit for entity-relationship data. It supports Cypher queries, which are readable and powerful. It scales well for the expected data volume.

## LLM

**Decision:** oMLX (Mac default), Ollama, LM Studio

**Rationale:** Local-first approach with auto-discovery and fallback chain. oMLX is the default for Mac users. Ollama and LM Studio provide alternatives. All three provide OpenAI-compatible APIs.

## API

**Decision:** FastAPI + OpenAPI

**Rationale:** FastAPI is modern, type-safe, and auto-generates OpenAPI documentation. All request/response schemas are Pydantic models.

## MCP

**Decision:** FastMCP

**Rationale:** FastMCP is a simple, standard implementation of the Model Context Protocol. It integrates well with FastAPI and Pydantic AI.

## Cache

**Decision:** Redis

**Rationale:** Redis is the industry standard for in-memory caching. It is fast, scalable, and has excellent Python support.

## Container

**Decision:** Docker

**Rationale:** Docker is simple, portable, and reproducible. It provides a consistent environment for development, testing, and production.

## CI/CD

**Decision:** GitHub Actions

**Rationale:** GitHub Actions is simple, integrated with GitHub, and free for open source projects.

## See Also

- [[agent-architecture]]
- [[technology-stack]]
- [[local-first-llm]]
- [[api-design]]
- [[mcp-server]]
- [[knowledge-graph-schema]]
- [[production-readiness]]
