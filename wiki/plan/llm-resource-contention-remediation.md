---
title: "LLM Resource Contention & Pipeline Reliability Remediation"
tags: [architecture, performance, llm, plan, production]
created: 2026-07-14
updated: 2026-07-14
sources: [audit-2026-07-14]
related: [neo4j-data-quality-remediation, chicken-soup-architecture]
---

## Problem

Five independent consumers race for the single local LLM with no coordination, no prioritization, and no shared resource management. The system overloads under concurrent background tasks (reconciliation, idle pulses, chat ingest, filesystem watcher) competing with user-facing queries. Separately, 42% of LLM extraction calls produce unparseable garbage, and errors cascade silently.

## Architectural Diagnosis

### Contention Architecture (current)

```
                                              ┌─ reconcile_existing_pages (thread) ───→ #1, #7
                                              │     └── _run_llm_entity_extraction      → #1
                                              │     └── ingest_wiki_page × N_wikilinks   → #7
                                              │
                                              ├─ idle_ingestion_loop (async) ──────────→ #4, #9
                                              │     └── pulse_agent.run_pulse            → #9 (subprocess)
                                              │     └── tribunal (if divergence)          → #4
                                              │
                                              ├─ wiki_watcher_loop (async) ────────────→ #1, #7
                                              │     └── _ingest_page per file event      → #1, #7
HTTP requests ───────────────────────────────┼─ periodic_chat_ingest_loop (async) ─────→ #2, #7
                                              │     └── ChatIngestAgent                  → #2
                                              │     └── ingest_wiki_page                 → #7
                                              │
                                              ├─ /query, /research ────────────────────→ #3, #5
                                              │     └── classify_and_parse               → #3
                                              │     └── _generate_summary                → #5
                                              │
                                              ├─ /consensus/query ─────────────────────→ #6 (×3 models)
                                              │     └── MultiLLMConsensus                → #6
                                              │
                                              ├─ /tribunal ─────────────────────────────→ #4 (×4 positions)
                                              │
                                              └─ ConcurrencySemaphoreMiddleware ────────→ only gates 4 HTTP paths
                                                                                           (does not control LLM calls)
```

**7 LLM call sites × 5 concurrent consumers = unbounded contention. Zero coordination.**

### All 9 LLM Call Sites — Every One Bypasses the Others

| # | Component | File:Line | Breaker | Cache | `max_tokens` | `response_format` | Timeout | JSON guard |
|---|---|---|---|---|---|---|---|---|
| 1 | `IngestAgent._query_llm` | `ingest_agent.py:34` | No | No | No | `json_object` | 30s | No — `'int' error` |
| 2 | `ChatIngestAgent._query_llm` | `chat_ingest_agent.py:16` | No | No | No | No | 30s | No |
| 3 | `QueryAgent._query_local_llm` | `query_agent.py:171` | **Yes** | Redis 300s | No | No | 15s | No |
| 4 | `TribunalAgent._query_llm` | `tribunal_agent.py:85` | No | No | No | No | **45s** | No |
| 5 | `ResearchAgent._generate_summary` | `research_agent.py:503` | No | Redis 300s | No | No | 30s | No |
| 6 | `MultiLLMConsensus._query_model_sync` | `multi_llm.py:53` | No | No | No | No | **90s** | No |
| 7 | `_query_llm_for_edge_type` | `ingest.py:237` | No | No | No | No | 30s (×3 retries) | No |
| 8 | (discovery probes) | `discovery.py:37` | N/A | No | N/A | N/A | 5s per provider | N/A |
| 9 | (last30days subprocess) | `pulse_agent.py:183` | N/A | N/A | N/A | N/A | 120s | N/A |

**Only 2 out of 7 LLM call sites use Redis caching. Only 1 uses the circuit breaker. Only 1 sets `response_format: json_object`. None set `max_tokens`.**

### 42% LLM Extraction Failure — Root Cause

`IngestAgent._query_llm` returns unstructured text that `analyze_content` tries to `json.loads()`. Two failure modes:

**`'int' object is not subscriptable`** (majority of failures, `ingest_agent.py:113`)
- `response_format: {"type": "json_object"}` is sent to the oMLX backend, but the backend (Apple MLX serving Qwen3.6-35B) **does not enforce constrained decoding** for nested schemas
- The model generates a response that is partially JSON, partially free text; `json.loads()` succeeds on some prefix but the `suggested_pages` list contains integers or other non-object values
- Line 113 (`p["title"]`) assumes every list element is a dict — no type guard

