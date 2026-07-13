# Wiki Internal-Content Audit Report

**Scope:** Full investigation of development/technical content in `wiki/` that is not public-facing or should not be ingested into the user-facing archive.  
**Date:** 2026-07-13  
**Auditor:** LLM (chickensoup codebase review)

---

## 1. What the app does with the wiki

The `wiki/` directory is the **single content vault** for both Project Chicken Soup and the public-facing UFO/Alien/Time Travel wiki. It is:
- Indexed into Neo4j via `POST /ingest/bulk` (`knowledge_graph/ingest.py`)
- Watched for changes by `WikiWatcher` for live reload
- Listed and rendered by `GET /wiki/pages` and `GET /wiki/page/{slug}`
- Auto-ingested by `ChatIngestAgent` and `WikiIngestAgent` background jobs
- Cross-referenced by the `[[wikiname]]` link system
- Served to the LLM discovery and query pipeline as context

Anything placed in `wiki/` under `entities/`, `concepts/`, or `projects/` is therefore implicitly in scope for:
- End-user search and browse
- Neo4j graph exposure via `/graph/{entity}`
- Context injection into the time-travel navigator and quantum scoring
- Logs and audits that may surface backend details

**There is no access-control mechanism separating "developer-internal" pages from "content" pages at the file-system level.** The only guard is tags and a `protected: true` frontmatter flag — and `protected` is a cleanup concept, not a visibility concept.

---

## 2. Legitimate public-facing content (preserved)

These pages are correctly in the wiki and should remain:

**Entities:** Persons, places, events, technologies — Roswell Crash, David Grusch, Bob Lazar, Area 51, Element 115, Varginha crash, Kordylewsky Clouds, Nikola Tesla, etc.  
**Concepts:** UFO science and time-travel theory — field manipulation, closed timelike curves, consciousness, exotic matter, quantum gravity, disclosure, credibility scoring, etc.  
**Projects:** Chicken Soup architecture — time-travel machinery, field geometry tensor, implementation plan.  
**Living Almanac:** The autonomous research brief system (appropriately described with its science).  
**Reference:** `science-reference-library`, `apple-reference-guides` index (the guides in `wiki/raw/` themselves are also legitimate reference data).

---

## 3. Internal-only content — complete inventory

### Tier A — Explicitly developer-internal (no public rationale)

These pages have no place in a public-accessible wiki vault. Each one is described below.

#### 3.1 Wiki internal infrastructure (pages that describe the wiki system itself)

| File | Lines | Problem |
|------|-------|---------|
| `wiki/entities/wiki-backup-restore.md` | 95 lines | Full spec of `src/wiki/backup.py`. Exposes environment variable names (`WIKI_BACKUP_ENABLED`, `WIKI_BACKUP_DIR`, `WIKI_BACKUP_RETENTION_DAYS`), directory layout, logger name `chickensoup.wiki.backup`, backup naming convention. No content rationale. |
| `wiki/entities/wiki-cleanup.md` | 131 lines | Full spec of `src/wiki/cleanup.py`. Exposes `ENGINEERING_TAGS` set of **200+ tag values** that the system uses to classify "preserved vs deletable" pages. This is a design-leak of the platform's own content-policy logic. Lists `CONTENT_TAGS` as "deletable." Log format (`[2026-06-26] cleanup | ...`). `clear_content_pages()` return value schema. |
| `wiki/concepts/wiki-file-system.md` | — | Describes the internal markdown CRUD layer. Exposes `write_page()`, `read_page()`, `page_exists()`, fuzzy-match query words, and the reconciliation algorithm. |
| `wiki/concepts/ingestion-pipeline.md` | — | Exposes `IngestAgent`, `POST /ingest/analyze`, `POST /ingest/pdf-folder`, file-upload slotting, analysis endpoint parameters. Agent internals exposed. |
| `wiki/concepts/chat-to-wiki-pipeline.md` | — | Exposes `ChatIngestAgent`, scheduler timing, conversation eligibility logic, `wiki/raw/conversation-{id}-{date}.md` artifact path, LLM promoter pattern. |
| `wiki/concepts/knowledge-graph-ingestion.md` | 147 lines | Full `src/knowledge_graph/ingest.py` implementation. Neo4j label set, relationship type matrix (with all edge types), LLM edge-classification prompt strategy, keyword heuristics, direction-reversal logic. This is the **backend graph design document** in the user-facing wiki. |
| `wiki/entities/knowledge-graph-ingestion.md` | (duplicate/shorter) | Same content, also in `entities/`. |

