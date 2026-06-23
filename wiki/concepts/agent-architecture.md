---
title: "Agent Architecture"
tags: [agent, architecture, multi-agent]
created: 2026-06-22
updated: 2026-06-22
sources: []
related: [pydantic-ai, pydantic-graph, langgraph, local-first-llm, ai-alien-connection]
---

# Agent Architecture

The agent architecture for Project Chicken Soup uses a hybrid approach with pydantic-graph for core orchestration and LangGraph for complex sub-workflows.

## Multi-Agent Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Orchestrator Graph                        │
│              (pydantic-graph at top level)                   │
└─────────────────────────────────────────────────────────────┘
            │
    ┌───────┴────────┐
    │                │
┌───▼───┐      ┌────▼────┐
│Query  │      │Research │
│Agent  │      │Agent     │
│pydantic-graph│ LangGraph │
└───────┘      └─────────┘
    │                │
┌───▼───┐      ┌────▼────┐
│Nav-   │      │Knowledge│
│gate   │      │Graph    │
│pydantic-graph│ pydantic-graph│
└───────┘      └─────────┘
```

## Multi-Agent Approach

- **Query Agent** — Receives user queries, determines intent, routes to appropriate sub-agent
- **Research Agent** — Explores the knowledge graph (Neo4j) for evidence, credibility, and related claims
- **Navigation Agent** — Runs the AI Navigator (PennyLane) to compute optimal paths through spacetime
- **Orchestrator Agent** — Coordinates the flow: query → research → navigation → answer

## Agent Communication

- **Shared state** — Agents communicate via shared state (Neo4j, Redis)
- **Message passing** — Agents can also communicate via message passing
- **Hybrid** — Hybrid approach for flexibility

## Agent Lifecycle

- **Creation** — Agents are created on demand
- **Initialization** — Agents are initialized with context
- **Shutdown** — Agents are shut down when no longer needed
- **Scaling** — Agents can be scaled horizontally

## Agent Fault Isolation

- **Isolated** — Each agent is isolated
- **Fault tolerance** — If one agent fails, others continue
- **Retry** — Agents can retry failed operations
- **Circuit breaker** — Circuit breaker pattern for external services

## See Also

- [[pydantic-ai]]
- [[pydantic-graph]]
- [[langgraph]]
- [[local-first-llm]]
- [[ai-alien-connection]]
