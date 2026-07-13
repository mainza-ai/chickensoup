---
title: "Logging & Observability"
tags: [logging, observability, tracing, metrics, opentelemetry]
created: 2026-06-22
updated: 2026-06-26
sources: [opentelemetry-2026]
related: [opentelemetry, production-readiness, agent-architecture, redis]
---

# Logging & Observability

Structured logging and OpenTelemetry-based observability for the time travel system. Implementation in `src/observability.py` (57 lines) and `logging` module throughout the codebase.

## Logging Setup

All modules use the standard Python `logging` module with module-specific loggers:

| Module | Logger Name |
|--------|-------------|
| API auth | `chickensoup.auth` |
| Tasks (Celery) | `chickensoup.tasks` |
| Neo4j ingestion | `chickensoup.neo4j.ingest` |
| Wiki backup | `chickensoup.wiki.backup` |
| Wiki cleanup | `chickensoup.wiki.cleanup` |
| Observability | `chickensoup.observability` |

## OpenTelemetry Configuration

### Tracing

```python
provider = TracerProvider()
processor = SimpleSpanProcessor(ConsoleSpanExporter())
provider.add_span_processor(processor)
trace.set_tracer_provider(provider)

tracer = trace.get_tracer("chickensoup.tracer")
```

- **Provider:** `TracerProvider` with `SimpleSpanProcessor`
- **Exporter:** `ConsoleSpanExporter` (outputs to stdout)
- **Tracer name:** `chickensoup.tracer`

### Metrics

```python
metric_reader = PeriodicExportingMetricReader(ConsoleMetricExporter())
meter_provider = MeterProvider(metric_readers=[metric_reader])
metrics.set_meter_provider(meter_provider)

meter = metrics.get_meter("chickensoup.metrics")
```

- **Provider:** `MeterProvider` with `PeriodicExportingMetricReader`
- **Exporter:** `ConsoleMetricExporter` (outputs to stdout)
- **Meter name:** `chickensoup.metrics`

## Application Metrics

| Metric | Type | Name | Description |
|--------|------|------|-------------|
| `agent_loop_executions` | Counter | `agent_loop_executions` | Number of times agent loop has executed |
| `quantum_simulation_duration` | Histogram | `quantum_simulation_duration_seconds` | Duration of quantum spacetime simulation runs |
| `cache_hits` | Counter | `cache_hits_total` | Total cache hits |
| `cache_misses` | Counter | `cache_misses_total` | Total cache misses |

## Integration Points

### Agent Observability

The orchestrator logs routing decisions, confidence gate status, and node execution. Each agent (Query, Research, Navigation, Status) produces log entries showing:
- Input parameters
- LLM provider used
- Confidence scores
- Routing decisions
- Timeout status

### API Observability

Each HTTP request is logged with:
- Method and path
- Request/response status codes
- Processing time
- Error details (if any)

### WebSocket Observability

The `/ws/agent` WebSocket endpoint logs:
- Connection establishment
- Message streaming chunks
- Disconnection events
- Error states

## Redis Metrics Integration

The Redis cache layer (`src/cache.py`) integrates with observability:
- `cache_hits` counter incremented on cache hits
- `cache_misses` counter incremented on cache misses
- Cache namespace prefixes: `cache:neo4j:*`, `cache:llm:*`, `cache:mcp:*`

## Configuration

All observability settings are controlled by the OpenTelemetry SDK defaults. Console exporters write to stdout, which can be:
- Piped to log aggregation services (Datadog, New Relic, etc.)
- Captured by Docker/logging drivers
- Redirected to files for local debugging

## See Also

- [[opentelemetry]] — OpenTelemetry framework
- [[production-readiness]] — Production readiness checklist
- [[redis]] — Caching layer with metrics integration
- [[agent-architecture]] — Agent observability integration points
