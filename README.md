<p align="center">
  <img src="assets/logo.png" alt="Project Chicken Soup Logo" width="200" />
</p>

# 🍲 Project Chicken Soup

<p align="center">
  <img src="https://img.shields.io/badge/status-active_development-orange.svg" alt="Active Development" />
</p>

> **A Local-First AI Spacetime Navigation Engine & Lore Knowledge Graph.**
> Bridging quantum computing simulation (Qiskit, CUDA-Q, PennyLane) with a rich graph of UFO/Alien/Time Travel history.

> [!WARNING]
> **Active Development**
> This repository is under constant and rapid development. APIs, schemas, configurations, and user interfaces are subject to frequent breaking changes as new features are integrated.

---

## 🌌 Overview

Project Chicken Soup is a production-quality, local-first system that simulates time travel physics via quantum computation and orchestrates discovery through an AI agent network. The system couples a multi-agent backend with a local knowledge base of extraterrestrial and temporal lore.

### Key Capabilities

- **Spacetime Simulation**: Computes time dilation, gravity effects, and closed timelike curves (CTCs) using **Qiskit**.
- **Field Manipulation**: Models field-propulsion metrics using **CUDA-Q**.
- **QML Navigation**: Plots optimal temporal coordinates via **PennyLane** neural networks, targeting hardware from **D-Wave** and **IonQ**.
- **Lore Knowledge Graph**: Maps whistleblower claims, historic crashes, and scientific anomalies using a **Neo4j** graph.
- **Clean Spacetime Timeline**: Filters out software blueprints, codebase configs, and engineering documentation from the events timeline to show only actual historical incidents, projects, and whistleblowers.
- **Local-First LLMs & Active Model Resolution**: Auto-discovers and falls back across local models (**oMLX** ➔ **Ollama** ➔ **LM Studio**), dynamically resolving active model names and base URLs to prevent UI desyncs when providers fall back.
- **Wiki Auto-Ingestion**: Upload files or folders — AI analyzes content and automatically creates wiki pages with cross-references.
- **Chat-to-Wiki Pipeline**: Periodic background conversion of user–AI conversations into wiki pages, research threads, and temporal events.
- **Apple SwiftUI Client**: Native macOS & iOS application with a warm, "chicken soup" systemOrange accent theme (`#FF9500`) powered by **SwiftData**.

---

## 🏛️ System Architecture

Project Chicken Soup implements a decoupled, modern multi-agent architecture:

<p align="center">
  <img src="assets/images/Spacetime_Navigation_Architecture_Overview.png" alt="Spacetime Navigation Architecture Overview" width="750" />
</p>

```mermaid
graph TD
    UI[SwiftUI macOS/iOS App] <--> API[FastAPI / FastMCP Server]
    
    subgraph AI_Orch ["AI Orchestration Layer (Python)"]
        Orchestrator[Orchestrator Graph: pydantic-graph]
        Query[Query Agent: TQL + LLM + Heuristic]
        Research[Research Agent: LangGraph + Wiki Fallback]
        Navigator[Navigation Agent: Quantum Pipeline]
        Ingest[Ingest Agent: File/Folder → Wiki]
        ChatIngest[Chat Ingest Agent: Conversation → Wiki]
        Scheduler[Scheduler: Periodic Chat Ingest Loop]
        
        Orchestrator --> Query
        Orchestrator --> Research
        Orchestrator --> Navigator
        Scheduler --> ChatIngest
    end
    
    API <--> Orchestrator
    API <--> Ingest
    API <--> ChatIngest
    Research <--> Graph[(Neo4j Knowledge Graph)]
    Research <--> Wiki[(Wiki Markdown Vault)]
    Navigator <--> QEngine[Quantum Engines: Qiskit, CUDA-Q, PennyLane]
```

- **Orchestrator**: Managed via `pydantic-graph` for top-level routing with confidence gating.
- **Sub-workflows**: Complex data fusion and research pipelines orchestrated by `LangGraph` (checkpointing, human-in-the-loop, parallel execution).
- **File Ingest Agent**: Analyzes uploaded `.txt`/`.md`/`.json`/`.csv` files via LLM, extracts entities/concepts/projects, commits to wiki + Neo4j.
- **Chat Ingest Agent**: Periodically scans eligible conversations (10+ messages, 30min idle), extracts new wiki content, detects user names, identifies temporal references.
- **Scheduler**: Background asyncio loop (every 5 minutes) managing conversation eligibility, idempotency, research thread detection, and conversation snapshots.

---

## 📊 Presentation Slide Deck

An in-depth presentation outlining the project vision, quantum architectures, and local AI agent networks:

- 📥 **Download Deck**: [PDF Presentation](assets/other/Project_Chicken_Soup_Quantum_AI.pdf) | [PowerPoint PPTX](assets/other/Project_Chicken_Soup_Quantum_AI.pptx)

### Slides Preview

<p align="center">
  <img src="assets/images/Project_Chicken_Soup_Quantum_AI-slide-deck/Project_Chicken_Soup_Quantum_AI.001.jpeg" alt="Slide 1: Title Slide" width="750" />