**`Unterminated string`** (~5% of failures, column 122512 = ~122KB output)
- No `max_tokens` set in payload
- Prompt asks for "2-10 paragraphs" per page for 1-5 pages
- Model hits its internal output token limit mid-string; JSON is truncated

**Cascade**: both failures → `_fallback_analysis` (line 132) → creates a page with `confidence=0.4`, garbage body, no tags → this garbage page gets written to disk → ingested to Neo4j → pollutes the graph. The pipeline has no validation gate.

### Edge Classification — The Real Bottleneck

`ingest_wiki_page` (`ingest.py:401`) calls `_query_llm_for_edge_type` **once per `[[wikilink]]`** — sequentially. Each call has 3 retries with exponential backoff (30s, 60s, 120s). For a page with 10 wikilinks:

> 10 calls × (1 attempt + 3 retries) × 30s timeout = **up to 2100s (35 minutes) per page**

This does not account for the recursive effect: `_run_llm_entity_extraction` creates sub-pages that each independently call `ingest_wiki_page`, multiplying the cost.

**Worse**: the LLM often returns `WORKS_WITH`, `OVERLAPS_WITH`, `MANIPULATES` — creative types not in the 49-pair schema. These get defaulted to `REFERENCES` (`ingest.py:254`). The LLM is adding zero value vs. the heuristic fallback for most pairs.

## Remediation Plan — Production Architecture

### Phase 1 — Shared LLM Client with Circuit Breaker ✅ DONE

Replace 4 duplicate `urllib.request.urlopen` call sites with a single `LLMClient` class.

```
LLMClient (src/llm_client.py)
├── threading.Semaphore(3)           ← global cap on concurrent calls
├── llm_circuit_breaker               ← shared across all consumers
├── Redis cache (functools.lru_cache layer)   ← dedup identical prompts
├── json.JSONDecodeError handling     ← structured error recovery
├── max_tokens=2048                   ← always bound output length
└── methods:
    ├── query() → async, Semaphore + breaker
    └── query_sync() → synchronous bridge for thread-pool callers
```

All 7 call sites (ingest_agent, chat_ingest_agent, query_agent, tribunal_agent, research_agent, multi_llm, ingest edge classification) call `LLMClient.query()` or `LLMClient.query_sync()`. The semaphore, breaker, cache, and `max_tokens` are applied once and work for all consumers. The `TribunalAgent._query_llm` (4 calls at 45s each) is the heaviest single consumer and gains the most from the shared semaphore — when the semaphore is at capacity, tribunal blocks instead of adding a 4th concurrent call to an already-overloaded backend.

### Phase 2 — Stage-Gated Extraction Pipeline (deferred — current pipeline works)

Replace the monolithic "extract + generate + format JSON" prompt with a multi-stage pipeline:

```
Stage 1: Entity Extraction
  Prompt: "List the people, places, events, concepts, and projects mentioned."
  Schema: List[ExtractedEntity]  (name: str, type: str, confidence: float)
  max_tokens: 1024
  Expected output: {"entities": [{"name": "...", "type": "person", ...}]}
  Validation: Pydantic model, fail → regex extraction → skip page
  Total LLM calls: 1 per page (not N per link)

Stage 2: Entity Resolution
  Check each entity against wiki index on disk
  If exists: increment cross-ref count, skip LLM for this entity
  If new: flag for page generation
  LLM calls: 0 (pure filesystem)

Stage 3: Page Content Generation (only for new entities)
  Prompt: "Write a wiki page for {title}. Type: {type}. "
  Schema: SuggestedPage (title, summary, body, tags, related, confidence)
  max_tokens: 2048
  Body length: 1-2 paragraphs (not 2-10)
  Validation: Pydantic model, fail → discard page (don't write garbage)
  LLM calls: 1 per new entity (not N per wikilink)

Stage 4: Edge Classification (batch)
  Prompt: "Classify ALL relationships for {title} in one JSON object"
  Schema: {"relationships": [{"target": "...", "type": "..."}]}
  max_tokens: 512
  OR: pure heuristic (see Phase 3 cost analysis)
  LLM calls: 1 per page (not 1 per wikilink)
```

