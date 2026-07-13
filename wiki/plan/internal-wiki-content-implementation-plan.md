# Internal Wiki Content — Implementation Plan

**Companion to:** `wiki/plan/internal-wiki-content-audit-report.md`  
**Status:** Ready for execution  
**Estimated scope:** ~62 file moves + ~5 code changes + ~20 link rewrites + 1 new lint test

---

## Phase 1 — Physical separation (no code changes required for correctness)

Done entirely via `git mv` so history is preserved.

### Step 1.1 — Create `wiki/dev/` skeleton

```
wiki/dev/
  skills/
    swiftui-pro.md
    swiftdata-pro.md
    swift-concurrency-pro.md
    swift-testing-pro.md
    agent-skills.md
  backup-restore.md        (from entities/)
  cleanup.md                (from entities/)
  ingestion.md              (from entities/knowledge-graph-ingestion.md)
  core-models.md            (from entities/)
  logging.md                (from migrated from entities/)
  opentelemetry.md          (from entities/)
  github-actions.md         (from entities/)
  dependencies/
    pydantic-ai.md
    pydantic-graph.md
    pydantic-settings.md
    pyproject-toml.md
    pytest.md
    docker.md
    docker-compose.md
    neo4j.md
    redis.md
    fastmcp.md
    langgraph.md
    celery.md
    ray.md
    omlx.md
    ollama.md
    lm-studio.md
  reference/
    apple/                  (all 21 wiki/raw/*.md Apple refs)
  api-design.md
  authentication.md
  production-readiness.md
  swift-frontend.md
  wiki-file-system.md
  mcp-server.md
  langgraph-features.md
  ingestion-pipeline.md
  chat-to-wiki-pipeline.md
  project-structure.md      (from concepts/)
  reference-guides.md       (replaces entities/apple-reference-guides.md)
```

### Step 1.2 — Relocate implementation plans

```
wiki/plan/internal/           (new subdir)
  master-implementation-plan.md   (from projects/)
  snapshot-feed-fixes.md          (keep? evaluate — currently operational)
  frontend-settings-menu.md       (keep? this is also a content feature plan)
```

