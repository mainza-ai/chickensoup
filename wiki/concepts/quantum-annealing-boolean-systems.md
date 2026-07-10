---
title: "Solving Boolean Multivariate Equations with Quantum Annealing"
tags: [quantum-computation, quantum-annealing, cryptography, research-paper, papers]
created: 2026-07-10
updated: 2026-07-10
sources: [PhysRevResearch.4.013096.pdf, Ramos-Calderer-2022]
related: [quantum-annealing, quantum-computation, quantum-algorithms, d-wave]
---

# Solving Boolean Multivariate Equations with Quantum Annealing

## Overview

"Solving systems of Boolean multivariate equations with quantum annealing" (Ramos-Calderer et al., Phys. Rev. Research **4**, 013096, February 2022) studies the **multivariate quadratic (MQ) problem** over the binary field and its embedding into Hamiltonians solvable on quantum annealing platforms.

## Key Contributions

- Three embedding options for the MQ problem into an annealing Hamiltonian, with analysis of quantum resource trade-offs
- **Machine-agnostic iterative algorithm**: repeatedly reduces the search space to better solve the problem Hamiltonian
- Successfully implemented on **D-Wave devices** for several MQ instances
- Applications in: symmetric and asymmetric cryptanalysis, multivariate-based post-quantum cryptography, coding theory, computer algebra

## Connection to Project Chicken Soup

- [[quantum-annealing]] — direct D-Wave implementation; connects AI Navigator optimization backend
- [[d-wave]] — hardware platform used in experiments
- [[quantum-algorithms]] — demonstrates hybrid classical-quantum algorithmic pattern
- [[quantum-computation]] — cryptanalysis angle connects to [[post-quantum-cryptography]] and the broader quantum threat landscape
- [[time-travel-machinery-architecture]] — annealing-based path optimization is a candidate AI Navigator subroutine

## Authors

Sergi Ramos-Calderer, Carlos Bravo-Prieto, Ruge Lin, Emanuele Bellini, Marc Manzano, Najwa Aaraj, José I. Latorre (TII Abu Dhabi, University of Barcelona, Mondragon Unibertsitatea, etc.).

## Source

- Phys. Rev. Research **4**, 013096 (2022) — [DOI: 10.1103/PhysRevResearch.4.013096](https://journals.aps.org/prresearch/abstract/10.1103/PhysRevResearch.4.013096)
