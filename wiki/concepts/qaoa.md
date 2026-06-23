---
title: "QAOA (Quantum Approximate Optimization Algorithm)"
tags: [quantum, algorithm, qaoa]
created: 2026-06-22
updated: 2026-06-22
sources: [Nielsen-Chuang-2010]
related: [quantum-algorithms, time-travel-machinery-architecture]
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

## See Also

- [[quantum-algorithms]]
- [[time-travel-machinery-architecture]]
