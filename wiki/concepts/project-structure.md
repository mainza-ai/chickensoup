---
title: "Project Structure"
tags: [project, structure, organization]
created: 2026-06-22
updated: 2026-06-25
sources: []
related: [agent-architecture, technology-stack, api-design, mcp-server, knowledge-graph-schema, wiki-file-system, chat-to-wiki-pipeline, ingestion-pipeline]
---

# Project Structure

## Root

```
chickensoup/
├── AGENTS.md               # Wiki schema for LLM agents
├── CHANGELOG.md            # Project changelog
├── README.md               # Project overview with logo + architecture
├── pyproject.toml          # Python dependencies (uv)
├── uv.lock                 # Python lockfile
├── skills-lock.json        # Agent skill lockfile
├── .env.example            # Environment variable documentation
├── .gitignore              # Xcode, Python, .env, development-docs
├── Dockerfile              # Container build
├── docker-compose.yml      # Neo4j + Redis services
├── assets/                 # Logos, favicons, images, slide decks
├── development-docs/       # Implementation plan, temp transcripts, videos
├── papers/                 # 3 academic PDFs
├── wiki/                   # Obsidian vault (179 pages)
├── src/                    # Python backend (22 source files)
├── tests/                  # Python test suite (9 files, ~30 tests)
├── Project Chicken Soup/   # SwiftUI macOS/iOS app (Xcode project, 33+ Swift files)
├── .agents/                # twostraws agent skills
├── .github/workflows/      # CI pipeline
└── .headroom/              # LLM memory persistence (SQLite)
```

## Python Backend (`src/`)

```
src/
├── main.py                 # FastAPI entry point (~1175 lines)
├── config.py               # Pydantic Settings (24+ fields)
├── models.py               # Core request/response Pydantic models (20+ models)
├── discovery.py            # LLM provider auto-discovery (158 lines)
├── cache.py                # RedisCache + cache_decorator (133 lines)
├── observability.py        # OpenTelemetry metrics + tracing (57 lines)
├── multi_llm.py            # Multi-LLM consensus engine (122 lines)
├── quantum_scheduler.py    # Quantum job scheduler (137 lines)
├── scheduler.py            # Periodic chat-to-wiki background loop (~465 lines)
├── tasks.py                # Celery async task definitions (83 lines)
├── agents/
│   ├── orchestrator.py     # pydantic-graph orchestration (262 lines)
│   ├── query_agent.py      # TQL/LLM/heuristic intent parser (245 lines)
│   ├── research_agent.py   # LangGraph research workflow (391 lines)
│   ├── navigation_agent.py # Quantum pipeline orchestration (44 lines)
│   ├── ingest_agent.py     # File/folder content analysis → wiki pages (182 lines)
│   └── chat_ingest_agent.py # Conversation-aware LLM extraction (208 lines)
├── wiki/
│   ├── writer.py           # Wiki page CRUD, cross-referencing, index/log (223 lines)
│   └── __init__.py
├── knowledge_graph/
│   ├── connection.py       # Neo4j connection singleton
│   ├── schema.py           # Constraints + indexes
│   ├── ingest.py           # Wiki→Neo4j ingestion pipeline (267 lines)
│   └── queries.py          # Cypher query functions
├── spacetime_engine/
│   └── qiskit_simulation.py # 2-qubit circuit simulation + fallback
├── field_manipulator/
│   └── cuda_simulation.py   # Bubble stability + resonance model
├── ai_navigator/
│   └── pennylane_qml.py     # Variational circuit pathfinding
└── mcp/
    └── tools.py             # FastMCP tools (6 tools)
```

## SwiftUI App (`Project Chicken Soup/`)