#### 3.2 Agent skills (developer-internal, not user content)

| File | Problem |
|------|---------|
| `wiki/entities/swiftui-pro.md` | Agent skill for SwiftUI code review (`.agents/skills/swiftui-pro/`). INSTALL_PATH, install commands, rule set (`foregroundStyle vs foregroundColor`, `#Preview over PreviewProvider`, etc.). All developer guidance. |
| `wiki/entities/swiftdata-pro.md` | Agent skill for SwiftData review. @Query rules, isEmpty == false crash warning, CloudKit constraints. |
| `wiki/entities/swift-concurrency-pro.md` | Agent skill for Swift concurrency review. Sendable rules, actor reentrancy, structured vs unstructured task rules. |
| `wiki/entities/swift-testing-pro.md` | Agent skill for Swift Testing review. #expect vs #require, struct vs class, parallel execution. |
| `wiki/concepts/agent-skills.md` | Aggregator page listing all four above. Trigger commands (`#swiftui-pro`). All developer-internal. |

#### 3.3 Apple platform reference guides (raw repo content imported into wiki vault)

| File/Area | Problem |
|-----------|---------|
| `wiki/entities/apple-reference-guides.md` | Master index pointing to all `wiki/raw/*.md` files imported from `development-docs/AppleAdditionalDocumentation/`. Lists all 20+ Apple platform docs with content descriptions. |
| `wiki/raw/Swift-Concurrency-Updates.md` | Full Apple developer documentation. |
| `wiki/raw/SwiftUI-Implementing-Liquid-Glass-Design.md` | Full Apple developer documentation. |
| `wiki/raw/UIKit-Implementing-Liquid-Glass-Design.md` | Same. |
| `wiki/raw/AppKit-Implementing-Liquid-Glass-Design.md` | Same. |
| `wiki/raw/WidgetKit-Implementing-Liquid-Glass-Design.md` | Same. |
| `wiki/raw/AppIntents-Updates.md` | Same. |
| `wiki/raw/Foundation-AttributedString-Updates.md` | Same. |
| `wiki/raw/FoundationModels-Using-on-device-LLM-in-your-app.md` | Same. |
| `wiki/raw/MapKit-GeoToolbox-PlaceDescriptors.md` | Same. |
| `wiki/raw/StoreKit-Updates.md` | Same. |
| `wiki/raw/Swift-Charts-3D-Visualization.md` | Same. |
| `wiki/raw/Swift-InlineArray-Span.md` | Same. |
| `wiki/raw/SwiftData-Class-Inheritance.md` | Same. |
| `wiki/raw/SwiftUI-AlarmKit-Integration.md` | Same. |
| `wiki/raw/SwiftUI-WebKit-Integration.md` | Same. |
| `wiki/raw/SwiftUI-New-Toolbar-Features.md` | Same. |
| `wiki/raw/SwiftUI-Styled-Text-Editing.md` | Same. |
| `wiki/raw/Implementing-Visual-Intelligence-in-iOS.md` | Same. |
| `wiki/raw/Implementing-Assistive-Access-in-iOS.md` | Same. |
| `wiki/raw/Widgets-for-visionOS.md` | Same. |

These 21 files are imported copies of Apple's own developer documentation. They describe `Observation`, `@Model`, `Chart3D`, Liquid Glass, WidgetKit, AppIntents, etc. — not UFO/alien/time-travel content. They live in `wiki/raw/` but are indexed/linked by `apple-reference-guides.md` and surfaced via that concept page in the app's wiki browser.

#### 3.4 Backend architecture and API documentation

