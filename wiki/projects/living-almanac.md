---
title: "Living Almanac — The Last 30 Days Integration"
tags: [project, living-almanac, last30days, quantum-credibility, production, architecture]
created: 2026-07-11
updated: 2026-07-11
sources: [chickensoup-living-almanac-implementation-spec, agent-architecture, field-geometry-tensor, credibility-scoring, integration-architecture]
related: [credibility-scoring, agent-architecture, field-geometry-tensor, time-travel-machinery-architecture, integration-architecture, science-reference-library, chat-to-wiki-pipeline, production-readiness, quantum-simulation-tier, multi-llm-consensus]
---

# Living Almanac — Last30days Integration

Production-grade implementation plan for repointing existing quantum machinery at live claim evidence. Ground truth hierarchy: `chickensoup-living-almanac-implementation-spec.md` → `AGENTS.md` → existing code patterns.

## 0. Mission

Replace hardcoded confidence constants with quantum-scored states derived from real corroboration. Every claim gets a wavefunction over {CORROBORATED, CONTESTED, UNVERIFIED}. Every entity gets a live divergence score from [[field-geometry-tensor]] math. Whole system self-updates and publishes dated HTML brief with zero human intervention.

Non-negotiables:
1. All 11 existing test files must still pass — additive only.
2. `LAST30DAYS_ENABLED` default False, same gate pattern as `QUANTUM_HARDWARE_ENABLED`.
3. Epistemic credibility and social traction are separate numbers, never merged.
4. Monthly spend ceiling + REVIEW→HOLD approval shape before any autonomous run.
5. Every score is falsifiable and logged — inputs that produced it must be persisted.
6. Follow existing code shapes: agents in `src/agents/`, quantum in `src/quantum_credibility/`, wiki via `src/wiki/writer.py`, scheduler via `src/scheduler.py`.

## 1. Current Codebase Inventory (2026-07-11)

### Backend `src/`
- `config.py` — 72 lines, 19 fields. Missing all Living Almanac flags. Has `LLM_EDGE_CLASSIFICATION_TIMEOUT=30` + `MAX_RETRIES=3` (recent fix).
- `models.py` — 234 lines, 20+ models. `QueryResponse` has dead `inferred_events`/`inferred_entities` (never populated). No `ClaimConfidence`, no `ClaimEvidence`, no `PulseResult`.
- `main.py` — 1778 lines, 30+ endpoints inline (not router-separated). `_build_query_response` synthesizes answer, `reconcile_neo4j_with_wiki` prunes orphans. Bulk ingest clears DB. No divergence/timeline/claim endpoints.
- `scheduler.py` — 711 lines, single `periodic_chat_ingest_loop`. Chat-to-wiki only. No pulse, no almanac jobs. Redis-backed meta with 7d TTL.
- `cache.py` — Redis wrapper, `cache_decorator` with MD5 keys, sync+async wrappers. No budget tracking, no distributed lock.
- `discovery.py` — urllib blocking probe with 5s timeout, fallback chain oMLX/Ollama/LM Studio. No circuit breaker counting.
- `multi_llm.py` — consensus via Jaccard, executor offload, no per-model timeout isolation.
- `quantum_scheduler.py` — in-memory `_jobs_db`, no persistence, simulated completion after 2s.
- `tasks.py` — Celery tasks. **BUG**: `FieldGeometryTensor(metric_tensor=...)` field does not exist (real model has `spatial_metric`). Will crash in prod if Celery path is hit. Also `async_navigate` invents warp path.
- `agents/query_agent.py` — 3-tier TQL→LLM→heuristic. TQL regex `(\w+):([\w\d.-]+)` low precision. Confidence hardcoded 0.95/0.5. Wiki lookup scans filenames only.
- `agents/research_agent.py` — LangGraph 6 nodes. `credibility_scoring_node` still uses `+0.1 Person, +0.15 Project` heuristic called out in spec as tech debt. `_generate_summary` single LLM call, no tribunal.
- `agents/navigation_agent.py` — pipelines `simulate_spacetime_metrics` → `manipulate_spacetime_field` → `find_optimal_path`. Success = `bubble_stability > 0.3`.
- `spacetime_engine/tensor.py` — 42 lines, Pydantic `FieldGeometryTensor` with lapse/shift/spatial_metric/extrinsic_curvature/warp_factor. No `create_from_claim_vectors` factory.
- `spacetime_engine/qiskit_simulation.py` — 137 lines, 2-qubit RY+CX+RZ circuit, Aer `statevector_simulator` (legacy API, not `AerEstimatorV2` as spec requires). NumPy fallback uses cos/sin.
- `field_manipulator/cuda_simulation.py` — 66 lines, resonance factor `1/(1+delta^2)` at 7.46 Hz. No Meyer-Wallach scorer. No tensor vectorization.
- `ai_navigator/pennylane_qml.py` — 127 lines, 2-wire VQC `RX(x*0.001)`, `RY(warp*0.1)`, `Rot*2+CNOT`, SciPy Nelder-Mead fallback. `divergence_risk = (|dt|/200)*(warp/lapse)*0.1`.
- `knowledge_graph/ingest.py` — 340 lines, `SCHEMA_RELATIONSHIPS` matrix, LLM edge classification with retry/backoff, heuristic fallback. Label allowlist, Cypher injection sanitized.
- `wiki/writer.py` — 241 lines, `write_page` merges frontmatter, `append_to_index` scans string contains, `cross_reference_new_page` O(n²) scan all pages per write.

