---
title: "Real-Time Progress Visibility Plan"
tags: [ui, observability, plan, production]
created: 2026-07-14
updated: 2026-07-14
sources: [audit-2026-07-14]
related: [neo4j-data-quality-remediation, llm-resource-contention-remediation]
---

## Problem

There are 6 concurrent background operations (reconciliation, idle ingestion, chat ingest, wiki watcher, fallback retry, daily rebuild) but zero visibility into what they're doing. When the server starts, the user sees nothing — no progress bar, no status indicators, no way to know if reconciliation is stuck or making progress.

## Design

Single Redis-backed `ProgressTracker` class. All background loops write to it at key execution points. A FastAPI endpoint exposes a flat, aggregated status dict. The UI polls it on a timer.

No WebSocket needed initially — polling every 1-2s is sufficient for human-scale progress visibility.

---

## Phase 1 — ProgressTracker Class

New file: `src/progress_tracker.py`

```python
"""
Thread-safe, Redis-backed progress tracker for all background operations.

Each section is a Redis hash keyed `progress:<section>`.
Background loops call update() at key execution points.
The UI reads via GET /status/progress.
"""
import json
import logging
import time
from typing import Optional

from src.cache import cache_store

logger = logging.getLogger("chickensoup.progress_tracker")

class ProgressTracker:
    PREFIX = "progress"

    @staticmethod
    def _key(section: str) -> str:
        return f"{ProgressTracker.PREFIX}:{section}"

    @staticmethod
    def update(section: str, **kwargs):
        """Set one or more fields on a progress section atomically."""
        if not cache_store.redis_client:
            return
        try:
            key = ProgressTracker._key(section)
            pipe = cache_store.redis_client.pipeline()
            for k, v in kwargs.items():
                if isinstance(v, (dict, list)):
                    v = json.dumps(v)
                elif isinstance(v, float):
                    v = f"{v:.3f}"
                else:
                    v = str(v)
                pipe.hset(key, k, v)
            pipe.execute()
        except Exception as e:
            logger.debug(f"ProgressTracker.update error: {e}")

    @staticmethod
    def increment(section: str, key: str, amount: int = 1):
        if not cache_store.redis_client:
            return
        try:
            cache_store.redis_client.hincrby(ProgressTracker._key(section), key, amount)
        except Exception as e:
            logger.debug(f"ProgressTracker.increment error: {e}")

    @staticmethod
    def get_all() -> dict:
        """Return all progress sections as a nested dict."""
        if not cache_store.redis_client:
            return {}
        try:
            keys = cache_store.redis_client.keys(f"{ProgressTracker.PREFIX}:*")
            result = {}
            for key in keys:
                section = key.split(":", 1)[1] if isinstance(key, str) else key.decode().split(":", 1)[1]
                raw = cache_store.redis_client.hgetall(key)
                data = {}
                for k, v in raw.items():
                    k = k.decode() if isinstance(k, bytes) else k
                    v = v.decode() if isinstance(v, bytes) else v
                    # Try to parse as JSON, fall back to string
                    try:
                        data[k] = json.loads(v)
                    except (json.JSONDecodeError, TypeError):
                        data[k] = v
                result[section] = data
            return result
        except Exception as e:
            logger.debug(f"ProgressTracker.get_all error: {e}")
            return {}
```

### Sections and Key Fields

```
progress:reconciliation
  status          → "idle" | "running" | "complete" | "stopped"
  current         → 45              (page number)
  total           → 495             (total pages)
  current_slug    → "bob-lazar"     (page being processed)
  pages_processed → 44
  errors          → 0
  started_at      → ISO timestamp
  completed_at    → ISO timestamp or null

progress:idle_ingestion
  status          → "idle" | "pulsing" | "waiting"
  current_slug    → "bob-lazar"
  pulses_success  → 12
  pulses_error    → 1
  last_result     → "success" | "error" | "preempted"
  last_run        → ISO timestamp

progress:chat_ingest
  status          → "idle" | "running" | "waiting"
  checked         → 5
  ingested        → 2
  last_run        → ISO timestamp

progress:fallback_retry
  status          → "idle" | "retrying"
  queue_size      → 3               (Redis set cardinality)
  retried         → 1
  succeeded       → 0
  failed          → 1
  last_run        → ISO timestamp

progress:llm_client
  total_calls     → 47
  success_calls   → 45
  failed_calls    → 2
  breaker_open    → false
  semaphore_usage → "2/2 high, 1/2 low"

progress:neo4j
  nodes           → 794
  relationships   → 6328
  person_count    → 24
  concept_count   → 454
  project_count   → 44
  last_updated    → ISO timestamp
```