| File | Problem |
|------|---------|
| `wiki/concepts/api-design.md` | 40+ endpoint table for `src/main.py`. Includes `POST /pulse/{entity}` implementation detail (`shell=False`), `POST /ingest/bulk` clears Neo4j, `/budget/approve`, `/almanac/generate`, MCP server auth, `/navigate`, `/quantum/schedule`. This is the **backend API spec** — not public content. |
| `wiki/entities/api-design.md` | Does not exist (explorer NOT FOUND). The API design content lives only at `wiki/concepts/api-design.md`. |
| `wiki/entities/core-models.md` | Full Pydantic model table including `WikiClearResponse`, `WikiExportResponse`, `WikiImportResponse`, `WikiDeleteResponse`, `LLMConfigRequest`, `ConfigRequest`, plus the Python→Swift model mapping table for `APIModels.swift`. |
| `wiki/concepts/api-authentication.md` | Dev-mode bypass logic (`if not settings.API_KEY: return`), key comparison code, partial-key log message ("X-API-Key: my-secret-key"). Security posture disclosure. |
| `wiki/concepts/production-readiness.md` | Checklist revealing 11 custom metric names, CIRCUIT BREAKER pattern, `LOG_IGNORE_PATTERNS`, budget Lua atomic, HOLD approval pattern, almanac hash comment format, Celery bug (`metric_tensor`→`spatial_metric`). |
| `wiki/concepts/swift-frontend-architecture.md` | Internal SwiftUI app structure — `AlmanacService.shared`, `BackendService.shared`, `ConfigService.isDarkMode`, service layer methods, `.environment()` injection. |
| `wiki/concepts/mcp-server.md` | Internal MCP server design — tool specifications, server code references, MCP endpoint patterns. |
| `wiki/concepts/langgraph-features.md` | LangGraph orchestration implementation details. |
| `wiki/concepts/temporal-query-pipeline.md` | Internal query routing — TQL → LLM → heuristic tier, confidence gating. |
| `wiki/concepts/quantum-job-scheduler.md` | Internal quantum job submission — IBM/D-Wave/IonQ routing code references. |
| `wiki/concepts/celery-tasks.md` | Celery task internals. |
| `wiki/concepts/evaluation-framework.md` | Internal evaluation metrics. |
| `wiki/entities/logging.md` | Logger names (`chickensoup.auth`, `chickensoup.tasks`, `chickensoup.wiki.backup`, `chickensoup.wiki.cleanup`), OpenTelemetry config code, metric names and types. |
| `wiki/entities/opentelemetry.md` | 4 custom metric names, `ObservabilityAndRateLimitMiddleware` in `src/main.py`, Jaeger/Zipkin/Prometheus export config. |
| `wiki/entities/github-actions.md` | CI/CD workflow files: `tests.yml`, `build.yml`, `deploy.yml`, `lint.yml` names and purposes. |
| `wiki/entities/pydantic-ai.md` | Agent framework, but specifically documents `src/` paths and framework wiring. Mixed. |
| `wiki/entities/pydantic-graph.md` | Graph orchestration internals. |
| `wiki/entities/pydantic-settings.md` | LLM config field names (`LLM_FALLBACK_CHAIN`, `LLM_ACTIVE_PROVIDER`, `LLM_ACTIVE_MODEL`). |
| `wiki/entities/pyproject-toml.md` | Build configuration. |
| `wiki/entities/pytest.md` | Testing framework usage. |
| `wiki/entities/docker.md` | Container config. |
| `wiki/entities/docker-compose.md` | Multi-container setup. |
| `wiki/entities/neo4j.md` | Database connection config. |
| `wiki/entities/redis.md` | Cache namespace prefixes (`cache:neo4j:*`, `cache:llm:*`, `cache:mcp:*`). |
| `wiki/entities/fastmcp.md` | MCP server framework. |
| `wiki/entities/langgraph.md` | Graph framework. |

#### 3.5 Implementation plans and internal scheduling

