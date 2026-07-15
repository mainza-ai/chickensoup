---
title: "Production Implementation Plan — Full System Remediation"
tags: [plan, production, neo4j, timeline, search, real-time, chat, navigator, data-quality]
created: 2026-07-14
updated: 2026-07-14
sources: [full-system-audit-2026-07-14, server-logs-2026-07-14]
related: [neo4j-data-quality-remediation, llm-resource-contention-remediation, real-time-progress-visibility, full-system-audit-2026-07-14]
---

# Production Implementation Plan — Full System Remediation

Date: 2026-07-14
Scope: Complete remediation of all gaps identified in the three-part audit, plus AI Chat production-grade overhaul, Space-Time Navigator fix, server log issues, and host date/time display.

---

## Design Tenets

1. **No shortcuts.** Every layer — database, API, caching, client — gets the correct production implementation. Simplify means redo, which is not productive.
2. **Data integrity is the foundation.** The graph must be trustworthy before any feature built on top can be trusted. Stale placeholders, fabricated timestamps, and dead indexes undermine every downstream consumer.
3. **Changes propagate immediately.** A wiki page save, an entity edit, a relationship update — all must be visible in search and the graph within seconds, not minutes.
4. **Real means real.** The Status tab shows live host time, real system state, and actual timestamps from the database — not fabricated dates, not time-only format, not stale cached data.
5. **Observability is a feature, not an afterthought.** Every operation logs its duration, result, and any errors. Every failure has a trace. Every component reports its health to the dashboard.
6. **The AI Chat is the primary user interface.** It must be a production-grade chat experience — streaming responses, copy, edit, delete, conversation management, approval actions, markdown rendering, code blocks.
7. **The Navigator must work end-to-end.** The "Solve Spacetime Geodesic" button must call a real backend endpoint, display real results, and the parameters must actually drive computation.

---

## Phase 0 — Host Date/Time Display (P0, 1 session)

### 0.1 Backend — `/status/time` Endpoint
**File:** `src/main.py` — new route

Add `GET /status/time` returning host machine's current time and timezone:
```python
@app.get("/status/time")
async def get_server_time():
    now = datetime.now()
    return {
        "iso8601": now.isoformat(),
        "unix": now.timestamp(),
        "timezone": str(datetime.now(timezone.utc).astimezone().tzinfo),
        "utc_offset": now.astimezone().strftime("%z"),
    }
```
- No auth required (same as `/status` and `/health`)
- No caching (always returns current time)
- No rate limiting (added to skip list alongside `/health`, `/status`, `/status/progress`)

### 0.2 SwiftUI — `ServerClockView`
**New file:** `Features/Status/Views/ServerClockView.swift`

A dedicated view component that:
- Polls `GET /status/time` every 1 second
- Displays host time in the device's local timezone (converted from server UTC)
- Format: "Jul 14, 2026  10:32:45 AM PDT" — full date + time + timezone abbreviation
- Shows a colored dot: green if last poll < 2s ago, yellow if 2-5s, red if >5s or error
- Falls back to device local time if server unreachable (graceful degradation)

### 0.3 Placement — Where the Clock Lives

| Location | Placement |
|---|---|
| **Status tab (iPhone)** | Top of `StatusDashboardView`, inside `NavigationStack`, above the `List` |
| **Status view (Desktop)** | Top-right of the detail area, alongside the "System Status" title, or in the toolbar as a trailing item |
| **All other tabs** | Not shown (avoids clutter) — only on Status tab where system monitoring lives |

### 0.4 Implementation Details

- `ServerClockView` uses `@State private var serverTime: Date?` + polling task
- Polling: `Task { while !Task.isCancelled { await fetch(); try await Task.sleep(nanoseconds: 1_000_000_000) } }`
- The `APIClient` gets a new method `fetchServerTime() -> ServerTimeResponse?`
- `ServerTimeResponse` model in `APIModels.swift`
- Polling cancels on disappear

### 0.5 Production Considerations
- 1s polling with server round-trip is fine for a single status view — not a hot path
- If server is unreachable for >5s, fall back to `Date.now` (device time) shown with a yellow warning indicator
- Zero impact on rate limiter (skip list)

---

## Phase 1 — Neo4j Data Integrity (P0, 2 sessions)

### 1.1 Fix `/events` Endpoint to Query Event Nodes Properly

**File:** `src/main.py:1597-1684`

**Problem:** `MATCH (e:Entity)` scans all 560 nodes, then applies client-side keyword heuristics. Dates are fabricated from tag/label scanning. 162 orphaned nodes were found in server logs — nodes with no corresponding wiki file — caused by pages being deleted without cleanup.

