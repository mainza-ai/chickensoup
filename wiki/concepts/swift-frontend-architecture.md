---
created: 2026-06-23
protected: true
related:
- ui-ux-design
- integration-architecture
- project-structure
- swiftui-pro
- swiftdata-pro
- swift-concurrency-pro
- api-design
- chat-to-wiki-pipeline
sources: []
tags:
- swift
- ios
- macos
- swiftui
- frontend
title: Swift Frontend Architecture
updated: '2026-06-25'
---

# Swift Frontend Architecture

The native client is a 50/50 macOS + iOS SwiftUI app (~11,500 lines, 33+ files) at `Project Chicken Soup/`.

## App Structure

```
Project_Chicken_SoupApp.swift  →  ContentView.swift  →  Feature Views
                                        │
                               ┌────────┴────────┐
                          Shared/           Features/
                      Services+Models      Timeline, Query,
                      +Networking          KnowledgeGraph,
                      +DesignSystem        AINavigator, Settings,
                                           DataIngestion
```

## Data Layer

### SwiftData Models (`Models/`)

Three `@Model` classes stored locally for offline operation:

1. **LoreEntity** — `id, name, type` (Person/Place/Concept/Object/Project), `summary, confidence, source, userNotes, sourcesRaw` (pipe-delimited)
2. **TemporalEvent** — `id, title, eventDescription, timestamp, confidence, source, type` (crash/testimony/anomaly/theory), `userNotes, sourcesRaw`, optional `branch: TimelineBranch?`
3. **TimelineBranch** — `id, name, isActive`, cascade relationship `events: [TemporalEvent]?`

### Services (`Shared/Services/`)

- **BackendService** (`@MainActor`, 573 lines) — Central service layer. Fetches events/entities from backend or SwiftData fallback, submits queries with `conversation_id`, simulates geodesics, fetches graph neighborhoods, manages navigation history stack, LLM config, and now **chat-to-wiki conversion** (status polling, manual trigger, user name management, notification tracking). Stores `ChatIngestStatus`, `unreadWikiPagesFromChat` badge count, chat preferences in UserDefaults.
- **LLMDiscoveryService** (`@MainActor ObservableObject`) — Probes providers (oMLX, Ollama, LM Studio), displays availability as a chevron chain with status indicators. Syncs `llmActiveModel`/`llmActiveProvider` to BackendService.
- **SyncService** (`@MainActor ObservableObject`) — Offline queue (`[SyncOperation]` persisted in UserDefaults), field-level merge resolution.

### Networking (`Shared/Networking/`)

- **APIClient** (actor, singleton) — Generic `request<T: Decodable>` with custom ISO8601 date decoding, 90s timeout, 5 error types. Base URL: `http://127.0.0.1:8000`.
- **APIModels** (474 lines) — 20+ Codable structs: `APITemporalEvent`, `APILoreEntity`, `APITimeTravelSimulationResponse`, `APIQueryResponse`, `APIDiscoveryStatus`, `NeighborhoodEntity/Connection/Response`, `APIConfigRequest/Response`, `APIAnalyzedPage`, `APIAnalyzeResponse`, `APIFileIngestResponse`, `APIFolderIngestResponse`, `APIChatIngestStatus`, `APIChatIngestNowResponse`, `APISetUserNameRequest/Response`, `APIIngestHistoryEntry`, `APIChatIngestNotification`.

### Design System (`Shared/DesignSystem/`)

- **DesignConstants** — Adaptive colors (light/dark), brand palette (`#FF9500`), radius, spacing, shadows, animations
- **SkeletonModifier** — Redacted shimmer loading effect
- **PremiumSlider** — Custom capsule slider with orange fill

## Frontend Features

### ContentView (`ContentView.swift`, 482 lines)
- **Desktop** (macOS/iPad): `NavigationSplitView` with `SidebarDetailsView` + segmented picker (Lore Graph / Spacetime Timeline)
- **Phone**: `TabView` with 4 tabs + chat overlay + settings sheets
- **Overlays**: `AINavigatorView` (top-right), `ChatHistoryView` (bottom), `WikiInsightNotificationView` (top notification banner)
- **Badge**: Ingest tab shows `.badge(backendService.unreadWikiPagesFromChat)` when chat-to-wiki creates new pages

### Timeline (`Features/Timeline/`)
- Custom `TimelineLayout` positioning events by date on parallel branch tracks
- Animated `CanvasView` with spacetime waves, particle streams, branching curves
- Filter controls (confidence slider, type selectors, branch selector) in `AdvancedTimelineFilterView`
- Branch merge sheet (`TimelineBranchMergeSheet`)

### Knowledge Graph (`Features/KnowledgeGraph/`)
- Interactive 2D graph with concentric ring layout, drag-to-pan, pinch-to-zoom, connection lines with relationship labels
- Type-colored circles: Person (orange), Place (green), Concept (purple), Project (pink), Object (blue), Event (red)
- `SidebarDetailsView` (316 lines) with search bar, entity card, relationship list, evidence history
- `EntityDetailView` (128 lines) entity sheet with edit capabilities

### AI Navigator (`Features/AINavigator/`, 296 lines)
- LLM fallback chain indicators with `StatusIndicator` subviews
- Spacetime Field Metrics sliders (Gravity Distortion, Travel Velocity, Field Density)
- `RealitySpacetimeView` 3D grid visualization
- "Solve Spacetime Geodesic" action button with progress state

### Query (`Features/Query/`)
- `QueryOverlayView` (161 lines) — Floating bar with TQL/Natural toggle, suggestion buttons, multimodal integration
- `ChatHistoryView` (139 lines) — Scrollable bubble list with user (orange) and assistant messages, wiki insight indicator badge, clear/close buttons
- `MultimodalInputView` (356 lines) — Voice dictation (SFSpeechRecognizer), photo picker (PhotosPicker + OCR via Vision), camera scanner
- `LiquidGlassView` — Glassmorphic view modifier

### Data Ingestion (`Features/DataIngestion/`)
- `DataIngestionView` (1090 lines) — Stats dashboard, drag-and-drop zone, platform-conditional `.fileImporter` (`.folder` on macOS, `.data/.zip` on iOS), 2-step analysis→commit UX, folder result breakdown, **chat contributions section** with status cards and "Run Now" button
- `WikiInsightNotificationView` (64 lines) — Auto-sliding banner that appears when `unreadWikiPagesFromChat > 0`, auto-dismisses after 6 seconds

### Settings (`Features/Settings/`, 704 lines)
- Quantum backend picker (5 options: numpy, qiskit, dwave, ibm, ionq)
- Hardware enable toggle + API credential fields with secure visibility toggle
- **LLM Configuration** section with provider picker, model picker from server-discovered list
- **Chat-to-Wiki Conversion** section with toggle, notify toggle, min conversation length stepper, user wiki name field with rename button

## Offline Strategy

- SwiftData is the read-through cache for Neo4j data
- `BackendService` falls back to local SwiftData when server is unreachable
- `SyncService` queues write operations offline and replays them when connected
- Merge: server confidence is authoritative, local notes win, sources are unioned

## See Also

- [[ui-ux-design]]
- [[integration-architecture]]
- [[project-structure]]
- [[swiftui-pro]]
- [[swiftdata-pro]]
- [[swift-concurrency-pro]]
- [[chat-to-wiki-pipeline]]
- [[api-design]]

