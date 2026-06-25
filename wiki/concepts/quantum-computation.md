---
title: "Quantum Computation"
tags: [quantum, computing, foundation]
created: 2026-06-22
updated: 2026-06-22
sources: [Nielsen-Chuang-2010, Babbush-2023]
related: [quantum-algorithms, quantum-systems, quantum-field-theory, field-geometry-tensor, integration-architecture]
---

# Quantum Computation

## What Makes Quantum Computation Different

Quantum computation uses three phenomena that have no classical analogue:

| Phenomenon | Classical Bit | Qubit |
|-------------|---------------|-------|
| **State** | 0 or 1 | α|0⟩ + β|1⟩ (any point on Bloch sphere) |
| **Entanglement** | No correlation beyond statistics | Non-separable joint states (Bell pairs) |
| **Measurement** | Read state, no change | Superposition collapses to 0 or 1 with probability α², β² |

### The Bloch Sphere
A qubit's state is a point on the surface of a unit sphere:
- |0⟩ at north pole, |1⟩ at south pole
- Any point on the sphere is a valid superposition
- Operations (gates) are rotations of the sphere
- Measurement projects onto the Z-axis (|0⟩ or |1⟩)

### Key Gates
| Gate | Action | Matrix |
|------|--------|--------|
| Hadamard (H) | Creates superposition | 1/√2 [[1,1],[1,-1]] |
| Pauli-X (NOT) | Flips |0⟩↔|1⟩ | [[0,1],[1,0]] |
| CNOT | Entangles two qubits | [[1,0,0,0],[0,1,0,0],[0,0,0,1],[0,0,1,0]] |
| Phase (S, T) | Adds relative phase | [[1,0],[0,e^iθ]] |

## The Circuit Model

Quantum algorithms are expressed as **circuits**: sequences of gates applied to qubits, followed by measurement.

```
|0⟩ ——— H ——— • ——— H ——— M —
               |
|0⟩ ——— H ——— ⊕ ——— H ——— M —
```

This circuit: applies Hadamards to two qubits, entangles them with CNOT, then measures both. The result is a Bell state — a maximally entangled pair.

## Why It Matters for This Project

Three layers of the time travel machinery map to distinct quantum computation paradigms:

### Spacetime Engine (Qiskit) — Hamiltonian Simulation
Simulating the Einstein field equations (G_μν = 8πT_μν) is a Hamiltonian simulation problem. The spacetime metric is encoded as a quantum Hamiltonian, and the circuit simulates its time evolution. Babbush et al. (2023) proved exponential quantum speedup for coupled oscillator systems — spacetime itself is a coupled oscillator system.

### Field Manipulator (CUDA-Q) — Hybrid Quantum-Classical
The Field Manipulator uses CUDA-Q's hybrid quantum-classical computing model. Classical GPU kernels compute the base metric; quantum kernels compute the perturbation δg. The hybrid model allows quantum circuits for the field transformation while using classical resources for everything else.

### AI Navigator (PennyLane) — Variational Quantum Algorithms
The Navigator uses variational quantum circuits — a parameterized quantum circuit trained by classical optimization. The circuit learns to map perturbed metrics to optimal paths. This is a quantum machine learning approach (see [[quantum-machine-learning]]).

## Current Capabilities and Limits

| Aspect | Current State | Impact on Project |
|--------|--------------|-------------------|
| Qubit count | 100-1000 (NISQ) | Limits circuit complexity; use amplitude encoding |
| Gate fidelity | 99.9% (superconducting), 99.99% (trapped ion) | Requires error mitigation for deep circuits |
| Decoherence | ~100μs (superconducting), ~1000s (trapped ion) | Limits circuit depth; use shorter circuits |
| Error correction | Not yet practical for our circuit sizes | Simulate with noise models (Qiskit Aer) |

**The practical path:** All three layers simulate on classical hardware during development (Qiskit Aer, PennyLane default.qubit, CUDA-Q simulator). Real quantum hardware (D-Wave, IonQ) is added in Phase 4 after algorithm validation. See [[quantum-simulation-tier]] for the three-mode simulation strategy.

## Project Chicken Soup Integration

- **Layer mapping:** All three layers use quantum computation via their respective platforms
- **Simulation tier:** Light mode (8³ grid, 1024 shots) for CI; heavy mode (64³ grid, 16384 shots) for production
- **Backend sensitivity:** Qiskit and PennyLane are simulator-compatible; CUDA-Q requires GPU for speed
- **Known limitations:** Decoherence limits circuit depth — our circuits are designed to fit within coherence time

## See Also

- [[quantum-algorithms]] — Algorithm catalog
- [[quantum-systems]] — Platform comparison
- [[quantum-field-theory]] — The physics behind the circuits
- [[field-geometry-tensor]] — What the circuits compute
- [[quantum-simulation-tier]] — Light/medium/heavy modes