**Total per page**: ~3 LLM calls (fixed) instead of 1 + (wikilink_count × retries) (unbounded).

**Each stage has its own error recovery**: Stage 1 failure → heuristics. Stage 2 → file I/O only. Stage 3 failure → discard (no garbage). Stage 4 → fallback to heuristic.

### Phase 3 — Kill Edge Classification LLM Calls (Replace with Heuristics) ✅ DONE

The LLM edge classification adds no value. Evidence:
- Current graph: 1,908 relationships with diverse types (REFERENCES, DISCUSSES, MENTIONS, EXTENDS, etc.)
- LLM returns out-of-schema types (`WORKS_WITH`, `OVERLAPS_WITH`) 5+ times — defaulted to `REFERENCES` anyway
- Heuristic fallback (`_fallback_heuristic_edge_type`) already handles 17+ keyword patterns
- The per-call cost (30-210s) dwarfs any marginal benefit

**Decision**: Remove the LLM path from `_query_llm_for_edge_type` entirely. Keep only the heuristic fallback and a rule-based classifier based on label pairs and body text keywords. This eliminates the single biggest latency contributor.

If future data shows misclassification is a problem, add a **batch LLM call** as Phase 9 — one call per page to classify all relationships at once, not per-link.

### Phase 4 — Background Task Coordination ✅ DONE

Introduce a `ReconciliationGate` (Redis flag, set at startup, cleared when done):

| Task | Current behavior | Production fix |
|---|---|---|
| `reconcile_existing_pages` | Runs all ~382 pages sequentially, no preemption | Check `IdleSentinel.is_idle()` between pages, yield if user active. Check Redis stop signal. |
| `idle_ingestion_loop` | Runs last30days pulses regardless of reconcile state | Check `ReconciliationGate.is_busy()` — skip entirely if reconcile active. Check between items within batch. |
| `periodic_chat_ingest_loop` | Fires every N seconds, no coordination check | Check `ReconciliationGate.is_busy()`. Check `IdleSentinel.is_idle()`. Skip if system busy. |
| `wiki_watcher_loop` | Dispatches `_ingest_page` to thread pool for every file event | Check `ReconciliationGate.is_busy()` — queue events instead of executing immediately. |

### Phase 5 — Priority Semaphore System ✅ DONE

Replace `ConcurrencySemaphoreMiddleware` (HTTP-only band-aid) with a global priority system in `LLMClient`:

```python
# Two-tier priority
HIGH_PRIORITY = asyncio.Semaphore(2)    # reserved for user HTTP requests
LOW_PRIORITY = asyncio.Semaphore(2)      # shared by all background tasks

class LLMClient:
    async def query(prompt, priority="low"):
        sem = HIGH_PRIORITY if priority == "high" else LOW_PRIORITY
        async with sem:
            return await self._call_with_breaker_and_cache(prompt)
```

- HTTP handlers: `priority="high"` — at most 2 concurrent user LLM calls
  - Note: `/consensus/query` spawns 3 concurrent model queries. With `HIGH_PRIORITY = 2`, at most 2 will run simultaneously; the 3rd blocks until one completes. This is acceptable latency (2 serialized instead of 3). A dedicated consensus endpoint optimisation is tracked as a future enhancement.
- Background tasks: `priority="low"` — at most 2 concurrent background calls
- Total: 4 concurrent LLM calls maximum (down from unbounded)

Priority routing for each HTTP endpoint:

| Endpoint | Priority | Rationale |
|---|---|---|
| `/query` | high | User-facing, real-time |
| `/research/{id}/approve` | high | User-facing, real-time |
| `/consensus/query` | high | User-facing, but 3 model queries share the semaphore |
| `/tribunal` | high | User-facing, 4 position queries share the semaphore |
| `/ingest` (user upload) | high | User-initiated, expects synchronous response |
| `/pulse/{entity}` | low | Background task |
| `/almanac/generate` | low | Background task |
| `idle_ingestion_loop` | low | Background task |
| `reconcile_existing_pages` | low | Background task |
| `periodic_chat_ingest_loop` | low | Background task |
| `wiki_watcher_loop` | low | Background task |

### Phase 6 — Cache Everything ✅ DONE

