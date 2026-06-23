---
title: "HHL Algorithm"
tags: [quantum, algorithm, hhl]
created: 2026-06-22
updated: 2026-06-22
sources: [Nielsen-Chuang-2010]
related: [quantum-algorithms, time-travel-machinery-architecture]
---

# HHL Algorithm (Harrow-Hassidim-Lloyd)

Quantum algorithm for solving linear systems of equations.

## Purpose

Solve linear systems $Ax = b$ exponentially faster than classical.

## Why We Need It

The equations that describe spacetime are linear systems. HHL solves $Ax = b$ in $O(\log N)$ time, which is exponentially faster than the classical $O(N\kappa)$ time.

## Complexity

$O(\log N \cdot \kappa^2)$ where $\kappa$ is the condition number.

## Qiskit Implementation

```python
from qiskit.algorithms import HHL
```

## See Also

- [[quantum-algorithms]]
- [[time-travel-machinery-architecture]]
