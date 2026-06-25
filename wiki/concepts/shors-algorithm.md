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
- shor
title: Shor's Algorithm
updated: '2026-06-25'
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

## Project Chicken Soup Integration

**Layer:** Spacetime Engine (Qiskit) — specialized subroutine, not core.

**Concrete use:** The periodic structure of closed timelike curves in compactified spacetime dimensions is described by modular periods. Shor's factorization finds the fundamental period of these modular structures, revealing the discrete spectrum of allowed CTC configurations. More broadly, Shor's algorithm demonstrates the type of exponential speedup this project relies on.

**Backend:** Qiskit (native implementation), CUDA-Q (custom circuit implementation).

**Known limitations:** Shor's algorithm requires thousands of logical qubits for cryptographically relevant problem sizes, well beyond current hardware. For our use case (factoring periods with bit length < 256), the qubit requirement is modest (~2000 physical qubits with error correction, or ~50 logical qubits). The algorithm is used sparingly — only when the period detection problem cannot be solved classically.

## See Also

- [[quantum-algorithms]]
- [[time-travel-machinery-architecture]]

