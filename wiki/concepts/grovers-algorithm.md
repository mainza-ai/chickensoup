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
- grover
title: Grover's Algorithm
updated: '2026-06-25'
---

# Grover's Algorithm

Grover's 1996 algorithm for searching an unstructured database with a quadratic speedup.

## Purpose

Search an unstructured database with $O(\sqrt{N})$ queries instead of $O(N)$.

## Why We Need It

We need to search through all possible time travel paths. Grover's algorithm provides a quadratic speedup for this search.

## Complexity

$O(\sqrt{N})$ for $N$ entries.

## Qiskit Implementation

```python
from qiskit.algorithms import Grover
```

## Project Chicken Soup Integration

**Layer:** AI Navigator (PennyLane) — path search acceleration

**Concrete use:** When the AI Navigator needs to select one path from many candidates, Grover's algorithm provides a quadratic speedup: O(√N) evaluations instead of O(N). The "database" is the space of possible trajectories, and the "search" finds the one with optimal cost function. The oracle encodes the path cost threshold — paths below threshold are "marked."

**Backend:** Qiskit (native Grover with custom oracle), PennyLane (differentiable amplitude amplification), CUDA-Q (GPU-accelerated oracle evaluation for large databases).

**Known limitations:** Grover's algorithm requires a quantum oracle that can evaluate the cost function — this oracle must be implementable as a quantum circuit. Continuous cost functions (like proper time) must be discretized for oracle encoding. The quadratic speedup is modest for our candidate path counts (typically 10³-10⁵ paths, so speedup from 10⁵ to ~316 evaluations).

## See Also

- [[quantum-algorithms]]
- [[time-travel-machinery-architecture]]