---

## Phase 2 — Instrument All Background Loops

### reconcile_existing_pages (watcher.py)

```python
from src.progress_tracker import ProgressTracker

ProgressTracker.update("reconciliation",
    status="running", current=0, total=total_pages,
    pages_processed=0, errors=0, started_at=now())

for i, (slug, subdir) in enumerate(pages):
    ProgressTracker.update("reconciliation",
        current=i+1, current_slug=slug)
    try:
        _ingest_page(slug, subdir)
        ProgressTracker.increment("reconciliation", "pages_processed")
    except Exception:
        ProgressTracker.increment("reconciliation", "errors")

ProgressTracker.update("reconciliation",
    status="complete", completed_at=now())
```

### idle_ingestion_loop (scheduler.py)

```python
ProgressTracker.update("idle_ingestion", status="pulsing", current_slug=slug)
try:
    result = pulse_agent.run_pulse(entity_name)
    key = "pulses_success" if result.status == "success" else "pulses_error"
    ProgressTracker.increment("idle_ingestion", key)
    ProgressTracker.update("idle_ingestion", last_result=result.status, last_run=now())
finally:
    ProgressTracker.update("idle_ingestion", status="idle" if idle else "waiting")
```

### LLMClient (llm_client.py)

```python
# After each LLM call:
ProgressTracker.increment("llm_client", "total_calls")
if result is not None:
    ProgressTracker.increment("llm_client", "success_calls")
else:
    ProgressTracker.increment("llm_client", "failed_calls")

ProgressTracker.update("llm_client",
    semaphore_usage=f"{HIGH_PRIORITY._value}/{HIGH_PRIORITY._value + LOW_PRIORITY._value} concurrent")
```

Note: `threading.Semaphore._value` is the current count. We can also track via a separate counter.

### fallback_retry_loop (scheduler.py)

```python
ProgressTracker.update("fallback_retry", status="retrying", queue_size=queue_size)
# ... after retry ...
if success:
    ProgressTracker.increment("fallback_retry", "succeeded")
else:
    ProgressTracker.increment("fallback_retry", "failed")
ProgressTracker.update("fallback_retry", status="idle", last_run=now())
```

### Neo4j counts (ingest.py)

After each `ingest_wiki_page` call:

```python
# Quick counter update — avoid querying after every page
ProgressTracker.increment("neo4j", "nodes", nodes_count)
ProgressTracker.increment("neo4j", "relationships", rels_count)
```

A periodic full sync (every 60s) can run:

```python
MATCH (n) RETURN count(n) as nodes, count(()-[r]->()) as rels
```

---

## Phase 3 — FastAPI Endpoint

Add to `src/main.py`:

```python
@app.get("/status/progress")
async def get_progress():
    """Returns real-time status of all background operations."""
    from src.progress_tracker import ProgressTracker
    return ProgressTracker.get_all()
```

The endpoint returns a flat dict:

```json
{
  "reconciliation": {
    "status": "complete",
    "current": 495,
    "total": 495,
    "current_slug": "",
    "pages_processed": "495",
    "errors": "0",
    "started_at": "2026-07-14T17:45:00",
    "completed_at": "2026-07-15T02:30:00"
  },
  "idle_ingestion": {
    "status": "idle",
    "current_slug": "",
    "pulses_success": "5",
    "pulses_error": "0",
    "last_run": "2026-07-14T20:00:00"
  },
  "llm_client": {
    "total_calls": "412",
    "success_calls": "398",
    "failed_calls": "14",
    "breaker_open": "false"
  },
  "neo4j": {
    "nodes": "794",
    "relationships": "6328",
    "last_updated": "2026-07-14T20:05:00"
  }
}
```

---

## Phase 4 — UI Integration (Frontend)

The web UI needs a status panel. Recommended location: top-right of the main page or a collapsible footer.

### Polling

```javascript
// In the web UI (conceptual)
setInterval(async () => {
  const res = await fetch('/status/progress');
  const data = await res.json();
  renderProgressPanel(data);
}, 2000);  // poll every 2 seconds
```

### Display Components

**Reconciliation Progress Bar:**
```
[████████████████░░░░░░░░░] 45/495 (bob-lazar)
```

