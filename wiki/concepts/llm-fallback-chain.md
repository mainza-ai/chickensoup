---
created: 2026-06-22
protected: true
related:
- local-first-llm
- llm-discovery
- omlx
- ollama
- lm-studio
sources:
- omlx-2026
- ollama-2026
- lmstudio-2026
tags:
- llm
- fallback
- discovery
- resilience
title: LLM Fallback Chain
updated: '2026-06-25'
---

# LLM Fallback Chain

The LLM fallback chain defines the order of preference for LLM providers and the retry/resilience behavior when providers fail.

## Fallback Order

1. **oMLX** (default for Mac, priority 1)
2. **Ollama** (universal, priority 2)
3. **LM Studio** (alternative, priority 3)

The chain is configurable via `.env`:

```bash
LLM_PROVIDER_ORDER=ollama,omlx,lm_studio
```

## How It Works

### Normal Flow
```
Request → oMLX (available) → Response
```

### Provider Failure Flow
```
Request → oMLX (timeout) → Retry (1s) → Retry (4s) → Retry (16s) → Ollama → LM Studio → Error
                                                                         ↓
                                                                   Circuit breaker opens
                                                                   (5 failures in 120s)
```

### Full Algorithm
1. Start with the highest-priority provider from the healthy list
2. Send the LLM request with the configured timeout
3. On success: return the response
4. On failure: retry with exponential backoff, then try the next provider
5. If all providers fail: return a structured error with details

## Timeouts

| Phase | Timeout | Cumulative |
|-------|---------|------------|
| Connection | 5s | 5s |
| Read (first token) | 10s | 15s |
| Read (total) | 30s | 45s |
| Total request | 60s | 60s |

Timeouts are per-provider. If oMLX takes 60s to time out, Ollaga still gets a fresh 60s.

## Retry Policy

| Attempt | Backoff | Jitter | Total Time |
|---------|---------|--------|------------|
| 1 | 1s (immediate) | ±0.5s | 1s |
| 2 | 4s | ±1s | 5s |
| 3 | 16s | ±2s | 21s |

After 3 retries on the same provider, move to the next provider in the chain.

## Circuit Breaker

| Parameter | Value |
|-----------|-------|
| Failure threshold | 5 failures |
| Reset timeout | 120s |
| Half-open test | 1 request |

When a provider trips the circuit breaker:
1. All subsequent requests skip that provider for 120s
2. After 120s, one request is allowed (half-open state)
3. If that request succeeds, the circuit closes (provider re-enabled)
4. If it fails, the circuit opens for another 120s

## Health Check Protocol

Each provider has a lightweight health check:

```
HEAD /v1/models
Expected: 200 OK (or 200 with body)
```

Health checks run every 30s. A failure does NOT immediately trip the circuit breaker — it sets a "degraded" flag that causes the provider to be tried last rather than skipped entirely.

## Configuration

```yaml
# config/default.yaml
llm:
  fallback:
    timeout:
      connect: 5
      read: 30
      total: 60
    retry:
      max_attempts: 3
      base_delay: 1
      max_delay: 16
      jitter: true
    circuit_breaker:
      failures: 5
      reset_timeout: 120
      half_open: true
    health_check:
      interval: 30
      failure_is_skip: false  # degraded, not removed
```

## See Also

- [[local-first-llm]] — LLM strategy overview
- [[llm-discovery]] — How providers are discovered
- [[omlx]] — oMLX provider
- [[ollama]] — Ollama provider
- [[lm-studio]] — LM Studio provider