```
Project Chicken Soup/
├── Project_Chicken_SoupApp.swift          # App entry + SwiftData seeding
├── ContentView.swift                      # Main orchestrator (482 lines)
├── Models/
│   ├── LoreEntity.swift                   # SwiftData @Model
│   ├── TemporalEvent.swift                # SwiftData @Model
│   └── TimelineBranch.swift               # SwiftData @Model
├── Shared/
│   ├── Services/
│   │   ├── BackendService.swift           # Central service (573 lines)
│   │   ├── LLMDiscoveryService.swift      # LLM provider discovery
│   │   └── SyncService.swift              # Offline queue + field merge
│   ├── Networking/
│   │   ├── APIClient.swift                # Actor-based HTTP client
│   │   └── APIModels.swift                # Codable API response models (474 lines)
│   └── DesignSystem/
│       ├── DesignConstants.swift          # Colors, spacing, radius, animations
│       ├── SkeletonModifier.swift         # Loading shimmer effect
│       └── PremiumSlider.swift            # Custom capsule slider
└── Features/
    ├── Timeline/
    │   ├── Layouts/TimelineLayout.swift   # Custom Layout for horizontal timeline
    │   └── Views/
    │       ├── TimelineView.swift         # Animated canvas timeline
    │       ├── AdvancedTimelineFilterView.swift # Confidence, type, branch filters
    │       └── TimelineBranchMergeSheet.swift   # Branch merging UI
    ├── KnowledgeGraph/
    │   ├── Views/
    │   │   ├── GraphExplorerView.swift    # 2D interactive graph
    │   │   ├── NodeView.swift             # Glassmorphic node circles
    │   │   ├── SidebarDetailsView.swift   # Entity detail sidebar (316 lines)
    │   │   ├── EntityDetailView.swift     # Entity card sheet (128 lines)
    │   │   └── EvidenceHistoryView.swift  # Confidence trajectory
    │   └── Views/GridBackgroundView.swift # Dot grid overlay
    ├── AINavigator/
    │   ├── Views/
    │   │   ├── AINavigatorView.swift      # Floating control panel (296 lines)
    │   │   └── RealitySpacetimeView.swift # 3D visualization
    ├── Query/
    │   └── Views/
    │       ├── QueryOverlayView.swift     # Floating query bar (161 lines)
    │       ├── ChatHistoryView.swift      # Conversation history (139 lines)
    │       ├── MultimodalInputView.swift  # Voice, photo, camera (356 lines)
    │       └── LiquidGlassView.swift      # Glassmorphic modifier
    ├── DataIngestion/
    │   └── Views/
    │       ├── DataIngestionView.swift    # File/folder/chat ingest (1090 lines)
    │       └── WikiInsightNotificationView.swift # Auto-sliding banner (64 lines)
    └── Settings/
        └── Views/SettingsView.swift       # Quantum + LLM + Chat-to-Wiki config (704 lines)
```

## Tests (`tests/`)

```
tests/
├── conftest.py              # Mock Neo4j + Redis fixtures
├── test_config.py           # Settings defaults, fallback parsing (3 tests)
├── test_discovery.py        # Provider discovery cascading (3 tests)
├── test_spacetime_engine.py # Tensor, classical, Qiskit (3 tests)
├── test_agents.py           # TQL, research, navigation, orchestrate (4 tests)
├── test_api.py              # Status, models, navigate, query (4 tests)
├── test_phase3.py           # WebSocket, cache (2 tests)
└── test_phase4.py           # Consensus, quantum scheduler (5 tests)
```

## Infrastructure

- **Docker**: Single Dockerfile, docker-compose for Neo4j + Redis
- **CI**: GitHub Actions (Python 3.12, uv, pytest)
- **Agent Skills**: 4 twostraws skills (SwiftUI, SwiftData, Concurrency, Testing)

## See Also

- [[technology-stack]]
- [[agent-architecture]]
- [[api-design]]
- [[mcp-server]]
- [[knowledge-graph-schema]]
- [[wiki-file-system]]
- [[chat-to-wiki-pipeline]]
- [[ingestion-pipeline]]
