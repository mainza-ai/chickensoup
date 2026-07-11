---
title: "Production Readiness"
tags: [production, readiness, living-almanac]
created: 2026-06-22
updated: 2026-07-12
sources: [living-almanac, api-design, credibility-scoring, frontend-settings-menu]
related: [local-first-llm, ai-alien-connection, living-almanac, api-design, credibility-scoring, frontend-settings-menu, agent-architecture, key-decisions]
---

# Production Readiness

## Checklist (Current — Post Living Almanac)

- [x] **Configurable** — All parameters externalized: `LAST30DAYS_ENABLED`, `MONTHLY_BUDGET_USD`, `COST_PER_PULL_USD`, `CADENCE_TIER1/2`, `PULSE_TIMEOUT`, `MAX_CLAIMS`, `SOCIAL_TRACTION_WEIGHT=0.15`, `SOCIAL_TRACTION_HALF_LIFE=7`, `DIVERGENCE_SPIKE_THRESHOLD=0.7`, `ALMANAC_INTERVAL=24`, plus all existing quantum/LLM/wiki/chat settings
- [x] **Observable** — Logs, metrics, traces: OpenTelemetry + 11 custom metrics (`agent_loop`, `quantum_sim_duration`, `cache_hits/misses`, `pulse_runs_total{status,entity}`, `pulse_latency_seconds`, `budget_spent_usd`, `wavefunction_state_total{state,collapsed}`, `divergence_risk`, `tribunal_runs_total{trigger}`, `almanac_generated_total{status}`, `almanac_generation_duration`), structured logging with claim scoring inputs, `wiki/log.md` append-only with `LOG_IGNORE_PATTERNS` to prevent pytest pollution
- [x] **Resilient** — Error handling, retries, fallbacks: pulse subprocess timeout+cath with degrade to no_data, wavefunction quantum → classical fallback (AerEstimatorV2 → Aer→ numpy), budget Lua fallback to non-atomic, divergence QML→classical cosine fallback, timeline git log failure→empty list (no crash), almanac idempotency no-material-change
- [x] **Scalable** — Budget Lua atomic safe across workers, `WIKI_DATA_DIR` centralized to `paths.py`, `clear_content_pages` tag-based preservation, pagination on `/wiki/pages`
- [x] **Testable** — 75 tests passing (was 9): 13 agent, 7 wavefunction calibration, 4 divergence (including grep-able shared call check), 4 entanglement (single vs multi-platform), 4 tribunal (uncontested 0 calls, contested 3 positions + citations), 3 timeline (3-point ordered chartable), 3 almanac (dry-run no files/budget, live correct paths + log + HTML validity, no-change logs instead), 5 pulse (disabled no-op, one file, budget refusal logged, shell=False safety, adapter json+markdown), 4 budget (disabled fallback, exceeded, atomic Lua, HOLD)
- [x] **Documented** — API docs (40+ endpoints in `api-design.md`), architecture docs (`agent-architecture.md` with tribunal, `credibility-scoring.md` with VQE calibration, `living-almanac.md` 445 lines + gap analysis, `frontend-settings-menu.md` SwiftUI plan to DOD, README with DOD commands, `living-almanac.md` index), usage examples for pulse/budget/divergence/timeline/tribunal/almanac
- [x] **Versioned** — Code, data, algorithms: `WAVEFUNCTION_SCORING_VERSION=v1-wavefunction` on `ClaimConfidence`, almanac hash in MD comment `<!-- hash: ... -->`, pulse snapshots carry provenance_chain
- [x] **Secure** — Auth (`X-API-Key` on mutating routes, dev mode bypass with 4-char log), input validation (`_sanitize_entity_name` rejects null/newline, 200 cap, Pydantic ge/le), `shell=False` always, budget ceiling enforcement, HOLD approval, CORS configurable, `LOG_IGNORE_PATTERNS`, `shell` injection test (`test_pulse_never_shell_true`)
- [x] **Deployable** — Containerized (Docker), CI/CD (GitHub Actions), 40+ endpoints, Celery fixed (`metric_tensor`→`spatial_metric` bug), both schedulers in lifespan (chat 5min + almanac 24h), uv package manager, `.venv`
- [x] **Monitored** — Alerts via budget HOLD, dashboards via `/status` now includes `last30days_enabled` + `budget_remaining`, health checks for Neo4j+Redis+LLM+quantum+last30days+badge counts, 11 metrics with attributes