</p>

<details>
  <summary>🔍 Click to expand and view all 11 slides</summary>
  <br/>
  <p align="center">
    <img src="assets/images/Project_Chicken_Soup_Quantum_AI-slide-deck/Project_Chicken_Soup_Quantum_AI.002.jpeg" alt="Slide 2" width="750" /><br/><br/>
    <img src="assets/images/Project_Chicken_Soup_Quantum_AI-slide-deck/Project_Chicken_Soup_Quantum_AI.003.jpeg" alt="Slide 3" width="750" /><br/><br/>
    <img src="assets/images/Project_Chicken_Soup_Quantum_AI-slide-deck/Project_Chicken_Soup_Quantum_AI.004.jpeg" alt="Slide 4" width="750" /><br/><br/>
    <img src="assets/images/Project_Chicken_Soup_Quantum_AI-slide-deck/Project_Chicken_Soup_Quantum_AI.005.jpeg" alt="Slide 5" width="750" /><br/><br/>
    <img src="assets/images/Project_Chicken_Soup_Quantum_AI-slide-deck/Project_Chicken_Soup_Quantum_AI.006.jpeg" alt="Slide 6" width="750" /><br/><br/>
    <img src="assets/images/Project_Chicken_Soup_Quantum_AI-slide-deck/Project_Chicken_Soup_Quantum_AI.007.jpeg" alt="Slide 7" width="750" /><br/><br/>
    <img src="assets/images/Project_Chicken_Soup_Quantum_AI-slide-deck/Project_Chicken_Soup_Quantum_AI.008.jpeg" alt="Slide 8" width="750" /><br/><br/>
    <img src="assets/images/Project_Chicken_Soup_Quantum_AI-slide-deck/Project_Chicken_Soup_Quantum_AI.009.jpeg" alt="Slide 9" width="750" /><br/><br/>
    <img src="assets/images/Project_Chicken_Soup_Quantum_AI-slide-deck/Project_Chicken_Soup_Quantum_AI.010.jpeg" alt="Slide 10" width="750" /><br/><br/>
    <img src="assets/images/Project_Chicken_Soup_Quantum_AI-slide-deck/Project_Chicken_Soup_Quantum_AI.011.jpeg" alt="Slide 11" width="750" />
  </p>
</details>

---

## 📸 Screen Demonstrations & Video

### 🎥 Demo Video

Watch the Spacetime Navigation Engine & Lore Knowledge Graph in action:

