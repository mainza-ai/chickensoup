---
title: "Retentive Neural Quantum States"
tags: [quantum-machine-learning, quantum-chemistry, neural-quantum-states, retnet, research-paper, papers]
created: 2026-07-10
updated: 2026-07-10
sources: [2411.03900v1.pdf, Knitter-2024]
related: [quantum-machine-learning, quantum-computation, vqe, quantum-computation]
---

# Retentive Neural Quantum States

## Overview

"Retentive Neural Quantum States: Efficient Ansätze for Ab Initio Quantum Chemistry" (Knitter et al., November 2024, arXiv:2411.03900) explores the **RetNet** architecture as a variational ansatz for solving electronic ground-state problems, replacing transformers in Neural-Network Quantum States (NQS).

## Key Contributions

- **RetNet as NQS ansatz**: RetNet processes data in parallel during training (like transformers) but recurrently during inference, overcoming the O(n²) time complexity bottleneck of transformers with respect to sequence length
- Establishes clear **threshold ratio** of problem-to-model size past which RetNet outperforms transformers
- Uses **variational neural annealing** training strategies to recover expressiveness lost vs. transformers
- Competitive accuracy on ab initio quantum chemistry ground-state problems
- Demonstrable time-complexity advantage for large-scale quantum chemistry simulations

## Connection to Project Chicken Soup

- [[quantum-machine-learning]] — RetNet as NQS directly extends the QML toolbox for the AI Navigator
- [[quantum-computation]] — variational ansatz efficiency is core to the quantum pipeline
- [[vqe]] — RetNet NQS is an alternative ansatz to UCCSD for VQE ground-state estimation
- Builds on [[structure-preserving-quantum-encodings]] — RetNet's recurrence structure may be seen as a structure-preserving encoding choice

## Authors

Oliver Knitter (University of Michigan), Dan Zhao (SandboxAQ / NYU), James Stokes, Martin Ganahl, Stefan Leichenauer, Shravan Veerapaneni.

## Source

- arXiv:2411.03900 [quant-ph] — November 2024