**Production fix:**
```python
@app.get("/events")
async def get_events():
    """Retrieves all Event-labeled nodes from Neo4j with their stored dates."""
    driver = neo4j_conn.get_driver()
    if not driver:
        return []
    query = """
    MATCH (e:Event)
    RETURN e.name AS name,
           e.display_name AS display_name,
           e.date AS date,
           e.tags AS tags,
           e.sources AS sources,
           e.content_preview AS preview,
           e.confidence AS confidence,
           labels(e) AS labels
    ORDER BY e.date ASC NULLS LAST
    """
```

**Changes:**
- Query `(e:Event)` instead of `(e:Entity)` — uses the label index, O(1) vs O(n)
- Return `date` property directly from the node (or null if not set)
- Remove all hardcoded date heuristics (lines 1650-1661)
- Remove type-fabrication heuristics (lines 1663-1669) — derive from graph data
- Add `@cache_decorator(prefix="neo4j", ttl=60)` — 1-minute TTL
- Add targeted cache invalidation on entity save (see 1.6)

### 1.2 Write `date` Property from Frontmatter into Neo4j

**File:** `src/knowledge_graph/ingest.py:296-317`

**Problem:** Wiki page frontmatter has `created` and `updated` fields, but `ingest_wiki_page` never writes them to Neo4j. The `Event.date` index indexes nothing. Additionally, 16 wiki pages have malformed YAML frontmatter causing parse errors — these must be caught and handled gracefully.

**Production fix:**
```python
# Parse date from frontmatter
created_str = metadata.get("created")
updated_str = metadata.get("updated")

# Handle malformed frontmatter gracefully
if not isinstance(metadata, dict):
    logger.warning(f"Invalid frontmatter for '{title}', using defaults")
    metadata = {}

# ... rest of ingest function ...

# In the MERGE query, add:
#   n.created = $created,
#   n.updated = $updated,
#   n.date = $date
```

### 1.3 Fix Confidence for Resolved Target Nodes

**File:** `src/knowledge_graph/ingest.py:339-344`

**Problem:** Target nodes from wikilinks always get `confidence = 0.5`, even when the target page exists and resolves. 53% of nodes are at 0.5.

**Production fix:**
Set confidence=1.0 for resolved targets, 0.5 for unresolved.

### 1.4 Create Neo4j Fulltext Index

**File:** `src/knowledge_graph/schema.py`

**Production fix:**
```python
session.run("""
CREATE FULLTEXT INDEX fulltext_entity IF NOT EXISTS
FOR (n:Entity)
ON EACH [n.name, n.display_name, n.content_preview]
OPTIONS {indexConfig: {
    `fulltext.analyzer`: 'standard',
    `fulltext.eventually_consistent`: false
}}
""")
```

### 1.5 Add Search API Endpoint

**New file:** `src/knowledge_graph/search.py`

Uses `CALL db.index.fulltext.queryNodes('fulltext_entity', $query) YIELD node, score` for BM25-scored results. Route: `GET /search?q=&limit=`.

### 1.6 Per-Entity Cache Invalidation

**File:** `src/cache.py`

Replace `invalidate_all()` with:
- `invalidate_entity(entity_name)` — invalidates that entity's neighborhood + all search caches
- Still use `invalidate_all()` for bulk operations only

### 1.7 Fix Orphan Accumulation (Server Log Issue #4)

**File:** `src/wiki/watcher.py` — `_on_file_event`

**Problem:** 162 orphaned Neo4j nodes were found (nodes with no corresponding wiki file). The reconciliation process (`reconcile_existing_pages`) deletes orphans whose wiki pages were deleted from disk, but there's a race: if a page is deleted while the server is down, the reconciliation catches it, but if the page is deleted while the watcher is running, the watcher deletes from Neo4j immediately.

**Production fix:**
In `_on_file_event`, handle the `"deleted"` event type:
```python
if event_type == "deleted" and file_path.suffix == ".md":
    slug = file_path.stem
    # Remove from Neo4j
    with driver.session() as session:
        session.run("MATCH (n:Entity {name: $name}) DETACH DELETE n", name=slug.replace("-", " "))
    # Remove from staleness queue
    cache_store.redis_client.zrem("staleness:queue", slug)
```

Also add a startup check that runs deletion reconciliation synchronously before the watcher starts (already exists but confirm it catches all cases).

---

## Phase 2 — Graph Integrity & Label Accuracy (P1, 2 sessions)

### 2.1 Extend Label Inference for Missing Labels

**File:** `src/knowledge_graph/ingest.py:17-23, 133-169`