## Phases (Original + Living Almanac)

### Phase 1: Foundation (Weeks 1-4) — Done

1. Knowledge graph schema — `knowledge_graph/schema.py` constraints + indexes
2. Project structure — 48 py files, 87 entities, 155 concepts, 7 projects, wiki/plan dir
3. Configuration system — `config.py` + 30+ fields including Living Almanac flags
4. Core models — `models.py` 310 lines, now ClaimEvidence/Confidence/Divergence/Pulse/Timeline/Budget
5. Knowledge graph implementation — Neo4j + wiki file fallback + retry/backoff
6. Agent framework — pydantic-graph + LangGraph (research 6 nodes, tribunal 4 nodes)
7. FastAPI — 40+ endpoints, WebSocket `/ws/agent`, debug routing, lifespan dual schedulers
8. Logging — otel + structured + log.md append-only + ignore patterns
9. Docker Compose — Neo4j + Redis + volumes

### Phase 2: Core Functionality (Weeks 5-8) — Done

10. Quantum circuits — Qiskit AerEstimatorV2 pattern + classical numpy cos/sin fallback
11. LLM integration — auto-discovery oMLX→Ollama→LM Studio, circuit breaker shape, probe endpoint
12. Graph ingestion from wiki — deterministic YAML frontmatter+`[[wikiname]]` + LLM edge classification
13. Query pipeline — TQL→LLM→heuristic 3-tier, wiki entity lookup, confidence gating <0.6→ResearchNode
14. Pydantic Graph — orchestrator with ClassifyNode+ResearchNode+NavigateNode+StatusNode, synthesize_answer post-processing
15. LangGraph — research graph + tribunal graph with checkpointing, human-in-the-loop
16. Evaluation framework — metrics tables, 15 test cases, calibration checks
17. Error handling — timeout isolation (15s classification, 30s summary, 60s orchestrator top-level), graceful degrade throughout
18. MCP server — 6 tools (`simulate_spacetime, analyze_field, find_paths, query_graph, get_evidence, explore_concept`)
19. **NEW Phase 2b: Quantum Credibility** — `quantum_credibility/` module: wavefunction 3-basis with VQE, `SOCIAL_TRACTION_WEIGHT=0.15` named constant, Meyer-Wallach reusable extractor, divergence engine reusing `FieldGeometryTensor` + `find_optimal_path`, entanglement correlation, timeline from pulse+git

### Phase 3: Enhancement (Weeks 9-12) — Done

20. Caching layer — Redis `RedisCache` + `cache_decorator` MD5 keys + sync/async dual API + `invalidate_by_pattern`
21. Async processing — Celery `async_ingest_page`, `async_navigate` with sync fallback, Qiskit job simulation
22. Batch processing — zip upload, folder ingest, PDF folder with pypdf
23. Observability — 11 metrics + tracing middleware + ConsoleMetricExporter
24. Multi-agent orchestration — orchestrator→query/research/navigator/pulse/tribunal, scheduler dual loops, research threads detection, adaptive confidence, conversation snapshots
25. API documentation — `api-design.md` 40+ endpoints with models table, middleware, lifecycle, source tier labeling
26. Docker — docker-compose with Neo4j + Redis, exports, imports, backup/restore
27. **NEW Phase 3b: Almanac Generator** — `almanac/` module: timeline reconstruction (pulse JSON + git log, no TSDB), `generate_daily_almanac()` dry-run + live + idempotency hash, self-contained HTML (inline CSS, no JS, dark mode media query, print-friendly), budget integration

### Phase 4: Advanced (Weeks 13-16) — Partial

28. Multi-LLM support — `multi_llm.py` Jaccard consensus via executor offload, `POST /consensus/query`
29. Real quantum hardware integration — `quantum_scheduler.py` IBM/D-Wave/IonQ submission + status polling, hardware toggle
30. Performance optimization — `paths.py` centralization, `LOG_IGNORE_PATTERNS`, vectorizer N_DIM=16 small for circuit encoding
31. Dashboard — Dashboard concept: timeline chart (Swift Charts 3D), divergence risk, entanglement map, budget burndown
32. User-facing UI — SwiftUI client with graph explorer, timeline, query overlay, AI navigator, settings, now planned Living Almanac settings per `frontend-settings-menu.md`
33. Enhanced knowledge graph — 250+ wiki pages, 61 PDFs all covered, Apple platform guides 20 docs indexed
34. Rate limiting & security — API key header auth, budget guardrails + HOLD, `shell=False`, sanitization, CORS configurable
35. Release process — develop→main merges, CHANGELOG, version tags

