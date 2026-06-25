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
- annealing
title: Quantum Annealing
updated: '2026-06-25'
---

# Quantum Annealing

Optimization approach based on adiabatic evolution or annealing-like quantum dynamics.

## Purpose

Find the global minimum of a function using quantum annealing.

## Why We Need It

The spacetime energy landscape has many local minima. Quantum annealing finds the global minimum, which corresponds to the optimal time travel path.

## Complexity

$O(1/\Delta^2)$ where $\Delta$ is the minimum gap.

## D-Wave Implementation

```python
from dwave.system import DWaveSampler
```

## Project Chicken Soup Integration

**Layer:** AI Navigator optimization backend (D-Wave)

**Concrete use:** The AI Navigator needs to find the optimal path through a perturbed metric. This is a combinatorial optimization problem — which sequence of spacetime points minimizes proper time while satisfying feasibility constraints. Quantum annealing finds the global minimum of the path cost function.

**Backend:** D-Wave hardware (heavy mode), D-Wave simulator (light/medium modes). The path cost function must be encoded as an Ising model or QUBO — this limits the types of cost functions that can be represented.

**Known limitations:** Limited to optimization problems. Requires QUBO/Ising formulation, which is lossy for continuous cost functions. Qubit count on current D-Wave systems (5000+ qubits) is sufficient for our grid sizes but connectivity (Chimera/Pegasus topology) may limit coupling between distant metric points.

## See Also

- [[quantum-algorithms]]
- [[time-travel-machinery-architecture]]