**Background Loops Status Table:**
| Operation | Status | Progress |
|---|---|---|
| Reconciliation | ✅ Complete | 495 pages, 0 errors |
| Idle Ingestion | ⏸ Idle | 5 pulses, last: 20:00 |
| Chat Ingest | ⏸ Waiting | 2 ingested |
| Fallback Retry | ▶ Retrying | 1/3 complete |
| LLM Client | 🟢 OK | 398 success, 14 failed |

**Neo4j Snapshot:**
| Nodes | Relationships |
|---|---|
| 794 | 6,328 |
| ↑ by 3 in last 60s | ↑ by 15 in last 60s |

### Status Colors

| Status | Color | Icon |
|---|---|---|
| running / pulsing / retrying | blue | ▶ |
| idle / waiting | gray | ⏸ |
| complete | green | ✅ |
| error | red | ❌ |
| stopped | orange | ⏹ |

---

## Phase 5 — Files Changed

| File | Change |
|---|---|
| **New: `src/progress_tracker.py`** | Redis-backed ProgressTracker with update/increment/get_all |
| `src/main.py` | Add `GET /status/progress` endpoint |
| `src/wiki/watcher.py` | Instrument `reconcile_existing_pages` |
| `src/scheduler.py` | Instrument `idle_ingestion_loop`, `fallback_retry_loop`, `periodic_chat_ingest_loop` |
| `src/llm_client.py` | Instrument success/failure counts, semaphore usage |
| `src/knowledge_graph/ingest.py` | Increment neo4j counters after each ingest |
| `src/wiki/watcher.py` | Add periodic Neo4j count sync (every 60s) |

---

## Phase 6 — SwiftUI App (iOS 26+, Swift 6.2)

The SwiftUI app polls `GET /status/progress` and displays a live dashboard. Built with `@Observable` for data flow, async/await for networking, and extracted subviews per the swiftui-pro conventions.

### Data Model

**File: `Sources/ProgressMonitor/Models/SystemProgress.swift`**

```swift
import Foundation

struct ProgressSnapshot: Codable, Sendable {
    var reconciliation: Section?
    var idleIngestion: Section?
    var chatIngest: Section?
    var fallbackRetry: Section?
    var llmClient: Section?
    var neo4j: Section?

    enum CodingKeys: String, CodingKey {
        case reconciliation
        case idleIngestion = "idle_ingestion"
        case chatIngest = "chat_ingest"
        case fallbackRetry = "fallback_retry"
        case llmClient = "llm_client"
        case neo4j
    }

    struct Section: Codable, Sendable {
        var status: String?
        var current: String?
        var total: String?
        var currentSlug: String?
        var pagesProcessed: String?
        var errors: String?
        var nodes: String?
        var relationships: String?

        enum CodingKeys: String, CodingKey {
            case status, current, total, errors, nodes, relationships
            case currentSlug = "current_slug"
            case pagesProcessed = "pages_processed"
        }
    }
}
```

### Observable View Model

**File: `Sources/ProgressMonitor/ViewModels/ProgressMonitor.swift`**

```swift
import Observation

@MainActor
@Observable
final class ProgressMonitor {
    var snapshot = ProgressSnapshot()
    private(set) var isConnected = false

    private let baseURL: URL

    init(baseURL: URL) {
        self.baseURL = baseURL
    }

    func startPolling() async {
        isConnected = true
        defer { isConnected = false }

        while !Task.isCancelled {
            do {
                let url = baseURL.appendingPathComponent("/status/progress")
                let (data, _) = try await URLSession.shared.data(from: url)
                snapshot = try JSONDecoder().decode(ProgressSnapshot.self, from: data)
            } catch {
                snapshot = ProgressSnapshot()
            }
            try await Task.sleep(for: .seconds(2))
        }
    }
}
```

### Views

Each section of the dashboard is an extracted subview in its own file.

**File: `Sources/ProgressMonitor/Views/ProgressDashboardView.swift`**

```swift
import SwiftUI

struct ProgressDashboardView: View {
    @State private var monitor: ProgressMonitor
    @State private var pollingTask: Task<Void, Never>?

    var body: some View {
        NavigationStack {
            List {
                ReconciliationSection(status: monitor.snapshot.reconciliation)
                IdleIngestionSection(status: monitor.snapshot.idleIngestion)
                ChatIngestSection(status: monitor.snapshot.chatIngest)
                FallbackRetrySection(status: monitor.snapshot.fallbackRetry)
                Neo4jSnapshotSection(status: monitor.snapshot.neo4j)
                LLMClientSection(status: monitor.snapshot.llmClient)
            }
            .navigationTitle("System Status")
            .toolbar {
                ToolbarItem {
                    ConnectionIndicator(isConnected: monitor.isConnected)
                }
            }
            .task {
                pollingTask = Task { [monitor] in
                    await monitor.startPolling()
                }
            }
            .onDisappear {
                pollingTask?.cancel()
                pollingTask = nil
            }
        }
    }
}
```

