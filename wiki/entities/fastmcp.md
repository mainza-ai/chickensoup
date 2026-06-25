---
created: 2026-06-22
protected: true
related:
- local-first-llm
- ai-alien-connection
sources:
- fastmcp-2026
tags:
- mcp
- fastmcp
title: FastMCP
updated: '2026-06-25'
---

# FastMCP

FastMCP is the Model Context Protocol (MCP) server implementation for Project Chicken Soup. It enables external tools and services to interact with the system.

## Key Features

- **Model Context Protocol** — Standard protocol for AI tool integration
- **Tool definitions** — Define tools that external clients can use
- **Tool discovery** — Clients can discover available tools
- **FastMCP server** — Built on FastAPI
- **Sampling support** — Agents can call back to MCP server for tools
- **Error handling** — Built-in error handling

## Configuration

- **Port:** `8000` (default, same as FastAPI)
- **Endpoint:** `/mcp`
- **Host:** `0.0.0.0`

## MCP Tools

- `analyze_field(query)` — Run field manipulation analysis
- `simulate_spacetime(params)` — Run spacetime simulation
- `find_paths(origin, destination)` — Find optimal time travel paths
- `query_graph(entity, depth)` — Query the knowledge graph
- `get_evidence(claim)` — Get evidence for a claim
- `explore_concept(concept)` — Explore a concept and related claims

## Integration

- **FastAPI** — Runs alongside FastAPI
- **Pydantic AI** — Uses Pydantic AI agents
- **Tool calling** — External clients can call tools
- **Sampling** — LLM can call MCP tools

## See Also

- [[local-first-llm]]
- [[ai-alien-connection]]

