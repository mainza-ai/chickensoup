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
- qft
title: Quantum Fourier Transform
updated: '2026-06-25'
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

## Project Chicken Soup Integration

**Layer:** Spacetime Engine (Qiskit) — used as a subroutine in QPE and HHL

**Concrete use:** The QFT transforms the metric from position space (values at grid points) to momentum/frequency space (periodic components). This reveals the periodic structure of spacetime — closed timelike curves appear as periodic modes in the frequency domain. QFT is also the core subroutine in quantum phase estimation, which extracts eigenvalues of the spacetime Hamiltonian.

**Backend:** Works identically on Qiskit and CUDA-Q (both support QFT circuits). PennyLane has a QFT template for differentiable QFT calculations.

**Known limitations:** QFT scale polynomially with qubit count. For our grid encoding (log₂(N) qubits per dimension), QFT requires O(log²N) gates — negligible compared to the Hamiltonian simulation cost.

## See Also

- [[quantum-algorithms]]
- [[time-travel-machinery-architecture]]