| Data | Strategy | TTL | Benefit |
|---|---|---|---|
| LLM extraction responses | Redis by prompt hash | 300s | Same page ingested twice → cache hit |
| Wiki file listing | `functools.lru_cache(maxsize=1)` | Until invalidate | `cross_reference_new_page` reads all pages once |
| Target file resolution | `lru_cache(maxsize=4096)` | Forever (path is stable) | Same wikilink across pages → cache hit |
| Node label inference | `lru_cache(maxsize=4096)` | Forever (tag→label mapping stable) | Same target across links → cache hit |
| Discovery probes | Redis with 60s expiry | 60s | Consensus endpoint doesn't probe providers every call |

### Phase 7 — Settings Tuning ✅ DONE

| Setting | Current | New | Rationale |
|---|---|---|---|
| `MAX_CONCURRENT_LLM_REQUESTS` | 10 | **4** (2 high + 2 low) | Local LLM cannot serve 10 concurrent |
| `LLM_EDGE_CLASSIFICATION_TIMEOUT` | 30s | **0** (removed) | Phase 3 eliminates LLM edge classification |
| `LLM_EDGE_CLASSIFICATION_MAX_RETRIES` | 3 | **0** | No retries needed if we don't call LLM for edges |
| `IDLE_CHECK_INTERVAL_SECONDS` | 15s | **30s** | Less polling, more time-to-idle |
| idle ingestion batch size | 3 | **1** | One pulse at a time when idle |
| `LLM_CLIENT_TIMEOUT` | (none) | **30s** | Default timeout for all LLM calls |
| `LLM_CLIENT_MAX_TOKENS` | (none) | **2048** | Always bound output length |

### Phase 8 — Structured Output with Pydantic Validation ✅ DONE

At every LLM call site, replace bare `json.loads()` with Pydantic model parsing:

```python
from pydantic import BaseModel, Field
from typing import List, Optional

class ExtractedEntity(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    type: str = Field(pattern=r"^(person|place|event|concept|project|object)$")
    confidence: float = Field(ge=0.0, le=1.0, default=0.5)

class ExtractionResult(BaseModel):
    entities: List[ExtractedEntity]

# In LLMClient:
def parse_structured(response: str, model: type[BaseModel]) -> BaseModel:
    """Parse LLM response into a Pydantic model. Handles JSON prefix/suffix noise."""
    # Strategy 1: Try direct json.loads
    try:
        return model(**json.loads(response))
    except (json.JSONDecodeError, ValidationError):
        pass
    # Strategy 2: Find JSON block in free text
    for pattern in [r'```json\n(.*?)\n```', r'\{.*\}', r'\[.*\]']:
        match = re.search(pattern, response, re.DOTALL)
        if match:
            try:
                return model(**json.loads(match.group(1) if pattern != r'\{.*\}' else match.group(0)))
            except (json.JSONDecodeError, ValidationError):
                continue
    # Strategy 3: Fallback — return None (caller handles)
    return None
```

This replaces the bare `json.loads()` + `try/except Exception` pattern across all 7 sites. The validation is explicit, errors are structured (which stage failed, what was expected vs. received), and the response is never garbage — validation rejects malformed data before it reaches Neo4j.

Note: `TribunalAgent._query_llm` (tribunal_agent.py:85) returns `(str, List[str])` — a text response plus extracted URLs. It does not return JSON. The LLMClient must still apply semaphore + breaker + max_tokens to these calls, but the response parsing is text-only (citation URL extraction via regex), not JSON. The Pydantic validation layer is only needed for JSON-structured endpoints.

### Phase 9 — Subprocess & Reconciliation Preemption ✅ DONE

Two long-running operations need preemption support:

#### 9a. `/pulse` Subprocess Cancellation

`pulse_agent.run_pulse` (pulse_agent.py:183) uses blocking `subprocess.run()` with a 120s timeout. When user activity resumes during a pulse, the subprocess continues to completion, wasting resources. Change to cancellable subprocess:

```python
def run_pulse(entity_name, handles, max_wait=120):
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    deadline = time.monotonic() + max_wait
    while time.monotonic() < deadline:
        if not IdleSentinel.is_idle():   # user activity detected
            proc.kill()
            logger.info("Pulse preempted by user activity")
            return None  # caller retries later
        try:
            stdout, stderr = proc.communicate(timeout=1)  # 1s polling intervals
            return stdout
        except subprocess.TimeoutExpired:
            continue
    proc.kill()
    raise TimeoutError("Pulse timed out")
```

