---
title: "Quantum Job Scheduler"
tags: [quantum, scheduling, hardware, ibm, dwave, ionq]
created: 2026-06-23
updated: 2026-06-23
sources: []
related: [quantum-simulation-tier, time-travel-machinery-architecture, api-design, field-geometry-tensor]
---

# Quantum Job Scheduler

## Purpose

The Quantum Job Scheduler submits and manages spacetime simulation jobs across quantum hardware providers. It is the bridge between the local simulation tier and real quantum hardware.

## Implementation

Located in `src/quantum_scheduler.py`. The `QuantumJobScheduler` class:

1. **Submits** jobs to the configured backend (IBM Quantum, D-Wave, IonQ, or local simulation)
2. **Polls** job status via `get_job_status(job_id)`
3. **Returns** results when complete with timing metadata

## Supported Backends

| Backend | Provider | Hardware Type | Status |
|---------|----------|---------------|--------|
| `ibm` | IBM Quantum | Superconducting | Requires token |
| `dwave` | D-Wave Leap | Quantum annealing | Requires token |
| `ionq` | IonQ | Trapped ion | Requires token |
| `simulated` | Local | NumPy fallback | Always available |

## API Endpoints

**POST** `/quantum/schedule` — Submit a spacetime simulation job. Request includes `target_year`, `energy_level`, and optional `frequency`.

**GET** `/quantum/job/{job_id}` — Poll job status and retrieve results. Returns `status: pending|completed|failed`, `result_url`, and `timing`.

## Lifecycle

```
Schedule → Validate → Dispatch → Poll → Complete
  │          │            │         │
  │          │         ┌──┴──┐      │
  │          │    IBM  D-Wave IonQ  │
  │          │         └─────┘      │
  │          │                      │
  └──────────┴──────────────────────┘
            ↗                    ↖
      Config screen        Status screen
      (SwiftUI)            (SwiftUI)
```

## Integration

The scheduler is called by the SwiftUI Config screen (`saveConfig`) and the Celery task `async_navigate` in `src/tasks.py`.

## See Also

- [[quantum-simulation-tier]]
- [[time-travel-machinery-architecture]]
- [[field-geometry-tensor]]
- [[api-design]]
