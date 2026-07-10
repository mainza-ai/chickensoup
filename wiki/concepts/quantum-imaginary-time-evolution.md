---
title: "Accelerating Quantum Imaginary-Time Evolution with Random Measurements"
tags: [quantum-computation, quantum-chemistry, variational-quantum-algorithms, research-paper, papers]
created: 2026-07-10
updated: 2026-07-10
sources: [PhysRevA.111.012424.pdf, Kolotouros-2025]
related: [quantum-computation, hamiltonian-simulation, quantum-machine-learning, vqe]
---

# Accelerating Quantum Imaginary-Time Evolution with Random Measurements

## Overview

"Accelerating quantum imaginary-time evolution with random measurements" (Kolotouros, Joseph, Narayanan, Phys. Rev. A **111**, 012424, January 2025) addresses the computational bottleneck in Quantum Imaginary-Time Evolution (QITE) for preparing thermal and ground states of Hamiltonians.

## Key Contributions

- QITE via hybrid quantum-classical approach is impractical for large m (number of parameters) because each step requires Θ(m²) state preparations to compute the Quantum Fisher Information Matrix (QFIM)
- **Main result**: If a parameterized state is rotated by a 2-design and measured in the computational basis, the QFIM can be inferred from partial-derivative cross-correlations of probability outcomes — one sample costs only Θ(m) state preparations
- **Second estimator family**: Replaces QFIM with averaged Classical Fisher Information Matrices (CFIMs); in an extreme case, just one CFIM sample is drawn for rapid descent
- **Algorithm**: Random-measurement imaginary-time evolution — tested on several molecular systems
- Proves rapid descent for the second estimator family

## Connection to Project Chicken Soup

- [[hamiltonian-simulation]] — QITE is an alternative to unitary Hamiltonian simulation for ground-state preparation in the Spacetime Engine
- [[quantum-machine-learning]] — QFIM estimation efficiency directly impacts training cost for variational circuits
- [[vqe]] — QITE is complementary to VQE for ground-state optimization
- [[quantum-computation]] — general technique for reducing parameterized circuit overhead

## Authors

Ioannis Kolotouros (SandboxAQ / University of Edinburgh), David Joseph (SandboxAQ), Anand Kumar Narayanan (SandboxAQ).

## Source

- Phys. Rev. A **111**, 012424 (2025) — [DOI: 10.1103/PhysRevA.111.012424](https://journals.aps.org/pra/abstract/10.1103/PhysRevA.111.012424)
