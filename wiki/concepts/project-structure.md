---
title: "Project Structure"
tags: [project, structure, organization, living-almanac]
created: 2026-06-22
updated: 2026-07-12
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
├── wiki/                   # Obsidian vault (250+ pages)
│   ├── entities/           # 87 pages
│   ├── concepts/           # 155+ pages (now including pulse-agent, budget-tracking, credibility-scoring, frontend-settings-menu)
│   ├── projects/           # 7 pages (including living-almanac plan)
│   ├── raw/                # 80+ immutable docs: 61 PDFs + Mannheim transcripts + 20 Apple guides + pulse/ + almanac/
│   │   ├── pulse/          # (NEW) Dated pulse snapshots — entity-scoped evidence JSON+MD
│   │   └── almanac/        # (NEW) Dated HTML+MD State of the Anomaly briefs
│   └── plan/               # (NEW) Frontend settings menu plan to final DOD
├── src/                    # Python backend (48 source files, was 22)
├── tests/                  # Python test suite (19 files, 75 passing — was 9)
├── Project Chicken Soup/   # SwiftUI macOS/iOS app (Xcode project, 50+ Swift files)
├── .agents/                # twostraws agent skills (swiftui-pro, swiftdata-pro, swift-concurrency-pro, swift-testing-pro)
├── .github/workflows/      # CI pipeline
└── .headroom/              # LLM memory persistence (SQLite)
```

## Python Backend (`src/`)

```
src/
├── main.py                 # FastAPI entry point (~2100 lines, was 1611) — 40+ endpoints + WebSocket + Living Almanac routes
├── config.py               # Pydantic Settings (30+ fields, was 24) — now LAST30DAYS_*, WAVEFUNCTION_*, ALMANAC_*, BUDGET_*, SOCIAL_TRACTION_*
├── models.py               # Core Pydantic models (310 lines, was 161) — now ClaimEvidence, ClaimConfidence, DivergenceResult, PulseResult, TimelinePoint, BudgetStatus
├── budget.py               # (NEW) BudgetTracker with Lua atomic check+incr, HOLD, approve_hold, reset_month (184 lines)
├── last30days_adapter.py   # (NEW) Normalizes last30days CLI JSON/md to ClaimEvidence[] with platform inference, URL extraction, market % detection (260 lines)
├── discovery.py            # LLM provider auto-discovery (158 lines)
├── cache.py                # RedisCache + cache_decorator (133 lines)
├── observability.py        # OpenTelemetry metrics + tracing — now 11 metrics including pulse/budget/wavefunction/divergence/tribunal/almanac
├── multi_llm.py            # Multi-LLM consensus via Jaccard (122 lines)
├── quantum_scheduler.py    # Quantum job scheduler IBM/D-Wave/IonQ (137 lines)
├── scheduler.py            # Chat-to-wiki loop (5min) + Almanac loop (24h interval, idempotency) dual schedulers (~778 lines)
├── tasks.py                # Celery async tasks — fixed metric_tensor→spatial_metric bug
├── agents/
│   ├── orchestrator.py     # pydantic-graph orchestration (263 lines) — confidence gating + synthesize_answer + inferred_events fix
│   ├── query_agent.py      # TQL/LLM/heuristic intent parser (245 lines)
│   ├── research_agent.py   # LangGraph research workflow — now wires ClaimWavefunction when pulse exists (<14d), graceful fallback, populates inferred_events/entities (~420 lines)
│   ├── navigation_agent.py # Quantum pipeline orchestration (44 lines)
│   ├── ingest_agent.py     # File/folder content analysis → wiki pages (182 lines)
│   ├── chat_ingest_agent.py # Conversation-aware LLM extraction (208 lines)
│   ├── pulse_agent.py      # (NEW) Entity-scoped last30days ingestion, budget-guarded, shell=False, disabled no-op, observability counters (308 lines)
│   └── tribunal_agent.py   # (NEW) Skeptic/Empiricist/Believer + referee LangGraph, gated cost control (258 lines)
├── quantum_credibility/    # (NEW) Quantum credibility module
│   ├── __init__.py         # Re-exports wavefunction, divergence, vectorizer
│   ├── wavefunction.py     # ClaimWavefunction 3-basis VQE scoring (334 lines) — diversity, engagement_mag, market_prior, contradiction, traction decayed separately via named constant 0.15
│   ├── divergence_engine.py # Narrative divergence — FieldGeometryTensor from two claim-vectors, reuses find_optimal_path (grep-able shared call) (135 lines)
│   ├── entanglement_corr.py # Meyer-Wallach over co-occurrence clusters, independent platforms > single cross-ref (185 lines)
│   └── vectorizer.py       # Claims→16-dim vector, canon→vector, vector→FieldGeometryTensor factory (198 lines) — avoids duplicating warp math
├── almanac/                # (NEW) Living Almanac artifacts
│   ├── __init__.py         # Re-exports timeline + almanac_generator
│   ├── timeline.py         # pulse/*.json + git log → chartable TimelinePoints, no TSDB (271 lines)
│   └── almanac_generator.py # generate_daily_almanac() dry-run+live+idempotency hash, self-contained HTML inline CSS no JS dark mode print-friendly (653 lines)
├── spacetime_engine/
│   ├── tensor.py           # FieldGeometryTensor ADM 3+1
│   ├── qiskit_simulation.py # 2-qubit circuit simulation + fallback
│   ├── entanglement.py     # (NEW) Meyer-Wallach reusable scorer meyer_wallach() + meyer_wallach_from_probs() + is_entangled_state() (73 lines)
│   └── vqe_runner.py       # (NEW) AerEstimatorV2 wrapper, build_claim_state_circuit(), run_vqe_estimation(), score_claim_state() (244 lines)
├── field_manipulator/
│   └── cuda_simulation.py   # Bubble stability + resonance model
├── ai_navigator/
│   └── pennylane_qml.py     # Variational circuit pathfinding — reused for divergence risk calc
├── wiki/
│   ├── writer.py           # Wiki page CRUD, cross-referencing, index/log + LOG_IGNORE_PATTERNS for pytest isolation (272 lines)
│   ├── paths.py            # (NEW) Central WIKI_DIR resolver get_wiki_dir(), get_raw_dir(), get_pulse_dir(), get_almanac_dir() (55 lines)
│   ├── pulse_writer.py     # (NEW) write_pulse_snapshot() json+md, list_pulse_snapshots(), load_recent_pulse_evidence() (183 lines)
│   ├── backup.py           # Snapshot export/import
│   └── cleanup.py          # Content vs engineering preservation
├── knowledge_graph/
│   ├── connection.py       # Neo4j connection singleton
│   ├── schema.py           # Constraints + indexes
│   ├── ingest.py           # Wiki→Neo4j ingestion pipeline — LLM edge classification retry+backoff + heuristic fallback
│   └── queries.py          # Cypher query functions
├── mcp/
│   └── tools.py             # FastMCP tools (6 tools)
└── api/
    └── auth.py              # API key header auth checker
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

