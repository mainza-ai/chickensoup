---
title: "AI Chat ↔ last30days ↔ Wiki ↔ Living Almanac — Integration Plan"
tags: [integration, planning, last30days, chat, wiki, almanac, agents]
created: 2026-07-13
updated: 2026-07-13
sources: [deep-audit-2026-07-13]
related: [langgraph-workflows, chat-to-wiki-conversion, living-almanac-engine, staleness-queue, pulse-agent, research-agent, query-agent, orchestration]
---

# AI Chat ↔ last30days ↔ Wiki ↔ Living Almanac — Integration Plan

**Companion to:** `wiki/plan/internal-wiki-content-audit-report.md`  
**Status:** In progress — Phases 0–3 complete; Phase 4 awaiting your review.  
**Scope source:** Deep-pass audit dated 2026-07-13. Four live bugs and four design phases.

---

## Execution Log

### Phase 0 — Live Correctness Bugs (complete, committed `bf34fbe`)

**0a — History pass-through in `/query` + WebSocket**: Fixed. `orchestrator.execute(request.query, history=history)` now passes conversation history in both the REST handler (`main.py:520`) and the WebSocket handler (`main.py:1191`). WebSocket handler now tracks `conversation_id` per connection, fetches history from Redis, stores updated history back after each turn, and returns `conversation_id` in the completed message.

**0b — Staleness queue directory scan**: Fixed. `rebuild_queue()` now scans `entities/`, `concepts/`, and `projects/` directories. Previously only `entities/` was scanned, making chat-created concepts and research-thread projects invisible to the idle pulse system.

**0c — Research approval endpoint**: Fixed. Added `POST /research/{thread_id}/approve` to `main.py`, modeled on the existing `/budget/approve` pattern. Resumes LangGraph execution with `human_approved=True`. Added `BackendService.approveResearch(threadId:)` Swift wrapper.

**0d — Redis `.decode()` calls**: Fixed. Removed four `.decode()` calls in `idle_sentinel.py:71,80` and `staleness_queue.py:36,53`. Redis client is initialized with `decode_responses=True`, so `.get()` already returns `str`. Before fix, `is_idle()` always returned `True` by exception fallback, causing `idle_ingestion_loop` to fire during active periods.

---

### Phase 1 — Option C: Chat-Triggered Auto-Pulse (complete, committed `77e1589`)

**1a — Queue seeding after page creation**: Implemented. After `ChatIngestAgent` creates a wiki page in `process_eligible_conversations()`, if `LAST30DAYS_ENABLED`, calls `staleness_queue.record_pulse_completed(slug)` to seed the Redis sorted set immediately. This eliminates the wait for the next `rebuild_queue()` cycle.

**1b — Wiki page enrichment after pulse**: Implemented. In `idle_ingestion_loop`, after a pulse completes with evidence, if the wiki page was chat-created (sources contain `conversation:`), the top 3 claims by engagement are appended as a `## External Evidence` section to the wiki body via `write_page()`.

**1c — Swift "Pulse Now" button**: Implemented. `WikiPageDetailView` now exposes a toolbar button calling `almanacService.triggerPulseAsync(entityName:)`. A `pollPulseStatus` task polls `fetchTaskStatus(taskId:)` every 2 seconds and refreshes the page when the pulse completes.

---

### Phase 2 — Option B: "Research Now" in Graph Views (complete, committed `ed8f46f`)

Implemented in `EntityDetailView.swift`. `GraphExplorerView` requires no changes — it already embeds `EntityDetailView` in both the macOS `NavigationSplitView` detail column and the iOS sheet, so the new toolbar button appears automatically in all contexts.

- **Toolbar button**: Added `Research Now` toolbar item wired to `almanacService.triggerPulseAsync(entityName:)`
- **Polling**: `pollPulseStatus(taskId:)` polls `fetchTaskStatus(taskId:)` every 2 seconds
- **Completion**: On terminal status (`completed`/`failed`/`success`), the view refreshes via `loader?.load()`
- **State**: `isPulsing` drives a `ProgressView("Researching...")` in the toolbar during the pulse

---

### Phase 3 — Option D: Almanac-Driven Chat Awareness (complete, committed `ed8f46f`)

Backend + Swift wiring complete. Uses the **banner-in-chat** approach (simpler than prompt injection, no LLM prompt changes).

