---
title: "Project Structure"
tags: [project, structure, organization, living-almanac]
created: 2026-06-22
updated: 2026-07-15
sources: [living-almanac, api-design, project-structure]
related: [agent-architecture, technology-stack, api-design, mcp-server, knowledge-graph-schema, wiki-file-system, chat-to-wiki-pipeline, ingestion-pipeline, frontend-settings-menu]
---

# Project Structure

## Root

```
chickensoup/
├── AGENTS.md               # Wiki schema for LLM agents + Apple guides index
├── CHANGELOG.md            # Project changelog
├── README.md               # Project overview + Living Almanac DOD commands
├── pyproject.toml          # Python dependencies (uv, 3.12+)
├── uv.lock                 # Python lockfile
├── skills-lock.json        # Agent skill lockfile
├── .env.example            # Environment vars including LAST30DAYS_* docs
├── .gitignore              # Xcode, Python, .env, development-docs
├── Dockerfile              # Container build
├── docker-compose.yml      # Neo4j + Redis services
├── assets/                 # Logos, favicons, images, slide decks
├── development-docs/       # Implementation plan, chickensoup-living-almanac-implementation-spec.md
├── papers/                 # 61 academic PDFs, all wiki-covered per science-reference-library.md
├── wiki/                   # Obsidian vault (635+ pages)
│   ├── entities/           # 59 pages
│   ├── concepts/           # 200+ pages
│   ├── projects/           # 80+ pages
│   ├── raw/                # 80+ immutable docs: 61 PDFs + Mannheim transcripts + 20 Apple guides + pulse/ + almanac/
│   │   ├── pulse/          # Dated pulse snapshots — entity-scoped evidence JSON+MD
│   │   └── almanac/        # Dated HTML+MD State of the Anomaly briefs
│   ├── dev/                # 30+ dev documentation pages (not ingested to Neo4j)
│   └── plan/               # 15+ implementation plans and audits
├── src/                    # Python backend
├── tests/                  # Python test suite (39 files, 102 tests)
├── Project Chicken Soup/   # SwiftUI macOS/iOS app (60+ Swift files, ~13,400 lines)
├── .agents/                # twostraws agent skills (swiftui-pro, swiftdata-pro, swift-concurrency-pro, swift-testing-pro)
├── .github/workflows/      # CI pipeline
└── .headroom/              # LLM memory persistence (SQLite)
```

## Python Backend (`src/`)

