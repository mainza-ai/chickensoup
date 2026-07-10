---
title: "Finding Dense Sub-Lattices as Low-Energy States of a Hamiltonian"
tags: [quantum-computation, lattice-cryptography, shortest-vector-problem, quantum-annealing, research-paper, papers]
created: 2026-07-10
updated: 2026-07-10
sources: [2309.16256v2.pdf, Barberá-Rodríguez-2024]
related: [quantum-annealing, quantum-algorithms, post-quantum-cryptography, grovers-algorithm, qaoa]
---

# Finding Dense Sub-Lattices as Low-Energy States of a Hamiltonian

## Overview

"Finding dense sub-lattices as low-energy states of a Hamiltonian" (Barberá-Rodríguez, Gama, Narayanan, Joseph, arXiv:2309.16256, November 2024) formulates the **K-Densest Sub-lattice Problem (K-DSP)** as finding the first excited state of a Z-basis Hamiltonian, making it amenable to quantum algorithmic investigation.

## Key Contributions

- Generalizes SVP to **K-DSP**: find the densest K-dimensional sub-lattice
- Formulates K-DSP as a Hamiltonian ground-state problem — solvable via: Grover search, quantum Gibbs sampling, adiabatic evolution, QAOA
- **Classical polynomial-time preprocessing**: converts arbitrary input basis into one suited to quantum algorithms, reducing qubit requirements to O(KN²) for N-dimensional lattices
- Empirical QAOA solver for low-dimensional K-DSP
- Discusses hardness of K-DSP relative to SVP and whether K-DSP could be a better foundation for post-quantum cryptography

## Connection to Project Chicken Soup

- [[quantum-annealing]] — QAOA solver links directly to D-Wave backend
- [[qaoa]] — K-DSP QAOA solver is a concrete instantiation
- [[post-quantum-cryptography]] — investigates alternative lattice problems for PQC foundations
- [[grovers-algorithm]] — Grover search applied as one solution method
- [[quantum-computation]] — preprocessing-to-quantum pipeline mirrors the AI Navigator's classical→quantum workflow

## Authors

Júlia Barberá-Rodríguez (ICFO), Nicolas Gama, Anand Kumar Narayanan, David Joseph (SandboxAQ).

## Source

- arXiv:2309.16256 [quant-ph] — November 2024