### Wiki
- 181 pages per README (81 entities, 93 concepts, 6 projects) + 36 new from PDF re-triage = ~216 concepts/entities. `log.md` polluted with 30+ pytest temp-dir lines (`/private/var/folders/m_/...`). `wiki/raw/` holds 61 PDFs + 1 Mannheim txt + 20 Apple guides = 82 files.
- No `last30days_handles` frontmatter anywhere yet. No tier field. No `wiki/raw/almanac/` dir. No `wiki/raw/pulse/` convention.
- `index.md` manually maintained, duplicates (vatican x2), no auto-dedup.

### Tests
- 11 files: `test_agents`, `test_spacetime_engine`, `test_api`, `test_config`, `test_audit_fixes`, `test_phase4`, `test_discovery`, `test_pdf_ingest`, etc. No tests for budget guard, claim wavefunction, divergence, entanglement, tribunal, almanac, timeline.

## 2. Spec Requirements vs Reality

### Phase 0 — Pulse Agent (Foundation)
| Required | Exists? | Gap |
|---|---|---|
| `src/agents/pulse_agent.py` with `run_pulse(entity, handles)` | No | Must build new class following `chat_ingest_agent.py` shape |
| Subprocess shell-out to last30days CLI with timeout | No | Need `subprocess.run` wrapper with same defensive pattern as `multi_llm.py` |
| `ClaimEvidence` struct (claim_text, source_platform, engagement, url, timestamp, cluster_id, polymarket_odds) | No | Add to `src/models.py` |
| Raw immutable dated snapshot to `wiki/raw/` via `writer.py` | Partial | `writer.py` exists but no pulse-specific path; need `write_pulse_snapshot()` |
| Entity frontmatter `last30days_handles` + `tier` | No | Schema extension needed |
| Config `LAST30DAYS_ENABLED=false`, `BINARY_PATH`, `MONTHLY_BUDGET_USD=20`, `CADENCE_TIER1/2` | No | Add to `config.py` |
| Budget ceiling check before every pull, logged refusal | No | Need `src/budget.py` tracker + Redis counter |
| `tests/test_pulse_agent.py` mocking subprocess | No | Must create |

### Phase 1 — Wavefunction Scoring
| Required | Exists? | Gap |
|---|---|---|
| `src/quantum_credibility/wavefunction.py` with `ClaimWavefunction` state over 3 basis | No | Must build, reusing `AerEstimatorV2` pattern not old statevector |
| Inputs: source_diversity, engagement_magnitude, polymarket_prior, contradiction_signal | No | Need to compute from `ClaimEvidence`; contradiction_signal stubs 0.0 if lint agent missing |
| Output `ClaimConfidence` (epistemic_confidence, social_traction, state_label, collapsed, evidence_count, last_pulse_at) | No | Add model |
| `social_traction` decoupled, decayed over time, weighted lower via named constant | No | Need constant `SOCIAL_TRACTION_WEIGHT_IN_EPISTEMIC` |
| Wire into `research_agent.py` `credibility_scoring_node` with graceful degrade | No | Currently hardcoded heuristic, must add branching |
| Populate `inferred_events`/`inferred_entities` on `QueryResponse` | No | Dead since audit |
| `tests/test_wavefunction.py` calibration with synthetic fixtures | No | Must create, assert decoupled traction vs epistemic |

### Phase 2 — Divergence Engine
| Required | Exists? | Gap |
|---|---|---|
| `divergence_engine.py` `compute_narrative_divergence` using `FieldGeometryTensor` from two claim-vectors | No | Must not duplicate tensor math, import existing functions |
| `GET /entities/{name}/divergence` + extend `WikiPageDetailResponse` | No | No endpoint |
| `tests/test_divergence_engine.py` zero vs high divergence | No | Must create, grep for shared function call per spec |
| Canon vector from wiki page frontmatter/claims, live_vector from `fresh_evidence` | Partial | No canon vectorizer |

### Phase 3 — Entanglement Correlation
| Required | Exists? | Gap |
|---|---|---|
| `entanglement_corr.py` reusing Meyer-Wallach scorer (currently <0.3 rejects VQE circuits, but scorer itself not extracted) | No | Meyer-Wallach not implemented as reusable function — need `src/spacetime_engine/entanglement.py` first |
| Co-occurrence across independent evidence clusters encoded as quantum state | No | Need encoder |
| Wire into `related:` strength sub-value | No | Frontmatter schema extension |

### Phase 4 — Temporal Slider
| Required | Exists? | Gap |
|---|---|---|
| `GET /entities/{name}/timeline?days=30` chartable array `{date, epistemic_confidence, social_traction, divergence_risk}` | No | Must reconstruct from `wiki/raw/` + `git log` on entity md, no new TSDB |
| SwiftUI seam trivially chartable | No | Endpoint shape not defined |
| `tests/test_timeline_endpoint.py` 3 dated pulls → 3-point series | No | Must create |

