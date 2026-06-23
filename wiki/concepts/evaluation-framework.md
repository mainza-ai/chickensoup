---
title: "Evaluation Framework"
tags: [evaluation, framework, testing, ci]
created: 2026-06-22
updated: 2026-06-22
sources: [evaluation-2026]
related: [production-readiness, quantum-simulation-tier, integration-architecture, field-geometry-tensor]
---

# Evaluation Framework

## The Problem

Time travel simulation has no empirical ground truth — we cannot test it against real time travel. Evaluation must therefore measure **internal consistency**, **physical plausibility**, and **reproducibility** rather than correctness against observation.

This framework defines how the system is evaluated at every level, from individual quantum circuits to end-to-end query responses.

## Concrete Metrics

### Quantum Algorithm Fidelity
| Metric | Target | Measurement |
|--------|--------|-------------|
| HHL linear system solution | > 0.95 fidelity | Compare output state to analytic solution |
| Hamiltonian simulation | > 0.90 fidelity | Overlap with classical PDE solver |
| Variational circuit convergence | < 1% variance across runs | Repeat 10 runs, measure std dev |
| Metrics above apply at "light" mode resolution (8³ grid, 1024 shots). Heavy mode targets +0.02 on each. |

### Metric Tensor Validity
| Check | Criterion | Pass/Fail |
|-------|-----------|-----------|
| Lorentzian signature | (-, +, +, +) at every grid point | Blocking |
| Non-degenerate | det(g_μν) < 0 everywhere | Blocking |
| Positive lapse | α > 0 everywhere | Blocking |
| Symmetry | γ_ij = γ_ji (within 1e-10) | Blocking |
| Energy conditions | T_μν satisfies weak energy condition | Warning (exotic matter flagged) |

### Path Optimality
| Metric | Target | Test Case |
|--------|--------|-----------|
| Geodesic deviation | < 1% from known solution | Schwarzschild, Kerr spacetimes |
| Path length variation | < 5% across runs | Same start/end, different random seeds |
| Cost function convergence | Monotonic decrease | Verify optimizer isn't diverging |
| CTC existence | At least one valid CTC | For spacetimes known to permit them |

### LLM Accuracy
| Task | Metric | Target |
|------|--------|--------|
| Entity extraction | Precision / Recall / F1 | > 0.85 F1 |
| Relationship classification | Accuracy (typed edges) | > 0.80 |
| Edge confidence calibration | Expected Calibration Error | < 0.10 |
| Response groundedness | % of claims traceable to source | > 95% |

### System Performance
| Endpoint | Light Mode | Medium Mode | Heavy Mode |
|----------|-----------|-------------|------------|
| POST /query | < 5s | < 15s | < 30s |
| POST /navigate | < 10s | < 30s | < 5min |
| GET /graph/{entity} | < 200ms | < 200ms | < 200ms |
| POST /ingest | < 30s | < 60s | < 5min |

## Benchmark Suite

A set of known test cases with analytic solutions. Each layer runs against these to validate correctness:

### Spacetime Engine Benchmarks
| Test Case | Type | Expected Output |
|-----------|------|-----------------|
| Minkowski metric | Flat spacetime | g_μν = diag(-1, 1, 1, 1), zero curvature |
| Schwarzschild | Non-rotating black hole | Known exterior metric, event horizon at r = 2M |
| Kerr | Rotating black hole | Known metric with frame dragging |
| FRW | Expanding universe | Time-dependent scale factor a(t) |
| Alcubierre (analytic) | Warp metric (incompressible) | Known shift vector β^i |

### Field Manipulator Benchmarks
| Test Case | Perturbation | Expected Output |
|-----------|-------------|-----------------|
| Zero perturbation | δg = 0 | Output = input (identity test) |
| Flat boost | Lorentz transform | Metric consistent with boosted frame |
| Linearized gravity | Small δg | Linearized Einstein equations satisfied |
| Bubble test | Spherical perturbation | Metric remains valid, no singularities |

### AI Navigator Benchmarks
| Test Case | Path | Expected Output |
|-----------|------|-----------------|
| Minkowski geodesic | Straight line | Path is straight, proper time = coordinate time |
| Schwarzschild orbit | Bound orbit | Closed elliptical orbit (precessing) |
| Kerr light ring | Photon orbit | Circular orbit at r = 1.5 R_s |
| CTC verification | Closed timelike curve | Path returns to same spacetime point |

## Evaluation Protocol

### Per-PR (Light Mode, CI)
- All benchmark test cases at 8³ resolution, 1024 shots
- All metric validity checks
- LLM extraction F1 on held-out wiki pages
- End-to-end latency within limits
- **Result:** Must pass all blocking checks. Warnings reviewed by human.

### Weekly (Medium Mode, Scheduled)
- Full benchmark suite at 32³ resolution, 4096 shots
- Cross-layer consistency (same metric through all three layers)
- Comparison to previous week's results (regression detection)
- **Result:** Regression report. Any metric degrading > 5% triggers review.

### Pre-Release (Heavy Mode, GPU-Accelerated)
- Full benchmark suite at 64³+ resolution, 16384 shots
- All test cases, all layers, end-to-end
- 10 runs with different random seeds
- **Result:** Release readiness score. Must exceed all targets.

## Pass/Fail Criteria

| Level | Criteria | Action |
|-------|----------|--------|
| **Blocker** | Metric validity fails, API returns 500, benchmark crash | PR not merged, release blocked |
| **Warning** | Path optimality > 5%, LLM F1 < 0.80, latency > 2x target | Flag for human review, non-blocking |
| **Info** | Latency regression > 20%, minor fidelity drop | Logged, tracked for trend |

## See Also

- [[production-readiness]] — Production checklist
- [[quantum-simulation-tier]] — Light/medium/heavy modes
- [[field-geometry-tensor]] — Validation rules for metric tensors
- [[integration-architecture]] — How layers compose (affects integration tests)
