---
title: "VQE (Variational Quantum Eigensolver)"
tags: [quantum, algorithm, vqe]
created: 2026-06-22
updated: 2026-06-22
sources: [Nielsen-Chuang-2010]
related: [quantum-algorithms, time-travel-machinery-architecture]
---

# Variational Quantum Eigensolver (VQE)

Hybrid quantum-classical algorithm for estimating ground-state energies.

## Purpose

Find the ground state of a Hermitian operator by minimizing the energy expectation value.

## Why We Need It

The ground state of the Hamiltonian represents the lowest energy configuration of spacetime. This is the most stable configuration for time travel.

## Complexity

$O(N)$ for $N$ qubits, where $N$ is the number of parameters.

## D-Wave Implementation

```python
from dwave.system import DWaveSampler
```

## See Also

- [[quantum-algorithms]]
- [[time-travel-machinery-architecture]]