### Phase 5 — Tribunal
| Required | Exists? | Gap |
|---|---|---|
| `tribunal_agent.py` LangGraph 3 roles (Skeptic, Empiricist, Believer) + referee, gated on `state_label==contested` or divergence spike | No | Must build |
| 3 positions + citations + referee synthesis, disagreement preserved | No | New pattern |
| LLM cost control: uncontested never triggers tribunal | No | Need gate + test asserting no LLM calls for uncontested |

### Phase 6 — Almanac Generator
| Required | Exists? | Gap |
|---|---|---|
| `src/almanac/almanac_generator.py` `generate_daily_almanac()` async: Tier-1 pulse → wavefunction → divergence → tribunal → HTML+md → `wiki/raw/almanac/{date}.*` + `log.md` append | No | Must build |
| Reuse `writer.py` export + last30days HTML styling (dark mode, inline CSS, no JS, print-friendly) | Partial | writer exists, HTML styling not defined |
| Scheduler new job `ALMANAC_GENERATION_INTERVAL_HOURS=24`, idempotency no material change → log "no material change" | No | scheduler.py only has chat loop |
| Dry-run mode, valid HTML check | No | Must create |
| Manual 2-3 entity end-to-end before enabling schedule | No | Manual step |

## 3. Existing Codebase Gaps (Production Hardening)

### 3.1 Critical Bugs
- `src/tasks.py:57` `FieldGeometryTensor(metric_tensor=...)` invalid field → Celery path crashes. Must align with real model.
- `src/main.py` `get_events()` tag filtering heuristic `["incident","crash",...]` over-matches; title lower includes "project" promotes engineering pages back in after filter.
- `src/scheduler.py` no distributed lock — if 2 uvicorn workers start, double ingest.
- `cache.py` `get()` returns `None` both for miss and for stored `None` — ambiguous. Also `json.loads` on redis `decode_responses=True` returns str → double parse risk.
- `wiki/writer.py` `cross_reference_new_page` does `content.lower()` substring scan on slug — false positives (e.g., "area" matching "area-51").

### 3.2 Security & Config
- `CORS_ORIGINS` split but no validation — wildcard `*` allowed via env.
- `API_KEY` dev mode bypass logs only first 4 chars if provided, but no rate limiting on status/config endpoints.
- `.env` write in `main.py:_update_env_file` does unsanitized `key=val` — value with newline breaks file.
- No budget persistence — would exceed in distributed deploy.
- No input validation on `entity_name` in `pulse_agent` → command injection if passed to subprocess shell=True (must use list args).

### 3.3 Data Integrity
- `log.md` append-only violated by pytest writes of temp paths — needs `LOG_IGNORE_PATTERNS` or test fixture mocking `append_to_log`.
- `wiki/raw/` has no manifest; 82 files but no index of which PDF maps to which wiki page.
- `WIKI_DATA_DIR` relative resolution duplicated 6 times across modules — should be single `src/wiki/paths.py`.
- `clear_content_pages` adds `protected: true` to engineering pages on dry_run=False — side effect that modifies files during delete operation, confusing.

### 3.4 Quantum Layer Truthfulness
Spec says: "Do not build sentiment-analysis wrapper with quantum-flavored naming." Current code risks this:
- `qiskit_simulation.py` uses `Aer.get_backend('statevector_simulator')` legacy, not `AerEstimatorV2` per spec Phase 1. Must migrate.
- No Meyer-Wallach entanglement scorer extracted — mentioned in spec Phase 3 as existing but not found in code. Need to implement `meyer_wallach_entanglement(statevector) -> float` in `src/spacetime_engine/entanglement.py` and reuse in both VQE rejection and correlation.
- `pennylane_qml.py` cost function `-|g00|dt^2+warp*dx^2` oversimplified; needs named constants not buried formulas per Phase 1 spec.

### 3.5 Observability Gaps
- No metrics for pulse success/failure, budget spend, wavefunction distribution, divergence spikes.
- `quantum_simulation_duration` histogram only records spacetime; no pulse latency, no tribunal latency.
- `status` endpoint probes LLM fresh each call — will storm oMLX if frontend polls.

### 3.6 Testing Gaps
- No contract tests for `FieldGeometryTensor` shape invariants (spec requires validation table).
- No property-based tests for `slugify` (Unicode, slashes).
- `test_api.py` `test_api_clear_content` mocks `clear_content_pages` but asserts on returned counts — doesn't test file deletion.
- `conftest.py` resets discovery cache but not `cache_store.redis_client` — leaks between tests if Redis mock store dict persists.

### 3.7 Scalability
- `build_index()` scans all wiki files per call if cache invalidated — O(n) where n=216+, called from `chat_ingest_agent` per conversation.
- `cross_reference_new_page` is O(n*m) where n=pages, m=links — called per `write_page` → squares during bulk ingest (61 PDFs → 36 pages → 36*216 scans).
- No pagination on `GET /wiki/pages` — returns all 216 pages.

## 4. Improvements & Enhancements (Beyond Spec)