**Backend:**
- `src/main.py`: Added `GET /almanac/summary`. Reads the most recent almanac `.md` file, returns `date`, `contested_claims` (top 10), `newly_contested` count, and `entities_processed` list.

**Swift:**
- `APIModels.swift`: Added `APIAlmanacSummaryResponse` with CodingKeys for snake_case JSON
- `AlmanacService.swift`: Added `almanacSummary: APIAlmanacSummaryResponse?` state, `isFetchingAlmanacSummary`, and `fetchAlmanacSummary()` (fires on app launch via `ContentView.fetchInitialData()`)
- `QueryOverlayView.swift`: Added `onAlmanacTap: (() -> Void)?` parameter and `almanacSummaryBanner` — a tappable orange banner shown when `almanacSummary.newlyContested > 0`. Tapping calls `onAlmanacTap` to navigate to the Almanac view.
- `ContentView.swift`: Passes `onAlmanacTap` closures to both `QueryOverlayView` instances — desktop switches `activeDetailTab = .almanac`, iPhone switches `activeTab = .almanac`.

---

## Executive Summary

Four subsystems already exist and each works in isolation:

| Subsystem | Swift entry | FastAPI endpoint | Agent / engine | Output |
|---|---|---|---|---|
| **AI Chat** | `QueryOverlayView` → `BackendService.submitQuery` | `POST /query` | `Orchestrator` → `QueryAgent` → `ResearchAgent` | `QueryResponse(answer, claim_confidences, inferred_events)` |
| **last30days Research** | `AlmanacService.triggerPulse` | `POST /pulse/{entity_name}` | `PulseAgent` → `last30days` CLI → `PulseWriter` | `PulseResult` + snapshot `wiki/raw/pulse/*.json` |
| **Wiki Ingestion** | `DataIngestionView` / `SettingsView` | `POST /ingest/file`, `POST /ingest/folder` | `IngestAgent` / `ChatIngestAgent` | wiki markdown in `wiki/{entities,concepts,projects}/` |
| **Living Almanac** | `LivingAlmanacView` | `POST /almanac/generate` | `AlmanacGenerator` → `PulseAgent` + `ClaimWavefunction` + `DivergenceEngine` + `TribunalAgent` | `wiki/raw/almanac/{date}.html` |

The diagnosis from the deep audit: **the four subsystems do not talk to each other in the directions the user naturally expects**. Chat can research only what is already in the wiki. Pulse runs on a schedule or when manually triggered. New topics from chat become wiki stubs that sit empty until someone manually pulses them. The almanac runs on a fixed tag-driven tier list and does not auto-adapt to whatever chat has been discussing. Before building integration on top of these subsystems, three small live bugs must be fixed because two of them actively undermine any later phase and the third makes Phase 1 cheaper.

This plan is split into **Phase 0** (live correctness fixes) and **Phases 1–4** (integration work in increasing order of complexity). None of the integration work starts until Phase 0 is complete and you have reviewed each subsequent phase.

---

## Phase 0 — Live Correctness Bugs

These are not design gaps. They are currently-active code problems that affect real behavior. Fix them before any integration work.

---

### 0a. Conversation history is not reaching the orchestrator

**Bug location 1:** `src/main.py:520`

```python
# Current (broken):
output = await orchestrator.execute(request.query)

# Required:
output = await orchestrator.execute(request.query, history=history)
```

**Bug location 2:** `src/main.py:1183`

```python
# Current (WebSocket handler — no history fetched at all):
output = await orchestrator.execute(data)
response = _build_query_response(data, output)

# Required: mirror the REST history-fetch pattern first, then pass it:
# 1. retrieve conversation_id from request or session
# 2. fetch history from Redis
# 3. pass history=history into orchestrator.execute()
# 4. include history in _build_query_response()
```

**Current effect:** Multi-turn queries have no conversational context. A follow-up like "did it find anything?" or "tell me more about that entity" is treated as a brand-new standalone query. The `ResearchAgent` summarizer, the `QueryAgent` entity extractor, and the pronoun resolver (`resolve_pronominal_references` in `query_agent.py:84-115`) all receive an empty history list.

