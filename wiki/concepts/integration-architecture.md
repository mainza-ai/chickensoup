---
title: "Integration Architecture"
tags: [architecture, integration, decisions]
created: 2026-06-22
updated: 2026-06-22
sources: [PROJECT_SPEC-2026]
related: [agent-architecture, field-geometry-tensor, knowledge-graph-schema, key-decisions, ui-ux-design, quantum-simulation-tier]
---

# Integration Architecture

This page documents the key architectural integration decisions for Project Chicken Soup — how the major subsystems connect, communicate, and compose.

## 1. Quantum Layer Integration: Sequential Pipeline

**Decision:** Sequential pipeline with pure functional interfaces.

**Not:** Independent calls or service bus.

Each quantum layer (Qiskit → CUDA-Q → PennyLane) is a **pure function** that takes a [[field-geometry-tensor]] and returns a transformed one:

```python
FieldGeometryTensor → Layer(FieldGeometryTensor, **params) → FieldGeometryTensor
```

The field geometry tensor is the **contract** between layers — its shape, components, and semantics are fixed. Any layer can be replaced as long as it respects this contract.

**Rationale:**
- Correctness first: sequential data flow makes it traceable when results are wrong
- Parallelization is additive: once sequential is verified, wrap layers in a pub/sub adapter
- The field geometry tensor encodes everything needed: metric, perturbation, stress-energy
- Pure functional interfaces are independently testable with synthetic inputs

**When the service bus becomes valuable:** For parallel exploration — testing 50 field configurations simultaneously. At that point, add a bus adapter around each pure function without changing the core logic.

## 2. Knowledge Graph: Neo4j as Source of Truth, SwiftData as Cache

**Decision:** Delegate graph queries to Neo4j; use SwiftData as a read-through cache for offline operation.

**Not:** A local Neo4j-like store on-device, or a thin client with no offline capability.

**Storage roles:**

| Store | Role | Online | Offline |
|-------|------|--------|---------|
| Neo4j | Single source of truth, all graph queries | Read/write | Unavailable |
| SwiftData | Recent query results, cached entities, user prefs, write queue | Sync from Neo4j | Serve cache, queue writes |
| oMLX | On-device LLM inference | Available | Available |

**Offline capability:**
- The Swift app works fully offline for anything already cached
- oMLX provides on-device LLM inference independently of backend status
- Queued writes sync when connectivity returns (last-write-wins with timestamps)
- Sync is entity-level, not full-graph — no attempt to replicate Neo4j on-device

**Rationale:**
- Neo4j's Cypher graph traversals (shortest-path, multi-hop, pattern matching) are the strongest architectural asset — replicating them in SwiftData is rebuilding Neo4j badly
- SwiftData is ideal for flat entity storage and relationships, not graph queries
- Entity-level sync with timestamps avoids merge conflicts

## 3. Wiki → Neo4j Ingestion: Two-Phase

**Decision:** Two-phase ingestion: deterministic first, LLM enrichment second.

| Phase | Method | What It Extracts | Cost |
|-------|--------|-----------------|------|
| Phase 1 | Deterministic parser | YAML frontmatter (title, tags, sources, related), `[[wikiname]]` links in body | Zero API cost |
| Phase 2 | LLM extraction | Entity mentions in body text that lack `[[wikiname]]` syntax | Per-page LLM call |

**Edge types by source:**

| Source | Phase 1 Edge | Phase 2 Edge |
|--------|-------------|-------------|
| `related:` frontmatter | `RELATED_TO` | Promoted to typed (e.g., `WORKED_AT`) |
| `[[wikiname]]` in body | `RELATED_TO` | Promoted to typed |
| Body text, no wikiname | — | LLM extracts typed edge |

Both edge types can coexist between the same nodes. Phase 2 enriches rather than replaces.

**The `[[wikiname]]` advantage:** Obsidian's `[[link]]` syntax is already structured data — it's essentially free edge extraction. A page `[[bob-lazar]]` containing `[[area-51]]` and `[[element-115]]` generates `RELATED_TO` edges to both without any NLP.

## 4. SwiftUI Platform Strategy: 50/50 Hybrid Universal

**Decision:** Single shared codebase with structural platform overrides. Not treating iOS as a scaled-down afterthought, nor ignoring mobile constraints.

**Navigation by platform:**

| Device | Container | Behavior |
|--------|-----------|----------|
| macOS | `NavigationSplitView` | True persistent multi-column sidebar |
| iPad (regular width) | `NavigationSplitView` | Desktop treatment with sidebar |
| iPhone (compact) | `TabView` + `NavigationStack` | Bottom tab bar for thumb reach |

**Implementation pattern:**

```swift
struct RootNavigationView: View {
    #if os(macOS)
    var body: some View {
        NavigationSplitView {
            SidebarView()
        } detail: {
            DetailView()
        }
    }
    #else
    @Environment(\.horizontalSizeClass) private var sizeClass
    var body: some View {
        if sizeClass == .compact {
            TabView {
                NavigationStack { SidebarView() }
                    .tabItem { Label("Home", systemImage: "house") }
            }
        } else {
            NavigationSplitView { SidebarView() }
            detail: { DetailView() }
        }
    }
    #endif
}
```