| File | Problem |
|------|---------|
| `wiki/projects/master-implementation-plan.md` | 6-stage dev plan with file paths, PR counts, bug catalog, conflict resolution for internal specs in `development-docs/`. Implementation artifacts — not content. |
| `wiki/plan/snapshot-feed-fixes.md` | Operational execution plan for fixing snapshot duplication. Bug identifiers (F1–F9), implementation workstreams (A/B/C), verification commands. |
| `wiki/plan/frontend-settings-menu.md` | SwiftUI implementation spec. DOD checklist, exact file changes (`LivingAlmanacView.swift`, `SettingsView.swift`, `ContentView.swift`), `#if os(macOS)` guards, `APIClient.shared.request` call examples. |
| `wiki/concepts/living-almanac-troubleshooting.md` | Internal diagnosis: exposes `_has_recent_empty_snapshot`, file naming convention (`project-serpo-2026-07-12.json`), `stat().st_mtime` edge case, `ls wiki/raw/pulse/` commands. Designed for devs debugging the system. |

#### 3.6 Secondary/quantum-internal (low urgency but mixed)

| File | Concern |
|------|---------|
| `wiki/concepts/credibility-scoring.md` | Credibility scoring doc — partly scientific (wavefunction over {CORROBORATED, CONTESTED, UNVERIFIED}), partly implementation detail (`VQE`, `reinforcement_count`, `epistemic_confidence`, `social_traction`). The category itself is a content concept, but the implementation details represent backend design. |
| `wiki/concepts/multi-llm-consensus.md` | How the multi-LLM consensus works — implementation detail. |
| `wiki/concepts/llm-discovery.md` | Auto-discovery code for LLM providers. |
| `wiki/concepts/llm-fallback-chain.md` | Provider fallback chain (oMLX → Ollama → LM Studio). Implementation. |

---

## 4. Cross-reference leaks in public pages

These public-facing pages link directly to internal pages. Each link makes the internal page browseable from the public section:

| Public page | Internal link exposed |
|-------------|----------------------|
| `wiki/index.md` | `[[wiki-backup-restore]]`, `[[wiki-cleanup]]`, `[[apple-reference-guides]]`, `[[swiftui-pro]]`, `[[swiftdata-pro]]`, `[[swift-concurrency-pro]]`, `[[swift-testing-pro]]`, `[[agent-skills]]`, `[[project-structure]]` |
| `wiki/overview.md` | `[[chat-to-wiki-pipeline]]` (with ChatIngestAgent reference), `[[frontend-settings-menu]]`, `[[agent-skills]]` |
| `wiki/log.md` | Free-form; many internal clues in commit history — binary paths, benchmark data, test names |
| `wiki/entities/logging.md` | Cross-links `[[wiki-backup-restore]]`, `[[wiki-cleanup]]` via logger paths |
| `wiki/entities/wiki-backup-restore.md` | Links `[[wiki-file-system]]`, `[[wiki-cleanup]]`, `[[redis]]` |
| `wiki/entities/wiki-cleanup.md` | Links `[[wiki-file-system]]`, `[[wiki-backup-restore]]`, `[[ingestion-pipeline]]`, `[[redis]]` |
| `wiki/concepts/api-authentication.md` | Links `[[production-readiness]]`, `[[mcp-server]]` |
| `wiki/concepts/production-readiness.md` | Links `[[apple-reference-guides]]` indirectly via `frontend-settings-menu` |

---

## 5. Risk summary by severity

### High — exposes system internals to end users

- `wiki/entities/wiki-backup-restore.md` — env var names, logger names, backup path convention
- `wiki/entities/wiki-cleanup.md` — 200+ tag classification list, dev-only page-policy
- `wiki/concepts/api-design.md` — full 40+ endpoint spec with implementation details
- `wiki/concepts/api-authentication.md` — dev-mode bypass logic
- `wiki/concepts/knowledge-graph-ingestion.md` — Neo4j internal design (also duplicated in `entities/`)
- `wiki/entities/core-models.md` — full Pydantic model table + Swift mapping table
- `wiki/concepts/swift-frontend-architecture.md` — internal SwiftUI service layer
- `wiki/concepts/production-readiness.md` — 11 metric names, Lua atomic, bug references
- All 4 `swift-*-pro.md` pages — developer agent skill specs with install commands and rules

### Medium — exposes developer workflow