**Why this gates everything:** Every integration option in Phases 1–4 depends, to some degree, on multi-turn behavior. Persona A explicitly wants "tell me everything we know about Topic X and what's new in the last 30 days" — that is a multi-turn shape. Option A's "enriching now, resuming later" flow requires conversational state to be meaningful. Fixing this is a two-line change in `/query` and roughly an eight-line addition in the WebSocket handler.

**Work required:**
- `src/main.py:520` — add `history=history` to `orchestrator.execute()`
- `src/main.py:1183` — in the WebSocket handler, add the same Redis history-fetch pattern the REST endpoint uses (lines 511-518), then pass it to both `orchestrator.execute(data, history=history)` and `_build_query_response(data, output, history=history)`

**Estimated effort:** ~10 lines total, no new tests required (existing handler structure matches the REST pattern exactly).

---

### 0b. Staleness queue silently excludes concepts and projects

**Bug location:** `src/staleness_queue.py:102-136`

```python
# Current (broken):
def rebuild_queue():
    wiki_dir = settings.WIKI_DATA_DIR
    entities_dir = os.path.join(wiki_dir, "entities")  # <-- only entities
    if not os.path.isdir(entities_dir):
        return
    slugs = []
    for filename in os.listdir(entities_dir):
        if filename.endswith(".md"):
            slugs.append(filename[:-3])
```

**Current effect:** `idle_ingestion_loop` calls `get_next_batch(3)` which draws from the Redis sorted set that `rebuild_queue()` populates. That sorted set is built exclusively from `wiki/entities/`. Chat-created pages in `wiki/concepts/` and `wiki/projects/` are structurally invisible to the idle pulse system. Even if a chat conversation creates a concept page (e.g. "remote viewing") or a research-thread project page (e.g. "Research Thread: Bob Lazar"), those pages will never surface in the idle pulse batch no matter how long the system runs.

**Why this gates Phase 1 (Option C):** The revised estimate for Option C depends on the staleness queue passively surfacing new chat-created pages. That passive surfacing only works for entity-type pages today. Concepts and projects — which `ChatIngestAgent` and `_detect_research_threads()` are structurally biased toward producing for genuinely new topics — are invisible.

**Work required:**

Extend `rebuild_queue()` to scan all three directories, using the same iterative pattern that `_load_tier_entities()` already uses in `almanac_generator.py:64-86`:

```python
def rebuild_queue():
    if not cache_store.redis_client:
        return

    logger.info("Rebuilding staleness priority queue...")
    try:
        wiki_dir = settings.WIKI_DATA_DIR
        slugs = []

        for page_type in ("entities", "concepts", "projects"):
            type_dir = os.path.join(wiki_dir, page_type)
            if not os.path.isdir(type_dir):
                continue
            for filename in os.listdir(type_dir):
                if filename.endswith(".md"):
                    slugs.append(filename[:-3])

        if not slugs:
            return

        mapping = {}
        for slug in slugs:
            score = compute_staleness_score(slug)
            mapping[slug] = score

        cache_store.redis_client.delete(QUEUE_REDIS_KEY)
        cache_store.redis_client.zadd(QUEUE_REDIS_KEY, mapping)
        logger.info(f"Rebuilt staleness queue with {len(mapping)} pages across entities/concepts/projects.")
    except Exception as e:
        logger.warning(f"Failed to rebuild staleness queue: {e}")
```

**Verification:** After this change, trigger `rebuild_queue()` with Redis available and confirm the log line reports pages from all three directories.

**Estimated effort:** ~15 lines. No new dependencies.

**Bonus finding that reduces Phase 1 scope:** Once this fix is in place, a brand-new entity page automatically scores at least 30 (`staleness_queue.py:42` — `days_stale = 30.0` for never-pulsed entities, with `w_t = 1.0`). That score is already high enough to surface near the top of the next `idle_ingestion_loop` batch with no additional code. The Phase 1 "impatient user immediate-pulse" path is optional, not required for the basic behavior to work.

---

### 0c. Research approval gate has no exit — live bug

**Bug location 1:** `src/agents/research_agent.py:268-271`

```python
for name, val in scores.items():
    if val < 0.4:
        human_approval_required = True
        break
```

Any entity scored below 0.4 confidence routes to the `human_approval_gate` node in the LangGraph workflow (`research_agent.py:322-331`). That node is terminal — it returns `{"human_approval_required": True}` and the graph ends. There is no downstream edge that resumes execution.

