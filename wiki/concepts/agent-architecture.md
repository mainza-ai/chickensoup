---
title: "Agent Architecture"
tags: [agent, architecture, multi-agent, pydantic-graph, langgraph]
created: 2026-06-22
updated: 2026-06-23
sources: []
related: [pydantic-ai, pydantic-graph, langgraph, local-first-llm, multi-llm-consensus, langgraph-workflows]
---

# Agent Architecture

Hybrid: pydantic-graph for top-level orchestration, LangGraph for complex sub-workflows with checkpointing and human-in-the-loop.

## Components

```
                  ┌──────────────────────────────┐
                  │   Orchestrator (pydantic-graph) │
                  │   4 nodes: Classify, Research,  │
                  │   Navigate, Status              │
                  └──────────┬───────────────────┘
                             │
              ┌──────────────┼──────────────┐
              │              │              │
       ┌──────▼──────┐ ┌────▼────┐  ┌──────▼──────┐
       │ Query Agent  │ │Research │  │ Navigation   │
       │ 3-tier parse │ │ Agent   │  │ Agent        │
       │ TQL→LLM→     │ │LangGraph│  │ pipe: sim→   │
       │ heuristic     │ │5 nodes │  │ field→path   │
       └──────┬──────┘ └────┬────┘  └──────┬──────┘
              │             │              │
              │        ┌────▼────┐         │
              │        │ Neo4j   │         │
              └────────┤ KG     ├─────────┘
                       │ queries │
                       └─────────┘
```

## Query Agent (`src/agents/query_agent.py`)

3-tier intent parsing:
1. **TQL regex parser** — `KEY:VALUE` patterns (TIMELINE, TIME TRAVEL, EVIDENCE, CAUSAL, ANOMALY)
2. **LLM classifier** — OpenAI-compatible JSON classification via local LLM
3. **Heuristic fallback** — Keyword-based intent detection when no LLM available

Returns `ParsedQuery(intent, entities, structured_filters, confidence)`. Response caching via `@cache_decorator(ttl=300)`.

## Research Agent (`src/agents/research_agent.py`)

LangGraph workflow with 6 nodes:
1. `extraction_node` — Entity extraction from query
2. `neo4j_lookup_node` — Fuzzy search + neighborhood traversal
3. `credibility_scoring_node` — Rule-based confidence (source count, recency, type)
4. `human_approval_gate` — Pause for human approval (interrupt)
5. `context_assembly_node` — Synthesize findings into context
6. `check_human_approval` — Conditional edge routing

Features: `MemorySaver` checkpointing, human-in-the-loop via LangGraph interrupts.

## Navigation Agent (`src/agents/navigation_agent.py`)

Pipelines three quantum layers:
1. `simulate_spacetime_metrics` (Spacetime Engine / Qiskit)
2. `manipulate_spacetime_field` (Field Manipulator / CUDA-Q)
3. `find_optimal_path` (AI Navigator / PennyLane)

Success determined by `bubble_stability > 0.3`.

## Orchestrator (`src/agents/orchestrator.py`)

pydantic-graph `OrchestratorGraph` with:
- **ClassifyNode** — routes to correct sub-agent
- **ResearchNode** — delegates to Research Agent
- **NavigateNode** — delegates to Navigation Agent
- **StatusNode** — returns system status

Dependency injection via `OrchestratorDeps`, thread-based execution per query.

## See Also

- [[pydantic-ai]]
- [[pydantic-graph]]
- [[langgraph]]
- [[langgraph-workflows]]
- [[local-first-llm]]
- [[multi-llm-consensus]]