[![Project Chicken Soup Demo Video](https://img.youtube.com/vi/orRyWnZc4Ek/0.jpg)](https://www.youtube.com/watch?v=orRyWnZc4Ek)

🔗 **Link**: [Watch on YouTube](https://www.youtube.com/watch?v=orRyWnZc4Ek)

### 🖥️ Application Screenshots

<p align="center">
  <img src="assets/screenshots/1.png" alt="Interactive Panning and Node Highlighting" width="750" />
  <br/>
  <em>macOS Client Interactive Lore Graph Exploration</em>
</p>

<p align="center">
  <img src="assets/screenshots/2.png" alt="Lore Knowledge Graph Interface on First Launch" width="750" />
  <br/>
  <em>iOS Client Graph Exploration Interface</em>
</p>

---

## 🛠️ Technology Stack

| Layer | Technologies |
| :--- | :--- |
| **Frontend Client** | [SwiftUI](file:///Users/mck/Desktop/chickensoup/Project%20Chicken%20Soup) (macOS & iOS, 33+ files), SwiftData, Swift Testing, os.Logger |
| **API Layer** | FastAPI, FastMCP (Model Context Protocol), WebSockets, custom API Key Security Middleware |
| **Agent AI** | Pydantic AI, `pydantic-graph`, LangGraph, Langchain |
| **Databases** | Neo4j (Knowledge Graph), Redis (Cache + Invalidation + Celery broker) |
| **Quantum Tier** | Qiskit (Spacetime), CUDA-Q (Field), PennyLane (Pathfinding QML), Quantum Hardware Job Scheduler |
| **Infrastructure** | Docker, Celery (Asynchronous Ingestion Workers), OpenTelemetry (observability, metrics, tracing), pytest |

---

## 📂 Project Structure

```
chickensoup/
├── development-docs/       # Project specifications & architecture docs
│   └── PROJECT_SPEC.md     # Core technical specification
├── wiki/                   # Markdown wiki (181 pages: entities, concepts, projects)
│   ├── entities/           # 81 pages (people, craft, places, events, programs)
│   ├── concepts/           # 93 pages (ideas, theories, frameworks)
│   ├── projects/           # 6 pages (time travel machinery specs)
│   └── raw/                # Immutable conversation snapshots
├── Project Chicken Soup/   # Native SwiftUI client (macOS & iOS, 33+ Swift files)
├── src/                    # Backend source code (22 Python files)
│   ├── main.py             # FastAPI entry point (30+ endpoints & WebSocket routing)
│   ├── config.py           # Config settings & environment variables
│   ├── discovery.py        # Local LLM auto-discovery fallback resolver
│   ├── cache.py            # Redis query & LLM cache layer with invalidation
│   ├── tasks.py            # Celery asynchronous worker tasks
│   ├── observability.py    # OpenTelemetry instrumented tracing & metrics
│   ├── multi_llm.py        # Consensus-based multi-LLM querying & scoring
│   ├── quantum_scheduler.py# Job routing to D-Wave, IonQ, and IBM Quantum
│   ├── scheduler.py        # Background scheduler for chat-to-wiki ingestion
│   ├── api/                # API router & auth dependencies
│   │   └── auth.py         # API key header authentication checker
│   ├── agents/             # pydantic-graph & LangGraph agents (orchestrator, query, navigation, research, ingest)
│   ├── wiki/               # Wiki vault interaction utilities
│   │   ├── writer.py       # YAML frontmatter page writer & indexer
│   │   ├── backup.py       # Safe pre-mutation automated backups
│   │   └── cleanup.py      # Secure lore clearing & metadata preservation
│   └── knowledge_graph/    # Neo4j query & ingestion layer
│       ├── ingest.py       # LLM relationship extraction & Cypher injection sanitizer
│       ├── connection.py   # Thread-safe driver connection lifecycle
│       ├── queries.py      # Neo4j query builder templates
│       └── schema.py       # Indexes and constraint builders
├── tests/                  # Backend unit and integration tests (9 files)
├── AGENTS.md               # LLM Agent instructions & wiki schema
├── CHANGELOG.md            # Project release log
└── pyproject.toml          # Python build config & dependencies
```

---

## 🚀 Getting Started

### 1. Requirements & Dependencies
- **Python**: 3.12+ (managed with `uv` or `.python-version`)
- **Xcode**: 16.0+ (for SwiftUI client)
- **Services**: Docker (for Neo4j & Redis)

### 2. Backend Setup
1. Clone this repository and enter the directory.
2. Initialize environment variables:
   ```bash
   cp .env.example .env
   ```
3. Boot services:
   ```bash
   docker-compose up -d
   ```
4. Install Python dependencies and launch the backend API:
   ```bash
   uv sync
   uv run uvicorn src.main:app --reload
   ```

### 3. SwiftUI Client Setup
1. Open the Xcode Project:
   ```bash
   open "Project Chicken Soup/Project Chicken Soup.xcodeproj"
   ```
2. Build and run target `Project Chicken Soup` on **macOS** or **iOS**.
3. *Optional*: Run unit tests using the modern **Swift Testing** framework (`@Test`).

---

## 📚 The Lore Wiki

The knowledge graph is hydrated from structured markdown files in the [wiki/](file:///Users/mck/Desktop/chickensoup/wiki) directory (180 content pages and growing).

Pages are automatically created through two mechanisms:
- **File/Folder Upload**: Upload `.txt`/`.md`/`.json`/`.csv` files → AI analyzes content → wiki pages created with cross-references → synced to Neo4j.
- **Chat-to-Wiki Pipeline**: Enable in Settings → conversations with 10+ messages are periodically analyzed → entities, concepts, and projects extracted → wiki pages auto-created.

| Wiki Section | Count | Description |
|:---|---:|:---|
| [Entities](file:///Users/mck/Desktop/chickensoup/wiki/entities) | 81 | People, places, objects, events, programs |
| [Concepts](file:///Users/mck/Desktop/chickensoup/wiki/concepts) | 93 | Theories, frameworks, ideas, claims |
| [Projects](file:///Users/mck/Desktop/chickensoup/wiki/projects) | 6 | Engineering work, architecture, specifications |
| [Raw](file:///Users/mck/Desktop/chickensoup/wiki/raw) | 1+ | Immutable source documents, conversation snapshots |

### Advanced Capabilities & Services

* **Consensus-based Multi-LLM Querying**: Exposes `/consensus/query` to route requests across multiple local LLM providers, calculating consensus scores for high-reliability outputs.
* **Auto-Discovery Fallback**: Resolves active local LLM runtime (oMLX, Ollama, LM Studio) dynamically, mapping model properties and base URLs.
* **Wiki Backup & Restore**: Features pre-mutation backup snapshots in `src/wiki/backup.py` to prevent data loss during clearance or import.
* **Wiki Cleanup & Sanitation**: Deletes lore-related content in `src/wiki/cleanup.py` while preserving core system documentation, engineering guides, and user profile metadata.
* **API Authentication Security**: Employs headers (`X-API-Key`) validation on mutating endpoints (POST, DELETE) to secure internal graph modification.
* **MCP Integration**: Integration of FastMCP exposing 6 custom tools for external client consuming applications.
* **Observability (OpenTelemetry)**: Instruments standard OpenTelemetry traces, spans, and latency metrics for Neo4j, Redis, and quantum spacetime solver executions.

---

## 👥 Author

- **Mainza Kangombe** — [LinkedIn](https://www.linkedin.com/in/mainza-kangombe-6214295/)

---

## 📝 License

Proprietary / Research Project.
