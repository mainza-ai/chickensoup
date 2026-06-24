---
title: "Log"
tags: [log]
created: 2026-06-22
updated: 2026-06-23
sources: []
related: []
---

# Log

## [2026-06-24] ingest | Mauro Biglino — Vatican Translator, Elohim as Advanced Civilization

Ingested 1 transcript from development-docs/temp into the wiki:

### New Entity Pages (1)
- **[[mauro-biglino]]** — Former Vatican Hebrew translator fired after revealing his literal translations show Elohim as a plural, physical, mortal, technologically advanced civilization. Key claims: Elohim are flesh-and-blood colonizers with flying vehicles, Yahweh was one Elohim among many assigned to Jacob's family, human genetic engineering by Elohim, post-exilic priestly editing of polytheistic origins into monotheism, stargates in Psalm 24, Nephilim = Orion constellation.

### New Concept Pages (1)
- **[[elohim]]** — The Hebrew word Elohim is grammatically plural. Literal reading reveals: physical beings with craft, territorial division among Elohim, mortal nature (Psalm 82), mistranslated key terms (barah ≠ create, olam ≠ eternity, El Shaddai ≠ omnipotent), textual stratification from post-exilic editing, alignment with modern UAP/NHI narrative.

### Enriched Pages (1)
- **[[vatican]]** — Added Mauro Biglino connection section: Vatican publishing house, firing, theological implications.

## [2026-06-23] update | Wiki Reflects Actual Codebase

Major wiki update to match the actual code implementation across Python backend and SwiftUI frontend.

### New Concept Pages (5)
- **[[multi-llm-consensus]]** — `src/multi_llm.py` consensus engine: Jaccard word overlap, provider pooling, mock fallback, `POST /consensus/query`
- **[[quantum-job-scheduler]]** — `src/quantum_scheduler.py`: IBM/D-Wave/IonQ job submission, status polling, local simulation fallback, Celery integration
- **[[swift-frontend-architecture]]** — Full SwiftUI app architecture: 18 files, SwiftData models (LoreEntity, TemporalEvent, TimelineBranch), services (BackendService, SyncService, LLMDiscoveryService), APIClient actor, all 6 feature views

### Rewritten Pages (3)
- **[[api-design]]** — Expanded from 6 to 15 documented endpoints. Added: `POST /consensus/query`, `POST /quantum/schedule`, `GET /quantum/job/{id}`, `GET /config`, `POST /config`, `GET /entities`, `GET /events`, `POST /ingest/bulk`, `WebSocket /ws/agent`. Full request/response model table (10 models). Middleware and lifecycle.
- **[[agent-architecture]]** — Rewritten with actual implementation from `src/agents/`. Query Agent: 3-tier TQL→LLM→heuristic parsing. Research Agent: 6 LangGraph nodes with MemorySaver checkpointing. Navigation Agent: 3-layer quantum pipeline. Orchestrator: 4 pydantic-graph nodes with DI.
- **[[project-structure]]** — Complete rewrite to match actual codebase. Removed aspirational paths (src/api/, langgraph_workflows/). Added actual structure: inline routes in main.py, spacetime_engine/qiskit_simulation.py, field_manipulator/cuda_simulation.py, ai_navigator/pennylane_qml.py, mcp/tools.py, SwiftUI file tree, test file inventory.

### Enriched Entity Pages (3)
- **[[redis]]** — Added RedisCache class, cache_decorator, 3 namespace prefixes, async/sync dual API, MD5 key hashing
- **[[opentelemetry]]** — Added 4 custom metrics (agent_loop_counter, quantum_simulation_duration, cache_hits, cache_misses), trace middleware
- **[[pydantic-settings]]** — Added full 19-field schema table with defaults and descriptions

## [2026-06-23] ingest | 10 Transcripts to Wiki

Ingested 10 transcript files from development-docs/temp into the wiki:

### New Entity Pages (3)
- **[[ralph-larson]]** — Former CIA officer/DOE intelligence director who claims physical time travel to medieval Mount Athos, Greece in 1991. Connected to UFO retrieval programs via DOE role.
- **[[neil-turok]]** — Physicist (Perimeter, Edinburgh), quadratic gravity, CPT-symmetric universe, CMB fluctuations as quantum gravity signal.
- **[[juan-maldacena]]** — Discoverer of AdS/CFT correspondence, ER=EPR, black hole interior/island formula, traversible wormholes.