### Phase 5: Living Almanac Autonomous DOD (Week 17) — Backend Done, Frontend Planned

36. **Final DOD**: Set `LAST30DAYS_ENABLED=true`, budget $20, `POST /pulse/bob-lazar` real CLI → evidence file appears, wavefunction score with auditable trail, divergence score, epi != trac, `POST /almanac/generate?dry_run=true` valid HTML no files/budget, `POST /almanac/generate?dry_run=false` → `wiki/raw/almanac/{date}.html` with real sourced content, scheduler overnight → dated brief appears unattended — **that last part is the whole point**
37. **Frontend DOD**: SwiftUI Settings section for budget display with HOLD approve, pulse triggers per Tier-1 entity, pulse history with platform icons, almanac dry-run sheet with WKWebView, almanac history list, timeline slider chart per entity — see `wiki/plan/frontend-settings-menu.md`
38. **Manual Live Verification**: `npm install -g last30days`, set env, curl commands in README section "Living Almanac — To Reach Final DOD", verify HTML self-contained inline CSS no JS dark mode print-friendly

## Risks (Updated Post Living Almanac)

| Risk | Mitigation | Status |
|------|-----------|--------|
| Quantum hype vs reality | Classical fallbacks at every layer; AerEstimatorV2 → Aer → numpy; divergence QML→cosine; tribunal simulated when no LLM; measure `entanglement_score` and log backend per claim | Done |
| Over-reliance on LLM | System works without LLM (simulated provider, heuristic fallback, wiki file fallback); tribunal skipped when uncontested; budget gate prevents API cost overrun | Done |
| Knowledge graph bloat | 250+ pages, tag-based preservation, `clear_content_pages` with ENGINEERING_TAGS vs CONTENT_TAGS, reconciliation `reconcile_neo4j_with_wiki` prunes orphans | Done |
| Neo4j scalability | `WIKI_DATA_DIR` centralization, `cache_decorator` TTL 300, `LOG_IGNORE_PATTERNS` prevents test pollution, pagination planned for /wiki/pages | Done |
| Complexity creep | 7-phase backend done additively (all 59 original tests still green + 16 new), 11 test files with calibration fixtures, explicit phase order P0→P1→P2→P4→P3→P5→P6 | Done |
| Data quality in wiki | Confidence scores from wavefunction (falsifiable scoring_inputs), source tracking via provenance_chain, ClaimEvidence with cluster_id, driving_claims explain divergence | Done |
| oMLX model discovery | Fallback chain oMLX→Ollama→LM Studio, probe endpoint, `LOG_IGNORE_PATTERNS`, `get_discovered(depth=fresh)` per call | Done |
| last30days cost overrun | Hard ceiling $20 default, Lua atomic check, HOLD at 2× cost remaining, `POST /budget/approve` to clear, dry-run default true for almanac, every score logged with inputs | Done |
| Command injection via entity name | `shell=False` always, `_sanitize_entity_name` rejects null/newline, 200 cap, tested `test_pulse_never_shell_true` with `; rm -rf /` | Done |
| Log pollution from tests | `LOG_IGNORE_PATTERNS` with `/tmp/`, `/private/var/folders/`, `pytest-of-`, `test_pdf_folder_` — tested | Done |
| Frontend pending | Backend fully shipped (40+ endpoints, 75 tests green), frontend plan detailed in `wiki/plan/frontend-settings-menu.md` — implement next with Apple guides (Charts 3D, Liquid Glass, WebKit) | Planned |

## See Also

- [[living-almanac]] — 7-phase plan, all phases done
- [[frontend-settings-menu]] — SwiftUI plan to DOD
- [[credibility-scoring]] — wavefunction calibration
- [[api-design]] — 40+ endpoints
- [[key-decisions]] — 30+ decisions
- [[agent-architecture]]
- [[project-structure]]