**Bug location 2:** `src/main.py` — no `POST /research/{thread_id}/approve` endpoint exists. The only approve endpoint is `/budget/approve` (`main.py:2055-2063`), which is for an unrelated budget-hold mechanism.

**Compounding factor from earlier audit:** The `last30days` adapter's JSON parsing (now fixed) was previously producing wavefunction scores flatlined near `epi ≈ 0.16` for most real entities, because the parser was reading raw JSON key fragments and bare URLs as claim text instead of actual synthesized findings. The adapter fix is already in the codebase, but **even with the fix, the trap remains for any legitimately low-confidence entity**. In a UAP/lore domain, thin evidence is common, not rare. A user asking about a marginal topic today will still hit the approval wall.

**Current effect:** Queries about low-confidence topics return `"PENDING APPROVAL: ..."` permanently. The human-in-the-loop mechanism is ceremonial — it pauses but has no resume path.

**Work required:**

Add `POST /research/{thread_id}/approve` modeled directly on the existing `/budget/approve` pattern:

```python
@app.post("/research/{thread_id}/approve", dependencies=[Depends(verify_api_key)])
async def post_research_approve(thread_id: str):
    try:
        from src.agents.research_agent import research_graph
        config = {"configurable": {"thread_id": thread_id}}
        current_state = research_graph.get_state(config)
        if not current_state or not current_state.values:
            raise HTTPException(status_code=404, detail=f"No paused research found for thread '{thread_id}'")
        updated_values = dict(current_state.values)
        updated_values["human_approved"] = True
        research_graph.update_state(config, updated_values)
        final_state = research_graph.invoke({}, config=config)
        summary = final_state.get("summary", "Approval processed.")
        return {"success": True, "thread_id": thread_id, "summary": summary}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Research approve failed: {e}")
        raise HTTPException(status_code=500, detail=f"Research approve failed: {str(e)}")
```

**Swift-side:** expose `approveResearch(threadId:)` in `BackendService`, add a button in the paused-research banner that calls it and refreshes the answer.

**Estimated effort:** ~10 lines Python, ~8 lines Swift. No new test infrastructure required — the `/budget/approve` pattern is already tested.

**Dependency note:** This should ship before Phase 2 at the latest. It could reasonably ship before Phase 1 since any contested entity a user manually researches via Phase 2's "Research Now" button could land in the approval gate.

---

### 0d. Redis `.decode()` calls on already-decoded strings — idle sentinel and staleness queue

**Bug location 1:** `src/idle_sentinel.py:71,80`

```python
# Current (broken):
if chat_ingest_active and chat_ingest_active.decode() == "running":
    ...
last_time = datetime.fromisoformat(val.decode())

# Required:
if chat_ingest_active and chat_ingest_active == "running":
    ...
last_time = datetime.fromisoformat(val)
```

**Bug location 2:** `src/staleness_queue.py:36,53`

```python
# Current (broken):
last_pulse = datetime.fromisoformat(last_pulse_val.decode())
state_label = label_val.decode() if label_val else "unverified"

# Required:
last_pulse = datetime.fromisoformat(last_pulse_val)
state_label = label_val if label_val else "unverified"
```

**Root cause:** `src/cache.py:18` initializes the Redis client with `decode_responses=True`:

```python
self.redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)
```

In `redis-py` 4.0+, this setting means all `.get()` responses are returned as `str`, not `bytes`. The `.decode()` method doesn't exist on `str`, causing `AttributeError: 'str' object has no attribute 'decode'`. The `idle_sentinel.py:88-90` exception handler catches it and returns `True` ("idle") as a fallback, so the system doesn't hard-fail — but the warning spam is persistent, and the fallback means the idle detection is running blind: it always says "idle" even when activity keys exist, because the comparison branch that would return `False` is what's throwing.

**Current effect:** 
1. Log spam on every `is_idle()` check that touches chat_ingest or query/websocket timestamps.
2. `is_idle()` returns `True` by default on exception, so the system may treat active periods as idle — causing `idle_ingestion_loop` to fire during real activity rather than only during genuine quiet windows.