**File: `Sources/ProgressMonitor/Views/ReconciliationSection.swift`**

```swift
import SwiftUI

struct ReconciliationSection: View {
    let status: ProgressSnapshot.Section?

    var body: some View {
        Section {
            if let status {
                LabeledContent("Status", value: status.status ?? "—")
                if let current = status.current, let total = status.total {
                    ProgressView(
                        "\(current) / \(total) pages",
                        value: Double(current) ?? 0,
                        total: Double(total) ?? 100
                    )
                }
                if let slug = status.currentSlug, !slug.isEmpty {
                    LabeledContent("Current", value: slug)
                }
                if let errors = status.errors, errors != "0" {
                    LabeledContent("Errors", value: errors)
                        .foregroundStyle(.red)
                }
            } else {
                ContentUnavailableView(
                    "No Data",
                    systemImage: "questionmark.circle",
                    description: Text("Reconciliation has not reported yet.")
                )
            }
        } header: {
            StatusHeader(title: "Reconciliation", status: status?.status)
        }
    }
}
```

**File: `Sources/ProgressMonitor/Views/StatusHeader.swift`**

```swift
import SwiftUI

struct StatusHeader: View {
    let title: String
    let status: String?

    var icon: String {
        switch status {
        case "running", "pulsing", "retrying": "arrow.triangle.2.circlepath"
        case "complete": "checkmark.circle.fill"
        case "error": "exclamationmark.circle.fill"
        case "stopped": "stop.circle"
        default: "circle.dashed"
        }
    }

    var tint: Color {
        switch status {
        case "running", "pulsing", "retrying": .blue
        case "complete": .green
        case "error": .red
        case "stopped": .orange
        default: .secondary
        }
    }

    var body: some View {
        HStack {
            Label(title, systemImage: icon)
                .foregroundStyle(tint)
                .imageScale(.large)
            Spacer()
        }
    }
}
```

**File: `Sources/ProgressMonitor/Views/Neo4jSnapshotSection.swift`**

```swift
import SwiftUI

struct Neo4jSnapshotSection: View {
    let status: ProgressSnapshot.Section?

    var body: some View {
        Section {
            if let status {
                LabeledContent("Nodes", value: status.nodes ?? "—")
                LabeledContent("Relationships", value: status.relationships ?? "—")
            } else {
                ContentUnavailableView("No Data", systemImage: "questionmark.circle")
            }
        } header: {
            StatusHeader(title: "Knowledge Graph", status: status?.status)
        }
    }
}
```

**File: `Sources/ProgressMonitor/Views/LLMClientSection.swift`**

```swift
import SwiftUI

struct LLMClientSection: View {
    let status: ProgressSnapshot.Section?

    var body: some View {
        Section {
            if let status {
                LabeledContent("Total Calls", value: status.current ?? "—")
                if let success = status.pagesProcessed,
                   let failed = status.errors {
                    HStack {
                        Text("Success Rate")
                        Spacer()
                        Text("\(success) / \(failed) failed")
                            .foregroundStyle(failed == "0" ? .green : .red)
                    }
                }
            }
        } header: {
            StatusHeader(title: "LLM Engine", status: status?.status)
        }
    }
}
```

**File: `Sources/ProgressMonitor/Views/ConnectionIndicator.swift`**

```swift
import SwiftUI

struct ConnectionIndicator: View {
    let isConnected: Bool

    var body: some View {
        Circle()
            .fill(isConnected ? Color.green : Color.red)
            .frame(width: 10, height: 10)
            .accessibilityLabel(isConnected ? "Connected" : "Disconnected")
    }
}
```

### Architecture Notes (per swiftui-pro conventions)

