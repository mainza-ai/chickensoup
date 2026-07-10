---
title: "Grover's Oracle for the Shortest Vector Problem"
tags: [quantum-computation, grover, shortest-vector-problem, post-quantum-cryptography, research-paper, papers]
created: 2026-07-10
updated: 2026-07-10
sources: [2402.13895v1.pdf, Prokop-2024]
related: [grovers-algorithm, quantum-computation, quantum-annealing, post-quantum-cryptography]
---

# Grover's Oracle for the Shortest Vector Problem

## Overview

"Grover's oracle for the Shortest Vector Problem and its application in hybrid classical-quantum solvers" (Prokop, Wallden, Joseph, arXiv:2402.13895, February 2024) provides the first concrete implementation of a Grover oracle for SVP and analyzes hybrid classical-quantum SVP solvers.

## Key Contributions

- Defines a concrete quantum circuit implementing Grover's oracle for SVP
- Evaluates cost in: number of qubits, number of gates, circuit depth, T-count
- Shows how to combine Grover quantum search with state-of-the-art classical lattice reducers (e.g., BKZ) — the quantum subroutine finds candidate vectors that the classical solver verifies/refines
- Demonstrates hybrid solver for SVP instances beyond classical reach, though still far from threatening cryptosystem parameters
- Spectrum of trade-offs depending on available quantum technology

## Connection to Project Chicken Soup

- [[grovers-algorithm]] — oracle construction is the primary technical contribution; directly applicable to the AI Navigator's search subroutines
- [[quantum-annealing]] — hybrid solver pattern (quantum proposal + classical verification) is the same approach used in [[time-travel-machinery-architecture]]
- [[post-quantum-cryptography]] — SVP hardness underlies lattice-based PQC (Dilithium, Falcon); this paper quantifies the quantum gap
- [[qaoa]] — alternative variational approach to SVP; this paper provides the classical baseline to compare against

## Authors

Miloš Prokop (University of Edinburgh / SandboxAQ), Petros Wallden (University of Edinburgh), David Joseph (SandboxAQ).

## Source

- arXiv:2402.13895 [quant-ph] — February 2024
