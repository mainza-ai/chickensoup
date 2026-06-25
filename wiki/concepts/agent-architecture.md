---
title: "Agent Architecture"
tags: [agent, architecture, multi-agent, pydantic-graph, langgraph]
created: 2026-06-22
updated: 2026-06-24
sources: []
related: [pydantic-ai, pydantic-graph, langgraph, local-first-llm, multi-llm-consensus, langgraph-workflows]
---

# Agent Architecture

Hybrid: pydantic-graph for top-level orchestration, LangGraph for complex sub-workflows with checkpointing and human-in-the-loop.

> **2026-06-24 update:** Major production hardening across all agents — see sections below for confidence gating, wiki file fallback, timeout isolation, and routing observability.

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
2. **LLM classifier** — OpenAI-compatible JSON classification via local LLM. Prompt now includes few-shot examples and explicit disambiguation (e.g. "plot timelines connected to Element 115" → `query`, not `navigate`)
3. **Heuristic fallback** — Keyword-based intent detection when no LLM available

Returns `ParsedQuery(intent, entities, structured_filters, confidence)`. Response caching via `@cache_decorator(ttl=300)`.

### Wiki Entity Lookup (2026-06-24)

Before LLM classification, a `_wiki_entity_lookup()` function scans `wiki/entities/`, `wiki/concepts/`, `wiki/projects/` filenames for fuzzy matches against query words. Discovered entities are injected into the LLM prompt as context hints and used as the primary entity list in the heuristic fallback. This fixes a key bug where "element 115" (uncapitalized) was passed as the entire query string instead of matched to `element-115.md`.

### Confidence Gating (2026-06-24)

The orchestrator's `ClassifyNode` checks `parsed.confidence < 0.6` before routing. Low-confidence classifications are redirected to `ResearchNode` regardless of intent, preventing LLM misclassifications (e.g. "plot" → `navigate`) from reaching the wrong sub-agent.

## Research Agent (`src/agents/research_agent.py`)

LangGraph workflow with 6 nodes:
1. `extraction_node` — Entity extraction from query
2. `neo4j_lookup_node` — Fuzzy search + neighborhood traversal; falls back to `_wiki_file_fallback()` when Neo4j returns nothing (2026-06-24)
3. `credibility_scoring_node` — Rule-based confidence (source count, recency, type)
4. `human_approval_gate` — Pause for human approval (interrupt)
5. `context_assembly_node` — Synthesize findings into context
6. `check_human_approval` — Conditional edge routing

Features: `MemorySaver` checkpointing, human-in-the-loop via LangGraph interrupts.

### Wiki File Fallback (2026-06-24)

When Neo4j is offline or returns no results, `_wiki_file_fallback()` reads wiki markdown files directly from `wiki/entities/`, `wiki/concepts/`, `wiki/projects/`. It parses YAML frontmatter, extracts content_preview and tags, and returns graph-context-shaped dicts that flow through the existing assembly pipeline unchanged. This makes the research agent functional even without a running Neo4j instance.

## Navigation Agent (`src/agents/navigation_agent.py`)

Pipelines three quantum layers:
1. `simulate_spacetime_metrics` (Spacetime Engine / Qiskit)
2. `manipulate_spacetime_field` (Field Manipulator / CUDA-Q)
3. `find_optimal_path` (AI Navigator / PennyLane)

Success determined by `bubble_stability > 0.3`.

### Entity-to-Navigation Mapping (2026-06-24)

`NavigateNode` now infers navigation parameters from extracted entities: 4-digit numbers are extracted as target_year, the first non-year entity is used as destination name. Falls back to defaults (Earth-2026 → Earth-1947) when no entities are available.

## Orchestrator (`src/agents/orchestrator.py`)

pydantic-graph `OrchestratorGraph` with:
- **ClassifyNode** — routes to correct sub-agent (with confidence gating: < 0.6 → ResearchNode)
- **ResearchNode** — delegates to Research Agent
- **NavigateNode** — delegates to Navigation Agent (produces `answer` key with human-readable summary)
- **StatusNode** — returns system status (produces `answer` key with status summary)

### Synthesize Answer Post-Processing (2026-06-24)

The `execute()` method applies a `synthesize_answer` pass after every graph run. If the output lacks an `answer` key or it is empty, the method synthesizes one from available data (navigation results → readable summary, system_status → status string, fallback → generic message). This ensures the HTTP and WebSocket endpoints always receive a non-empty answer regardless of which node executed.

### Timeout Isolation (2026-06-24)

Three-tier timeout architecture:
| Tier | Component | Timeout |
|------|-----------|---------|
| 1 | LLM intent classification | 15s |
| 2 | LLM summarization | 30s |
| 3 | Orchestrator top-level | 60s |

Each timeout is independently configurable in the source file. A timeout at any tier returns a graceful error message rather than hanging indefinitely.

### Observability (2026-06-24)

`GET /debug/routing?query=...` runs the classification step only and returns the parsed query, wiki matches, routing decision, and confidence gate status without executing the full pipeline.

## Shared Answer Extraction (2026-06-24)

The `_build_query_response()` helper in `main.py` consolidates the previously duplicated `output.get("answer", "No response generated.")` pattern across the HTTP POST `/query` handler and the WebSocket `/ws/agent` handler. It handles paused states, error states, and conversation history consistently.

Dependency injection via `OrchestratorDeps`, thread-based execution per query.

## See Also

- [[pydantic-ai]]
- [[pydantic-graph]]
- [[langgraph]]
- [[langgraph-workflows]]
- [[local-first-llm]]
- [[multi-llm-consensus]]
