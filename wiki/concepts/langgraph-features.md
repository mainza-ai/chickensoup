---
title: "LangGraph Features"
tags: [langgraph, features]
created: 2026-06-22
updated: 2026-06-22
sources: [langgraph-2026]
related: [langgraph, pydantic-graph, local-first-llm, ai-alien-connection]
---

# LangGraph Features

LangGraph provides a rich set of features for building complex sub-workflows in Project Chicken Soup.

## Features

### Checkpointing
Save state at every superstep for durable execution.

### Human-in-the-loop
Interrupt and resume workflows with human input.

### Streaming
Native streaming support for real-time outputs.

### Subgraphs
First-class subgraph support for nested workflows.

### Persistence
Built-in, memory, and Postgres persistence.

### Parallel Execution
Run nodes in parallel for better performance.

### Conditional Edges
Dynamic routing between nodes based on conditions.

### Memory
Short-term and long-term memory support.

### Interrupt Handling
Handle interrupts gracefully.

### Command Handling
External commands affect the graph.

## Use Cases

- **Research workflow** — Complex research with checkpointing
- **Navigation workflow** — Navigation with human-in-the-loop
- **Evaluation workflow** — Evaluation with streaming

## See Also

- [[langgraph]]
- [[pydantic-graph]]
- [[local-first-llm]]
- [[ai-alien-connection]]
