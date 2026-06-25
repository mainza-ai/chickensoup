---
created: 2026-06-22
protected: true
related:
- api-design
- production-readiness
- local-first-llm
sources:
- opentelemetry-2026
tags:
- observability
- opentelemetry
- metrics
- tracing
title: OpenTelemetry
updated: '2026-06-25'
---

# OpenTelemetry

Observability instrumentation for Project Chicken Soup. Implementation in `src/observability.py` + middleware in `src/main.py`.

## Custom Metrics (4)

Defined in `src/observability.py`:

1. **`agent_loop_counter`** (Counter) — Tracks agent loop iterations per status (running/complete/failed)
2. **`quantum_simulation_duration`** (Histogram) — Duration of quantum simulation jobs
3. **`cache_hits`** (Counter) — Cache hit events
4. **`cache_misses`** (Counter) — Cache miss events

## Tracing

- **HTTP spans** — All FastAPI request handlers tracked
- **WebSocket spans** — Real-time agent streaming tracked

## Middleware

`ObservabilityAndRateLimitMiddleware` in `src/main.py` attaches trace context to every HTTP request and WebSocket message.

## Configuration

Instrumentation initializes at module load time with OpenTelemetry SDK defaults. Exports can be routed to Jaeger, Zipkin, or Prometheus via environment variables.

## Use Cases

- Track agent execution frequency and failure rates
- Measure quantum simulation latency per backend
- Monitor cache effectiveness (hit/miss ratio)
- Debug request flow through the orchestrator graph

## See Also

- [[api-design]]
- [[production-readiness]]
- [[local-first-llm]]

