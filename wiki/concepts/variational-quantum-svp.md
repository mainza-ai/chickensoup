---
title: "Variational Quantum Solutions to the Shortest Vector Problem"
tags: [quantum-computation, variational-quantum, shortest-vector-problem, post-quantum-cryptography, research-paper, papers]
created: 2026-07-10
updated: 2026-07-10
sources: [q-2023-03-02-933.pdf, Albrecht-2023]
related: [quantum-computation, qaoa, vqe, quantum-annealing, post-quantum-cryptography]
---

# Variational Quantum Solutions to the Shortest Vector Problem

## Overview

"Variational Quantum Solutions to the Shortest Vector Problem" (Albrecht, Prokop, Shen, Wallden, 2023) maps SVP to a Hamiltonian ground-state problem and solves it with NISQ-era variational algorithms, achieving dimension-28 lattice instances on quantum emulation.

## Key Contributions

- Maps SVP to Hamiltonian ground-state minimization problem via qubit encoding
- **New lattice enumeration bounds** — tighter than prior results; fewer qubits needed per dimension
- Excludes zero vector from optimization via two alternative methods: different classical loop, or modified Hamiltonian mapping
- Solves SVP in dimension up to **28 on quantum emulation** — significantly beyond prior special-case results
- Extrapolates to estimate ~10³ qubits required for cryptographically hard SVP instances

## Connection to Project Chicken Soup

- [[qaoa]] — the variational approach is functionally equivalent to QAOA for this problem
- [[quantum-annealing]] — SVP on quantum hardware is a key benchmark for the D-Wave backend
- [[post-quantum-cryptography]] — SVP hardness underpins Dilithium and Falcon; this paper quantifies NISQ-era gap to cryptographically relevant sizes
- [[time-travel-machinery-architecture]] — variational lattice problems are a test case for the quantum pathfinding layer

## Authors

Martin R. Albrecht (King's College London / SandboxAQ), Miloš Prokop (University of Edinburgh), Yixin Shen (Royal Holloway), Petros Wallden (University of Edinburgh).

## Source

- ePrint: 2023/933 — [quant-ph](https://eprint.iacr.org/2023/933)
