---
created: 2026-06-22
protected: true
related:
- quantum-algorithms
- time-travel-machinery-architecture
sources:
- Nielsen-Chuang-2010
tags:
- quantum
- algorithm
- qpe
title: Quantum Phase Estimation
updated: '2026-06-25'
---

# Quantum Phase Estimation (QPE)

QPE extracts the eigenvalues of a unitary operator. It's one of the most important quantum algorithms.

## Purpose

Measure the energy eigenvalues of the spacetime Hamiltonian.

## Why We Need It

Time evolution in quantum mechanics is governed by the Hamiltonian operator $H$. QPE extracts the eigenvalues of $H$, which correspond to the energy levels of spacetime. These energy levels determine the time dilation effects.

## Complexity

$O(1/\epsilon)$ for precision $\epsilon$.

## Qiskit Implementation

```python
from qiskit.algorithms import PhaseEstimation
from qiskit.circuit.library import QFT
```

## Project Chicken Soup Integration

**Layer:** Spacetime Engine (Qiskit) — key subroutine for HHL and Hamiltonian analysis.

**Concrete use:** QPE extracts the eigenvalues of the spacetime Hamiltonian H. These eigenvalues correspond to the allowed energy levels of the gravitational field at each grid point. They determine time dilation (eigenvalue → proper time rate) and identify closed timelike cycles (periodic eigenvalues → temporal periodicity).

**Backend:** Qiskit (native QPE implementation), CUDA-Q (via custom phase kickback circuits), PennyLane (via differentiable QPE for gradient computation).

**Known limitations:** QPE precision scales as O(1/ε) in circuit depth. High-precision eigenvalue estimation requires deep circuits that exceed NISQ coherence limits. The "light mode" simulation uses fewer precision qubits (3-4 bits of phase, error ~6%), while "heavy mode" uses 8-10 bits (error ~0.2%).

## See Also

- [[quantum-algorithms]]
- [[time-travel-machinery-architecture]]

