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
- qaoa
title: QAOA (Quantum Approximate Optimization Algorithm)
updated: '2026-06-25'
---

# Quantum Approximate Optimization Algorithm (QAOA)

Hybrid quantum-classical algorithm for approximate combinatorial optimization.

## Purpose

Solve combinatorial optimization problems using alternating cost and mixer Hamiltonians.

## Why We Need It

The AI Navigator needs to find the best path through spacetime. QAOA is a variational algorithm that finds approximate solutions to optimization problems on quantum computers.

## Complexity

$O(p)$ for $p$ layers, typically $p \approx 10-100$.

## D-Wave Implementation

```python
from dwave.system import DWaveSampler
```

## Project Chicken Soup Integration

**Layer:** AI Navigator (PennyLane, D-Wave backend)

**Concrete use:** QAOA finds the optimal path through spacetime by encoding the path as a binary optimization problem: which grid points should the path go through? The cost Hamiltonian penalizes paths with high proper time or energy; the mixer Hamiltonian allows transitions between candidate paths. Alternating layers refine the solution.

**Backend:** PennyLane (variational QAOA implementation, differentiable), D-Wave (hardware-native QUBO encoding), IonQ (high-precision QAOA for small instances).

**Known limitations:** QAOA approximation ratio depends on the number of layers p — more layers give better solutions but require deeper circuits. For p = 1, QAOA often finds the global optimum on small instances but degrades on large ones. Our grid sizes (8³ to 64³) require p ≥ 10 for reliable solutions, which is at the edge of current NISQ capabilities.

## See Also

- [[quantum-algorithms]]
- [[time-travel-machinery-architecture]]

