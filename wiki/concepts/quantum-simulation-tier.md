---
title: "Quantum Simulation Tier"
tags: [quantum, simulation, testing, ci]
created: 2026-06-22
updated: 2026-06-22
sources: []
related: [field-geometry-tensor, integration-architecture, quantum-systems]
---

# Quantum Simulation Tier

## Progression Path

Development follows four stages of quantum fidelity:

| Stage | Backend | When | Purpose |
|-------|---------|------|---------|
| 1 — Classical fallback | NumPy/SciPy, array math | Now | Correctness reference, CI without any quantum stack |
| 2 — Local simulation | Qiskit Aer, PennyLane default.qubit, CUDA-Q simulator | Now | Algorithm development, unit tests, rapid iteration |
| 3 — Cloud simulation | IBM cloud simulators, AWS Braket simulators | After local validation | Large-scale validation, noise model tuning |
| 4 — Cloud quantum hardware | IBM Quantum (Qiskit), D-Wave Leap, IonQ via cloud | After simulation passes all benchmarks | Production, real-world quantum advantage measurement |

**Each stage is a prerequisite for the next.** No stage is skipped.

## Three Simulation Modes (Stage 2)

| Mode | Backend | Grid Resolution | Shots | Use Case |
|------|--------|-----------------|-------|----------|
| Light | Qiskit Aer, PennyLane default.qubit | 8³ or 16³ | 1024 | CI, unit tests, rapid iteration |
| Medium | Same backends, higher precision | 32³ | 4096 | Development, local testing |
| Heavy | Same + GPU acceleration | 64³ or 128³ | 16384 | Production-quality results |

## Classical Fallbacks (Stage 1)

Every quantum layer has a pure-classical fallback — no quantum stack required:

| Layer | Quantum | Classical |
|-------|---------|-----------|
| Spacetime Engine (Qiskit) | Hamiltonian simulation via Aer | Einstein tensor via NumPy/SciPy |
| Field Manipulator (CUDA-Q) | Quantum kernel for perturbation | Array manipulation (NumPy) |
| AI Navigator (PennyLane) | QML variational circuit | Geodesic integration (scipy.optimize) |

The classical path is always available. It serves as:
- A **correctness reference** — quantum results must match classical results within tolerance
- A **performance baseline** — quantum advantage is measured against classical runtime
- A **zero-dependency fallback** — the system works with just `pip install numpy scipy`

## Hardware Progression (Stage 3 → 4)

| Hardware | Access | Stage | Use Case |
|----------|--------|-------|----------|
| IBM Quantum (Qiskit) | Cloud (IBM Quantum Platform) | 3-4 | Spacetime Engine circuits, Qiskit-native |
| D-Wave Advantage | Cloud (D-Wave Leap) | 3-4 | QUBO optimization for pathfinding |
| IonQ Aria/Forte | Cloud (AWS Braket, Azure Quantum) | 4 | High-precision Navigator circuits |
| NVIDIA CUDA-Q GPU | Local GPU | 2-3 | Field Manipulator acceleration |

**Cloud simulation** (Stage 3) uses the same code paths as local simulation but runs on IBM/AWS simulators with higher qubit limits and realistic noise models. This is the validation gate before touching real hardware.

## Measurement of Quantum Advantage

For each layer, we measure:

```
Quantum_advantage = Classical_runtime / Quantum_runtime
```

A layer graduates to hardware only when:
1. Classical fallback produces correct results (all benchmarks pass)
2. Local quantum simulation matches classical results within tolerance
3. Cloud quantum simulation shows > 1.5× advantage over classical
4. Cloud hardware shows > 1.0× advantage (breakeven or better)

If no layer achieves quantum advantage on real hardware, the system still works — it uses the classical fallbacks. The quantum stack is additive, not required.

## See Also

- [[field-geometry-tensor]]
- [[integration-architecture]]
- [[quantum-systems]]
