---
title: "Key Decisions"
tags: [project, decisions, architecture]
created: 2026-06-22
updated: 2026-07-12
sources: [PROJECT_SPEC-2026, living-almanac]
related: [agent-architecture, local-first-llm, api-design, mcp-server, knowledge-graph-schema, technology-stack, credibility-scoring, living-almanac, frontend-settings-menu]
---

# Key Decisions

## Decision Table (Current — 30+ decisions)

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Agent framework | pydantic-graph + LangGraph | Type-safety (pydantic-graph) + features (LangGraph) — tribunal is LangGraph 4-node workflow |
| Knowledge graph | Neo4j | Natural fit for entity-relationship data, Cypher queries |
| LLM | oMLX (Mac default), Ollama, LM Studio | Local-first, auto-discovery, fallback chain |
| API | FastAPI + OpenAPI | Modern, type-safe, auto-generated docs — now 40+ endpoints |
| MCP | FastMCP | Standard protocol, simple integration |
| Cache | Redis | Industry standard + Lua atomic budget tracker |
| Container | Docker | Simple, portable, reproducible |
| CI/CD | GitHub Actions | Simple, integrated, free |
| UI | SwiftUI | Native Apple design, macOS + iOS |
| UI theme | Light mode default | Warm, inviting, "chicken soup" |
| UI accent | #FF9500 (systemOrange) | Warm, distinctive |
| UI data | SwiftData | Simpler than Core Data |
| Quantum integration | Sequential pipeline | Pure functions, field geometry tensor as contract |
| Graph storage | Neo4j (source of truth) + SwiftData (cache) | Delegate graph queries, cache results locally |
| Wiki ingestion | Two-phase (deterministic → LLM) | Free edges from `[[wikiname]]`, LLM enrichment later |
| Platform | 50/50 macOS + iOS | Single codebase, structural platform overrides |
| Simulation tier | Three modes (light/medium/heavy) | CI through production, classical fallbacks |
| Confidence gate | 0.6 threshold for intent routing | Prevents low-confidence LLM misclassifications from reaching wrong sub-agent |
| Wiki file fallback | Direct file read when Neo4j unavailable | Research agent functional without running Neo4j |
| Timeout architecture | 3 tiers (15s/30s/60s) + 120s orchestrator | Stops hung LLM calls from blocking |
| Conversation storage | Redis, last 20 turns, 24h TTL | Multi-turn without client state |
| **Wiki paths centralization** | `src/wiki/paths.py` | Resolves `WIKI_DATA_DIR` once, replaces 6 duplications |
| **Log ignore patterns** | `LOG_IGNORE_PATTERNS` in writer.py | Prevents pytest temp paths from polluting `wiki/log.md` |
| **Claim wavefunction** | 3-basis {corroborated,contested,unverified} via AerEstimatorV2 | Replaces hardcoded `0.95/0.5/0.8/+0.1/+0.15` constants, falsifiable inputs logged, named constant `SOCIAL_TRACTION_WEIGHT=0.15` not buried |
| **Social vs epistemic** | Two separate numbers, never merged | `ClaimConfidence` carries both; calibration test asserts decoupling; UI shows two badges/gauges side-by-side |
| **Meyer-Wallach extractor** | `src/spacetime_engine/entanglement.py` reusable | VQE rejection at <0.3 + entanglement correlation share same scorer |
| **Divergence reuse** | `claims_to_vector` + `vector_to_field_geometry` + `find_optimal_path` | Spec requires grep-able shared function call, not duplicate warp formula |
| **Timeline reconstruction** | `wiki/raw/pulse/*.json` + `git log`, no new TSDB | Chartable shape trivially plottable for SwiftUI |
| **Tribunal gate** | Contested or divergence>0.7, uncontested never triggers | Cost control — 0 LLM calls for uncontested (tested) |
| **Budget guardrails** | Lua atomic check+incr + HOLD | Redis `BUDGET_LUA_CHECK` + `BUDGET_HOLD_LUA`, `budget:YYYY-MM` hash, `POST /budget/approve` to clear |
| **Network opt-in tier** | `LAST30DAYS_ENABLED=false` default, `source_tier` labeling | Local-first boundary explicit, same gate shape as `QUANTUM_HARDWARE_ENABLED` |
| **Subprocess security** | `shell=False` always, list args | Entity name with `; rm -rf /` passed as single arg, not shell interpreted (tested) |
| **Almanac idempotency** | Hash of confidence states | Same hash → `no_material_change` logged not redundant brief |
| **Almanac HTML quality** | Inline CSS, no JS, dark mode media query, print-friendly | Self-contained brief opens offline |

## Agent Framework

**Decision:** pydantic-graph + LangGraph

**Rationale:** pydantic-graph type-safety for core routing. LangGraph for complex sub-workflows: research graph (6 nodes, checkpointing, human-in-the-loop), tribunal (4 nodes, 3 roles + referee), time travel workflows. See [[agent-architecture]].

## Knowledge Graph