- `wiki/concepts/living-almanac-troubleshooting.md` — diagnostic commands, internal path conventions
- `wiki/concepts/ingestion-pipeline.md` — IngestAgent implementation
- `wiki/concepts/chat-to-wiki-pipeline.md` — ChatIngestAgent, scheduler set-up
- `wiki/entities/logging.md` — logger names, OpenTelemetry code
- `wiki/entities/opentelemetry.md` — 4 metric names, middleware code
- `wiki/plan/frontend-settings-menu.md` — SwiftUI line-by-line implementation plan
- `wiki/plan/snapshot-feed-fixes.md` — operational fix plan
- `wiki/projects/master-implementation-plan.md` — 6-stage implementation plan

### Low — Apple raw docs + infrastructure entities

- 21 files in `wiki/raw/` mapped via `apple-reference-guides.md`
- `wiki/entities/github-actions.md`, `wiki/entities/pydantic-*.md`, `wiki/entities/docker*.md`, `wiki/entities/neo4j.md`, `wiki/entities/redis.md`, `wiki/entities/fastmcp.md`, `wiki/entities/langgraph.md`, `wiki/entities/celery.md`, `wiki/entities/ray.md`, `wiki/entities/omlx.md`, `wiki/entities/ollama.md`, `wiki/entities/lm-studio.md`, `wiki/entities/pyproject-toml.md`, `wiki/entities/fastapi.md`

---

## 6. Does this leak to the user-facing archive?

**Yes, in three ways:**

1. **Wiki browser (`GET /wiki/pages`, `GET /wiki/page/{slug}`):** Returns all pages. A user browsing `entities/wiki-backup-restore` or `entities/swiftui-pro` from the index sees internal developer docs as if they were content pages.

2. **Neo4j graph (`POST /ingest/bulk`):** All pages in `entities/`, `concepts/`, `projects/` are ingested as nodes. Internal pages appear as Neo4j nodes alongside Roswell Crash and David Grusch. Rendered graph includes them as navigable entities.

3. **Chat-based archive ingestion (`ChatIngestAgent`):** Internal pages are equally eligible for LLM summarization and conversion into `wiki/raw/conversation-{id}-{date}.md`. A developer's conversation about `wiki-cleanup.py` or `apple-reference-guides.md` can be turned into a "brief" that gets exposed to the public archive.

4. **Cross-reference index (`wiki/index.md`):** Links to `[[wiki-backup-restore]]`, `[[swiftui-pro]]`, etc. from the user-facing index page make those pages discoverable without any auth barrier.

---

## 7. Fix — production-grade implementation plan

The guiding principle: **separate public content from developer-internal documentation at the file-system level**, and make the visibility boundary explicit and enforceable.

### Phase 1 — Immediate (no breaking changes)

**Goal:** Make internal content un-discoverable from the public wiki browser and graph.

