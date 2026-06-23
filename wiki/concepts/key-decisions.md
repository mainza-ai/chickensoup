---
title: "Key Decisions"
tags: [project, decisions, architecture]
created: 2026-06-22
updated: 2026-06-22
sources: [PROJECT_SPEC-2026]
related: [agent-architecture, local-first-llm, api-design, mcp-server, knowledge-graph-schema, technology-stack]
---

# Key Decisions

## Decision Table

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Agent framework | pydantic-graph + LangGraph | Type-safety (pydantic-graph) + features (LangGraph) |
| Knowledge graph | Neo4j | Natural fit for entity-relationship data |
| LLM | oMLX (Mac default), Ollama, LM Studio | Local-first, auto-discovery, fallback chain |
| API | FastAPI + OpenAPI | Modern, type-safe, auto-generated docs |
| MCP | FastMCP | Standard protocol, simple integration |
| Cache | Redis | Industry standard, fast, scalable |
| Container | Docker | Simple, portable, reproducible |
| CI/CD | GitHub Actions | Simple, integrated, free for open source |
| UI | SwiftUI | Native Apple design, macOS + iOS |
| UI theme | Light mode default | Warm, inviting, "chicken soup" |
| UI accent | #FF9500 (systemOrange) | Warm, distinctive |
| UI data | SwiftData | Simpler than Core Data |
| Quantum integration | Sequential pipeline | Pure functions, field geometry tensor as contract |
| Graph storage | Neo4j (source of truth) + SwiftData (cache) | Delegate graph queries, cache results locally |
| Wiki ingestion | Two-phase (deterministic → LLM) | Free edges from `[[wikiname]]`, LLM enrichment later |
| Platform | 50/50 macOS + iOS | Single codebase, structural platform overrides |
| Simulation tier | Three modes (light/medium/heavy) | CI through production, classical fallbacks |

## Agent Framework

**Decision:** pydantic-graph + LangGraph

**Rationale:** pydantic-graph provides type-safety for core agent orchestration. LangGraph provides advanced features (checkpointing, streaming, human-in-the-loop) for complex sub-workflows. The two-framework approach adds complexity but provides the best of both worlds.

## Knowledge Graph

**Decision:** Neo4j

**Rationale:** Neo4j is a natural fit for entity-relationship data. It supports Cypher queries, which are readable and powerful. It scales well for the expected data volume.

## LLM

**Decision:** oMLX (Mac default), Ollama, LM Studio

**Rationale:** Local-first approach with auto-discovery and fallback chain. oMLX is the default for Mac users. Ollama and LM Studio provide alternatives. All three provide OpenAI-compatible APIs.

## API

**Decision:** FastAPI + OpenAPI

**Rationale:** FastAPI is modern, type-safe, and auto-generates OpenAPI documentation. All request/response schemas are Pydantic models.

## MCP

**Decision:** FastMCP

**Rationale:** FastMCP is a simple, standard implementation of the Model Context Protocol. It integrates well with FastAPI and Pydantic AI.

## Cache

**Decision:** Redis

**Rationale:** Redis is the industry standard for in-memory caching. It is fast, scalable, and has excellent Python support.

## Container

**Decision:** Docker

**Rationale:** Docker is simple, portable, and reproducible. It provides a consistent environment for development, testing, and production.

## CI/CD

**Decision:** GitHub Actions

**Rationale:** GitHub Actions is simple, integrated with GitHub, and free for open source projects.

## UI

**Decision:** SwiftUI (not React + Vite)

**Rationale:** Native Apple design, native performance, Apple's design system, future direction. Works on macOS, iOS, iPadOS, watchOS, visionOS from a single codebase.

## UI Theme

**Decision:** Light mode as default, dark mode as toggle

**Rationale:** Warm, inviting, approachable, more accessible, more "chicken soup". Light mode feels more like a book, more like a research journal.

## UI Accent

**Decision:** #FF9500 (systemOrange)

**Rationale:** Warm, inviting, feels like chicken soup. Not cold like blue, not too sweet like pink. A strong accent that works well with Apple's light mode aesthetic.

## UI Data

**Decision:** SwiftData (not Core Data)

**Rationale:** Simpler, more intuitive, future direction. Less powerful than Core Data, but plenty for Chicken Soup.

## Quantum Integration

**Decision:** Sequential pipeline with pure functional interfaces

**Rationale:** Each quantum layer (Qiskit → CUDA-Q → PennyLane) is a pure function taking and returning a [[field-geometry-tensor]]. This makes layers independently testable, traceable (data flows left-to-right), and parallelization is additive (wrap in a bus adapter later without changing core logic). See [[integration-architecture]] for details.

## Knowledge Graph Storage

**Decision:** Neo4j as source of truth, SwiftData as read-through cache

**Rationale:** Neo4j's Cypher graph traversals (shortest-path, multi-hop, pattern matching) are too valuable to replicate in SwiftData. SwiftData handles offline cache, recent results, and write queues. Sync at entity level with timestamps.

## Wiki Ingestion

**Decision:** Two-phase ingestion (deterministic → LLM)

**Rationale:** Phase 1 parses YAML frontmatter and `[[wikiname]]` links for free edge extraction — zero LLM cost, complete correctness. Phase 2 enriches edges with semantic types via LLM, adding edges that wikiname syntax missed. See [[integration-architecture]].

## Platform Strategy

**Decision:** 50/50 macOS + iOS from a single shared codebase with structural platform overrides

**Rationale:** NavigationSplitView on macOS/iPad, TabView + NavigationStack on iPhone. Shared models, services, and business logic. Platform-adaptive views via conditional compilation and horizontalSizeClass.

## Simulation Tier

**Decision:** Three simulation modes: light (CI), medium (dev), heavy (production)

**Rationale:** All quantum layers have classical CPU/GPU fallbacks. Light mode completes in seconds for CI without quantum hardware. Heavy mode uses full resolution with GPU acceleration. See [[quantum-simulation-tier]].

## Tensor Summaries

**Decision:** MCP tensor summaries are computed on the server and cached in SwiftData. Client does not recompute locally.

**Rationale:** Full tensors are large (64³ × 4×4 × 8 bytes ≈ 8 MB per metric). Summaries (a few floats + validity flags) are trivial to cache. Server has the authoritative physics pipeline. Cached summaries display with "last refreshed" indicator; a refresh button makes a lightweight API call.

## Sync Merge Strategy

**Decision:** Field-level merge strategy, not blanket last-write-wins.

**Rationale:** Different fields need different strategies: `confidence` is server-authoritative, `user_notes` is client-authoritative, `sources[]` is union-with-dedup. Conflicts with confidence discrepancy > 0.1 are logged for manual review. See [[integration-architecture]] for the full merge table.

## Wiki Edge Promotion

**Decision:** Phase 2 (LLM enrichment) runs as a batch post-processing pass, not per-page.

**Rationale:** LLM calls are expensive and rate-limited. Batching 5-10 pages per call gives the LLM more context. Phase 1 (deterministic) runs per-page during ingestion and already produces a complete, correct graph. Phase 2 promotes `RELATED_TO` edges to typed edges only above a confidence threshold (default 0.7). See [[integration-architecture]].

## See Also

- [[agent-architecture]]
- [[technology-stack]]
- [[local-first-llm]]
- [[api-design]]
- [[mcp-server]]
- [[knowledge-graph-schema]]
- [[production-readiness]]
- [[ui-ux-design]]
