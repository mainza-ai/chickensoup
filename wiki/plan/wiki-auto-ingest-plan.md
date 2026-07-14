# Wiki Auto-Ingest — Implementation Plan

**Status:** Ready for execution  
**Dependencies:** `watchfiles` (already transitive via `uvicorn[standard]`)

---

## Problem

The system has zero capability to auto-detect new wiki pages added to the filesystem (via `git restore`, `cp`, `mv`, `scp`, etc.). A page dropped into `wiki/entities/` or `wiki/concepts/` is invisible to Neo4j, the index, the log, the staleness queue, and the pulse loop. The planned `WikiWatcher` at `src/wiki/watcher.py` was never implemented.

Separately, the idle ingestion loop spins forever on orphaned slugs (pages deleted from disk but still in the Redis staleness queue) because no code removes them, and `rebuild_queue()` is never called in production.

---

## Phase 0 — WikiWatcher (FS event monitor)

**File:** `src/wiki/watcher.py` (new)

An async filesystem watcher using `watchfiles.awatch` that monitors `wiki/{entities,concepts,projects}/*.md` for new and modified files.

### Behavior

```
new/modified .md file detected (via kqueue/inotify)
        │
        ├─ debounce 2s (batch rapid writes from git restore/rsync)
        │
        ├─ NEW file (didn't exist in previous snapshot):
        │     ├─ cross_reference_new_page(slug)
        │     ├─ ingest_wiki_page(driver, title, content) → Neo4j
        │     ├─ append_to_index()
        │     ├─ append_to_log()
        │     ├─ record_pulse_completed(slug) → staleness queue
        │     └─ invalidate_index_cache()
        │
        └─ MODIFIED file:
              ├─ re-ingest into Neo4j
              └─ record_pulse_completed(slug) → resets staleness clock
```

### Integration

- Started as `asyncio.create_task()` in FastAPI lifespan alongside `periodic_chat_ingest_loop` and `idle_ingestion_loop`
- Watched directories: `wiki/entities/`, `wiki/concepts/`, `wiki/projects/`
- Directory is configurable via `settings.WIKI_DATA_DIR`
- Graceful shutdown on `CancelledError`

### Error handling

- Individual file errors are caught and logged (don't crash the watcher)
- Neo4j unavailability is logged but doesn't block file processing
- File is tracked via an in-memory `dict[str, float]` (path → mtime) to distinguish new from modified

---

## Phase 1 — Fix orphan spins + startup sync

### 1a. Orphan removal in idle loop

**File:** `src/scheduler.py`, inside `idle_ingestion_loop()` at line ~762-765

When `read_page(slug)` returns `None` (page doesn't exist on disk):
- Log a warning
- Call `cache_store.redis_client.zrem("staleness:queue", slug)` to remove the orphan
- `continue` to next slug

### 1b. Startup queue rebuild

**File:** `src/main.py`, inside `lifespan()` at startup

After starting the watcher and loops, call `rebuild_queue()` once to sync the Redis sorted set with the actual filesystem. This clears any orphaned entries that accumulated before the fix.

---

## Phase 2 — Engineering page exclusion from pulse

**File:** `src/scheduler.py`, inside `idle_ingestion_loop()` before `run_pulse()`

After reading the page frontmatter:
- Check if tags are a subset of `ENGINEERING_TAGS` (no overlap with `CONTENT_TAGS`)
- If engineering-only: skip pulse, call `record_pulse_completed()` with a low baseline score so the page doesn't keep surfacing, but the watcher can still re-queue it on modification
- Only content pages (with `CONTENT_TAGS` overlap) and mixed pages get pulsed

---

## Phase 3 — Queue seeding completeness

### 3a. Ingest endpoints seed the queue

**File:** `src/main.py`, inside `_process_ingested_content()` or the endpoint handlers

After each page is created via `/ingest/file` or `/ingest/folder`, call `record_pulse_completed(slug)` to add it to the staleness queue.

### 3b. Daily `rebuild_queue()`

**File:** `src/scheduler.py` (or `src/main.py` lifespan)

Add a third async loop that calls `rebuild_queue()` every 24 hours. This catches any drift between Redis and the filesystem.

---

## Phase 4 — Monitoring

### 4a. Status endpoint

`GET /system/idle-ingestion/status` (or extend existing `/status`):
- Queue size (cardinality of `staleness:queue`)
- Next 3 slugs in batch
- Last run timestamp
- Watcher: files watched, files queued

### 4b. Consecutive-batch health check

Add a counter in the idle loop that tracks how many consecutive times the same batch of 3 slugs was returned. If > 5 consecutive identical batches, log a warning at ERROR level (catches the orphan-spin bug automatically).