```
src/
├── main.py                 # FastAPI entry point (~2878 lines) — 69+ endpoints + WebSocket + SSE + middleware
├── config.py               # Pydantic Settings (50+ fields)
├── models.py               # Core Pydantic models (383 lines)
├── llm_client.py           # LLM query client with semaphore concurrency, circuit breaker, model fallback chain (293 lines)
├── llm_circuit_breaker.py  # Lightweight circuit breaker for LLM calls (108 lines)
├── discovery.py            # LLM provider auto-discovery — local (omlx/ollama/lmstudio) + cloud (nvidia/openrouter/custom) (194 lines)
├── cache.py                # RedisCache + cache_decorator (149 lines)
├── rate_limiter.py         # In-memory sliding window rate limiter (62 lines)
├── progress_tracker.py     # Redis-backed progress tracking for 7 background sections (93 lines)
├── reconciliation_gate.py  # Redis busy-flag coordination for background tasks (111 lines)
├── idle_sentinel.py        # System-wide activity tracker using Redis (119 lines)
├── observability.py        # OpenTelemetry metrics + tracing — 12 metrics, no console exporter (128 lines)
├── multi_llm.py            # Multi-LLM consensus via Jaccard word overlap (106 lines)
├── quantum_scheduler.py    # Quantum job scheduler — in-memory jobs, IBM/D-Wave/IonQ stubs (137 lines)
├── scheduler.py            # Background scheduling loops: chat ingest, idle ingestion, queue rebuild, fallback retry (1014 lines)
├── budget.py               # BudgetTracker with Lua atomic check+incr, HOLD, approve_hold, reset_month
├── last30days_adapter.py   # Normalizes last30days CLI JSON/md to ClaimEvidence[]
├── agents/
│   ├── orchestrator.py     # pydantic-graph orchestration (353 lines) — Classify→Research→Navigate→Status→Enrich
│   ├── query_agent.py      # TQL/LLM/heuristic intent parser (302 lines)
│   ├── research_agent.py   # LangGraph research workflow — 6 nodes, RedisKVCheckpointer, human approval gate (578 lines)
│   ├── navigation_agent.py # Quantum pipeline orchestration (44 lines)
│   ├── pulse_agent.py      # Entity-scoped last30days ingestion, budget-guarded, shell=False (397 lines)
│   ├── tribunal_agent.py   # Skeptic/Empiricist/Believer + referee LangGraph, gated cost control (255 lines)
│   ├── ingest_agent.py     # LLM-based content analysis for wiki page extraction (169 lines)
│   └── chat_ingest_agent.py # Conversation-aware LLM extraction for chat-to-wiki (206 lines)
├── knowledge_graph/
│   ├── connection.py       # Neo4j driver singleton with circuit breaker, connection pooling (124 lines)
│   ├── schema.py           # Constraints + indexes + fulltext index probe (67 lines)
│   ├── ingest.py           # Wiki→Neo4j ingestion pipeline — label inference, date extraction, edge heuristics (519 lines)
│   ├── queries.py          # Fulltext search + neighborhood + evidence queries (133 lines)
│   ├── temporal.py         # Temporal event queries with Redis caching (100 lines)
│   └── temporal_causality.py # PRECEDED_BY + CAUSED relationship builder (108 lines)
├── wiki/
│   ├── writer.py           # Wiki page CRUD, cross-referencing, index/log (295 lines)
│   ├── watcher.py          # Filesystem watcher + reconciliation engine (327 lines)
│   ├── paths.py            # Centralized path resolution (55 lines)
│   ├── backup.py           # Wiki backup, export, import, cleanup (180 lines)
│   ├── cleanup.py          # Content vs engineering page deletion (253 lines)
│   ├── pulse_writer.py     # Pulse snapshot read/write (171 lines)
│   └── pdf_extract.py      # PDF text extraction (62 lines)
├── almanac/
│   ├── __init__.py
│   └── timeline.py         # pulse/*.json + git log → TimelinePoints (349 lines)
├── spacetime_engine/       # Qiskit/NumPy spacetime simulation
├── field_manipulator/      # Bubble stability + resonance model (CUDA-Q or NumPy)
├── ai_navigator/           # PennyLane variational circuit pathfinding
├── mcp/
│   └── tools.py            # FastMCP tools
└── api/
    └── auth.py             # API key header auth checker
```

## SwiftUI App (`Project Chicken Soup/`)

Current (before frontend Living Almanac plan):