Add `Algorithm`, `Paper`, and `QuantumPlatform` to `_INFERENCE_WEIGHTS` with appropriate strong/weak keywords. Add them to the candidate labels list in `_infer_primary_label`.

### 2.2 Fix Target Node Label Inference

**File:** `src/knowledge_graph/ingest.py:337`

Instead of calling `_infer_primary_label(target_display, [])` (no tags), read tags from the target page's frontmatter via a new helper `_resolve_target_wiki_tags(name)`. Also pass the source page's body for contextual clues.

### 2.3 Expand Heuristic Edge Classification

**File:** `src/knowledge_graph/ingest.py:211-253`

Expand keyword→relationship mapping from ~30 entries to ~60, covering all 50 defined relationship types. Add keywords for CREATED, FOUNDED, DISCLOSED, CONTRADICTS, EQUIVALENT_TO, DEMONSTRATES, CAUSED, HOSTS, STORED_IN, PART_OF, and others that currently never fire.

### 2.4 Wipe and Bulk Re-Ingest

After Phase 1.1-1.6 and 2.1-2.3 are deployed.

---

## Phase 3 — Timeline Integration with Neo4j (P1, 2 sessions)

### 3.1 Store Event Dates in Neo4j

**File:** `src/knowledge_graph/ingest.py`

Store `created`, `updated`, and `date` from frontmatter into Neo4j nodes (covered in 1.2). Additionally, for Event-labeled nodes, infer date from body text and tags.

### 3.2 Build Temporal Graph Queries

**New file:** `src/knowledge_graph/temporal.py`

`get_temporal_events(driver, start_date, end_date, limit)` — queries Event nodes with date range.
`get_temporal_neighborhood(driver, entity_name)` — gets events before/after an entity.

Routes: `GET /timeline`, `GET /entities/{name}/temporal-context`

### 3.3 Cache Timeline Builder

**File:** `src/almanac/timeline.py`

Add Redis-based caching with 5-minute TTL. Invalidate on new pulse snapshot for the entity.

### 3.4 Extend Timeline Beyond 30 Days

**File:** `src/almanac/timeline.py`

Change default from 30 to 365 days. Add `include_all` flag to bypass cutoff entirely.

---

## Phase 4 — Search & Responsiveness (P1/P2, 2 sessions)

### 4.1 Full-Text Search API (Done in Phase 1.5)

### 4.2 SwiftUI Search Integration

**Files:** `Features/Wiki/Views/WikiBrowserView.swift`, `Features/KnowledgeGraph/Views/SidebarDetailsView.swift`, `Features/DataIngestion/Views/LoreRepositoryView.swift`

Wire the three search implementations to call `GET /search?q=` with debounced input. Keep client-side filtering as fallback. Add `APISearchResult` and `APISearchResponse` models.

### 4.3 Real-Time Index Notifications via SSE

**New file:** `src/main.py` — SSE endpoint

`GET /events/stream` — SSE stream that broadcasts `{type, entity, timestamp}` whenever an entity is created/updated/deleted. SwiftUI client connects via `URLSession.bytes` and invalidates local cache on each event.

### 4.4 Debounce Search Input

Add 300ms debounce to all three SwiftUI search fields using `Task.sleep(nanoseconds:)` pattern.

### 4.5 Search History

**New file:** `Shared/Services/SearchHistoryService.swift`

UserDefaults-backed recent searches (max 20). Show history on empty search focus. Clear button.

---

## Phase 5 — Real-Time Architecture (P2, 1 session)

### 5.1 Differentiated Rate Limiting

**File:** `src/rate_limiter.py`

Categorize routes: search (60 req/min), read (30 req/min), write (10 req/min), general (20 req/min default).

### 5.2 WebSocket for Graph Changes

**File:** `src/main.py` — new WebSocket route

`/ws/graph` — pushes graph change events to connected clients.

---

## Phase 6 — AI Chat Production Overhaul (P0, 3 sessions)

This is a major effort. The chat is the primary user interface and is currently V0 quality.

### 6.1 Critical Bug: Pending Approval UI Never Renders

**Files:** `ChatHistoryView.swift:16, 101-159`, `ContentView.swift`, `BackendService.swift`

**Problem:** A user switches the LLM model → model reloads → research credibility scores drop below 0.4 → the human approval gate triggers → `/query` returns `answer = "PENDING APPROVAL: ..."` → the assistant bubble shows "PENDING APPROVAL: Human approval required for credibility evaluation." text as a normal message, with NO approve button. The `onApproveResearch` closure is threaded through `ChatHistoryView → ChatBubbleView` but **no button is rendered** (line 146-159 only shows a retry button for "failed" status, nothing for approval).