1. **No `ObservableObject`** — uses `@Observable` macro with `@MainActor` as required by the data flow guide.
2. **Extracted subviews** — each section is its own `View` struct in its own file (ReconciliationSection, IdleIngestionSection, etc.) per the views guide.
3. **Structured concurrency** — polling runs via `Task { ... }` inside `.task {}` modifier, cancelled on `onDisappear`. No unstructured `Task {}` leaks.
4. **Button actions extracted** — not applicable here since there are no interactive elements, but the pattern holds.
5. **iOS 26 deployment target** — uses `ContentUnavailableView` (iOS 17+), `LabeledContent` (iOS 16+), `ProgressView` with value/total (iOS 15+).
6. **Accessibility** — `ConnectionIndicator` has `accessibilityLabel()`. All section content uses `LabeledContent` which provides automatic accessibility pairing. No icon-only buttons.
7. **Performance** — polling at 2s intervals, minimal state updates (entire snapshot replaced on each tick). `@Observable` diffing means only changed views re-render.

---

## Troubleshooting

### Status Tab Shows All "Idle"

If every section shows `Status: idle` when you expect activity, check:

```bash
# 1. Is the server running?
curl -s http://localhost:8000/status | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['status'])"

# 2. Are progress keys in Redis?
redis-cli KEYS "progress:*"

# 3. What does the raw progress data look like?
redis-cli HGETALL "progress:reconciliation"
redis-cli HGETALL "progress:idle_ingestion"
redis-cli HGETALL "progress:llm_client"
```

**Common causes:**

| Symptom | Cause | Fix |
|---|---|---|
| `progress:*` keys exist but UI shows idle | JSON decoded integers/bools instead of strings (pre-fix behavior) | Update to latest `develop` (commit 074af94 removes `json.loads` in `get_all()`) |
| No `progress:*` keys in Redis | Background operations haven't started, or Redis connection failed silently | Check server logs: `grep -i "progress\|redis" /tmp/chickensoup-server.log` |
| Sections flicker between data and idle | Reconciliation thread yields to `IdleSentinel` during user HTTP requests | Wait without making API calls; or reduce `IDLE_THRESHOLD_MINUTES` |
| Reconciliation shows `stopped` | Stop signal was set via `/wiki/reconcile-stop` | Clear signal: `redis-cli DEL reconciliation:stop` and re-trigger |
| `progress:reconciliation` present but data is stale | Server was restarted during reconciliation | Wait for next progress update (throttled to 2s polling, update only when values change) |

### Progress Data Persistence

Progress data is stored in Redis hashes with **no TTL**. Keys persist across server restarts. To reset:

```bash
redis-cli DEL progress:reconciliation progress:idle_ingestion progress:chat_ingest progress:fallback_retry progress:wiki_watcher progress:llm_client progress:neo4j
```

### Response Format

All values are strings (not integers or booleans). The Swift `APIStatusProgressSection` expects `String?` for every field:

```json
{
  "reconciliation": {
    "status": "running",
    "current": "45",
    "total": "495",
    "current_slug": "bob-lazar",
    "pages_processed": "44",
    "errors": "0"
  }
}
```

If any value appears as a non-string (`true`, `42`), the `get_all()` function has a bug — remove `json.loads` from the decode path.

### SwiftUI Specific

| Issue | Cause | Fix |
|---|---|---|
| Sections show "No Data" instead of "idle" | Using old `ContentUnavailableView` fallback | Update to latest code: replace with `LabeledContent("Status", value: "idle")` |
| `foregroundColor()` doesn't compile with ternary | Type inference fails for `foregroundStyle(condition ? .red : .green)` | Extract to a computed `Color` property, use `foregroundStyle(colorProperty)` |
| Polling task continues after view disappears | Task created with `Task {}` instead of `.task {}` | Use `.task { }` modifier — it auto-cancels on disappear |
| Tab not visible on macOS | `DetailTab` enum missing `.status` case | Add `case status = "System Status"` to `DetailTab` and corresponding ZStack entry |

## Rollup Example: What the User Sees

```
═══════════════════════════════════════════════
  SYSTEM STATUS
═══════════════════════════════════════════════

  RECONCILIATION  ✅ Complete
  495 pages processed, 0 errors
  Started 17:45 · Finished 02:30 (8h 45m)

  IDLE INGESTION  ⏸ Idle
  5 successful pulses
  Last: bob-lazar (20:00) — success

  CHAT INGEST     ⏸ Waiting
  2 conversations ingested
  Next check in 4m 30s

  FALLBACK RETRY  ▶ Retrying
  1/3 pages — 1 succeeded, 1 failed
  Last: clausius-entropy (20:03) — success

  LLM ENGINE     🟢 Online
  412 calls · 96.6% success · Breaker: closed

  KNOWLEDGE GRAPH
  794 nodes · 6,328 relationships
  +3 nodes / +15 rels in last 60s
```