1. **Move internal pages out of `entities/`, `concepts/`, `projects/`.**

   Move these files to `wiki/dev/` (new top-level directory, tracked by git but excluded from ingestion):

   - `wiki/entities/wiki-backup-restore.md` → `wiki/dev/backup-restore.md`
   - `wiki/entities/wiki-cleanup.md` → `wiki/dev/cleanup.md`
   - `wiki/entities/swiftui-pro.md` → `wiki/dev/skills/swiftui-pro.md`
   - `wiki/entities/swiftdata-pro.md` → `wiki/dev/skills/swiftdata-pro.md`
   - `wiki/entities/swift-concurrency-pro.md` → `wiki/dev/skills/swift-concurrency-pro.md`
   - `wiki/entities/swift-testing-pro.md` → `wiki/dev/skills/swift-testing-pro.md`
   - All 21 `wiki/raw/*.md` Apple references → `wiki/dev/reference/apple/`
   - `wiki/entities/knowledge-graph-ingestion.md` → `wiki/dev/ingestion.md`
   - `wiki/entities/core-models.md` → `wiki/dev/core-models.md`
   - `wiki/entities/logging.md` → `wiki/dev/logging.md`
   - `wiki/entities/opentelemetry.md` → `wiki/dev/opentelemetry.md`
   - `wiki/entities/github-actions.md` → `wiki/dev/github-actions.md`
   - All `wiki/entities/pydantic-*.md`, `wiki/entities/docker*.md`, `wiki/entities/neo4j.md`, `wiki/entities/redis.md`, `wiki/entities/fastmcp.md`, `wiki/entities/langgraph.md`, `wiki/entities/celery.md`, `wiki/entities/ray.md`, `wiki/entities/pyproject-toml.md`, `wiki/entities/fastapi.md` → `wiki/dev/dependencies/`
   - `wiki/concepts/api-design.md` → `wiki/dev/api-design.md`
   - `wiki/concepts/api-authentication.md` → `wiki/dev/authentication.md`
   - `wiki/concepts/production-readiness.md` → `wiki/dev/production-readiness.md`
   - `wiki/concepts/swift-frontend-architecture.md` → `wiki/dev/swift-frontend.md`
   - `wiki/concepts/wiki-file-system.md` → `wiki/dev/wiki-file-system.md`
   - `wiki/concepts/mcp-server.md` → `wiki/dev/mcp-server.md`
   - `wiki/concepts/langgraph-features.md` → `wiki/dev/langgraph-features.md`
   - `wiki/concepts/ingestion-pipeline.md` → `wiki/dev/ingestion-pipeline.md`
   - `wiki/concepts/chat-to-wiki-pipeline.md` → `wiki/dev/chat-to-wiki-pipeline.md`
   - `wiki/concepts/agent-skills.md` → `wiki/dev/agent-skills.md`
   - `wiki/entities/project-structure.md` (in `concepts/`) → `wiki/dev/project-structure.md`

   **Files NOT moved (legitimate content):**
   - `wiki/concepts/credibility-scoring.md` — keep; this is a core UFO science concept
   - `wiki/concepts/multi-llm-consensus.md`, `wiki/concepts/llm-discovery.md`, `wiki/concepts/llm-fallback-chain.md` — evaluate per case; LLM internals can stay if framed as user-facing architecture, else move

