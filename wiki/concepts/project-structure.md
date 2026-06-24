---
title: "Project Structure"
tags: [project, structure, organization]
created: 2026-06-22
updated: 2026-06-23
sources: []
related: [agent-architecture, technology-stack, api-design, mcp-server, knowledge-graph-schema]
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
├── wiki/                   # Obsidian vault (160+ pages)
├── src/                    # Python backend
├── tests/                  # Python test suite (8 files, ~30 tests)
├── Project Chicken Soup/   # SwiftUI macOS/iOS app (Xcode project)
├── .agents/                # twostraws agent skills
├── .github/workflows/      # CI pipeline
└── .headroom/              # LLM memory persistence (SQLite)
```

## Python Backend (`src/`)

```
src/
├── main.py                 # FastAPI entry point (~706 lines, all routes inline)
├── config.py               # Pydantic Settings (19 fields)
├── models.py               # Core request/response Pydantic models (10 models)
├── discovery.py            # LLM provider auto-discovery
├── cache.py                # RedisCache + cache_decorator
├── observability.py        # OpenTelemetry metrics + tracing
├── multi_llm.py            # Multi-LLM consensus engine
├── quantum_scheduler.py    # Quantum job scheduler (IBM/D-Wave/IonQ)
├── tasks.py                # Celery async task definitions
├── agents/
│   ├── orchestrator.py     # pydantic-graph orchestration
│   ├── query_agent.py      # TQL/LLM/heuristic intent parser
│   ├── research_agent.py   # LangGraph research workflow
│   └── navigation_agent.py # Quantum pipeline orchestration
├── knowledge_graph/
│   ├── connection.py       # Neo4j connection singleton
│   ├── schema.py           # Constraints + indexes
│   ├── ingest.py           # Wiki→Neo4j ingestion pipeline
│   └── queries.py          # Cypher query functions
├── spacetime_engine/
│   └── qiskit_simulation.py # 2-qubit circuit simulation + fallback
├── field_manipulator/
│   └── cuda_simulation.py   # Bubble stability + resonance model
├── ai_navigator/
│   └── pennylane_qml.py     # Variational circuit pathfinding
├── mcp/
│   └── tools.py             # FastMCP tools (6 tools)
└── configuration.py         # (inline in config.py)
```

## SwiftUI App (`Project Chicken Soup/`)

```
Project Chicken Soup/
├── Project_Chicken_SoupApp.swift
├── ContentView.swift               # Main orchestrator (541 lines)
├── Shared/
│   ├── Models/
│   │   ├── LoreEntity.swift        # SwiftData @Model
│   │   ├── TemporalEvent.swift     # SwiftData @Model
│   │   └── TimelineBranch.swift    # SwiftData @Model
│   ├── Services/
│   │   ├── BackendService.swift    # Central service (423 lines)
│   │   ├── LLMDiscoveryService.swift
│   │   └── SyncService.swift       # Offline queue + field merge
│   └── Networking/
│       ├── APIClient.swift          # Actor-based HTTP client
│       └── APIModels.swift          # Codable API response models
└── Features/
    ├── Timeline/
    │   └── TimelineView.swift       # Custom Layout timeline
    ├── KnowledgeGraph/
    │   ├── GraphExplorerView.swift  # 2D interactive graph
    │   ├── NodeView.swift
    │   ├── SidebarDetailsView.swift
    │   └── EvidenceHistoryView.swift
    ├── AINavigator/
    │   ├── AINavigatorView.swift    # Floating control panel
    │   └── RealitySpacetimeView.swift # 3D visualization
    ├── Query/
    │   ├── QueryOverlayView.swift   # Floating query bar
    │   └── MultimodalInputView.swift # Voice, photo, camera
    ├── DataIngestion/
    │   └── DataIngestionView.swift  # Drag-drop + bulk ingest
    └── Settings/
        └── SettingsView.swift       # Quantum backend config
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