```
Project Chicken Soup/
├── Project_Chicken_SoupApp.swift
├── ContentView.swift                      # Main orchestrator (496 lines) — NavigationSplitView desktop + TabView phone + badge
├── Models/
│   ├── LoreEntity.swift
│   ├── TemporalEvent.swift
│   └── TimelineBranch.swift
├── Shared/
│   ├── Services/
│   │   ├── BackendService.swift           # Central (454 lines) — will add 9 almanac methods per frontend-settings-menu.md plan
│   │   ├── GraphService.swift             # 211 lines
│   │   ├── WikiService.swift
│   │   ├── ChatService.swift              # 136 lines
│   │   ├── ConfigService.swift            # will add last30daysEnabled + budget fields
│   │   ├── LLMDiscoveryService.swift
│   ├── Networking/
│   │   ├── APIClient.swift                # Actor, 90s timeout, 5 error types
│   │   └── APIModels.swift                # 822 lines, 20+ structs — will add 15 almanac structs per plan
│   └── DesignSystem/
│       ├── DesignConstants.swift
│       ├── SkeletonModifier.swift
│       └── PremiumSlider.swift
└── Features/
    ├── Timeline/
    │   ├── Layouts/TimelineLayout.swift
    │   └── Views/ (TimelineView, TimelineNodeView, EventDetailView, AdvancedTimelineFilterView, TimelineBranchMergeSheet)
    │   └── (NEW) LivingAlmanacTimelineView.swift — chart + scrubber per frontend-settings-menu.md
    ├── KnowledgeGraph/Views/ (GraphExplorerView with ConnectionLineShape, SidebarDetailsView 316 lines, EntityDetailView 128 lines, EvidenceHistoryView)
    │   └── (NEW) ClaimConfidenceRow.swift — epi/trac gauges, state badge — per plan
    ├── AINavigator/Views/ (AINavigatorView 296 lines, RealitySpacetimeView)
    ├── Query/Views/ (QueryOverlayView 161, ChatHistoryView 139, MultimodalInputView 356, LiquidGlassView)
    ├── DataIngestion/Views/ (DataIngestionView 1090, LoreRepositoryView, WikiInsightNotificationView 64)
    ├── Wiki/Views/ (WikiBrowserView, WikiPageDetailView — will add divergence + claim_confidences rows per plan)
    └── Settings/Views/SettingsView.swift (771 lines — will add livingAlmanacSection per plan: budget display, HOLD approve, pulse per entity, pulse history, almanac dry-run/live + history WKWebView)
```

Planned additions per `wiki/plan/frontend-settings-menu.md`:

- APIModels: 15 new Codable structs (ClaimEvidence, ClaimConfidence, DrivingClaim, DivergenceResult, PulseResult, TimelinePoint/Response, PulseHistoryEntry/Response, BudgetStatus, AlmanacHistoryEntry/Response, EntanglementEntry/Response, TribunalResponse/Disagreement)
- BackendService: 9 new async methods (fetchBudgetStatus, approveBudgetHold, triggerPulse, fetchPulseHistory, fetchDivergence, fetchTimeline, fetchEntanglement, runTribunal, generateAlmanac, fetchAlmanacHistory)
- SettingsView: livingAlmanacSection with 5 subsections (network opt-in toggle, budget display with HOLD banner, entities+tiers with Pulse Now, pulse history list, almanac generation dry-run sheet + history WKWebView)
- TimelineView: LivingAlmanacTimelineView with Swift Charts 3D (3 lines epi/trac/divergence) + scrubber
- EntityDetail/Wiki detail: divergence risk badge + driving claims + claim confidence rows

## Tests (`tests/`)

39 files, 102 tests passing (`test_new_features.py` covers 38 tests across all new endpoints).

Key test files: `test_new_features.py`, `conftest.py` (mocked Neo4j+Redis). Core endpoints tested: `/health`, `/search`, `/timeline`, `/simulate`, `/events`, `/temporal/causality`, `/query`, `/config`, rate limiting, circuit breaker, SSE streaming (1 skipped — TestClient incompatibility).

## Infrastructure

- Docker: Dockerfile (single-stage, needs `.dockerignore` and non-root user) + docker-compose for Neo4j + Redis (no healthchecks, no resource limits)
- CI: No CI/CD configured (`.github/workflows/` directory doesn't exist)
- LLM providers: NVIDIA (cloud, 116 models), omlx (local, 6 models), OpenRouter (config slot), custom (config slot)

## See Also

- [[technology-stack]]
- [[agent-architecture]] — includes tribunal + wavefunction wiring
- [[api-design]] — 40+ endpoints
- [[mcp-server]]
- [[knowledge-graph-schema]]
- [[wiki-file-system]]
- [[chat-to-wiki-pipeline]]
- [[ingestion-pipeline]]
- [[credibility-scoring]]
- [[pulse-agent]]
- [[budget-tracking]]
- [[frontend-settings-menu]]
- [[project-structure]] — self
- [[living-almanac]] — 7-phase plan (all phases shipped)