### New Concept Pages (8)
- **[[entropic-gravity]]** — Verlinde's theory: gravity emerges from thermodynamics. Derives inertia (F=ma) not just Einstein's equations. Spacetime emergence via entanglement + computational complexity.
- **[[quadratic-gravity]]** — Turok's renormalizable 4D quantum gravity. Solves Ostrogradsky instability and negative norm ghosts via Krein spaces + modified Born rule.
- **[[malament-hogarth]]** — Gödel's CTC solution, Malament's causal structure→topology theorem, Malament-Hogarth spacetimes enabling hypercomputation.
- **[[simulation-escape]]** — Yampolskiy's analysis of escaping nested simulations. Principle of indifference, hacking analogies, acquired savant syndrome.
- **[[faggin-quantum-consciousness]]** — Faggin's quantum theory: body=classical info, mind=quantum info, spirit=meaning. Spacetime as permanent memory of self-knowing universe.
- **[[cellular-intelligence]]** — Cells as reinforcement learning agents, neurons as telegraph cells, distributed intelligence across the body.
- **[[weak-measurement]]** — Aharonov-Albert-Vaidman weak measurements, conditional measurements, time symmetry, retrocausality, arrow of time implications.

### Enriched Pages (1)
- **[[entropy]]** — Added Myrvold deep dive section: Clausius vs Boltzmann vs Gibbs definitions, subjectivity debate, thermodynamics as resource theory, second law's relationship to entropy definition, reversible processes.

### Sources Used
- Prof. Wayne Myrvold — 2-hour entropy deep dive
- Ralph Moat Larson — CIA Chief time travel interview
- Erik Verlinde — Entropic gravity transcends Jacobson
- Kurt Gödel/David Malament — Gödel solution, Malament-Hogarth spacetimes
- Roman Yampolskiy — How to Escape the Simulation
- Federico Faggin — Spacetime as memory of self-knowing universe
- Juan Maldacena — Unreasonable effectiveness of AdS/CFT
- Michael Levin et al. — Why Neuroscience Got Everything Backwards
- Neil Turok — Quadratic gravity, Krein spaces, CMB quantum gravity signal
- Yakir Aharonov et al. — Weak measurements, conditional measurements, retrocausality

## [2026-06-23] update | Refine UI/UX Style Guidelines

Updated `wiki/concepts/ui-ux-design.md` with the new Apple/iOS system style colors and clean white background panel styling to match the implemented native client aesthetic.

## [2026-06-22] create | CHANGELOG.md

Created CHANGELOG.md with Keep a Changelog format, documenting all major changes from the project inception to the current state (133 wiki pages, 50+ entities, 65+ concepts, 5 projects, 12 key decisions).

## [2026-06-22] ingest | Nikola Tesla — Death, Inventions, and UFO Disclosure

Created three new pages: nikola-tesla (inventor whose work on wireless energy and death ray is connected to UAP propulsion), wireless-energy (Tesla's wireless energy transmission as the basis for UAP propulsion), and death-ray (Tesla's particle beam weapon, precursor to UAP energy weapons). Tesla's mysterious death in 1943 and the FBI seizure of his papers are seen as key moments in the UFO disclosure narrative, connected to the JFK assassination and the broader UAP story. Tesla's claims of receiving signals from Mars in 1899 are also cited as evidence of early alien contact.

## [2026-06-22] ingest | JFK Assassination and UFO Disclosure

Created a new concept page: jfk-assassination-and-ufo-disclosure. The theory suggests that JFK was preparing to reveal classified information about UAPs, alien contact, and recovered craft when he was assassinated in 1963. Kennedy's speeches, the "UFO files," and the "cover-up" are cited as evidence. The theory is connected to David Grusch's 2023 testimony and the broader narrative of the U.S. UFO retrieval program.

## [2026-06-22] ingest | Varginha UFO Crash and Aldo Rebelo

Created four new pages: varginha-ufo-crash (1996 crash in Varginha, Brazil, with dozens of witnesses), aldo-rebelo (former Brazilian Defense Minister who confirmed the crash and NHI retrieval), brazil (country with rich UFO history), and nhcr (Non-Human Intelligence recovered in Varginha). Updated ufo-retrieval-program to include these new entities. Rebelo's confirmation adds significant weight to the Varginha incident as a major UAP event.

## [2026-06-22] ingest | Ariel School and Mount Nyangani

