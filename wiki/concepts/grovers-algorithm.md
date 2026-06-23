---
title: "Grover's Algorithm"
tags: [quantum, algorithm, grover]
created: 2026-06-22
updated: 2026-06-22
sources: [Nielsen-Chuang-2010]
related: [quantum-algorithms, time-travel-machinery-architecture]
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

## See Also

- [[quantum-algorithms]]
- [[time-travel-machinery-architecture]]