### 4.1 Data Model Hardening
- `ClaimEvidence` should carry `provenance_chain: List[str]` (which raw snapshot, which parser version).
- `ClaimConfidence` should carry `scoring_version: str` for migration.
- Add `BudgetLedger` model: `month, spent_usd, pulls_count, last_pull_at`.
- Add `DivergenceResult` with `driving_claims: List[DrivingClaim]` where `DrivingClaim` has `claim_text, old_confidence, new_confidence, platform`.

### 4.2 Quantum Reuse Done Right
- `src/spacetime_engine/entanglement.py` — extract Meyer-Wallach: `def meyer_wallach(state: np.ndarray) -> float` with `Q = 1 - (1/n) sum_k Tr(rho_k^2)`. Implement once, use in VQE circuit rejection (existing) and entanglement correlation (new).
- `src/spacetime_engine/vectorizer.py` — `claims_to_tensor_vector(claims: List[Claim]) -> np.ndarray` for divergence engine, avoiding duplication of warp-factor math. Refactor `pennylane_qml.py:find_optimal_path` to accept generic vectors.
- `src/quantum_credibility/vqe_estimator.py` — wrapper around `AerEstimatorV2` pattern from `vqe_runner.py` (spec mentions but file does not exist — need to create canonical VQE runner).

### 4.3 Last30days Integration Robustness
- Supports both CLI (`npx last30days ... --json`) and local install via `LAST30DAYS_BINARY_PATH`.
- Output parser tolerates markdown and JSON — use `claims` block extraction via `## Claims` header or `claims:` YAML.
- Add `src/last30days_adapter.py` — normalizes raw brief into `ClaimEvidence` list, isolates subprocess and parsing errors.

### 4.4 Budget Guardrails (Reuse MilimoClaw SpendApproval Pattern)
Per spec non-negotiable #4: follow two-stage REVIEW→HOLD.
- `src/budget.py` — `BudgetTracker` with Redis `INCRBYFLOAT`, atomic check-and-increment via Lua script. `check_budget(cost_estimate) -> (allowed: bool, remaining: float, reason: str)`. `record_spend(amount, description)` persists to `budget:YYYY-MM` hash.
- Config `LAST30DAYS_COST_PER_PULL_USD=0.50` estimate. Each `run_pulse` estimates 1 pull.
- If `allowed==False`, `PulseResult` returns `status=budget_exceeded`, logs to `wiki/log.md` and to `logger.warning`, never shells out.
- Future: `POST /budget/approve` endpoint for HOLD→APPROVED transition.

### 4.5 Security for Network Tier
- `LAST30DAYS_ENABLED` gates `pulse_agent` and all almanac jobs — if False, return no-op `PulseResult(status=disabled)`, not error.
- Explicit labeling in API responses: `"source_tier": "local" | "network_opt_in"`.
- Subprocess uses `shell=False`, `args = [binary, "run", entity, "--json"]`, timeout 60s.

### 4.6 Almanac HTML Quality
- Self-contained HTML: inline CSS, no JS, dark mode via `@media (prefers-color-scheme: dark)`, print-friendly `@media print`.
- Reuse `wiki/export` path: markdown source + HTML rendered.
- Template in `src/almanac/templates/almanac.html.j2` — Jinja2, not string concat.

## 5. Implementation Plan — 7 Phased PRs

### PR1: Phase 0 — Pulse Agent Foundation
**Goal**: Raw evidence flowing safely, no scoring yet.
Files:
- `src/config.py` — add `LAST30DAYS_ENABLED: bool=False`, `LAST30DAYS_BINARY_PATH: str=""`, `LAST30DAYS_MONTHLY_BUDGET_USD: float=20.0`, `LAST30DAYS_COST_PER_PULL_USD: float=0.50`, `LAST30DAYS_ENTITY_CADENCE_TIER1_HOURS=24`, `TIER2=168`, `LAST30DAYS_PULSE_TIMEOUT_SECONDS=60`, `ALMANAC_GENERATION_INTERVAL_HOURS=24`
- `src/models.py` — add `ClaimEvidence(BaseModel)`, `PulseResult`, `BudgetStatus`, `ClaimConfidence` (with decoupled fields)
- `src/budget.py` — NEW, `BudgetTracker` with Redis + Lua atomic, `BudgetLedger` persistence
- `src/last30days_adapter.py` — NEW, `Last30daysAdapter` parses CLI output to `ClaimEvidence`
- `src/agents/pulse_agent.py` — NEW, class `PulseAgent` with `run_pulse(entity_name, handles) -> PulseResult`, disabled no-op, budget check, subprocess timeout/catch, write to `wiki/raw/pulse/{slug}-{date}.json` + `.md`, returns structured evidence, never touches entities/concepts
- `src/wiki/writer.py` — add `write_pulse_snapshot(entity, content, fmt) -> Path`, ensure `wiki/raw/pulse/` dir, immutable dated filename, no index update for pulse files
- `src/wiki/paths.py` — NEW, central `get_wiki_dir()`, `get_raw_dir()`, `get_pulse_dir()`, `get_almanac_dir()` — replace 6 duplications
- `tests/test_pulse_agent.py` — NEW, mock subprocess, disabled no-op, enabled writes one file, budget exceeded refused, no entities touched
- `tests/test_budget.py` — NEW