**Additionally:** The `QueryResponse` model (`APIQueryResponse`) has no `thread_id` or `status` field, so the client can't even call `POST /research/{thread_id}/approve` even if a button existed. The thread_id is only available server-side in the orchestrator response, but `_build_query_response` doesn't propagate it to the client.

**Production fix — Two-part:**

**Part A — Backend (`src/main.py:543-583`, `src/models.py`):**
Add `thread_id` and `status` fields to `APIQueryResponse`:
```python
class QueryResponse(BaseModel):
    answer: str
    status: str = "completed"  # "completed" | "paused_for_human_approval" | "researching"
    thread_id: Optional[str] = None
    task_id: Optional[str] = None
    conversation_id: Optional[str] = None
    inferred_events: List[Dict] = []
    inferred_entities: List[Dict] = []
    sources: List[str] = []
```

Update `_build_query_response` to propagate `thread_id` and `status` from the orchestrator output.

**Part B — SwiftUI (`ChatHistoryView.swift`, `BackendService.swift`, `APIModels.swift`):**
1. Add `status` field to `ChatMessage` model (defined at line 3 of ChatHistoryView.swift — move this to a shared model file)
2. Detect `status == "paused_for_human_approval"` in the message response
3. Render an "Approve Research" button in `ChatBubbleView` when status is `paused_for_human_approval`
4. On tap, call `POST /research/{thread_id}/approve` with the thread_id from the message
5. After approval, poll for the completed result

```swift
// In ChatBubbleView, add after the research-status section:
if message.researchStatus == "pending_approval", let threadId = message.threadId {
    HStack(spacing: 8) {
        Button("Approve Research") {
            onApprove?(threadId)
        }
        .buttonStyle(.borderedProminent)
        .tint(.green)
        
        Button("Deny") {
            // Cancel the thread
        }
        .buttonStyle(.bordered)
        .tint(.red)
    }
}
```

### 6.2 Streaming Responses (WebSocket)

**Current:** Client polls `GET /tasks/{taskId}` every 2 seconds. Response appears all at once. No streaming.

**Production fix:**

**Backend (`src/main.py`):** New WebSocket endpoint:
```python
@app.websocket("/ws/chat")
async def websocket_chat(websocket: WebSocket):
    await websocket.accept()
    while True:
        data = await websocket.receive_json()
        # Process query, stream response tokens
        async for token in orchestrator.stream_query(data["query"]):
            await websocket.send_json({"type": "token", "content": token})
        await websocket.send_json({"type": "done", "task_id": task_id})
```

**SwiftUI (`APIClient.swift`, `BackendService.swift`):** WebSocket connection with token-by-token rendering:
```swift
func sendStreamingQuery(_ text: String) -> AsyncStream<String> {
    AsyncStream { continuation in
        Task {
            let ws = await APIClient.shared.connectWebSocket("/ws/chat")
            await ws.send(text)
            for await message in ws.messages {
                if message.type == "token" {
                    continuation.yield(message.content)
                } else if message.type == "done" {
                    continuation.finish()
                }
            }
        }
    }
}
```

`ChatBubbleView` renders tokens incrementally as they arrive.

### 6.3 Chat Message Features

**Problem:** `ChatMessage` is defined inside `ChatHistoryView.swift` (line 3), not shareable. Missing fields for copy, edit, delete, streaming state.

**Production fix:**

**New file:** `Shared/Models/ChatMessage.swift`

```swift
struct ChatMessage: Identifiable, Codable {
    var id = UUID()
    var isUser: Bool
    var text: String
    var timestamp = Date()
    var taskId: String? = nil
    var threadId: String? = nil
    var researchStatus: String? = nil  // "researching" | "completed" | "failed" | "pending_approval"
    var isStreaming: Bool = false
    var streamingText: String = ""
    var sources: [String] = []
    var canEdit: Bool { isUser }
    var canDelete: Bool { true }
    var canCopy: Bool { true }
}
```

### 6.4 ChatBubbleView Production Features

**File:** `ChatHistoryView.swift:101-165`

**Production rewrite:**

