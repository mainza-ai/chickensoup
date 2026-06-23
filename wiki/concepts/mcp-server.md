---
title: "MCP Server"
tags: [mcp, fastmcp]
created: 2026-06-22
updated: 2026-06-22
sources: [fastmcp-2026]
related: [fastmcp, local-first-llm, ai-alien-connection]
---

# MCP Server

The MCP (Model Context Protocol) server for Project Chicken Soup exposes tools for external consumers.

## Tools

- **analyze_field** — Run field manipulation analysis on a region of spacetime
- **simulate_spacetime** — Run a spacetime simulation with configurable parameters
- **find_paths** — Find optimal time travel paths between two points
- **query_graph** — Query the knowledge graph for entities and relationships
- **get_evidence** — Get evidence for a claim from the knowledge graph
- **explore_concept** — Explore a concept and related claims with depth

## Protocol

- **MCP version** — Latest MCP version
- **Client types** — LLM agents, web apps, desktop apps
- **Discovery** — Clients can discover available tools
- **Error handling** — Built-in error handling

## Integration

- **FastAPI** — Runs alongside FastAPI
- **Pydantic AI** — Uses Pydantic AI agents
- **Tool calling** — External clients can call tools
- **Sampling** — LLM can call MCP tools

## See Also

- [[fastmcp]]
- [[local-first-llm]]
- [[ai-alien-connection]]