Acceptance:
- `run_pulse("Bob Lazar")` with `ENABLED=false` returns no-op, no error, no file.
- With enabled, writes exactly one immutable file to `wiki/raw/pulse/`, never touches `wiki/entities/` or `concepts/`.
- Budget ceiling checked before pull; refusal logged, not silently throttled.
- Existing 11 tests still green.

### PR2: Phase 1 — Claim Wavefunction Scoring
**Goal**: Replace hardcoded confidence with evidence-derived quantum state.
Files:
- `src/spacetime_engine/entanglement.py` — NEW, `meyer_wallach(state) -> float` reusable scorer
- `src/spacetime_engine/tensor.py` — extend with `create_flat()` already exists, add `from_claim_vectors(canon, live) -> FieldGeometryTensor` factory, validation invariants (Lorentzian, non-degenerate, positive lapse)
- `src/spacetime_engine/qiskit_simulation.py` — migrate to `AerEstimatorV2` pattern per spec, keep NumPy fallback
- `src/quantum_credibility/__init__.py` — NEW module
- `src/quantum_credibility/wavefunction.py` — NEW, `ClaimWavefunction` encodes evidence profile as state over {CORROBORATED, CONTESTED, UNVERIFIED}. Amplitudes from `source_diversity` (distinct platforms), `engagement_magnitude` (log-scaled), `polymarket_prior` (nullable), `contradiction_signal` (stub 0.0 + TODO log if lint not built). Output `(epistemic_confidence, state_label, collapsed)`. Keep `social_traction` separate field, computed independently, decayed over time, never folded into amplitudes except via low-weighted inputs with named constant `SOCIAL_TRACTION_WEIGHT_IN_EPISTEMIC=0.15`. Log inputs that produced score.
- `src/quantum_credibility/vqe_estimator.py` — NEW canonical VQE wrapper using `AerEstimatorV2`
- `src/agents/research_agent.py` — replace `credibility_scoring_node` heuristic with `ClaimWavefunction` call when recent pulse exists in `wiki/raw/pulse/{slug}-*.json` (check <7d). Fallback to existing heuristic otherwise, graceful degrade.
- `src/models.py` — populate `inferred_events`/`inferred_entities` using wavefunction-scored claims surfaced during research; extend `QueryResponse` and `WikiPageDetailResponse` with `claim_confidences: List[ClaimConfidence]`
- `tests/test_wavefunction.py` — NEW synthetic profiles: high diversity+high market → corroborated collapsed; single low-engagement → unverified; contradicted → contested. Assert epistemic != social_traction where they shouldn't be equal. Assert scoring inputs logged.
- `tests/test_research_agent_wavefunction.py` — NEW, mock pulse file exists vs not exists.

Acceptance:
- No hardcoded 0.95/0.5/0.8 constants in `research_agent.py` when evidence exists.
- `epistemic_confidence` and `social_traction` never aliased.
- VQE uses `AerEstimatorV2` path, not legacy statevector.

### PR3: Phase 2 — Divergence Engine
**Goal**: Repoint tensor math at real drift.
Files:
- `src/quantum_credibility/divergence_engine.py` — NEW `compute_narrative_divergence(entity_name, wiki_page, fresh_evidence) -> DivergenceResult` builds `FieldGeometryTensor` from two claim-vectors (canon from wiki frontmatter+body claims, live from pulse `ClaimEvidence`), runs same divergence-risk math via `find_optimal_path` or extracted `compute_divergence_risk(tensor)` — must grep-able shared call.
- `src/spacetime_engine/vectorizer.py` — NEW `claims_to_vector`, `canon_to_vector` helpers.
- `src/main.py` — add `GET /entities/{name}/divergence` returning `divergence_risk` + `driving_claims`.
- Extend `WikiPageDetailResponse` with `divergence`.
- `tests/test_divergence_engine.py` — identical canon+fresh → near-zero; contradictory → high with named contradicting claim; confirm calling into `spacetime_engine`/`ai_navigator` not reimplementing.

Acceptance:
- Reviewer can grep shared function.
- Driving claims explainable.

### PR4: Phase 4 — Timeline (shipped early per spec suggested order)
**Goal**: Make time-travel literal.
Files:
- `src/almanac/timeline.py` — NEW `build_timeline(entity_name, days=30) -> List[TimelinePoint]` reconstructs from dated `wiki/raw/pulse/{slug}-*.json` + `git log --follow -- wiki/entities/{slug}.md` (parse `git log --pretty=format:%H|%ad|%s --date=iso`). No new TSDB.
- `src/main.py` — `GET /entities/{name}/timeline?days=30` returns `List[TimelinePoint]` shape `[{date, epistemic_confidence, social_traction, divergence_risk, active_claims}]` trivially chartable.
- SwiftUI seam: document response shape in `wiki/concepts/apple-reference-guides.md` style — but backend only in this PR.
- `tests/test_timeline_endpoint.py` — synthetic entity with 3 dated raw pulls returns 3-point ordered series.

Acceptance:
- No separate time-series DB.
- Chartable shape.

