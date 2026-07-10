---
title: "Orbital Optimization via AI-Accelerators"
tags: [quantum-chemistry, dmrg, gpu-computing, orbital-optimization, research-paper, papers]
created: 2026-07-10
updated: 2026-07-10
sources: [2503.20700v1.pdf, Legeza-2025]
related: [quantum-computation, quantum-machine-learning, dmrg]
---

# Orbital Optimization via AI-Accelerators

## Overview

"Orbital optimization of large active spaces via AI-accelerators" (Legeza et al., March 2025) presents an orbital optimization procedure combining the **DMRG method** with **CAS-SCF** (Complete Active Space Self-Consistent Field) for quantum chemistry, achieving unprecedented active space sizes using NVIDIA GPU hardware.

## Key Contributions

- DMRG-SCF orbital optimization reaching **CAS(82,82)** (82 electrons in 82 orbitals) — previously intractable active space sizes
- Benchmarking on **NVIDIA DGX-A100 and DGX-H100** hardware with detailed scaling and error analysis
- GPU-accelerated, spin-adapted DMRG as the engine; CAS-SCF as the orbital optimization loop
- Molecular systems with active spaces of **hundreds of electrons in thousands of orbitals**
- ORCA program package integration

## Connection to Project Chicken Soup

- [[quantum-computation]] — large-scale quantum chemistry simulation is a benchmark for the Spacetime Engine
- [[quantum-machine-learning]] — GPU acceleration patterns mirror AI Navigator training infrastructure
- [[time-travel-machinery-architecture]] — CAS-SCF orbital optimization is a classical precursor to quantum state preparation for spacetime field configurations
- [[dmrg]] — see related quantum chemistry computational methods

## Authors

Örs Legeza (Wigner Research Centre / TUM), Andor Menczer, Ádám Ganyecz, Miklós Antal Werner, Kornél Kapás, Jeff Hammond (NVIDIA), Sotiris S. Xantheas (PNNL), Martin Ganahl (SandboxAQ), Frank Neese (Max Planck).

## Source

- arXiv:2503.20700 [quant-ph] — March 2025