| Feature | Implementation |
|---------|---------------|
| **Copy button** | Long-press or tap-and-hold shows menu with "Copy". Or a small copy icon appears on hover. Uses `UIPasteboard.general.string = text` / `NSPasteboard.general` |
| **Markdown rendering** | Replace `Text(message.text)` with a Markdown renderer that handles `**bold**`, `*italic*`, `` `code` ``, `` ```code blocks``` ``, `[links]()`, `- lists`, `1. numbered lists` |
| **Code blocks with syntax highlighting** | Wrap code blocks in a monospaced view with a copy button and language label |
| **Timestamp** | Show `message.timestamp` in a small caption below each bubble (relative: "2m ago", or absolute on hover) |
| **Edit button (user messages)** | Tap edit → message becomes editable TextField → save updates the message locally (and optionally resubmits to server) |
| **Delete button** | Swipe-to-delete or context menu with "Delete" → removes message from list |
| **Message reactions** | Thumbs up/down buttons below assistant messages (stored in-memory, not persisted) |
| **Inline citations** | Parse `[1]`, `[2]` patterns in text and render as tappable source references |
| **Suggested replies** | After assistant response, show 2-3 quick-action chips |
| **Typing indicator** | During streaming, show animated dots at the end of the current token stream |
| **Cancel button** | During streaming/researching, show a stop button to cancel the request |
| **Error differentiation** | Separate visual treatment for timeout, server error, rate limit, and model errors |
| **Skeleton loading** | While initial message list loads, show placeholder shimmer views |

### 6.5 Conversation Management

**Current:** Messages stored in `@State private var messages: [ChatMessage] = []` in `ContentView`. Lost on app restart. No list, no persistence.

**Production fix:**

**New file:** `Shared/Services/ConversationService.swift`

```swift
@MainActor @Observable
final class ConversationService {
    private(set) var conversations: [Conversation] = []
    private(set) var activeConversationId: String?
    private let storage: UserDefaults = .standard
    
    struct Conversation: Identifiable, Codable {
        var id: String  // UUID
        var title: String  // First query or auto-generated
        var createdAt: Date
        var updatedAt: Date
        var messageCount: Int
        var modelId: String
    }
    
    func createNew() -> String { ... }
    func delete(_ id: String) { ... }
    func rename(_ id: String, to title: String) { ... }
    func switchTo(_ id: String) { ... }
    func persistMessages(_ messages: [ChatMessage], for conversationId: String) { ... }
    func loadMessages(for conversationId: String) -> [ChatMessage] { ... }
}
```

**Storage:** JSON-encoded in `UserDefaults` (simple, no CoreData dependency for conversation metadata). Messages stored per-conversation as JSON array, max 100 most recent per conversation.

**UI changes:**
- On iPhone: Add a conversations list accessible from a "☰" button in the chat header
- On Desktop: Show conversation list in a sidebar panel alongside the chat
- Conversation titles auto-generated from the first query ("What is the Vatican UFO connection?")
- Swipe-to-delete conversations
- "New Chat" button at top

### 6.6 Model Selector & Settings

**Current:** Model switching is in `SettingsView` (deep navigation). No system prompt, no parameters. User sees "pending approval" when switching because the new model resets context and credibility drops below threshold.

**Production fix:**

Add a model picker directly in the chat header (not buried in settings):
- Dropdown showing `[model name]` with a chevron
- Quick-switch between discovered models without leaving chat
- Show latency/capability hints (e.g., "Fast", "Capable", "Specialized")
- Show current model's context window size

Add LLM parameter controls:
- Temperature slider (0-1)
- Max tokens limit
- System prompt editor (per-conversation or global)

### 6.7 Chat Architectural Improvements

| Gap | Fix |
|-----|-----|
| `ChatMessage` in view file | Move to `Shared/Models/ChatMessage.swift` |
| No conversation service | Create `ConversationService` (6.5) |
| No persistence | JSON-backed storage per conversation |
| 2s hardcoded polling | Configurable interval, exponential backoff (1s, 2s, 4s, max 10s) |
| Placeholder message replacement fragile | Use `taskId` as stable key for message replacement |
| No streaming model | WebSocket `AsyncStream<String>` for token-by-token |
| No cancel | WebSocket close or `POST /tasks/{id}/cancel` |
| No error recovery in polling | Exponential backoff, surface error in UI as tappable retry |

---

## Phase 7 — Space-Time Navigator Fix (P0, 1 session)

### 7.1 Critical Bug: `/simulate` Endpoint Missing

**Problem:** `AINavigatorView.simulateTimeTravel()` calls `POST /simulate` with `{gravity, velocity, intensity}`. This route does not exist in `src/main.py`. The request gets HTTP 404. The catch block logs "Solver failed" but the user sees nothing happen.

**Root cause:** The backend has `POST /navigate` (expects `{origin, destination, target_year, energy_level}`) but the UI sends different field names and shapes. Neither endpoint was connected during development.

### 7.2 Backend Fix — Add `/simulate` Endpoint

**File:** `src/main.py`