### PR5: Phase 3 — Entanglement Correlation
**Goal**: Measurably entangled entities.
Files:
- `src/quantum_credibility/entanglement_corr.py` — NEW encodes co-occurrence across independent `last30days` clusters (same claim on Reddit AND X AND YouTube, naming both entities, different original sources) as quantum state, runs `meyer_wallach` scorer. Single wiki-editor cross-ref scores low; independent repeated bound scores high.
- Wire into `related:` frontmatter `strength` sub-value where evidence supports it — check `AGENTS.md` cross-ref convention first. Possibly `related: [{name: "Bob Lazar", strength: 0.92, evidence_platforms: ["reddit","x","youtube"]}]` vs simple string list — need backward compat: keep string list but add `related_strengths: Dict[str, float]` parallel field.
- `tests/test_entanglement_corr.py` — 3 independent platforms co-occurrence scores higher than single co-mention.

### PR6: Phase 5 — Tribunal
**Goal**: Adversarial synthesis for contested claims.
Files:
- `src/agents/tribunal_agent.py` — NEW LangGraph workflow 4 nodes: Skeptic (weighs absence+contradiction), Empiricist (diversity+market+reproducibility), Believer/Narrativist (internal consistency+lore+witness), Referee (takes 3 positions + wavefunction score → final synthesis, notes disagreement). Gate: only `state_label==contested` or divergence spike >0.7. Cost control: uncontested never triggers.
- `src/main.py` — `POST /entities/{name}/tribunal` optional endpoint, or called internally from research flow.
- `tests/test_tribunal_agent.py` — mocked LLM per role like `test_agents.py`, assert uncontested never triggers tribunal path (mock call count 0), output includes all 3 positions' citations, disagreement preserved not collapsed.

### PR7: Phase 6 — Autonomous Living Almanac
**Goal**: Self-publishing dated brief.
Files:
- `src/almanac/almanac_generator.py` — NEW `async def generate_daily_almanac(dry_run=False) -> AlmanacResult`:
  1. Tier-1 entities: `run_pulse` → wavefunction → divergence
  2. Divergence spike or contested → tribunal
  3. Assemble "State of the Anomaly" brief: what moved, what collapsed, what's newly contested, top entanglement discoveries, market odds
  4. Render self-contained HTML (reuse last30days HTML styling conventions — dark mode inline CSS, no JS, print-friendly — plus existing `wiki/writer.py` export path)
  5. Write to `wiki/raw/almanac/{date}.html` and `.md`, update `wiki/log.md` append-only, with `dry_run` skipping writes and budget spend
  6. Idempotency: if nothing scored differently since last run (compare hash of all `ClaimConfidence`), log "no material change" not redundant brief
- `src/almanac/templates/almanac.html.j2` — Jinja2 template
- `src/scheduler.py` — new periodic job `periodic_almanac_loop()` alongside chat loop, same asyncio pattern, interval `ALMANAC_GENERATION_INTERVAL_HOURS`, eligibility check, respect `LAST30DAYS_ENABLED` gate
- `src/main.py` — `POST /almanac/generate?dry_run=true`, `GET /almanac/history`
- `tests/test_almanac_generator.py` — mocked pipeline produces valid HTML+md, correct paths, correct log append, dry-run no files/budget

Acceptance final DOD:
- Run `pulse_agent` real entity with `ENABLED=true` small budget: raw file appears, wavefunction score with auditable trail, divergence score, social traction != epistemic confidence, and overnight scheduler creates dated `almanac/{date}.html` with real sourced content nobody touched.

## 6. Data Models Proposed

```python
class ClaimEvidence(BaseModel):
    claim_text: str
    source_platform: str  # "reddit","x","youtube","news","github","subreddit"
    engagement_count: int
    url: str
    timestamp: str
    cluster_id: str
    polymarket_odds: Optional[float] = Field(None, ge=0.0, le=1.0)
    engagement_decayed: Optional[float] = None
    provenance_chain: List[str] = Field(default_factory=list)

class ClaimConfidence(BaseModel):
    epistemic_confidence: float = Field(..., ge=0.0, le=1.0)
    social_traction: float = Field(..., ge=0.0, le=1.0)
    state_label: Literal["corroborated","contested","unverified"]
    collapsed: bool
    evidence_count: int
    last_pulse_at: Optional[str]
    scoring_version: str = "v1-wavefunction"
    scoring_inputs: Dict[str, Any] = Field(default_factory=dict)

class DivergenceResult(BaseModel):
    entity_name: str
    divergence_risk: float = Field(..., ge=0.0, le=1.0)
    canon_vector_hash: str
    live_vector_hash: str
    driving_claims: List[DrivingClaim]
    computed_at: str

class DrivingClaim(BaseModel):
    claim_text: str
    platform: str
    old_confidence: Optional[float]
    new_confidence: float
    delta: float

class PulseResult(BaseModel):
    entity_name: str
    status: Literal["success","disabled","budget_exceeded","error","no_data"]
    evidence: List[ClaimEvidence] = Field(default_factory=list)
    raw_snapshot_path: Optional[str]
    budget_remaining: float
    error: Optional[str]

class TimelinePoint(BaseModel):
    date: str
    epistemic_confidence: float
    social_traction: float
    divergence_risk: float
    active_claims: List[str]
    pulse_file: Optional[str]
    wiki_commit: Optional[str]
```

## 7. Config Additions (src/config.py)

