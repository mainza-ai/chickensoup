---
title: "Shor's Algorithm"
tags: [quantum, algorithm, shor]
created: 2026-06-22
updated: 2026-06-22
sources: [Nielsen-Chuang-2010]
related: [quantum-algorithms, time-travel-machinery-architecture]
---

# Shor's Algorithm

Peter Shor's 1994 algorithm for integer factorization and discrete logarithm.

## Purpose

Solve discrete logarithm and integer factorization in polynomial time.

## Why We Need It

The equations that describe spacetime structure involve factorization. Shor's algorithm solves these in polynomial time, which is exponentially faster than classical methods.

## Complexity

$O((\log N)^3)$ for factoring $N$.

## Qiskit Implementation

```python
from qiskit.algorithms import Shor
```

## See Also

- [[quantum-algorithms]]
- [[time-travel-machinery-architecture]]