```python
class SimulateRequest(BaseModel):
    gravity: float = Field(0.5, ge=0, le=1)
    velocity: float = Field(0.5, ge=0, le=1)
    intensity: float = Field(0.5, ge=0, le=1)


class SimulateResponse(BaseModel):
    success: bool
    gravity_metric: float
    velocity_metric: float
    field_intensity: float
    resolved_path_confidence: float
    logs: List[str]
    geometry_tensor: Optional[Dict[str, Any]] = None


@app.post("/simulate", response_model=SimulateResponse)
async def simulate_spacetime(req: SimulateRequest):
    """Run spacetime simulation with given field parameters."""
    try:
        # Map slider values (0-1) to physical parameters
        target_year = _map_velocity_to_year(req.velocity)
        energy_level = _map_intensity_to_energy(req.intensity)
        
        result = await run_spacetime_simulation(
            gravity=req.gravity,
            target_year=target_year,
            energy_level=energy_level,
        )
        return SimulateResponse(
            success=True,
            gravity_metric=result.gravity_metric,
            velocity_metric=result.velocity_metric,
            field_intensity=req.intensity,
            resolved_path_confidence=result.confidence,
            logs=result.logs,
            geometry_tensor=result.tensor,
        )
    except Exception as e:
        logger.error(f"Simulation failed: {e}")
        return SimulateResponse(
            success=False,
            gravity_metric=req.gravity,
            velocity_metric=req.velocity,
            field_intensity=req.intensity,
            resolved_path_confidence=0.0,
            logs=[f"Simulation failed: {str(e)}"],
        )
```

The `run_spacetime_simulation` function in `src/spacetime_engine/qiskit_simulation.py` already exists as `simulate_spacetime_metrics(target_year, energy_level)`. It needs to be adapted to accept gravity as a direct parameter instead of deriving it.

### 7.3 Add Origin/Destination Fields to UI

**File:** `AINavigatorView.swift`

The backend `/navigate` endpoint (and the underlying spacetime engine) needs `origin` and `destination` to compute meaningful results. The slider-only UI can't produce useful navigation.

**Production fix:**

Add two text fields above the sliders:
```swift
@State private var originEntity: String = ""
@State private var destinationEntity: String = ""
```

With autocomplete from local SwiftData entities (reuse `SidebarDetailsView` pattern). The full solve flow becomes:

1. User enters origin entity, destination entity
2. User adjusts sliders (gravity, velocity, field density)
3. User taps "Solve Spacetime Geodesic"
4. UI sends `POST /simulate` with `{origin, destination, gravity, velocity, intensity}`
5. Backend resolves entities → runs Qiskit simulation → CUDA-Q field manipulation → PennyLane path optimization
6. Response includes `{path, warp_factor, divergence_risk, geometry_tensor, logs}`
7. UI updates: 3D grid warps to show the path, log stream shows each computation step, result metrics display

### 7.4 Enhanced Result Display

**Current:** After solve, slider values update and logs append. That's it.

**Production fix:**

Add a result summary section below the button:
```swift
if let result = simulationResult {
    VStack(alignment: .leading, spacing: 4) {
        Text("Path Result")
            .font(.caption).bold()
            .foregroundStyle(.secondary)
        
        HStack {
            Label("Confidence", systemImage: "chart.bar.fill")
            Spacer()
            Text(result.confidence, format: .percent)
                .foregroundStyle(result.confidence > 0.7 ? .green : .orange)
        }
        
        HStack {
            Label("Warp Factor", systemImage: "speedometer")
            Spacer()
            Text(result.warpFactor, format: .number.precision(.fractionLength(3)))
        }
        
        if let tensor = result.geometryTensor {
            Label("Geometry Tensor", systemImage: "square.grid.3x3")
            Text(tensor.description)
                .font(.system(.caption2, design: .monospaced))
        }
    }
    .padding()
    .background(DesignConstants.controlBackground, in: RoundedRectangle(cornerRadius: 8))
}
```

### 7.5 UI Error Handling

**Current:** Error appends to log stream as "Solver failed: ..." — no visual differentiation from success logs.

**Production fix:**
- Add `@State private var simulationError: String?` 
- Show error as a red banner above the button
- Differentiate error types: network error vs model error vs computation error
- Add retry button on error

---

## Phase 8 — Server Log Issues (P1, 1 session)

Issues found in server logs during audit.

### 8.1 LLM `parse_structured` Failures (49 occurrences)

**Problem:** `src/llm_client.py` — `parse_structured` fails for `IngestResponse` model because the LLM returns JSON arrays instead of objects. The `**` unpacking in `src/agents/ingest_agent.py` can't handle lists.