**Desktop element handling:**
- **Hover:** Wrapped in `.onHover` — iOS ignores for touch but works with trackpad
- **Keyboard shortcuts:** Attached via `.keyboardShortcut` — iOS strips without external keyboard
- **Context menus:** `.contextMenu` works natively on both platforms
- **List styles:** `.sidebar` on macOS/iPad, `.insetGrouped` on iPhone
- **Toolbar:** Shift items to `.bottomBar` when navigation bar is crowded on iPhone

## 5. Quantum Simulation Tier: Three Modes

**Decision:** Three simulation tiers, not just one.

| Mode | Backend | Grid Resolution | Shots | Use Case |
|------|--------|-----------------|-------|----------|
| Light | Qiskit Aer, PennyLane default.qubit | 8³ or 16³ | 1024 | CI, unit tests, rapid iteration |
| Medium | Same backends, higher precision | 32³ | 4096 | Development, local testing |
| Heavy | Same + GPU acceleration | 64³ or 128³ | 16384 | Production-quality results |

**Rationale:**
- Qiskit Aer simulates Qiskit circuits with configurable noise models (approximates real hardware)
- PennyLane's `default.qubit` simulates quantum circuits for the Navigator
- CUDA-Q includes its own simulator for Field Manipulator kernels
- "Light mode" completes in seconds, enabling CI without quantum hardware
- "Heavy mode" is still classical simulation, but at sufficient fidelity to validate results before deploying to D-Wave/IonQ

**All three quantum layers have classical CPU/GPU fallbacks** (NumPy/SciPy for Spacetime Engine, array math for Field Manipulator, scipy.optimize for Navigator) — ensuring the system functions without any quantum stack installed.

## 6. MCP Tensor Summaries: Server-Computed, Client-Cached

**Decision:** The tensor summary fields (mean_curvature, max_perturbation, valid_metric) are computed on the server and cached alongside query results in SwiftData. The client does not compute summaries locally.

**Not:** Recomputing summaries from raw tensor data on-device.

**Rationale:**
- The full tensor is large (64³ × 4×4 × 8 bytes ≈ 8 MB per metric) — storing more than a handful of recent tensors on-device is impractical
- The summary (a few floats + validity flags) is trivial to cache
- The server has the authoritative physics pipeline and knows the correct invariants
- Cached summaries have a configurable TTL (default 5 min)
- A "refresh summary" button makes a lightweight API call (recompute, not re-simulate)

**Offline behavior:**
- Display cached summary with "last refreshed" indicator
- All cached data still usable — summaries are for display/information, not for computation

## 7. Sync Merge Strategy: Field-Level, Not Blind LWW

**Decision:** The sync merge uses field-level strategies, not blanket last-write-wins. Different fields have different merge semantics.

| Field Category | Strategy | Rationale |
|----------------|----------|-----------|
| `timestamp`, `updated_at` | LWW (later wins) | Pure ordering, no semantic value |
| `confidence`, `credibility_score` | Server-authoritative | These are computed by the backend analysis pipeline |
| `user_notes`, `tags`, `annotation` | Client wins | User-generated, no server analog |
| `sources[]`, `evidence[]` | Union with dedup | Both sides may add valid sources independently |
| Relationship edges | Server-authoritative | Graph topology is managed by Neo4j |

**Merge process on reconnect:**
1. Client sends queued writes to server
2. Server classifies each field by merge strategy
3. Server applies the merge
4. Server returns the reconciled entity to the client
5. Client replaces its cached entity with the reconciled version

**Conflict log:** Any merge where confidence discrepancy > 0.1 or field-level conflict occurs is logged for manual review. This is critical because losing a confidence score update could affect research agent outputs.

**What triggers a confidence score update:** New source ingested, LLM re-analysis of existing sources, user feedback (explicit rating, usage patterns), cross-referencing across independent sources.

## 8. Wiki Edge Promotion: Batch Post-Processing

**Decision:** Phase 2 (LLM enrichment) runs as a batch post-processing pass, not per-page. Phase 1 (deterministic) runs per-page during ingestion.

**Phase 1 (inline, per-page):**
- Parse YAML frontmatter → node properties
- Parse `related:` field → `RELATED_TO` edges
- Parse `[[wikiname]]` links in body → `RELATED_TO` edges
- Store page node with `last_deterministic_processed` timestamp

**Phase 2 (scheduled, batch):**
- A scheduled/polled job finds all page nodes where `last_llm_enriched < last_deterministic_processed`
- Batch processes pages in groups (configurable: 5-10 pages per LLM call)
- For each `RELATED_TO` edge, the LLM examines surrounding context and assigns a semantic type
- For body text mentions without `[[wikiname]]`, LLM proposes new nodes and typed edges
- Stores results with confidence score for each promoted edge
- Updates `last_llm_enriched` on the page node

**Confidence threshold for edge promotion:**
- LLM edge classification comes with a confidence score
- Only promote edges above a configurable threshold (default: 0.7)
- Below threshold: keep as `RELATED_TO` and flag for manual review

**Why batch:** LLM calls are expensive and rate-limited. Processing pages in batch gives the LLM more context (it sees multiple related pages per call). The deterministic Phase 1 graph is already useful and complete — Phase 2 is refinement.

## See Also

- [[field-geometry-tensor]] — The contract between layers
- [[agent-architecture]] — Multi-agent orchestration
- [[key-decisions]] — All key decisions
- [[knowledge-graph-schema]] — Graph schema and ingestion
- [[ui-ux-design]] — UI platform strategy
- [[quantum-systems-comparison]] — Platform choices
