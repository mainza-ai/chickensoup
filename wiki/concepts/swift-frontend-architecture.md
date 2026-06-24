---
title: "Swift Frontend Architecture"
tags: [swift, ios, macos, swiftui, frontend]
created: 2026-06-23
updated: 2026-06-23
sources: []
related: [ui-ux-design, integration-architecture, project-structure, swiftui-pro, swiftdata-pro, swift-concurrency-pro]
---

# Swift Frontend Architecture

The native client is a 50/50 macOS + iOS SwiftUI app (~7,000 lines, 18 files) at `Project Chicken Soup/`.

## App Structure

```
Project_Chicken_SoupApp.swift  →  ContentView.swift  →  Feature Views
                                       │
                              ┌────────┴────────┐
                         Shared/           Features/
                     Services+Models      Timeline, Query,
                     +Networking          KnowledgeGraph,
                                          AINavigator, Settings
```

## Data Layer

### SwiftData Models (Shared/Models/)

Three `@Model` classes stored locally for offline operation:

1. **LoreEntity** — `name`, `type`, `description`, `confidence`, `sources` (pipe-delimited string), `sourcesRaw`
2. **TemporalEvent** — `title`, `description`, `year`, `confidence`, `entity`, branch relationship to `TimelineBranch`
3. **TimelineBranch** — `name`, `color`, `opacity`, `events` (cascading delete, inverse relationship)

### Services (Shared/Services/)

- **BackendService** (@MainActor, 440+ lines) — Central service layer. Fetches events/entities from backend or SwiftData fallback, submits queries, simulates geodesics, fetches graph neighborhoods, manages navigation history stack, handles LLM config (model selection, discovery refresh). Communicates via `APIClient`.
- **LLMDiscoveryService** (@MainActor ObservableObject singleton) — Probes providers (oMLX, Ollama, LM Studio), displays availability in UI. Now also tracks `availableModels`, `selectedModel`, `activeProvider` from backend config.
- **SyncService** (@MainActor ObservableObject singleton) — Offline queue (`[SyncOperation]` persisted in UserDefaults), field-level merge resolution.

### Networking (Shared/Networking/)

- **APIClient** (actor, singleton) — Generic `request<T: Decodable>` with custom ISO8601 date decoding, 90s timeout, 5 error types (`invalidURL, requestFailed, decodingFailed, serverError, unknown`). Base URL: `http://127.0.0.1:8000`.
- **APIModels** — 10 Codable structs mirroring backend models: `APITemporalEvent`, `APILoreEntity`, `APITimeTravelSimulationResponse`, `APIQueryResponse`, `APIDiscoveryStatus`, `NeighborhoodEntity/Connection/Response`, `APIConfigRequest/Response`.

## Frontend Features

### Timeline (`Features/Timeline/`)
Custom `Layout` protocol positioning events by date along parallel branch tracks. Horizontal on macOS, vertical on iOS.

### Knowledge Graph (`Features/KnowledgeGraph/`)
Interactive 2D node graph with concentric ring layout, drag-to-pan, pinch-to-zoom, connection lines with relationship labels. Type-colored circles + SF Symbols. Sidebar entity detail panel with search and evidence history comparison.

### AI Navigator (`Features/AINavigator/`)
Floating control panel with LLM fallback chain indicators (chevron chain), spacetime sliders (Gravity Distortion, Travel Velocity, Field Density), log stream, and "Solve Spacetime Geodesic" button. 3D grid visualization (RealityKit ARView fallback to SwiftUI Canvas).

### Query (`Features/Query/`)
Floating query bar with Natural/TQL toggle, suggestion dropdown, execute button, loading state. Multimodal input: voice dictation (SFSpeechRecognizer + mic level visualization), photo picker (PhotosPicker + OCR via Vision), camera scanner, attachment chips.

### Data Ingestion (`Features/DataIngestion/`)
Stats dashboard (avg confidence, total entities, sync queue size), drag-and-drop file zone, file browser, bulk ingest button, AI extraction preview, entity list with edit/delete.

### Settings (`Features/Settings/`)
Quantum backend picker (5 options: numpy, qiskit, dwave, ibm, ionq), hardware enable toggle, API credential fields with secure visibility toggle, **LLM Configuration section** with active provider label, model picker (from server-discovered list), refresh models button, apply button.

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
