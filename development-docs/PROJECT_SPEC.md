---
title: "Project Chicken Soup — Specification"
tags: [project, specification, chicken-soup]
created: 2026-06-22
updated: 2026-06-22
sources: [Grusch-2023, Lazar-1989]
related: [time-travel-machinery, quantum-systems, earth-as-space-craft, ai-alien-connection]
---

# Project Chicken Soup — Specification

## Overview

Project Chicken Soup is a production-quality, local-first AI system that simulates and explores time travel using quantum computation, with a rich knowledge graph of UFO/Alien/Time Travel lore, and an AI agent that orchestrates everything.

## Architecture

### Three-Layer Architecture

1. **Spacetime Engine (Qiskit)** — Simulates the fabric of time, calculates time dilation based on velocity and gravity, models closed timelike curves
2. **Field Manipulator (CUDA-Q)** — Manipulates the field of spacetime itself, creates a bubble, shifts the field, lets the traveler ride the wave
3. **AI Navigator (PennyLane)** — Uses a neural-field model to find optimal paths, learns patterns in the field via quantum machine learning, hardware backends: D-Wave (optimization), IonQ (precision)

### Timeline Model

Many-Worlds. When you travel back in time, you don't change the past — you branch into a new timeline. The original timeline continues unchanged.

### LLM Layer (Local-First)

- **oMLX** (default for Mac) — `http://127.0.0.1:9000/v1`
- **Ollama** — `http://localhost:11434/v1`
- **LM Studio** — `http://localhost:1234/v1`

Auto-discovery on startup, fallback chain: oMLX → Ollama → LM Studio.

## Technology Stack

| Layer | Technology |
|-------|-----------|
| API | FastAPI |
| Agent Framework | Pydantic AI + pydantic-graph |
| Complex Workflows | LangGraph |
| MCP | FastMCP |
| Knowledge Graph | Neo4j |
| Spacetime Engine | Qiskit |
| Field Manipulator | CUDA-Q |
| AI Navigator | PennyLane |
| Optimization | D-Wave |
| Precision | IonQ |
| Config | Pydantic Settings |
| Cache | Redis |
| Batching | Celery/Ray |
| Observability | OpenTelemetry |
| Testing | pytest |
| Build | pyproject.toml |
| Container | Docker + docker-compose |

## Project Structure

```
chickensoup/
├── AGENTS.md
├── PROJECT_SPEC.md
├── README.md
├── pyproject.toml
├── .python-version
├── .env.example
├── .gitignore
├── docker-compose.yml
├── Dockerfile
├── papers/
├── wiki/
├── src/
│   ├── main.py
│   ├── config.py
│   ├── discovery.py
│   ├── models.py
│   ├── api/
│   ├── mcp/
│   ├── agents/
│   ├── langgraph_workflows/
│   ├── knowledge_graph/
│   ├── spacetime_engine/
│   ├── field_manipulator/
│   ├── ai_navigator/
│   ├── llm/
│   ├── cache/
│   └── utils/
├── tests/
└── notebooks/
```

## Agent Design

### Multi-Agent Approach

Uses **pydantic-graph** for core agent orchestration and **LangGraph** for complex sub-workflows.

- **Query Agent** — Receives user queries, determines intent, routes to appropriate sub-agent
- **Research Agent** — Explores the knowledge graph (Neo4j) for evidence, credibility, and related claims
- **Navigation Agent** — Runs the AI Navigator (PennyLane) to compute optimal paths through spacetime
- **Orchestrator Agent** — Coordinates the flow: query → research → navigation → answer

### Multi-Agent Architecture

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

### LangGraph Features

LangGraph provides the following features for complex sub-workflows:

- **Checkpointing** — Save state at every superstep for durable execution
- **Human-in-the-loop** — Interrupt and resume workflows with human input
- **Streaming** — Native streaming support for real-time outputs
- **Subgraphs** — First-class subgraph support for nested workflows
- **Persistence** — Built-in, memory, and Postgres persistence
- **Parallel execution** — Run nodes in parallel for better performance
- **Conditional edges** — Dynamic routing between nodes based on conditions
- **Memory** — Short-term and long-term memory support
- **Interrupt handling** — Handle interrupts gracefully
- **Command handling** — External commands affect the graph

## Knowledge Graph Schema

### Nodes
- Person, Place, Concept, QuantumPlatform, Algorithm, Event, Object, Project, Entity, Paper

### Relationships
- WORKED_AT, TESTIFIED_AT, CLAIMED_BY, PART_OF, USES, IMPLEMENTS, RELATED_TO, HAS_PROPERTY, CONNECTED_TO, ORCHESTRATES, CITES

### Properties
- confidence (0-1), source, date, type

## API Design

### Endpoints
- `POST /query` — Submit a query, get AI interpretation
- `GET /graph/{entity}` — Retrieve entity and related data
- `POST /navigate` — Compute optimal time travel path
- `GET /status` — System health (LLM, Neo4j, quantum backends)
- `GET /models` — List available LLM models
- `POST /ingest` — Ingest new wiki content into knowledge graph

### Request/Response
All Pydantic models, typed.

## MCP Server

### Tools
- analyze_field
- simulate_spacetime
- find_paths
- query_graph
- get_evidence
- explore_concept

## Implementation Phases

### Phase 1: Foundation (Weeks 1-4)
1. Knowledge graph schema
2. Project structure
3. Configuration system
4. Core models
5. Knowledge graph implementation
6. Agent framework
7. FastAPI
8. Logging
9. Docker Compose