**Root cause:** The LLM prompt doesn't enforce a single-object response. The LLM returns a list of suggested pages (which is conceptually correct since `IngestResponse.suggested_pages` is a list). But `parse_structured` tries to parse the entire LLM output as the Pydantic model, not as JSON containing the model.

**Production fix:** 
- Add explicit JSON schema in the LLM prompt (output must be a JSON object with `suggested_pages: [...]`)
- Add post-processing in `parse_structured` to handle list responses: if the parsed result is a list, wrap it in `{"suggested_pages": result}`
- Add better logging that includes the raw LLM response (not just "all strategies failed")

### 8.2 LLM Entity Extraction Failures (85 instances)

**Problem:** Same root cause as 8.1 — `parse_structured` returns a list, `_run_llm_entity_extraction` does `IngestResponse(**result)` which fails because `result` is a list, not a dict.

**Production fix:** Same as 8.1 — handle list wrapping in `parse_structured` or in the caller.

### 8.3 YAML Frontmatter Errors (16 pages)

**Problem:** 16 wiki pages have malformed YAML frontmatter. The `yaml.safe_load` in `parse_markdown_frontmatter` throws, resulting in empty metadata and default tags/sources.

**Production fix:** 
- Add a YAML repair step: try `yaml.safe_load`, on failure try `yaml.safe_load_all` (multi-document), on failure try regex-based key-value extraction
- Log the specific YAML parse error with the page slug for manual fixing
- Add a lint command that validates all frontmatter across the wiki

### 8.4 Starlette Deprecation Warning

**File:** `src/main.py:769`

Replace `HTTP_422_UNPROCESSABLE_ENTITY` with `starlette.status.HTTP_422_UNPROCESSABLE_CONTENT`.

### 8.5 RedisSearch Not Available

**Problem:** Redis checkpointer falls back to `MemorySaver` because RedisSearch (`FT._LIST`) is not available.

**Production fix:** Install `redis-stack-server` or `redistimeseries` module. Or switch to a simple Redis key-value checkpointer that doesn't require RedisSearch (store serialized state under a hash key).

### 8.6 OpenTelemetry Log Noise

**Problem:** ~99% of server log output is OpenTelemetry JSON traces/metrics. Actionable log lines are buried.

**Production fix:**
- Set OpenTelemetry export to batch with longer interval (60s → 300s)
- Or export to a separate file (otel.log) that doesn't mix with app logs
- Or disable the ConsoleSpanExporter in production and use a real OTEL collector
- Reduce `ConsoleMetricExporter` verbosity — only export metric snapshots, not per-request traces

### 8.7 Staleness Queue Orphan

**File:** `src/scheduler.py`

`microsoft-q` was stuck in the staleness queue. Already detected by the consecutively-identical-batch check. The fix in `_on_file_event` (Phase 1.7) prevents future orphans.

---

## Phase 9 — SwiftUI Unification (P2, 1 session)

### 9.1 Unified Search Component

**New file:** `Features/Search/Views/SearchBarView.swift`

Reusable search component replacing all 3 implementations. Configurable debounce, search history integration, server-side suggestions.

### 9.2 Date/Time on All Status Sections

**Files:** `Features/Status/Views/*SectionView.swift`

Replace the 5 duplicate `formatTimestamp()` implementations with a shared `StatusDateFormatter` enum. Use relative formatting: "2m ago" (<1hr), "2:30 PM" (today), "Jul 13, 2:30 PM" (older), "—" (no data).

### 9.3 Move ChatMessage to Shared Model

Move from `ChatHistoryView.swift` to `Shared/Models/ChatMessage.swift`. Add fields for streaming state, approval state, thread ID, sources, etc.

### 9.4 Move BackendService to Actor-Based Concurrency

**Current:** `BackendService` is `@MainActor @Observable` — all network calls run on the main actor. Heavy operations can block the UI.

**Production fix:** Keep `@Observable` for UI-bound state but use a separate non-isolated actor for network operations:
```swift
actor NetworkActor {
    func submitQuery(...) async throws -> QueryResponse { ... }
    func fetchStatusProgress() async throws -> APIStatusProgress { ... }
}
```

---

## Phase 10 — Production Hardening & Testing (P1/P2, 2 sessions)

### 10.1 Neo4j Connection Resilience

**File:** `src/knowledge_graph/connection.py`

Add connection pooling, health check pings, circuit breaker for Neo4j operations. Graceful degradation: if Neo4j is down, search falls back to wiki index.

### 10.2 Fulltext Index Maintenance

Add periodic probe to verify fulltext index health. Log and alert on stale results.

### 10.3 Testing Coverage

