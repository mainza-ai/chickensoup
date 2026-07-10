---
title: "SAIR: Synthetic Dataset for Protein-Ligand Binding Affinity"
tags: [ml-bio, drug-discovery, quantum-chemistry, machine-learning, research-paper, papers]
created: 2026-07-10
updated: 2026-07-10
sources: [2025.06.17.660168v1.full.pdf, Lemos-2025]
related: [quantum-chemistry, quantum-computation, machine-learning]
---

# SAIR: Synthetic Dataset for Protein-Ligand Binding Affinity

## Overview

"SAIR: Enabling Deep Learning for Protein-Ligand Interactions with a Synthetic Structural Dataset" (Lemos et al., SandboxAQ & NVIDIA, June 2025) introduces the **Structurally Augmented IC50 Repository** — the largest publicly available dataset of protein-ligand 3D structures with binding activity data.

## Key Contributions

- **5,244,285 structures** across 1,048,857 unique protein-ligand systems — an order of magnitude larger than prior datasets
- Curated from ChEMBL and BindingDB; computationally folded using **Boltz-1x** model
- ~3% of structures exhibit physical anomalies (mostly internal energy violations)
- Benchmarks: Vina, Vinardo, Onionnet-2, AEV-PLIG — ML models outperform classical scoring functions but neither correlates strongly with ground truth
- Demonstrates need for models fine-tuned to synthetic-structure distributions

## Connection to Project Chicken Soup

- [[quantum-chemistry]] — protein-ligand binding is a quantum mechanical problem; classical ML datasets are proxies for quantum simulation outputs
- [[quantum-computation]] — quantum advantage in drug discovery remains speculative; SAIR provides benchmark for when quantum chemistry beats classical ML
- [[machine-learning]] — the benchmark suite design mirrors the [[evaluation-framework]] for the Chicken Soup navigation engine
- [[time-travel-machinery-architecture]] — binding affinity prediction via AI Navigator is a speculative high-value application

## Authors

Pablo Lemos, Zane Beckwith, Sasaank Bandi, Maarten van Damme, Jordan Crivelli-Decker, Benjamin J. Shields, Thomas Merth, Punit K. Jha, Nicola De Mitri, Tiffany J. Callahan, AJ Nish, Paul Abruzzo, Romelia Salomon-Ferrer, Martin Ganahl — SandboxAQ & NVIDIA.

## Source

- bioRxiv / medRxiv preprint — June 2025