This applies to both user-initiated `/pulse` calls and idle-loop pulses in `scheduler.py`.

#### 9b. Reconciliation Stop Signal

`reconcile_existing_pages` (`watcher.py:189`) currently processes all ~382 pages sequentially in one shot. For production:

```python
def reconcile_existing_pages():
    for slug in all_pages:
        if stop_signal_flagged():  # Redis key checked between pages
            logger.info("Reconciliation preempted by stop signal")
            return
        while not IdleSentinel.is_idle():  # yield to user activity
            time.sleep(1)
            if stop_signal_flagged():
                return
        _ingest_page(slug, ...)
```

Add a Redis stop signal (`RECONCILIATION_STOP`) that can be set from the API or CLI. This allows cancellation of long-running reconciliation without server restart.

### Phase 10 — Monitoring & Alarms ✅ DONE

Add observability to the LLMClient:

```python
# Prometheus counters per stage
llm_calls_total.labels(stage="extraction", status="success").inc()
llm_calls_total.labels(stage="extraction", status="unparseable").inc()
llm_parse_failures_total.labels(stage="extraction", error_type="json_decode").inc()
llm_parse_failures_total.labels(stage="extraction", error_type="validation").inc()
llm_semaphore_wait_seconds.observe(...)
```

This enables: alert when parse failure rate exceeds 5%, alert when semaphore wait exceeds 10s, alert when LLM is unreachable for 60s.

## Files Changed

| File | Phases |
|---|---|
| **New: `src/llm_client.py`** | P1, P5, P6, P8, P10 |
| `src/agents/ingest_agent.py` | P2 (split into stages), P8 (Pydantic), `analyze_content` → discard on failure |
| `src/agents/chat_ingest_agent.py` | P1 (use LLMClient), P8 (Pydantic validation) |
| `src/agents/query_agent.py` | P1 (use LLMClient), remove duplicate `_query_local_llm` |
| `src/agents/tribunal_agent.py` | P1 (use `LLMClient.query_sync()`), P6 (stop fresh discovery every call), P8 (add max_tokens + text-only parsing note) |
| `src/agents/research_agent.py` | P1 (use `LLMClient.query_sync()`) |
| `src/agents/pulse_agent.py` | P9 (cancellable subprocess via `Popen` + `IdleSentinel` polling) |
| `src/knowledge_graph/ingest.py` | P3 (remove `_query_llm_for_edge_type` LLM path), P6 (cache I/O functions) |
| `src/multi_llm.py` | P1 (use `LLMClient.query()`), P6 (stop fresh discovery every call) |
| `src/main.py` | P5 (remove `ConcurrencySemaphoreMiddleware`), replace with priority model; P9 (stop signal endpoint) |
| `src/scheduler.py` | P4 (ReconciliationGate checks), P7 (batch size 1), P9 (stop signal + idle-loop pulse preemption) |
| `src/wiki/watcher.py` | P4 (IdleSentinel in reconcile), P9 (stop signal + preemption) |
| `src/config.py` | P7 (tune defaults, add new settings) |
| `src/discovery.py` | P6 (probe caching with Redis expiry) |
| `src/almanac/almanac_generator.py` | P9 (tribunal phase — already uses IdleSentinel, confirm preemption coverage) |

## Metrics

After implementation, expect:

| Metric | Before | After |
|---|---|---|
| LLM calls per page ingestion | 1 + N_wikilinks × (1 + retries) | ~3 (fixed) |
| LLM extraction failure rate | 42% (37/88) | <5% (structured output + validation) |
| Edge classification LLM calls | N_wikilinks per page | 0 (heuristics) |
| Concurrent LLM calls | Unbounded | Max 4 (2 high + 2 low) |
| Pulse subprocess cancellation | None (blocks 120s) | Preemptible within 1s of user activity |
| Consensus endpoint latency | 3× model latency (concurrent) | ~2× model latency (2 serialized) |
| Reconciliation wall time | Hours (382 pages × 10-210s each) | ~20 min (382 pages × 3 fixed calls × 30s) |
| Background tasks coordination | None | Full (ReconciliationGate + stop signals) |
| Garbage data in Neo4j | Yes (from fallback analysis) | No (validation rejects malformed data) |