### Phase 2: Core Functionality (Weeks 5-8)
10. Quantum circuits (Qiskit-first)
11. LLM integration (multi-provider)
12. Graph ingestion from wiki
13. Query pipeline
14. Pydantic Graph
15. LangGraph integration
16. Evaluation framework
17. Error handling
18. MCP server

### Phase 3: Enhancement (Weeks 9-12)
19. Caching layer (Redis)
20. Async processing
21. Batch processing
22. Observability (OpenTelemetry)
23. Multi-agent orchestration
24. API documentation
25. CI/CD pipeline
26. Docker

### Phase 4: Advanced (Weeks 13-16)
27. Multi-LLM support
28. Real quantum hardware integration
29. Performance optimization
30. Dashboard
31. User-facing UI
32. Enhanced knowledge graph
33. Rate limiting & security
34. Release process

## Risks & Mitigation

| Risk | Mitigation |
|------|-----------|
| Quantum hype vs. reality | Classical baselines; measure advantage empirically |
| Over-reliance on LLM | System works without LLM; multi-LLM support |
| Knowledge graph bloat | Graph partitioning; hierarchical indexing |
| Neo4j scalability | Plan for partitioning; migration to distributed graph |
| Complexity creep | Phase platform additions; start minimal |
| Data quality in wiki | Confidence scores; source tracking |
| Two-framework complexity | Clear boundaries; shared agent definitions |
| oMLX model discovery | Robust fallback chain; explicit config |

## Key Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Agent framework | pydantic-graph + LangGraph | Type-safety + features |
| Knowledge graph | Neo4j | Natural fit for entities |
| LLM | oMLX (Mac default), Ollama, LM Studio | Local-first, auto-discovery |
| API | FastAPI + OpenAPI | Modern, type-safe, auto-docs |
| MCP | FastMCP | Standard protocol |
| Cache | Redis | Industry standard |
| Container | Docker | Simple, portable |
| CI/CD | GitHub Actions | Simple, integrated |
| UI | SwiftUI | Native Apple design, macOS + iOS |
| UI theme | Light mode default | Warm, inviting, "chicken soup" |
| UI accent | #FF9500 (systemOrange) | Warm, distinctive |
| UI data | SwiftData | Simpler than Core Data |

## UI/UX Design

The UI is built with **SwiftUI** (not React + Vite), works on **macOS and iOS** from a single codebase, uses **light mode as default**, and has a **warm, inviting** design language inspired by Apple's Human Interface Guidelines.

### Design Language
- **Liquid Glass** — dynamic material that changes based on what's behind it
- **SF Pro Typography** — Apple's type scale, hierarchy through size and weight
- **SF Symbols** — 5000+ icons, adapt to light/dark mode
- **Material Hierarchy** — thin, regular, thick materials for depth
- **Rounded Corners** — 12-20px for panels, 8-12px for buttons
- **Subtle Gradients** — barely noticeable, add polish
- **Generous Whitespace** — airy, uncluttered
- **Restraint** — not everything is animated or colorful

### Core Interfaces
1. **Temporal Query Interface** — natural language input, structured query toggle, streaming output
2. **Knowledge Graph Explorer** — interactive graph, pan/zoom/click
3. **Timeline View** — visual timeline of events across time
4. **AI Navigator** — recommendations, predictions, field configuration
5. **Data Ingestion** — upload, AI entity extraction, quality scoring

### Platform Strategy
- **macOS-first** — windowed layout with NavigationSplitView (sidebar + main content)
- **iOS** — full-screen, gesture-driven, tab-based navigation
- **Shared codebase** — SwiftData models, services; different views for each platform

## Agent Skills

Four agent skills from Paul Hudson (twostraws) are installed in `.agents/skills/` and automatically referenced during Swift implementation:

| Skill | Repository | What It Covers |
|-------|-----------|----------------|
| **SwiftUI Pro** | twostraws/swiftui-agent-skill | iOS 26+ APIs, deprecated API, VoiceOver, performance, navigation, data flow, animations, design |
| **SwiftData Pro** | twostraws/SwiftData-Agent-Skill | @Model, @Query, predicates, indexes, migrations, relationships, iCloud, class inheritance |
| **Swift Concurrency Pro** | twostraws/Swift-Concurrency-Agent-Skill | async/await, actors, Sendable, task groups, @concurrent, structured concurrency, cancellation, async streams |
| **Swift Testing Pro** | twostraws/Swift-Testing-Agent-Skill | @Test, #expect, #require, parameterized tests, traits, exit tests, confirmations |

### Key Rules from Agent Skills

- **@Query must only be used inside SwiftUI views** — not in classes
- **isEmpty == false crashes at runtime** — use !isEmpty instead
- **Don't use @unchecked Sendable** — prefer actors, value types, or sending parameters
- **Swift Testing does NOT support UI tests** — use XCTest for UI tests
- **Target iOS 26+ and Swift 6.2+** — new features are current
- **Prefer async/await over closure-based variants**
- **Prefer structured concurrency (task groups) over unstructured Task {}**
- **Break different types into different Swift files** — not multiple structs in one file
- **Use consistent project structure by feature** — not by type

### Installation

Installed via `npx skills add` into `.agents/skills/`:
```bash
npx skills add https://github.com/twostraws/swiftui-agent-skill --skill swiftui-pro
npx skills add https://github.com/twostraws/SwiftData-Agent-Skill --skill swiftdata-pro
npx skills add https://github.com/twostraws/Swift-Concurrency-Agent-Skill --skill swift-concurrency-pro
npx skills add https://github.com/twostraws/Swift-Testing-Agent-Skill --skill swift-testing-pro
```

Each skill has a `SKILL.md` and `references/` directory with detailed rules loaded on demand during code review.
