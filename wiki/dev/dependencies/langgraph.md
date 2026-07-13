---
title: "LangGraph"
tags: [agent, langgraph]
created: 2026-06-22
updated: 2026-06-22
sources: [langgraph-2026]
related: [pydantic-graph, pydantic-ai, local-first-llm, ai-alien-connection]
---

# LangGraph

LangGraph is a low-level orchestration framework designed for building, managing, and deploying long-running, stateful agents. It is used for complex sub-workflows in Project Chicken Soup.

## Key Features

- **Checkpointing** — Durable execution, save state at every superstep
- **Human-in-the-loop** — Built-in support for human interrupts
- **Streaming** — Native streaming support
- **Subgraphs** — First-class subgraph support
- **Persistence** — Built-in, memory, Postgres
- **Parallel execution** — Run nodes in parallel
- **Conditional edges** — Dynamic routing between nodes
- **Memory** — Short-term and long-term memory
- **Interrupt handling** — Handle interrupts gracefully
- **Command handling** — External commands affect the graph

## Installation

```bash
pip install langgraph
```

## Configurations

- **Checkpointing** — Save state at every superstep
- **Human-in-the-loop** — Interrupt and resume
- **Streaming** — Stream outputs for better UX
- **Persistence** — Postgres, in-memory, or custom
- **Subgraphs** — Nested workflows
- **Parallel execution** — Run nodes in parallel
- **Conditional edges** — Dynamic routing
- **Memory** — Short-term and long-term memory
- **Interrupt handling** — Handle interrupts gracefully
- **Command handling** — External commands affect the graph

## Agent Patterns

- **State machine** — Graph acts as a state machine
- **Subgraph** — Nested workflows
- **Parallel execution** — Run nodes in parallel
- **Conditional routing** — Dynamic routing between nodes

## Trade-offs

- **Pros:** Rich features, mature, well-documented
- **Cons:** More setup cost, more complex

## See Also

- [[pydantic-graph]]
- [[pydantic-ai]]
- [[local-first-llm]]
- [[ai-alien-connection]]
