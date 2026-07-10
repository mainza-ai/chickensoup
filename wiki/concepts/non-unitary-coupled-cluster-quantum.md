---
title: "Non-Unitary Coupled Cluster Enabled by Mid-Circuit Measurements"
tags: [quantum-computation, quantum-chemistry, coupled-cluster, quantum-measurement, research-paper, papers]
created: 2026-07-10
updated: 2026-07-10
sources: [2406.11574v2.pdf, Fleury-2024]
related: [quantum-coupled-oscillator-simulation, hamiltonian-simulation, quantum-computation, quantum-machine-learning]
---

# Non-Unitary Coupled Cluster Enabled by Mid-Circuit Measurements

## Overview

"Non-unitary Coupled Cluster Enabled by Mid-circuit Measurements on Quantum Computers" (Fleury et al., SandboxAQ & UC Davis, June 2024, arXiv:2406.11574) proposes a state preparation method for quantum chemistry using mid-circuit measurements within coupled cluster (CC) theory, moving beyond the unitary-only constraint of standard VQE/UCCSD ansatze.

## Key Contributions

- **Non-unitary CC ansatz**: Incorporates mid-circuit measurements into circuit construction, enabling richer state preparation than unitary-only methods
- **Energy evaluation and state overlap verification** on small chemical systems
- **28% reduction in CNOT gates**, **57% reduction in T gates** on average vs. UCCSD
- Demonstrates that non-unitary CC with measurements outperforms unitary-only ansatze for quantum chemistry ground-state estimation

## Connection to Project Chicken Soup

- Directly connects to [[quantum-coupled-oscillator-simulation]] — this paper provides the CC methodology that the WISER/Classiq implementation builds on
- Links to [[hamiltonian-simulation]] — mid-circuit measurement techniques reduce gate depth for Hamiltonian simulation
- Relevant to [[quantum-machine-learning]] — variational ansatze efficiency directly impacts QML training cost
- CC methods are used in [[time-travel-machinery-architecture]] preparation of spacetime field configurations

## Authors

Alexandre Fleury (SandboxAQ), James Brown (qBraid), Erika Lloyd (SandboxAQ), Maritza Hernandez (SandboxAQ), Isaac H. Kim (UC Davis).

## Source

- [arXiv:2406.11574](https://arxiv.org/abs/2406.11574) — June 2024
- Complementary to: [arXiv:2603.05479](https://arxiv.org/abs/2603.05479) — Quantum Simulation of Coupled Harmonic Oscillators
