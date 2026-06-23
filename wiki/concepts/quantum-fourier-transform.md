---
title: "Quantum Fourier Transform"
tags: [quantum, algorithm, qft]
created: 2026-06-22
updated: 2026-06-22
sources: [Nielsen-Chuang-2010]
related: [quantum-algorithms, time-travel-machinery-architecture]
---

# Quantum Fourier Transform (QFT)

The quantum analogue of the discrete Fourier transform. Used in many quantum algorithms.

## Purpose

Transform between position and momentum space in spacetime.

## Why We Need It

The QFT reveals periodicity in quantum states, which corresponds to the periodicity in time (closed timelike curves). It is used in Shor's algorithm, quantum phase estimation, and many other algorithms.

## Complexity

$O(\log^2 n)$ for $n$ qubits.

## Qiskit Implementation

```python
from qiskit.circuit.library import QFT
```

## See Also

- [[quantum-algorithms]]
- [[time-travel-machinery-architecture]]
