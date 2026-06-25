---
created: 2026-06-22
protected: true
related:
- pydantic-ai
- langgraph
- local-first-llm
- ai-alien-connection
sources:
- pydantic-ai-2026
tags:
- agent
- pydantic
- graph
title: Pydantic Graph
updated: '2026-06-25'
---

# Pydantic Graph

pydantic-graph is a lightweight, type-centric graph framework for building agent workflows. It is the core orchestration layer for Project Chicken Soup.

## Key Features

- **Type-centric** — Uses Python type hints for edges
- **Lightweight** — Low setup cost
- **Simple** — Easy to understand and use
- **Async support** — Native async/await
- **Graph builder** — Declarative graph construction
- **State management** — Built-in state management
- **Step context** — Rich context for each step

## Installation

```bash
pip install pydantic-graph
```

## Example

```python
from pydantic_graph import BaseNode, End, GraphBuilder

@dataclass
class MyNode(BaseNode):
    data: str

    async def run(self, ctx: GraphRunContext) -> NextNode | End[str]:
        # Process data
        return End("result")
```

## Agent Patterns

- **Agent-as-graph** — Each agent is a node in a graph
- **Graph orchestration** — Graph manages the flow between agents
- **State machine** — Graph acts as a state machine

## Trade-offs

- **Pros:** Type-safe, simple, fast
- **Cons:** Less features than LangGraph, newer

## See Also

- [[pydantic-ai]]
- [[langgraph]]
- [[local-first-llm]]
- [[ai-alien-connection]]