**Work required:** Remove the four bare `.decode()` calls listed above. The Redis client already returns strings. No other files need changes — `src/scheduler.py:59,83` already use `isinstance(..., bytes)` guards and are safe.

**Estimated effort:** ~4 lines. No new tests required.

---

## Phase 1 — Option C: Chat-Triggered Auto-Pulse (rescoped)

**Revised from original estimate.** The deep audit found that the infrastructure for this option already mostly exists, obscured by the Phase 0b directory-scan bug. Once 0b is fixed, a chat-created page automatically scores high enough in the staleness queue to be picked up by `idle_ingestion_loop` on its next cycle. The genuinely new work is narrow.

### What already exists (no new code needed)

- `staleness_queue.compute_staleness_score()` — seeds `days_stale = 30.0` for never-pulsed entities (`staleness_queue.py:42`), which with `w_t = 1.0` gives a baseline score of 30. That is already in the high-priority range.
- `staleness_queue.record_pulse_completed()` — updates Redis sorted set after a pulse. Can be called immediately after page creation to seed the queue.
- `idle_ingestion_loop()` — already polls `get_next_batch(3)` and runs `PulseAgent.run_pulse()` for each slug.
- `PulseAgent.run_pulse()` — reads wiki frontmatter for `last30days_handles`, runs the CLI, writes snapshots, records spend.
- `ChatIngestAgent.analyze_conversation()` — already produces `suggested_pages` with titles, page types, and confidence scores.

### What is genuinely missing (new code needed)

**1. Seed the staleness queue immediately after page creation**

**Location:** `src/scheduler.py:215-222` (inside `process_eligible_conversations()`, in the loop over `result.get("suggested_pages", [])`)

After `write_page()` creates or updates a page, check if last30days is enabled. If so, call `staleness_queue.record_pulse_completed(slug)` to seed the Redis sorted set with the initial "never pulsed" score. This eliminates the wait for the next `rebuild_queue()` cycle.

```python
# After write_page() succeeds, add:
if settings.LAST30DAYS_ENABLED:
    try:
        from src.staleness_queue import record_pulse_completed
        record_pulse_completed(slug, divergence_risk=0.0, state_label="unverified")
    except Exception as queue_err:
        logger.warning(f"Failed to seed staleness queue for '{slug}': {queue_err}")
```

**Effect:** A chat-created page appears in the idle pulse queue within seconds of creation, not after the next `rebuild_queue()` cycle (which may be hours or never, since `rebuild_queue` is only called by manual API trigger, not on a schedule).

**Estimated effort:** ~5 lines.

**2. Optional "pulse now" Swift UI button**

**Location:** `Project Chicken Soup/Project Chicken Soup/Features/Wiki/Views/WikiPageDetailView.swift`

`AlmanacService.triggerPulseAsync(entityName:)` already exists at `AlmanacService.swift:156-173`. It calls `POST /pulse/{entity_name}` and returns `APIAsyncTaskResponse` with a `task_id`. Add a toolbar button on the wiki page detail view that calls this method, then polls `fetchTaskStatus(taskId)` and shows a progress indicator. On completion, refresh the page detail from the wiki.

This is the single piece of new Swift work needed for Phase 1. It is optional from a backend perspective but is the difference between "the system auto-pulses eventually" and "the user can also force the issue now."

**Estimated effort:** ~20 lines Swift.

**3. Optional wiki page enrichment after pulse**

**Location:** `src/scheduler.py` — in the `idle_ingestion_loop`, after `pulse_agent.run_pulse()` returns evidence, if the page was chat-created (source contains `conversation:{cid}`), append a `## External Evidence` section to the wiki page body with the top 3 claims by engagement count.

This is the only piece that genuinely needs new backend logic, and it is ~15 lines in the idle loop post-pulse hook. It is optional for the core auto-pulse behavior.

**Estimated effort:** ~15 lines.

### What is explicitly NOT needed (per revised audit)

- A new `AutoPulseQueue` class — `staleness_queue` already serves this role.
- A new `enqueue_pulse(slug, priority)` method — `record_pulse_completed` already produces the desired effect.
- A separate background task type — `idle_ingestion_loop` already processes the queue.
- Any changes to `_load_tier_entities()` — the selection mechanism is already dynamic over all three dirs.

### Revised Phase 1 estimate