2. **Add `dev/` to `.gitignore` under `wiki/`** for git cleanliness (optional — `wiki/dev/` can stay tracked; just don't ingest it).

3. **Remove internal links from public pages:**
   - `wiki/index.md` lines referencing: `wiki-backup-restore`, `wiki-cleanup`, `apple-reference-guides`, `swiftui-pro`, `swiftdata-pro`, `swift-concurrency-pro`, `swift-testing-pro`, `agent-skills`, `project-structure`
   - `wiki/overview.md` lines referencing: `chat-to-wiki-pipeline` (from the pipeline architecture bullet), `agent-skills`, `frontend-settings-menu`
   - `wiki/entities/logging.md` links to `wiki-backup-restore` and `wiki-cleanup` → remove

4. **Create a stub `wiki/entities/apple-reference-guides.md`** with a one-line redirect or remove the `apple-reference-guides.md` from `wiki/entities/` entirely. The index.md link line 51 is the only link to it.

5. **Update `wiki/concepts/apple-reference-guides.md`** tags: remove `[apple, swift, swiftui, reference, development]` as an index keyword; it is developer-reference, not a content concept.

### Phase 2 — Enforce wall at ingestion (no new internal docs can leak)

**Goal:** Even if a developer accidentally writes to `wiki/`, the system should not ingest dev-only content.

1. **Filter `POST /ingest/bulk`** in `knowledge_graph/ingestion.py` and `WikiWatcher` to skip files under `wiki/dev/`. Add a check at the top of `ingest_wiki_page()`:
   ```python
   path_parts = Path(filepath).parts
   if "dev" in path_parts:
       return  # Skip developer-internal docs
   ```

2. **Filter `/wiki/pages` API** (`GET /wiki/pages`, `GET /entities`, `/graph/{entity}`) to exclude `wiki/dev/` from listing. Add a path-prefix filter in `wiki/page_service.py` (or equivalent).

3. **Update `wiki-cleanup.py`** `ENGINEERING_TAGS` set to include `dev`, `skill`, `backup`, `restore`, `reference`, `raw-guide`, `implementation-plan`. This makes the cleanup system aware that dev docs are preserved-as-is rather than classified as deletable content. Also, `clear_content_pages()` should automatically move (not delete) any page under `wiki/dev/` that it encounters — a sanity check.

4. **Update `WikiWatcher`** to ignore `wiki/dev/` directory for live-reload triggers.

### Phase 3 — Content-model fix (long-term hygiene)

**Goal:** Re-train the wiki authoring convention to keep dev docs out of content directories from the start.

1. **Amend `AGENTS.md` wiki conventions section** to explicitly state:
   - `wiki/dev/` is the only place for implementation docs, agent skill specs, CI docs, environment config docs, and Apple reference copies.
   - `wiki/entities/`, `wiki/concepts/`, `wiki/projects/` are **content-only**. Writing anything with internal code paths, env var names, or implementation line counts to any of these three directories is forbidden.

2. **Add a lint step** (`tests/test_wiki_internal_content_lint.py`) that scans `wiki/entities/`, `wiki/concepts/`, `wiki/projects/` for internal content patterns:
   ```python
   INTERNAL_PATTERNS = [
       r"src/[\w/]+\.py",           # file paths
       r"chickensoup\.\w+",          # logger names
       r"WIKI_\w+|API_KEY|\.env",   # env vars / secrets
       r"\d+ lines\)",               # line-count disclosure
       r"npx skills add",            # install commands
       r"npx last30days",            # internal tooling
   ]
   ```
   Lint should fail CI if any of these patterns appear in `entities/`, `concepts/`, `projects/`.

3. **Review cross-references:** add a CI check that `[[wikilink]]` targets in public pages do not resolve to `wiki/dev/` pages.

---

## 8. File counts

| Category | Count |
|----------|-------|
| Tier A — Wiki infrastructure docs | ~8 |
| Tier A — Agent skills (4 files + 1 hub) | 5 |
| Tier A — Apple reference guides (`wiki/raw/`) | 21 |
| Tier A — Backend architecture/API docs | ~23 |
| Tier A — Implementation plans | ~4 |
| Tier A — Living almanac troubleshooting doc | 1 |
| **Total files to move** | **~62** |
| Internal links to remove from public pages | ~20 |
| Cross-reference leaks to seal | ~10 |

---

## 9. What NOT to move

| File | Rationale |
|------|---------|
| `wiki/concepts/credibility-scoring.md` | Core content concept: wavefunction scoring over CORROBORATED/CONTESTED/UNVERIFIED. User-facing science, not just the Python implementation. Strip implementation details if they make the page internal-only, but keep the concept. |
| `wiki/concepts/multi-llm-consensus.md` | Partially public — keep but strip `Jaccard agreement scoring` implementation detail. |
| `wiki/concepts/llm-discovery.md` | Keep — auto-discovery is a platform feature worth documenting publicly. Strip file paths. |
| `wiki/concepts/llm-fallback-chain.md` | Keep — the fallback chain (oMLX → Ollama → LM Studio) is a user-relevant "how it works" fact. Strip implementation layer. |
| `wiki/concepts/pulse-agent.md` | Keep — what pulses do is a content concept. Strip `_sanitize_entity_name` code, strip file paths, strip `src/agents/pulse_agent.py`. |
| `wiki/entities/project-structure.md` (in `concepts/`) | Move to `wiki/dev/` — directory tree and file counts are internal. |
| `wiki/entities/primary-researcher.md` | Keep — it's a user entity. |
| `wiki/log.md` | **Keep** — it is append-only history of content ingestions, not system internals. However, sanitize old entries that reveal file paths or binary paths (the `last30days_binary_path`, `laser-sim.py` threads, test fixture paths). |
| `wiki/raw/pulse/` and `wiki/raw/almanac/` | Subdirectories of `raw/`; move to `wiki/dev/data/pulse/` and `wiki/dev/data/almanac/`. They contain runtime artifacts (snapshot files), not human content. |

---

## 10. Summary of the risk

The issue is not that the wiki contains technical docs — it's that those docs share a namespace with content and are ingestible as graph nodes or rendered wiki pages. A user opening `entities/swiftui-pro` or `entities/wiki-backup-restore` from the index would see:
- Installation commands for developer agent skills
- Environment variable names for backup configuration
- 200+ tag values used by the page-classification engine
- Apple developer documentation (Liquid Glass, Foundation Models, etc.) unrelated to UFOs

These surfaces are inconsistent with the stated purpose of the wiki and with the production posture of the platform. The fix is a structural separation enforced at both the file-system layer and the ingestion layer, backed by a CI lint that catches future regressions.