`master-implementation-plan.md` is unambiguously internal. Move it definitively.  
`snapshot-feed-fixes.md` and `frontend-settings-menu.md` are borderline — they document user-facing features. Move `snapshot-feed-fixes.md` to `wiki/plan/internal/` (it's a bug-fix execution record). Keep `frontend-settings-menu.md` but strip SwiftUI line-by-line implementation details (see Phase 2).

### Step 1.3 — Move runtime artifacts out of `wiki/raw/`

```
wiki/raw/   ← keep only content ORIGINALS (PDFs, transcripts, Apple guides, etc.)
wiki/dev/data/pulse/    (from wiki/raw/pulse/)
wiki/dev/data/almanac/  (from wiki/raw/almanac/)
```

`wiki/raw/pulse/` and `wiki/raw/almanac/` contain runtime-generated snapshot files, not canonical references. They are currently referenced from multiple internal pages — those references should all be updated.

### Step 1.4 — Remove internal `[[wikilinks]]` from public pages

| Page | Remove links to |
|------|----------------|
| `wiki/index.md` | `wiki-backup-restore`, `wiki-cleanup`, `apple-reference-guides`, `swiftui-pro`, `swiftdata-pro`, `swift-concurrency-pro`, `swift-testing-pro`, `agent-skills`, `project-structure` |
| `wiki/overview.md` | `chat-to-wiki-pipeline` (pipeline bullet), `agent-skills`, `frontend-settings-menu` |
| `wiki/entities/wiki-backup-restore.md` | `wiki-file-system`, `wiki-cleanup`, `redis` |
| `wiki/entities/wiki-cleanup.md` | `wiki-file-system`, `wiki-backup-restore`, `ingestion-pipeline`, `redis` |
| `wiki/entities/logging.md` | `wiki-backup-restore`, `wiki-cleanup` |
| `wiki/entities/api-design.md` (in concepts/) | `fastapi`, `multi-llm-consensus`, `quantum-job-scheduler`, `mcp-server` — kept |
| `wiki/entities/core-models.md` | `api-design`, `pydantic-ai`, `pydantic-graph`, `swift-frontend-architecture` |
| `wiki/concepts/api-authentication.md` | `mcp-server`, `production-readiness` |
| `wiki/concepts/production-readiness.md` | all links to `frontend-settings-menu`, `apple-reference-guides` |

---

## Phase 2 — Code changes (enforce the wall)

### Step 2.1 — Add `dev/` to ingestion exclusion list

In `src/knowledge_graph/ingest.py` (`ingest_wiki_page` and `POST /ingest/bulk`):

```python
def _is_dev_path(filepath: str) -> bool:
    return "dev" in Path(filepath).parts

# at top of ingest_wiki_page():
if _is_dev_path(filepath):
    return None  # or (0, 0) — no node created
```

### Step 2.2 — Add `dev/` to `WikiWatcher` exclusion

In the fs watcher setup (likely in `src/wiki/watcher.py` or an async watcher):

```python
WATCH_PATHS = [p for p in WATCH_PATHS if "dev" not in p.parts]
```

### Step 2.3 — Add `dev/` to `GET /wiki/pages` filter

In the wiki page listing endpoint:

```python
if "dev" in Path(filepath).parts:
    continue
```

### Step 2.4 — Strip internal content from three borderline pages (in-place edits)

**`wiki/concepts/ingestion-pipeline.md`** — remove agent class names, `Post /ingest/analyze` endpoint table, `IngestAgent.analyze_content()` reference. Replace with: "Content arrives through the wiki's upload pipeline. Pages are analyzed for structure and converted to wiki format. Full technical documentation: see `wiki/dev/ingestion-pipeline.md`."

**`wiki/concepts/chat-to-wiki-pipeline.md`** — same treatment. Remove scheduler timing, `wiki/raw/conversation-{id}-{date}.md` path, `ChatIngestAgent` class name.

**`wiki/concepts/wiki-file-system.md`** — remove function signatures (`write_page()`, `read_page()`, `page_exists()`), fuzzy-match algorithm details, reconciliation pseudo-code.

### Step 2.5 — Sanitize `wiki/log.md`

Remove or replace entries containing:
- Binary paths: `last30days_binary_path`, `laser-sim.py`
- Test fixture paths: `wiki/raw/pulse/bob-lazar-...`, `bob-lazar;-rm--rf---`
- Internal error messages that reference file paths
- Benchmark numbers from specific runs

Add a schema for log entries: `## [YYYY-MM-DD] <verb> | <one-line-public-summary>` with no file paths or binary names.

---

## Phase 3 — Testing

### Step 3.1 — New test: no dev docs in Neo4j

```python
def test_ingest_bulk_skips_wiki_dev():
    # Write a page to wiki/dev/test.md
    # Run POST /ingest/bulk
    # Assert no node created in Neo4j for "test"
```

### Step 3.2 — New test: `GET /wiki/pages` skips dev

```python
def test_wiki_pages_excludes_dev_directory():
    # Create wiki/dev/internal.md
    # GET /wiki/pages
    # Assert "internal" not in response
```

### Step 3.3 — Update existing tests that referenced moved pages

Affected test files (check and update):
- `tests/test_wiki_backup_restore.py` — if exists
- `tests/test_wiki_cleanup.py` — if exists
- `tests/test_ingestion_pipeline.py`
- `tests/test_knowledge_graph_ingestion.py`
- `tests/test_api_design.py`

### Step 3.4 — Update `wiki-cleanup.py` `ENGINEERING_TAGS` set

Add: `"dev", "skill", "backup", "restore", "reference", "raw-guide", "implementation-plan"`

This prevents `wiki/dev/` pages from being classified as `CONTENT_TAGS` (deletable). They should skip classification entirely.

---

## Phase 4 — CI lint (long-term gate)

### Step 4.1 — New lint test: `tests/test_wiki_content_hygiene.py`

```python
INTERNAL_PATTERNS = [
    (re.compile(r"src/[\w/]+\.py"), "file path to backend module"),
    (re.compile(r"chickensoup\.\w+"), "Python logger name"),
    (re.compile(r"WIKI_\w+|API_KEY|\.env"), "env var or secret name"),
    (re.compile(r"\d+\s+lines?\)"), "internal line count"),
    (re.compile(r"npx\s+skills\s+add"), "skill install command"),
    (re.compile(r"npx\s+last30days"), "internal binary reference"),
    (re.compile(r"wiki/(?:raw|dev)/\S+"), "internal file path"),
]

PUBLIC_DIRS = ["wiki/entities/", "wiki/concepts/", "wiki/projects/"]

def test_no_internal_markers_in_public_wiki_dirs():
    for public_dir in PUBLIC_DIRS:
        for md_file in Path(public_dir).rglob("*.md"):
            content = md_file.read_text()
            for pattern, description in INTERNAL_PATTERNS:
                assert not pattern.search(content), \
                    f"{md_file}: contains internal marker ({description})"
```

### Step 4.2 — Add lint to `pyproject.toml` pre-commit or CI

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
# lint-test runs in CI alongside main suite
```

---

## Execution order

| Order | Action | Risk |
|-------|--------|------|
| 1 | `git mv` all internal pages to `wiki/dev/` | Low — git history preserved |
| 2 | `git mv` internal plans to `wiki/plan/internal/` | Low |
| 3 | `git mv` runtime artifacts out of `wiki/raw/` | Medium — update any code referencing those paths |
| 4 | Edit `wiki/index.md` and `wiki/overview.md` to remove internal links | Low |
| 5 | Strip internal content from `ingestion-pipeline.md`, `chat-to-wiki-pipeline.md`, `wiki-file-system.md` | Low |
| 6 | Code changes: `ingest.py`, watcher, `/wiki/pages` endpoint | Medium — needs test coverage |
| 7 | Sanitize `wiki/log.md` | Low |
| 8 | Add `ENGINEERING_TAGS` additions to `wiki-cleanup.py` | Low |
| 9 | Add `tests/test_wiki_content_hygiene.py` | Low |
| 10 | Run full test suite, fix regressions | Medium |
| 11 | Commit and push | Low |

---

## What won't change

- `wiki/concepts/credibility-scoring.md` stays; it is a user-facing concept. Its implementation details (VQE, wavefunction, reinforcement_count) should be extracted to `wiki/dev/credibility-scoring-impl.md` but the concept page remains public.
- `wiki/concepts/multi-llm-consensus.md`, `wiki/concepts/llm-discovery.md`, `wiki/concepts/llm-fallback-chain.md` stay but get stripped of file paths and agency internals.
- `wiki/entities/project-structure.md` content (the concept page) stays but the directory tree section is moved to `wiki/dev/project-structure-impl.md`.