| Component | Lines |
|---|---|
| Queue seeding in scheduler | ~5 |
| Optional Swift "Pulse Now" button | ~20 |
| Optional wiki enrichment after pulse | ~15 |
| Tests | ~10 |
| **Total** | **~50 (vs. ~120 in original scope)** |

---

## Phase 2 — Option B: Explicit "Research Now" in Graph Views

Audit confirmed: `AlmanacService.triggerPulseAsync` already exists (`AlmanacService.swift:156-173`). Backend endpoint `POST /pulse/{entity_name}` already exists and returns `AsyncTaskResponse`. No new backend code required.

**What is missing:** Wiring. The entity detail views in the graph explorer have no button to trigger a pulse, view divergence, or refresh evidence for a selected entity.

### Swift-side work

**Location 1:** `Project Chicken Soup/Project Chicken Soup/Features/KnowledgeGraph/Views/EntityDetailView.swift`

Add a `Button("Research Now")` in the toolbar section that calls `almanacService.triggerPulseAsync(entityName: entity.name)`. On success, store the `task_id` and poll `fetchTaskStatus(taskId)` on a 2-second timer. When the task completes, refresh the entity detail view and the pulse history section.

**Location 2:** `Project Chicken Soup/Project Chicken Soup/Features/KnowledgeGraph/Views/GraphExplorerView.swift`

Same button in the context menu or toolbar for the currently selected entity.

**Location 3 (optional):** Add a small `PulseStatusBadge` view that shows "Pulsing...", "Completed", or "Error" next to the entity name in the graph node.

**Dependency:** Phase 0c (approval gate). If a manually triggered pulse returns a low-confidence result that routes to human approval, the UI needs a way to resume. Shipping Phase 0c first is strongly recommended.

**Estimated effort:** ~30 lines Swift, one small reusable view for pulse status.

---

## Phase 3 — Option D: Almanac-Driven Chat Awareness

Low risk, read-only addition. No changes to existing generation or ingestion flows.

### What is missing

When a new almanac is generated, the system surfaces contested claims and newly moved entities in the HTML/MD file, but nothing propagates that information back to the chat subsystem. The conversational AI has no awareness that "today's briefing" changed anything.

### Work required

**1. Backend: `GET /almanac/summary`**

**Location:** `src/main.py`

Add a new lightweight endpoint that reads the most recent almanac HTML file and extracts structured summary data:

```python
@app.get("/almanac/summary")
async def get_almanac_summary():
    """Returns top contested claims and newly moved entities from the latest almanac."""
    try:
        from src.wiki.paths import get_almanac_dir
        ad = get_almanac_dir()
        md_files = sorted(ad.glob("*.md"), reverse=True)
        if not md_files:
            return {"date": None, "contested_claims": [], "newly_contested": 0, "entities_processed": 0}
        latest = md_files[0]
        with open(latest, "r", encoding="utf-8") as f:
            content = f.read()
        # Parse markdown for contested claims and entity headers
        contested = re.findall(r"- \*\*contested\*\*.*: (.+)", content)
        entities = re.findall(r"^## (.+)$", content, re.MULTILINE)
        return {
            "date": latest.stem,
            "contested_claims": contested[:10],
            "newly_contested": len(contested),
            "entities_processed": [e for e in entities if not e.startswith("State of the Anomaly")],
        }
    except Exception as e:
        logger.error(f"Almanac summary failed: {e}")
        return {"date": None, "contested_claims": [], "newly_contested": 0, "entities_processed": 0}
```

**2. Swift: `AlmanacService.fetchAlmanacSummary()`**

Add a method to `AlmanacService.swift` that calls `GET /almanac/summary` and stores the result. Call it on app launch and after almanac generation completes.

**3. Swift: inject into chat context**

In `BackendService.submitQuery`, before calling the API, check if a fresh almanac summary exists. If it does, prepend it to the user's query as a system-context paragraph:

```
[System context — Daily Almanac Briefing for 2026-07-13:
  - 2 newly contested claims (Bob Lazar, Element 115)
  - 5 entities processed]
```

The `QueryAgent` LLM prompt will then be aware of the latest system state without any change to the orchestrator.

**Alternative UI approach:** Show a banner in `QueryOverlayView` with a badge: "⚠️ 2 newly contested claims today". Tapping the banner scrolls to the Almanac view. This is simpler than injecting into the prompt and requires no LLM prompt changes.