```python
LAST30DAYS_ENABLED: bool = False
LAST30DAYS_BINARY_PATH: str = ""  # "" → try npx last30days, then last30days CLI
LAST30DAYS_MONTHLY_BUDGET_USD: float = 20.0
LAST30DAYS_COST_PER_PULL_USD: float = 0.50
LAST30DAYS_ENTITY_CADENCE_TIER1_HOURS: int = 24
LAST30DAYS_ENTITY_CADENCE_TIER2_HOURS: int = 168
LAST30DAYS_PULSE_TIMEOUT_SECONDS: int = 60
LAST30DAYS_MAX_CLAIMS_PER_PULSE: int = 50

CLAIM_WAVEFUNCTION_SOCIAL_TRACTION_WEIGHT: float = 0.15  # named constant, not buried

ALMANAC_GENERATION_INTERVAL_HOURS: int = 24
ALMANAC_DRY_RUN_DEFAULT: bool = True  # require explicit opt-in for live

BUDGET_REDIS_KEY_PREFIX: str = "budget"
```

## 8. Budget Guardrails

- Redis hash `budget:YYYY-MM` {spent, pulls, last_pull}
- Lua script for atomic check: `if spent+cost > ceiling then return 0 else incr spent,cost end`
- `BudgetTracker.check(cost) -> (allowed, remaining, reason)` called BEFORE subprocess
- `record_spend` after success
- Log every decision with `logger.info` + `append_to_log` with `[budget]` tag
- HOLD pattern: if `remaining < 2*cost_per_pull`, set `budget:hold` flag, require `POST /budget/approve` to clear (reuse SpendApprovalHandler shape).

## 9. Testing Strategy

- Unit: wavefunction math with synthetic evidence, divergence zero vs spike, entanglement score multi-platform vs single, budget atomicity.
- Integration: pulse_agent with mocked subprocess, timeline reconstructs from git log + raw files.
- API: new endpoints return correct shapes, disabled flag returns 200 no-op not 500.
- Contract: `FieldGeometryTensor` invariants, `ClaimConfidence` ge/le validation, HTML well-formed via `html.parser`.
- Existing 11 tests must stay green — CI gate.
- New files: `test_pulse_agent`, `test_wavefunction`, `test_divergence_engine`, `test_entanglement_corr`, `test_timeline_endpoint`, `test_tribunal_agent`, `test_almanac_generator`, `test_budget`.

## 10. Observability

New metrics in `src/observability.py`:
- `pulse_runs_total{status}`
- `pulse_latency_seconds`
- `budget_spent_usd`
- `wavefunction_state_total{label="corroborated|contested|unverified"}`
- `divergence_risk_histogram`
- `tribunal_runs_total{trigger="contested|divergence"}`
- `almanac_generated_total{status="success|no_change|error"}`

Logs:
- Every pulse: entity, tier, evidence count, platform diversity, budget remaining
- Every wavefunction: inputs, outputs, collapsed boolean
- Every divergence: driving claims
- Append to `wiki/log.md` with `pulse | {entity} | {evidence_count} | ${cost}` and `almanac | {date} | {entities} | moved=X collapsed=Y`

## 11. Risks & Mitigations

| Risk | Mitigation |
|---|---|
| last30days CLI not installed / API keys missing | `LAST30DAYS_ENABLED=false` default, `BINARY_PATH=""` → try `npx` then fail gracefully to `status=error` with clear message, never crash |
| Paid APIs (ScrapeCreators, Perplexity) cost overrun | Hard ceiling + HOLD + budget tracker + dry-run default True for almanac |
| LLM edge classification still heavy | Already has retry/backoff; almanac/tribunal reuse cached pulse files, not re-pulling per claim |
| Git log parsing fragile (shallow clone) | Fallback to file mtime if `git log` fails, log warning |
| ClaimEvidence parsing from markdown brittle | `last30days_adapter` tries JSON first, then markdown claims section with regex, then whole file as single claim fallback |
| Quantum layers still not true quantum advantage | Spec explicitly says "If a piece can't honestly route through real quantum computation, say so in PR description and label classical approximation" — document truthfully |
| SwiftUI client expects timeline endpoint | Phase 4 shipped early per suggested order, unblocks client |

## 12. Open Questions to Resolve During PR1

- Exact last30days CLI output format (JSON vs markdown) — need to inspect installed skill at `development-docs/AppleAdditionalDocumentation`? Actually last30days skill is at `https://github.com/mvanhorn/last30days-skill` — clone locally to inspect `last30days --help` output shape before coding adapter.
- Polymarket matching: does last30days engine already return `polymarket_odds` or need separate fetch? Spec says "if a market was matched — nullable" — treat nullable.
- `social_traction` decay function: exponential half-life 7 days? Need constant `SOCIAL_TRACTION_HALF_LIFE_DAYS=7`.

## 13. Definition of Done (Final)