```
tests/
├── conftest.py              # Mock Neo4j + Redis fixtures
├── test_config.py           # Settings defaults, fallback parsing
├── test_discovery.py        # Provider discovery cascading (URL fix for 127.0.0.1 vs localhost)
├── test_spacetime_engine.py # Tensor, classical, Qiskit
├── test_agents.py           # TQL, research, navigation, orchestrate
├── test_api.py              # Status, models, navigate, query
├── test_phase3.py           # WebSocket, cache
├── test_phase4.py           # Consensus, quantum scheduler
├── test_audit_fixes.py      # File size limits, clear-content safeguard, backup exclusion, protected delete, Obsidian integrity
├── test_pdf_ingest.py       # PDF folder ingestion
├── test_pulse_agent.py      # (NEW) Disabled no-op, enabled writes one file, budget exceeded refused+logged no subprocess, shell=False safety, adapter JSON+markdown (5 tests)
├── test_budget.py           # (NEW) Disabled Redis fallback, exceeded, atomic Lua, HOLD blocks (4 tests)
├── test_wavefunction.py     # (NEW) High diversity+market→corroborated collapsed, single low→unverified not collapsed, contradicted→contested, decoupled epi/trac, no evidence fallback, version+inputs logged, batch scoring (7 tests)
├── test_divergence_engine.py # (NEW) Identical near-zero, contradicting high with driving named, grep-able shared call, empty fresh (4 tests)
├── test_entanglement_corr.py # (NEW) Single mention low, multi-platform high, no cooccurrence zero, three platforms > single (4 tests)
├── test_tribunal_agent.py   # (NEW) Uncontested never triggers 0 LLM calls, contested triggers 3 positions + citations, divergence spike triggers, all citations preserved (4 tests)
├── test_timeline_endpoint.py # (NEW) 3 dated pulls→3-point ordered chartable, empty entity empty, git fallback no crash (3 tests)
└── test_almanac_generator.py # (NEW) Dry-run no files/budget + valid HTML (inline CSS no JS dark mode print-friendly), live correct paths+log+HTML validity, no material change logs instead (3 tests)
```

75 tests passing.

## Infrastructure

- Docker: Dockerfile + docker-compose for Neo4j + Redis
- CI: GitHub Actions Python 3.12 uv pytest
- Agent Skills: 4 twostraws skills in .agents/skills/
- Apple ref guides: 20 docs in wiki/raw/ indexed by apple-reference-guides.md concept page

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