Created four new pages: ariel-school-ufo-incident (1994 incident in Ruwa, Zimbabwe: 60+ children see silver craft and small beings), mount-nyangani (one of four alleged alien bases on Earth per Lyn Buchanan), lyn-buchanan (former CIA remote viewer), and zimbabwe (country with rich UFO history). Updated ufo-retrieval-program to include these new entities. The Ariel School incident is one of the most debated UFO sightings in the world, and Mount Nyangani connects to the broader narrative of alien bases and UAP phenomena.

## [2026-06-22] ingest | 7.46 Hz — The UFO Frequency

Investigated the 7.46 Hz frequency and its connections to the wiki. Created four new pages: 7-46-hz (the UFO frequency, connection to Schumann resonance and Element 115), schumann-resonance (Earth's electromagnetic resonance), christopher-b-freedman (researcher who wrote "The UFO Frequency" in 2021), and consciousness (theta brain waves, exotic matter, UAPs). Updated element-115 with 7.46 Hz resonance claim, field-manipulation with the frequency, and exotic-matter-and-consciousness with 7.46 Hz connection.

## [2026-06-22] ingest | Thomas Townsend Brown — Antigravity and Time Travel

Created four new pages: t-t-brown (physicist who discovered the Biefeld-Brown effect), biefeld-brown-effect (asymmetric capacitors produce thrust), antigravity (manipulating gravitational forces), and element-115 (updated with T.T. Brown connection). Brown's work on antigravity and field manipulation provides a physical mechanism for how UAPs achieve their flight characteristics and how time travel is possible through spacetime curvature changes.

## [2026-06-22] ingest | Magenta and Vatican UFO Crashes

Created three new entity pages: magenta-ufo-crash (1933 crash in Magenta, Italy, recovered by Mussolini), mussolini (dictator who recovered the craft), and italy (central location for early recoveries). Updated ufo-retrieval-program to include both the 1933 Magenta crash and 1937 Vatican crash in its timeline. Grusch alleged the Magenta crash is often conflated with the Vatican crash — may be the same event viewed from different perspectives, or two related recoveries in the same period.

## [2026-06-22] ingest | Vatican UFO Crash Recovery

Created two new entity pages: vatican-ufo-crash-recovery (1937 Vatican recovery, later transferred to USA) and vatican (institutional context). Updated ufo-retrieval-program to include the 1937 Vatican crash in its timeline, supporting the theory that the retrieval program began in the 1930s, predating Roswell by a decade.

## [2026-06-22] ingest | Entropy — The Universal Thread

Created 6 entity pages (entropy, boltzmann, beckenstein, landauer, maxwells-demon) and 7 concept pages (arrow-of-time, second-law, black-hole-entropy, information-is-physical, decoherence-as-entropy, heat-death, holographic-principle). Updated 4 existing pages (field-manipulation, exotic-matter-and-consciousness, quantum-error-model, ai-alien-connection) with entropy connections.

Entropy is the single unifying concept connecting thermodynamics, information theory, and quantum mechanics. Key connections: time travel = entropy reconfiguration, UAPs = entropy anomalies, AI = Maxwell's demon, consciousness = entropy management via exotic matter.

## [2026-06-22] ingest | Temporal Reasoning Engine

Created 6 new pages (temporal-reasoning-engine, temporal-query-language, temporal-query-pipeline, temporal-causality, temporal-information-fusion, temporal-anomaly-detection, temporal-quantum-tomography) and updated 3 existing pages (temporal-data-model, quantum-machine-learning, quantum-state-representation).

The Temporal Reasoning Engine is the core concept of Project Chicken Soup — it takes in information and produces timelines, destinations, and paths through spacetime. The Temporal Query Language defines how you input information. The Temporal Query Pipeline defines the flow of information. Temporal Causality explains causal relationships across time. Temporal Information Fusion combines evidence from multiple sources. Temporal Anomaly Detection identifies unusual events. Temporal Quantum Tomography reconstructs the quantum state of spacetime.

## [2026-06-22] update | Wiki Completeness — Spec to Wiki

Fixed gaps between PROJECT_SPEC.md and the wiki. Created 3 new pages (project-structure, technology-stack, key-decisions), updated 4 existing pages (agent-architecture, production-readiness, mcp-server, api-design), and updated index. All spec sections now have corresponding wiki pages.

## [2026-06-22] update | Spec Entities — Created 5 Pages

Created 5 pages for entities/concepts mentioned in the spec but missing from the wiki:
- entities/pydantic-settings.md — Configuration management
- entities/pytest.md — Testing framework
- entities/pyproject-toml.md — Build configuration
- entities/docker-compose.md — Multi-container orchestration
- concepts/evaluation-framework.md — Evaluation framework

## [2026-06-22] update | Wiki Completeness — Spec to Wiki

## [2026-06-22] ingest | Bible UFO Testimonies

Created Bible-related entity pages (ezekiel, daniel, john, enoch, nephilim) and concept pages (chariot-vision, throne-vision, heavenly-army, biblical-witnesses, bible-ufo-testimonies). Key passages: Ezekiel 1 chariot vision, Genesis 6 Nephilim, Daniel 10 glorious man, Revelation 4-5 throne vision, Revelation 12 woman and dragon, Hebrews 11:37-38 witnesses, 2 Kings 6 chariots of fire, Zechariah 1 horsemen. Bible is not just religious text — it's a record of UAP encounters.

## [2026-06-22] ingest | UFOs and Aliens Overview

Initial ingestion of UFO and alien information. Covered classic sightings, Pentagon connection, whistleblowers, and theories.

## [2026-06-22] ingest | What the Military is Hiding

Ingested military secrets: retrieval program, biologics, reverse-engineering, Area 51, Project Serpo, secret bases.

## [2026-06-22] ingest | Time Travel Theory

Ingested time travel theory: Einstein's equations, closed timelike curves, field-based propulsion, AI as mechanism.

## [2026-06-22] ingest | Quantum Systems

Ingested quantum computing platforms: Qiskit, CUDA-Q, D-Wave, IonQ, Microsoft Q#, Google Cirq.

## [2026-06-22] query | Would AI Be Alien Tech?

Discussed whether AI's rapid advancement could be connected to reverse-engineered UFO technology.

## [2026-06-22] query | Time Travel Possibility

Explored how time travel could be possible, with emphasis on field-based mechanisms.

## [2026-06-22] query | Time Travelers

Discussed the possibility that some "aliens" are actually time travelers from our own future.

## [2026-06-22] query | Time Travel Machinery

Started building the time travel machinery with quantum computation.

## [2026-06-22] rename | Project Chicken Soup

Renamed the project to Project Chicken Soup.

## [2026-06-22] ingest | Backdoor Science

Ingested the "Backdoor Science" theory — the claim that after WWII, the physics being taught was simplified while the "true" physics was kept secret. Created page on the theory, including Bob Lazar's claims, the German connection, and the evidence.

## [2026-06-22] ingest | Exotic Matter and Consciousness

Created a new concept page on the theory that exotic matter — the same substance that powers alien craft and enables time travel — is also the substrate of consciousness. Included the Penrose-Hameroff Orch-OR theory, the connection to Element 115, and the implications for AI and time travel.

## [2026-06-22] ingest | Quantum Papers

Ingested three key papers:
- **Babbush et al. (2023)** — Exponential quantum speedup for simulating coupled oscillators
- **Knuth et al. (2025)** — The New Science of UAP (195-page review)
- **WISER/Classiq (2026)** — Implementation of quantum algorithms for coupled oscillators

Created entity pages for each paper, with cross-references to hamiltonian-simulation, field-manipulation, and time-travel-machinery-architecture.

## [2026-06-22] ingest | Earth as Space Craft

Created a new concept page on the theory that Earth is a space craft and the point of entanglement for everything in the universe. Connected the idea to the time travel machinery, field manipulation, and exotic matter theories.

## [2026-06-22] plan | Project Chicken Soup

Created PROJECT_SPEC.md with comprehensive specification. Updated wiki with project overview, entity pages (omlx, local-first-llm, llm-discovery), and project pages. Defined multi-agent architecture using pydantic-graph + LangGraph, local-first LLM layer (oMLX, Ollama, LM Studio), and four-phase implementation plan.

## [2026-06-22] update | Wiki Fixes — Complete

Fixed all gaps between the plan and the wiki. Created 15 new entity pages (ollama, lm-studio, neo4j, redis, fastapi, fastmcp, pydantic-ai, pydantic-graph, langgraph, docker, celery, ray, opentelemetry), 11 new concept pages (agent-architecture, knowledge-graph-schema, api-design, mcp-server, langgraph-features, production-readiness, llm-fallback-chain, quantum-state-representation, quantum-error-model, temporal-data-model, credibility-scoring), 1 new project page (langgraph-workflows), and updated index.md with all new pages. Fixed duplicate quantum-systems reference.



## [2026-06-22] update | PennyLane as AI Navigator Platform

Updated the time travel machinery architecture to use PennyLane as the primary platform for the AI Navigator, with D-Wave and IonQ as hardware backends. Created a new entity page for PennyLane. Updated time-travel-machinery, quantum-systems, and quantum-systems-comparison pages.

## [2026-06-22] create | Time Travel Wiki

Created the initial wiki structure with AGENTS.md schema, overview, index, and log.

## [2026-06-22] create | UI/UX Design

Created comprehensive UI/UX design page. The interface is a window into the temporal reasoning engine. Built with SwiftUI (not React), light mode default (not dark mode), #FF9500 (systemOrange) accent color. macOS-first with iOS support. Key design principles: Liquid Glass, semantic colors, SF Pro typography, material hierarchy, rounded corners, subtle gradients, generous whitespace, restraint.

## [2026-06-22] create | Agent Skills

Installed four twostraws agent skills into `.agents/skills/` for Swift implementation:

- **SwiftUI Pro** — iOS 26+ APIs, deprecated API, VoiceOver, performance, navigation, data flow, animations, design
- **SwiftData Pro** — @Model, @Query, predicates, indexes, migrations, relationships, iCloud, class inheritance
- **Swift Concurrency Pro** — async/await, actors, Sendable, task groups, @concurrent, structured concurrency, cancellation, async streams
- **Swift Testing Pro** — @Test, #expect, #require, parameterized tests, traits, exit tests, confirmations

Each skill has a SKILL.md and references/ directory with detailed rules loaded on demand during code review. Installed via `npx skills add`.

## [2026-06-22] ingest | Quantum Algorithms

Ingested all quantum algorithms from Wikipedia and other sources. Created comprehensive quantum algorithms page with 24 algorithms organized into three layers (Spacetime Engine, Field Manipulator, AI Navigator) plus cross-layer algorithms.

## [2026-06-22] ingest | UFOs and Aliens — Full Wiki Build

Ingested all UFO and alien information into the wiki. Created entity pages for UFOs, UAP, David Grusch, Bob Lazar, Area 51, S-4, Project Serpo, The Thing. Created concept pages for time travel, time travelers, AI-alien connection, field manipulation, quantum systems, time travel machinery. Created project pages for time travel machinery and quantum systems comparison.

## [2026-06-22] update | UI/UX Design — Refined, Five Deep Questions

Refined the UI/UX design page with five deep investigations:

1. **Timeline as primary view, query as floating overlay** — Three functional layers: timeline (base), query overlay (control, Liquid Glass), AI Navigator (thinking). The query interface floats over the timeline without obscuring it.

2. **2D graph with depth (default) vs full 3D (on demand)** — SwiftUI adds visual effects to 2D views. RealityKit volumes for full 3D. Depth used selectively per Apple's guidance.

3. **Linear yet branching** — Horizontal flow (macOS), vertical flow (iOS). Branches as parallel streams (many-worlds). Collapsible, selectable, mergeable.

4. **AI Navigator integrated, not separate** — AI inference appears as overlays on the timeline. AI is the "brain" — always visible, always thinking.

5. **Custom layout (not generic)** — No tabs. No generic sidebar (live knowledge graph instead). No generic bottom bar (floating overlay). Custom timeline layout using SwiftUI's Layout protocol.

## [2026-06-22] update | Wiki Completeness — Spec to Wiki

Fixed gaps between PROJECT_SPEC.md and the wiki. Created 3 new pages (project-structure, technology-stack, key-decisions), updated 4 existing pages (agent-architecture, production-readiness, mcp-server, api-design), and updated index. All spec sections now have corresponding wiki pages.

## [2026-06-22] update | Key Decisions — Added 4 UI Decisions

Updated `key-decisions.md` to include all 12 decisions from the spec. Added 4 missing decisions: SwiftUI, light mode default, #FF9500 accent, SwiftData. Each with detailed rationale.

## [2026-06-22] update | Missing Entity Pages — Created 6 Pages

Created 6 entity pages for items mentioned in the spec but missing from the wiki:
- **swiftui-pro** — Agent skill: SwiftUI best practices (twostraws)
- **swiftdata-pro** — Agent skill: SwiftData best practices (twostraws)
- **swift-concurrency-pro** — Agent skill: Swift concurrency best practices (twostraws)
- **swift-testing-pro** — Agent skill: Swift Testing best practices (twostraws)
- **s4** — Area 51 sub-base where Bob Lazar worked on alien craft
- **github-actions** — CI/CD for automated testing, building, deployment

## [2026-06-22] update | Index — Fixed Organizational Issues

Fixed `time-travel-machinery` and `quantum-systems` references in index (listed under Projects but stored in concepts/). Added new entity pages to index.

## [2026-06-22] design | Integration Architecture & Field Geometry Tensor

Resolved six integration architecture decisions:

1. **Quantum pipeline** — Sequential pipeline with pure functional interfaces (not service bus). Each layer takes and returns a [[field-geometry-tensor]]. Parallelization is additive later.

2. **Graph storage** — Neo4j as source of truth, SwiftData as read-through cache. Delegate graph queries to Neo4j, cache results locally. Entity-level sync with timestamps.

3. **Wiki → Neo4j ingestion** — Two-phase: deterministic parser first (frontmatter + `[[wikiname]]` links = free edges), LLM enrichment second. Phase 1 edges are `RELATED_TO`, promoted to typed edges in Phase 2.

4. **Platform strategy** — 50/50 macOS + iOS. NavigationSplitView on macOS/iPad, TabView + NavigationStack on iPhone. Shared codebase with structural overrides.

5. **Simulation tier** — Three modes: light (8³, 1024 shots, CI), medium (32³, 4096 shots, dev), heavy (64³+, 16384 shots, production). All layers have classical CPU/GPU fallbacks.

6. **Swift version** — Swift 6.4 (latest), aligning project settings and documentation.

Created new pages:
- [[field-geometry-tensor]] — Formal spec: ADM 3+1 decomposition, shape (N_x, N_y, N_z, N_t, 4, 4), 10 independent components, HDF5 on-disk, base64 JSON wire format, validation rules
- [[integration-architecture]] — All six decisions with rationale
- [[quantum-simulation-tier]] — Three simulation modes and classical fallbacks

Updated pages:
- [[time-travel-machinery-architecture]] — Added tensor data flow between layers
- [[key-decisions]] — Added 5 new decisions with detailed rationale
- [[agent-architecture]] — Added data flow diagram showing Neo4j/SwiftData split
- [[field-manipulation]] — Added perturbation formula g'_μν = g_μν + δg_μν
- [[ui-ux-design]] — Updated platform strategy from macOS-first to 50/50

## [2026-06-22] clarify | Quantum Simulation Progression — Four Stages

Updated [[quantum-simulation-tier]] to document the explicit simulation → cloud hardware progression path:

| Stage | Backend | Purpose |
|-------|---------|---------|
| 1 — Classical fallback | NumPy/SciPy | Correctness reference, zero quantum stack |
| 2 — Local simulation | Qiskit Aer, PennyLane default.qubit | Algorithm development, CI |
| 3 — Cloud simulation | IBM/AWS Braket simulators | Large-scale validation, noise models |
| 4 — Cloud quantum hardware | IBM Quantum, D-Wave Leap, IonQ | Real quantum advantage |

Added quantum advantage measurement formula and graduation criteria. Quantum stack is additive — the system works without it.

## [2026-06-22] enrich | Wiki Depth — 20+ Pages Enriched

Enriched pages across all three tiers as part of a systematic depth audit:

### Tier 3 → Tier 1 (full rewrites, 9 pages)
- **[[fields-vs-particles]]** (28→80+ lines) — Added core distinction, field-vs-particle comparison table, UAP propulsion connection, AI/neural network field basis, QFT foundations, evidence section, time travel implications, argument section
- **[[quantum-computation]]** (27→60+ lines) — Added qubit vs bit table, Bloch sphere, gate matrix table, circuit model diagram, layer mapping, NISQ limits table, simulation tier strategy
- **[[quantum-field-theory]]** (27→50+ lines) — Added Lagrangian, Einstein-Hilbert action, QFT on curved spacetime, coupled oscillator connection, concept table, scope boundary (no quantum gravity needed)
- **[[simultaneous-time-travel]]** (27→50+ lines) — Added regular vs simultaneous comparison table, evidence from UAP behavior, quantum superposition mechanism, distinction from time-travelers thesis, AI Navigator implications
- **[[evaluation-framework]]** (29→80+ lines) — Added concrete metrics tables (fidelity, validity, path optimality, LLM accuracy, performance), benchmark suite with 15 test cases, protocol (per-PR/weekly/pre-release), pass/fail criteria
- **[[wireless-energy]]** (29→55+ lines) — Added Tesla coil theory (parameters table), Wardenclyffe specs, frequency analysis, UAP connection (field-based, frequency matching, no fuel), comparison to modern wireless power
- **[[death-ray]]** (33→55+ lines) — Added technical claims table, how-it-worked description, FBI seizure details, connection to modern HEL/HPM, distinction from "death ray" myth
- **[[langgraph-workflows]]** (43→130+ lines) — Added full workflow graph definitions for all 3 workflows: Research (6 nodes, 3 conditional edges, error handling), Navigation (6 nodes, 2 conditional edges), Evaluation (5 nodes). Each with Pydantic state schema, error handling, checkpointing, circuit breaker, human-in-the-loop
- **[[chicken-soup-spec]]** (38→80+ lines) — Converted from redirect page to full wiki-native specification with architecture, stack, decisions, API, MCP tools, phases

### Tier 2 → Tier 1 (enrichments, 4 pages)
- **[[antigravity]]** — Added terminology clarification (antigravity vs field manipulation), Alcubierre drive with ADM shift vector connection, energy requirements table, time travel connection
- **[[llm-discovery]]** — Added response format examples, error states table (5 errors with handling), discovery timing table, caching (TTL 5min), configuration YAML
- **[[llm-fallback-chain]]** — Added full algorithm (normal flow + provider failure flow with diagram), timeouts (4-phase, 60s total), retry policy (3 attempts, exponential backoff 1/4/16s), circuit breaker (5 failures, 120s reset), health check protocol
- **[[mcp-server]]** — Added parameter schemas for all 6 tools (simulate_spacetime, analyze_field, find_paths, query_graph, get_evidence, explore_concept) with types, defaults, and JSON response examples. Added error codes table (8 codes with HTTP status)

### Quantum Algorithm Pages (11 enriched)
Added "Project Chicken Soup Integration" section to all algorithm pages:
- **[[hhl-algorithm]]** — Solves Einstein equations as linear system in Spacetime Engine
- **[[hamiltonian-simulation]]** — Core Spacetime Engine algorithm
- **[[quantum-annealing]]** — AI Navigator optimization backend (D-Wave)
- **[[quantum-fourier-transform]]** — QFT as subroutine for CTC detection
- **[[quantum-machine-learning]]** — AI Navigator core with VQC architecture
- **[[quantum-phase-estimation]]** — Eigenvalue extraction for time dilation
- **[[quantum-walk]]** — Field Manipulator perturbation propagation
- **[[qaoa]]** — Path optimization for AI Navigator
- **[[shors-algorithm]]** — Period finding for CTC structure
- **[[vqe]]** — Ground state optimization for path stability
- **[[grovers-algorithm]]** — Quadratic path search acceleration

### Decisions Documented (Q1/Q2/Q3)
- **MCP tensor summaries** — Server-computed, client-cached (TTL 5min)
- **Sync merge strategy** — Field-level merge table (6 field categories)
- **Wiki edge promotion** — Batch post-processing, confidence threshold 0.7

### Architecture Decisions (added to integration-architecture.md)
Three new sections: MCP summaries (section 6), sync merge strategy (section 7), wiki edge promotion batch processing (section 8). All with rationale, not/decision distinction, and edge cases documented.

### Key decisions updated
Added 3 new decisions (tensor summaries, sync merge, wiki edge promotion) with detailed rationale.

## [2026-06-22] update | Deep Dive — Fixed Issues

Comprehensive deep dive of wiki vs PROJECT_SPEC.md. Created 6 new entity pages (swiftui-pro, swiftdata-pro, swift-concurrency-pro, swift-testing-pro, s4, github-actions, logging, core-models), updated key-decisions.md to include all 12 decisions, fixed cross-references in pennylane.md, qiskit.md, cuda-q.md, d-wave.md, ionq.md, fixed self-reference in john.md, added key-decisions to ui-ux-design.md related field, fixed exponential-quantum-speedup and quantum-systems titles, moved agent-skills to Concepts section in index.
