---
title: "Parallel DMRG Quarter petaFLOPS Implementation"
tags: [dmrg, strongly-correlated-systems, gpu-computing, quantum-chemistry, high-performance-computing]
created: 2026-07-10
updated: 2026-07-10
sources: [parallel-implementation-of-the-density-matrix-renormalization-group-method-achieving-a-quarter-petaflops-performance-on.pdf, Menczer-van-Damme-et-al-2024]
related: [dmrg-orbital-optimization, quantum-systems, quantum-computation]
---

# Parallel DMRG Quarter petaFLOPS Implementation

Menczer, van Damme, Rask, Huntington, Hammond, Xantheas, Ganahl, Legeza (2024) report a hybrid CPU-multi-GPU DMRG implementation achieving 0.25 petaFLOPS on a single DGX-H100 GPU node for strongly correlated quantum systems.

## Overview

Density Matrix Renormalization Group (DMRG) is the premier method for 1D quantum many-body systems. This paper achieves unprecedented performance by combining CPU pre-processing with multi-GPU tensor network contractions.

## Key Results

- Hybrid CPU + multi-GPU architecture on NVIDIA DGX-H100
- 8 A100 GPUs used for core tensor contractions
- 0.25 petaFLOPS peak performance on a **single node**
- Methods for efficient matrix product operator (MPO) / matrix product state (MPS) contractions across GPU memory hierarchies
- Applied to strongly correlated electron systems; paves way for 2D DMRG at quantum chemistry accuracy

## Technical Approach

- Distributed tensor contractions across GPU NVLink/NVSwitch fabric
- Load-balanced parallelization of DMRG sweeps
- I/O and communication optimization for arbitrary MPS/MPO topologies

## Wiki Connections

- [[dmrg-orbital-optimization]] — orbital-optimized DMRG improving active space selection
- [[quantum-systems]] — classical approximation methods for quantum many-body systems
- [[quantum-computation]] — benchmarking quantum advantage targets for Hamiltonian simulation
- [[dense-sub-lattice-hamiltonian]] — lattice Hamiltonian first-excited-state methods complementing DMRG

## Source

- `parallel-implementation-of-the-density-matrix-renormalization-group-method-achieving-a-quarter-petaflops-performance-on.pdf`; Menczer et al., J. Chem. Theory Comput. 2024, 20, 8397–8404