| Test | What it covers |
|------|---------------|
| Search endpoint | `GET /search?q=bob` returns 200 with scored results |
| Fulltext index creation | Query `db.indexes()` for `fulltext_entity` |
| `/events` returns only Event nodes | Assert no non-Event nodes in results |
| Date properties written on ingest | After ingest, check `n.date` is not null |
| Per-entity cache invalidation | Ingest A, search for A+B, verify A appears, B still cached |
| Timeline cached and invalidated | First call slow, second fast; pulse write invalidates |
| Host clock endpoint | `GET /status/time` returns valid ISO8601 |
| SSE broadcasts on entity save | Connect to `/events/stream`, ingest page, verify event |
| Differentiated rate limiting | Search requests don't count toward write quota |
| Chat approval flow | Submit query with force_approval → get pending → approve → get result |
| Streaming chat | Connect to `/ws/chat`, send query, receive token stream |
| `/simulate` endpoint | POST with gravity/velocity/intensity → returns valid response |
| Space-Time Navigator full flow | Solve with origin/destination → path result displayed |
| YAML frontmatter repair | Page with broken YAML → graceful fallback without crash |
| LLM parse_structured list wrapper | LLM returns list → wrapped into `{"suggested_pages": [...]}` |
| Conversation persistence | Save messages → restart app → messages restored |
| Message copy/delete/edit | Verify each action produces correct state change |
| Orphan cleanup on file delete | Delete wiki page → Neo4j node removed |
| Staleness queue no orphans | Delete page → queue entry removed |

### 10.4 Smoke Test Updates

Update `wiki/plan/INTENSIVE-SMOKE-TEST-PLAN.md` with test cases for all new endpoints and features.

---

## Implementation Order Summary

| # | Phase | Sessions | Dependencies | Priority |
|---|---|---|---|---|
| 0 | Host date/time display | 1 | None | P0 |
| 1.1 | Fix `/events` endpoint | 0.5 | None | P0 |
| 1.2 | Write date property | 0.5 | None | P0 |
| 1.3 | Fix target confidence | 0.5 | None | P0 |
| 1.4 | Fulltext index | 0.5 | None | P0 |
| 1.5 | Search API | 0.5 | 1.4 | P0 |
| 1.6 | Per-entity cache invalidation | 0.5 | None | P0 |
| 1.7 | Fix orphan accumulation | 0.5 | None | P0 |
| 2.1 | Extend label inference | 0.5 | None | P1 |
| 2.2 | Fix target label inference | 0.5 | 2.1 | P1 |
| 2.3 | Expand edge heuristics | 0.5 | None | P1 |
| 2.4 | Wipe/re-ingest | 1 | 1.1-1.6, 2.1-2.3 | P1 |
| 3.1-3.4 | Timeline integration | 2 | 1.2, 1.6 | P1 |
| 4.1-4.5 | Search & responsiveness | 2 | 1.4, 1.5 | P1 |
| 5.1-5.2 | Real-time architecture | 1 | None | P2 |
| 6.1 | Fix approval UI | 1 | None | P0 |
| 6.2 | Streaming chat WebSocket | 1 | 6.1 | P0 |
| 6.3-6.4 | Chat message features | 1 | 6.1 | P1 |
| 6.5 | Conversation management | 1 | None | P1 |
| 6.6 | Model selector in chat | 0.5 | None | P1 |
| 7.1-7.5 | Space-Time Navigator | 1 | None | P0 |
| 8.1-8.7 | Server log issues | 1 | None | P1 |
| 9.1-9.4 | SwiftUI unification | 1 | 6.3 | P2 |
| 10.1-10.4 | Testing & hardening | 2 | All above | P1 |

**Total: ~18 sessions**

---

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Wipe/re-ingest fails mid-way | Low | Medium | Source wiki files are intact; re-run the wipe |
| Fulltext index slows writes | Low | Low | Index is small (<1MB for 560 nodes); synchronous index update adds <1ms per write |
| SSE clients consume memory | Low | Medium | Dead client detection via queue full + periodic heartbeat |
| Rate limit change breaks existing clients | Low | High | Client-side retry handles 429; announce change; keep default as fallback |
| Streaming WebSocket adds complexity | Medium | Medium | Fall back to polling if WebSocket fails; keep polling path as backup |
| Approval gate unwired for months — users may rely on "PENDING APPROVAL" text as a feature | Medium | Low | Approval gate is a gating mechanism — showing text without action is worse than hard-failing. Fix is additive. |
| `/simulate` endpoint duplicates `/navigate` | Low | Low | `/simulate` is the UI-facing endpoint; `/navigate` stays as the internal agent-facing path. Both work. |