**Estimated effort:** ~20 lines Python, ~15 lines Swift (for either the prompt-injection or banner approach; both are small).

---

## Phase 4 — Option A: Tight Deep-Research Mode in `/query`

Last and hardest. Explicitly gated on **Phase 0a** (history wiring) being complete, because Option A's "enriching now, resuming later" flow requires conversational state to be meaningful.

### What the user expects

> "Research Bob Lazar and what's new in the last 30 days"

The AI should:
1. Immediately return what it knows from the wiki (fast path)
2. In the background, pulse Bob Lazar via last30days for fresh evidence
3. Update the wiki page with new evidence
4. Stream an updated enriched answer when the research completes

### Why this is hard

`POST /query` is currently synchronous and returns within seconds. `PulseAgent.run_pulse()` takes 30–120 seconds (subprocess call to last30days CLI). Making this work without blocking the chat requires:
- Async task creation and tracking
- Frontend polling
- State reconciliation when the background task completes
- Handling the case where the background pulse hits human_approval_required

### Backend work

**1. Add `PulseAgent` as an `OrchestratorDeps` dependency**

**Location:** `src/agents/orchestrator.py`

```python
@dataclass
class OrchestratorDeps:
    query_agent: QueryAgent
    research_agent: ResearchAgent
    navigation_agent: NavigationAgent
    pulse_agent: PulseAgent  # new
```

**2. New intent branch: `enrich`**

Add an `"enrich"` intent to `ParsedQuery` that routes to a new `EnrichNode`. The `QueryAgent` prompt (`query_agent.py:223-247`) should return `"enrich"` when the user asks for current/recent/new information about an entity.

**3. `EnrichNode` — async handoff**

```python
@dataclass
class EnrichNode(BaseNode[OrchestratorState, OrchestratorDeps]):
    async def run(self, ctx: GraphRunContext) -> End[OrchestratorState]:
        entities = ctx.state.parsed_query.entities if ctx.state.parsed_query else []
        # Check which entities need fresh pulse data
        # Spawn background task: PulseAgent for each stale entity
        # Return immediately with task_id + current wiki answer
```

The node returns `status: "enriching"`, `task_id`, and the current wiki-based answer. The frontend polls `/research/status/{task_id}`.

**4. `POST /research/{thread_id}/approve` (already in Phase 0c)**

This endpoint also serves as the resume point for enrichment tasks that hit the approval gate.

**5. Task status endpoint**

```python
@app.get("/research/status/{task_id}")
async def get_research_status(task_id: str):
    from src.tasks import task_registry
    task = task_registry.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task.status.model_dump()
```

(`task_registry` and `AsyncTaskResponse` already exist in `src/tasks.py` and `src/models.py`.)

**6. WebSocket streaming for enrichment completion**

When the background pulse completes and wavefunction scoring is done, push an update to any open WebSocket connection for that conversation thread with the enriched answer. This requires the WebSocket handler (`main.py:1159-1193`) to maintain a `conversation_id → websocket` mapping.

### Frontend work

**Locations:** `QueryOverlayView.swift`, `ChatHistoryView.swift`

- After submitting a query that triggers enrichment, show a "Researching..." card below the answer with a progress indicator
- Poll `GET /research/status/{task_id}` every 2 seconds
- On completion, update the displayed answer and show "Enriched with N external evidence items"
- Handle `"paused_for_human_approval"` by showing an "Approve" button that calls `POST /research/{thread_id}/approve`

**Estimated effort:** ~60 lines Swift.

### Estimated backend effort

| Component | Lines |
|---|---|
| `OrchestratorDeps` + `EnrichNode` | ~50 |
| `QueryAgent` new intent + prompt | ~15 |
| `POST /research/status/{task_id}` | ~10 |
| WebSocket task-completion push | ~40 |
| Approval endpoint (Phase 0c) | ~10 |
| Tests | ~30 |
| **Total** | **~155** |

**Dependency chain:** Requires Phase 0a (history pass-through) to be complete, because the enrichment context needs conversation history to be meaningful. Depends on Phase 0c for the approval resume path.

---

## Phase Order Summary

