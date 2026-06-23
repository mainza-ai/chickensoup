---
title: "Project Chicken Soup Specification"
tags: [project, specification, architecture]
created: 2026-06-22
updated: 2026-06-22
sources: []
related: [integration-architecture, field-geometry-tensor, agent-architecture, knowledge-graph-schema, api-design, mcp-server, ui-ux-design, key-decisions]
---

# Project Chicken Soup Specification

This page is the wiki-native summary of the full specification (see `development-docs/PROJECT_SPEC.md` for the complete document). It covers the architecture, decisions, and design at a high level with links to detailed pages.

## Architecture

### Three-Layer Quantum Pipeline

```
Qiskit (Spacetime Engine) → CUDA-Q (Field Manipulator) → PennyLane (AI Navigator)
```

Sequential pipeline with the [[field-geometry-tensor]] as the contract between layers. Each layer is a pure function: `FGT → Layer(FGT, **params) → FGT`. See [[integration-architecture]] for the decision rationale.

### Multi-Agent System

| Agent | Framework | Responsibility |
|-------|-----------|---------------|
| Orchestrator | pydantic-graph | Coordinates query → research → navigation → answer |
| Query Agent | pydantic-graph | Intent detection, query decomposition |
| Research Agent | LangGraph | Knowledge graph exploration, evidence scoring |
| Navigation Agent | pydantic-graph + LangGraph | Path computation via AI Navigator |
| Knowledge Graph | pydantic-graph | Entity/relationship storage and query |

See [[agent-architecture]] for details.

### Local-First LLM Layer

Auto-discovery with fallback: **oMLX → Ollama → LM Studio**. All three provide OpenAI-compatible APIs. The system works without a backend — oMLX provides on-device inference for the SwiftUI app.

## Technology Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| API | FastAPI + OpenAPI | REST endpoints, auto-generated docs |
| Agents | Pydantic AI + pydantic-graph | Core orchestration |
| Workflows | LangGraph | Complex sub-workflows (research, navigation, eval) |
| MCP | FastMCP | Tool exposure for external agents |
| Knowledge Graph | Neo4j | Entity/relationship storage |
| Cache | Redis | LLM response cache, quantum result cache |
| Spacetime Engine | Qiskit | Metric tensor computation |
| Field Manipulator | CUDA-Q | Metric perturbation |
| AI Navigator | PennyLane + D-Wave + IonQ | Path optimization |
| Frontend | SwiftUI + SwiftData | macOS + iOS app |
| Observability | OpenTelemetry | Tracing, metrics, logging |
| Container | Docker + docker-compose | Reproducible environments |

## Key Decisions

All decisions with rationale are in [[key-decisions]]. Major themes:

- **Swift 6.4** — Latest Swift version for implementation
- **SwiftUI** — Native Apple UI (not React)
- **Neo4j + SwiftData** — Graph DB for queries, local cache for offline
- **Sequential pipeline** — Correctness first, parallelization later
- **Two-phase wiki ingestion** — Deterministic frontmatter parsing first, LLM enrichment second
- **Three-mode simulation** — Light (CI), medium (dev), heavy (production)
- **50/50 platform** — Equal macOS and iOS investment

## API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/query` | POST | Submit a query, get AI interpretation |
| `/graph/{entity}` | GET | Retrieve entity and related data |
| `/navigate` | POST | Compute optimal time travel path |
| `/status` | GET | System health (LLM, Neo4j, quantum backends) |
| `/models` | GET | List available LLM models |
| `/ingest` | POST | Ingest new wiki content into knowledge graph |

See [[api-design]] for full schemas.

## MCP Tools

| Tool | Purpose |
|------|---------|
| `analyze_field` | Run field manipulation analysis on a region of spacetime |
| `simulate_spacetime` | Run a spacetime simulation with configurable parameters |
| `find_paths` | Find optimal time travel paths between two points |
| `query_graph` | Query the knowledge graph for entities and relationships |
| `get_evidence` | Get evidence for a claim from the knowledge graph |
| `explore_concept` | Explore a concept and related claims with depth |

See [[mcp-server]] for parameter schemas and example calls.

## Implementation Phases

| Phase | Duration | Focus |
|-------|----------|-------|
| 1: Foundation | Weeks 1-4 | KG schema, project structure, config, core models, API, Docker |
| 2: Core | Weeks 5-8 | Quantum circuits, LLM integration, wiki ingestion, agent pipeline |
| 3: Enhancement | Weeks 9-12 | Redis caching, async processing, observability, CI/CD |
| 4: Advanced | Weeks 13-16 | Multi-LLM, real quantum hardware, UI frontend, security |

See `development-docs/PROJECT_SPEC.md` for the detailed implementation plan.

## See Also

- [[integration-architecture]] — How subsystems connect
- [[field-geometry-tensor]] — The contract between quantum layers
- [[agent-architecture]] — Multi-agent design
- [[key-decisions]] — All architectural decisions
- [[knowledge-graph-schema]] — Graph node/edge types
- [[api-design]] — Endpoint schemas
- [[mcp-server]] — MCP tool definitions
- [[ui-ux-design]] — Frontend design language
- [[quantum-simulation-tier]] — Simulation modes
