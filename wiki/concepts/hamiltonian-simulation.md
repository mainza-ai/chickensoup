---
title: "Hamiltonian Simulation"
tags: [quantum, algorithm, hamiltonian]
created: 2026-06-22
updated: 2026-06-22
sources: [Nielsen-Chuang-2010]
related: [quantum-algorithms, time-travel-machinery-architecture]
---

# Hamiltonian Simulation

Family of quantum algorithms for simulating the time evolution of quantum systems governed by a Hamiltonian.

## Purpose

Simulate the time evolution of the spacetime field.

## Why We Need It

The Hamiltonian that describes spacetime is complex. We need to simulate its evolution to understand how the field behaves under different conditions.

## Complexity

$O(t^2)$ for time $t$ with Trotter-Suzuki decomposition.

## Qiskit Implementation

```python
from qiskit.algorithms.evolution import HamiltonianSimulation
```

## Project Chicken Soup Integration

**Layer:** Spacetime Engine (Qiskit) — this is the core quantum algorithm of the entire layer.

**Concrete use:** The spacetime Hamiltonian H encodes the Einstein field equations as a quantum operator. Hamiltonian simulation evolves an initial metric state forward in time: |ψ(t)⟩ = e^(-iHt) |ψ(0)⟩. The Trotter-Suzuki decomposition breaks the evolution into discrete steps that map to quantum gates.

**Backend:** Qiskit Aer (simulation) uses Trotterization with configurable number of steps. CUDA-Q can accelerate the Trotter steps via GPU-parallelized gate application. PennyLane can differentiate through the simulation for gradient-based optimization.

**Known limitations:** Trotter error accumulates with simulation time t and number of qubits. The Babbush et al. (2023) coupled-oscillator algorithm offers an alternative that avoids Trotter error but requires more qubits.

## See Also

- [[quantum-algorithms]]
- [[time-travel-machinery-architecture]]