| Phase | What | New code (approx.) | Must be before |
|---|---|---|---|
| **0a** | Fix `history=` pass-through in `/query` + WebSocket | ~10 lines | Everything |
| **0b** | Extend `rebuild_queue()` to scan `concepts/` + `projects/` | ~15 lines | Phase 1 |
| **0c** | Add `POST /research/{thread_id}/approve` | ~10 lines + ~8 Swift | Phase 2, Phase 4 |
| **0d** | Remove stale `.decode()` calls in idle sentinel / staleness queue | ~4 lines | Phase 1, Phase 3 |
| **1** | Chat → auto-pulse + optional Swift "Pulse Now" button | ~40 + ~20 Swift | Phase 0b, 0d |
| **2** | "Research Now" button in entity detail views | ~30 Swift | Phase 0c |
| **3** | Almanac summary → chat context (banner or prompt injection) | ~20 + ~15 Swift | 0d |
| **4** | Async `POST /query/enrich` with task polling + WebSocket push | ~155 + ~60 Swift | Phase 0a, 0c |

**Recommended execution order:** 0a → 0b → 0c → 0d → 1 → 2 → 3 → 4. All four Phase 0 items are small, independent, and currently active bugs. Phases 1–3 are ordered by decreasing risk / increasing complexity. Phase 4 is architecturally the hardest and is explicitly gated on 0a.

---

## Risk Register

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| **last30days API spend** | Medium | Medium | `ResourceLedger` already tracks budget. Add per-entity daily cap in Phase 1. |
| **Pulse latency degrades `/query`** | Low (Phase 4 only) | High | `/query` stays synchronous; enrichment is background-only until Phase 4. |
| **Chat-to-wiki noise** | Low | Medium | Existing filters: `WIKI_MIN_CONFIDENCE`, `CHAT_WIKI_MIN_CONVERSATION_LENGTH`, dedupe against existing pages. |
| **Almanac staleness if 0b is not fixed** | High (until 0b ships) | High | Concepts and projects structurally invisible. Fix 0b before Phase 1. |
| **User confusion about evidence source** | Medium | Low | Distinguish "wiki knowledge" from "external evidence" with clear badges in Swift UI. |
| **Approval trap for legitimately low-confidence entities** | High (until 0c ships) | High | UAP/lore domain has many thin-evidence topics. Fix 0c before Phase 2. |
| **Conversational amnesia in multi-turn** | High (until 0a ships) | High | Every persona in this plan depends on it. Fix 0a first. |
| **Idle sentinel false-idle fallback** | High (until 0d ships) | Medium | `.decode()` exceptions always fall through to `return True`, causing `idle_ingestion_loop` to fire during active periods. Fix 0d first. |

---

## Open Questions for Review

1. **Phase 0 ordering**: Should 0a (history pass-through) ship independently first, or can 0a/0b/0c/0d ship as a single small PR? 0a is the only one that touches the WebSocket handler, which has its own test surface; 0b/0d are pure backend fixes with no Swift surface.

2. **Phase 1 wiki enrichment**: The optional `## External Evidence` section append is the only piece that mutates wiki pages after pulse. Do you want wiki pages updated automatically with pulse evidence, or should that remain a manual/draft-only action?

3. **Phase 3 UX path**: Banner-in-chat vs. prompt-injection for almanac awareness. Banner is simpler and more explicit. Prompt injection is more invisible but changes LLM behavior. Which do you prefer?

4. **Phase 4 trigger detection**: Should the `"enrich"` intent be LLM-classified (QueryAgent returns it), or should it be triggered by a UI affordance (e.g. a "Research" button next to the send button)? LLM classification is more natural but more fragile; a UI button is explicit but adds friction.

5. **Resource budget for auto-pulse**: Once Phase 1 ships, any chat-created page immediately seeds the staleness queue and will be pulsed on the next idle cycle. Do you want a per-entity daily cap on auto-pulse to bound last30days API spend, or is the existing `ResourceLedger` global ceiling sufficient?

6. **Phase 0d severity**: The idle sentinel `.decode()` bug causes `is_idle()` to always return `True` on exception. This means `idle_ingestion_loop` may fire during active periods. Do you want this fixed before Phase 1 (recommended), or is the current "always idle" fallback acceptable as a temporary state?

Awaiting your review and approval on all of the above before any implementation begins.