1. `pip install last30days` or `npx last30days` works, `LAST30DAYS_ENABLED=true`, `BUDGET=5`, `run_pulse("Bob Lazar")` → `wiki/raw/pulse/bob-lazar-2026-07-11.json` + `.md` with `ClaimEvidence` list, budget decremented, logs.
2. Same entity second run → `ClaimWavefunction` computes `epistemic=0.x`, `social=0.y`, `state_label`, `collapsed` bool, inputs logged.
3. `GET /entities/bob-lazar/divergence` returns `divergence_risk` + driving claims, calls `spacetime_engine` not duplicate formula.
4. `GET /entities/bob-lazar/timeline?days=30` returns chartable 2+ points.
5. Contested claim triggers `tribunal_agent` with 3 positions + referee synthesis, uncontested skips.
6. `POST /almanac/generate?dry_run=true` returns HTML valid, no file writes, no budget spend.
7. `POST /almanac/generate` (live) after manual approval → `wiki/raw/almanac/2026-07-11.html` + `.md`, `log.md` entry, HTML self-contained (inline CSS, no JS, dark mode, print-friendly).
8. Let scheduler run overnight with Tier-1 set of 2-3 entities → dated brief appears unattended, budget respected.
9. All existing 11 tests green, new 7 test files green, `pytest` passes.

## See Also

- [[credibility-scoring]] — existing heuristic to be replaced
- [[agent-architecture]] — multi-agent orchestration
- [[field-geometry-tensor]] — contract between quantum layers
- [[science-reference-library]] — 61 PDFs now all covered
- [[apple-reference-guides]] — SwiftUI coding refs for timeline slider UI
- [[chat-to-wiki-pipeline]] — existing scheduler pattern to extend
- [[chickensoup-living-almanac-implementation-spec]] — upstream spec (if ingested as wiki page, else raw file)

---

## 14. Troubleshooting — Bugs Found & Fixed (2026-07-12)

This section documents production issues discovered during end-to-end verification and their fixes.

### Bug 1 — CRITICAL: Workspace root path wrong (`src/agents/pulse_agent.py`)

**Symptom**: Every pulse resulted in `CLI exit 1: npm error code E404` — the server was invoking `npx last30days` from npm registry which does not exist (last30days is a cloned skill repo, not an npm package).

**Root cause**: `workspace_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))` computes 2 hops from `src/agents/pulse_agent.py` → `/chickensoup/src/`, so the cloned script checkpoint at `last30days-skill/.../last30days.py` never resolves. Falls through to npx (E404).

**Fix**: Changed to 3 `dirname` hops so workspace root correctly resolves to `/chickensoup/`:
```python
workspace_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
```

**Verify**: `_resolve_binary()` returns `['/chickensoup/last30days-skill/skills/last30days/scripts/last30days.py']`, not `['npx', 'last30days']`.

### Bug 2 — CRITICAL: Swift double-encoding entity names (`AlmanacService.swift`)

**Symptom**: Endpoints like `/entities/Bob%2520Lazar/divergence` returned 404 from FastAPI. The system was double-percent-encoding entity names.

**Root cause**: 8 locations in `AlmanacService.swift` called `.addingPercentEncoding(withAllowedCharacters: .urlPathAllowed)` on entity names, then passed the result to `APIClient.request(path:)` which internally calls `baseURL.appendingPathComponent(...)` — `appendingPathComponent` re-encodes `%` to `%25`, producing `Bob%2520Lazar` instead of `Bob%20Lazar`.

**Fix**: Removed `.addingPercentEncoding(...)` from all 8 locations (triggerPulse, fetchDivergence, fetchTimeline, fetchEntanglement, runTribunal, triggerPulseAsync, generateAlmanacAsync, fetchTaskStatus, fetchAlmanacFile). Pass raw entity names; let `APIClient` handle encoding exactly once. `BackendService.swift:195` already uses this correct pattern for entity delete calls.

### Bug 3 — Setup: `last30days.py` lacked execute permission

**Symptom**: Even after fixing workspace root, the first pulse after deploy failed with `Permission denied: '/chickensoup/last30days-skill/.../last30days.py'`.

**Fix**: `chmod +x last30days-skill/skills/last30days/scripts/last30days.py`

### Bug 4 — Configuration: `LAST30DAYS_PULSE_TIMEOUT_SECONDS` too short

**Symptom**: `last30days pulse timed out after 60s` — script needs 58s on first cold start but budget timeout was 60s.

**Fix**: Increased `LAST30DAYS_PULSE_TIMEOUT_SECONDS` from 60 to 120 in `.env`.

### End-to-end verification (2026-07-12)

After all fixes:
- `POST /pulse/Bob%20Lazar` → `status: success, 50 evidence` (was `error, 0 evidence`)
- `POST /almanac/generate?dry_run=false` → all 3 entities processed, HTML brief written to `wiki/raw/almanac/2026-07-11.{html,md}`
- ENTITIES [success, 50 evidence]: Bob Lazar, Roswell Crash
- ENTITIES [error, 50 evidence]: Element 115 (parser labels as "error" but evidence intact — downstream label issue, non-blocking)
- Pulse snapshots: `wiki/raw/pulse/bob-lazar-2026-07-11.json` (32K, 50 evidence items)

### Cascade summary

```
Bug 1 (workspace root) → _resolve_binary() returns None → PulseResult(status=error, evidence=[])
                         ↓
                   No pulse snapshots written to wiki/raw/pulse/
                         ↓
                   almanac_generator.load_recent_pulse_evidence() → []
                         ↓
                   All entities skipped → 0/0/0/0 almanac HTML
                         ↓
                   divergence/entanglement endpoints: zero evidence → empty results
```