**Decision:** Neo4j with wiki file fallback + LLM edge classification (retry + backoff + heuristic fallback)

**Rationale:** Cypher queries for entity/relationship data. Wiki file fallback when Neo4j unavailable. LLM edge classification with exponential backoff (`LLM_EDGE_CLASSIFICATION_TIMEOUT=30`, `MAX_RETRIES=3`). See [[knowledge-graph-schema]].

## LLM

**Decision:** oMLX (Mac default), Ollama, LM Studio — auto-discovery fallback chain

**Rationale:** Local-first. All OpenAI-compatible `/v1` endpoints. Discovery via `/v1/models` probe with 5s timeout. See [[local-first-llm]].

## Quantum Credibility

**Decision:** Every claim gets a wavefunction over 3 basis states, scored via real `FieldGeometryTensor` math + Qiskit VQE (AerEstimatorV2 pattern)

**Rationale:** Spec says "Do not build sentiment-analysis wrapper with quantum-flavored naming. The scoring math must actually run through the existing tensor/circuit infrastructure — reuse `FieldGeometryTensor`, reuse the Meyer-Wallach entanglement scorer, reuse the VQE estimator pattern."

Implementation:
- `src/spacetime_engine/entanglement.py: meyer_wallach()` — reusable Q measurement
- `src/spacetime_engine/vqe_runner.py: score_claim_state()` — AerEstimatorV2 wrapper, claim state circuits via RY encoding
- `src/quantum_credibility/vectorizer.py: claims_to_vector()` — 16-dim interpretable vector (diversity, eng_mag, platforms, polymarket, contradiction, recency)
- `src/quantum_credibility/wavefunction.py: ClaimWavefunction.score_claim()` — full pipeline with audit inputs + named constant weight

See [[credibility-scoring]] and [[living-almanac]]. If honestly can't route through quantum computation, label classical approximation in PR (spec instruction).

## Budget & Network Tier

**Decision:** Hard monthly ceiling + HOLD + atomic Lua + two-stage REVIEW→HOLD approval shape

**Rationale:** `last30days` hits paid APIs (ScrapeCreators, Perplexity). Must have budget guard before any scheduled/autonomous run.

- Redis hash `budget:YYYY-MM` {spent, pulls, last_pull, last_description}
- Lua `BUDGET_LUA_CHECK`: if spent+cost > ceiling → refuse, else incr spent+pulls atomically
- HOLD when remaining < threshold*cost (default 2x) — requires `POST /budget/approve`
- `LAST30DAYS_ENABLED=false` default — same gate as `QUANTUM_HARDWARE_ENABLED`
- `source_tier: local | network_opt_in` explicit labeling in QueryResponse and API docs per non-negotiable #2
- See `src/budget.py` and [[api-design]].

## API

**Decision:** FastAPI + OpenAPI — now 40+ endpoints

**Rationale:** FastAPI modern, type-safe, auto-generates docs. All schemas Pydantic v2. See [[api-design]] for full 40+ endpoint table including Living Almanac: `/pulse`, `/divergence`, `/timeline`, `/entanglement`, `/tribunal`, `/budget/status|approve`, `/almanac/generate|history`.

## Security

**Decision:** Defense in depth for network tier

- `pulse_agent.py` `shell=False` always — no command injection
- `_sanitize_entity_name` rejects null bytes, newlines, caps 200 chars
- `LOG_IGNORE_PATTERNS` prevents pytest from polluting `log.md`
- `CORS_ORIGINS` configurable
- `verify_api_key` on mutating endpoints; read-only divergence/timeline/entanglement public
- Budget refusal logged, not silently throttled — `PulseResult(status=budget_exceeded)` with reason
- Disabled returns no-op `PulseResult(status=disabled)` not error

## UI

**Decision:** SwiftUI + Living Almanac settings plan

- Light mode default, #FF9500 accent, warm design
- SwiftData for offline cache
- Settings: quantum backend picker + LLM config + chat-to-wiki + new Living Almanac section (budget display with HOLD approve, pulse triggers per entity, pulse history with platform icons, almanac dry-run sheet with WKWebView, almanac history list, timeline slider chart)
- Timeline: Swift Charts 3D for epistemic/social/divergence over time + scrubber
- Entity detail: divergence badge + driving claims + claim confidence rows with distinct epi/trac gauges, no blended number

See [[frontend-settings-menu]] (wiki/plan/frontend-settings-menu.md), [[swift-frontend-architecture]], [[ui-ux-design]], [[apple-reference-guides]].

## See Also

- [[agent-architecture]] — includes tribunal cost control
- [[technology-stack]] — updated with 48 py files, 19 test files
- [[local-first-llm]]
- [[api-design]] — 40+ endpoints
- [[mcp-server]]
- [[knowledge-graph-schema]]
- [[production-readiness]] — checklist + phases
- [[ui-ux-design]]
- [[living-almanac]] — 7-phase implementation (all phases done, 75 tests green)
- [[frontend-settings-menu]] — final DOD plan
