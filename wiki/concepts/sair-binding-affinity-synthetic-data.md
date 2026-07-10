---
title: "SAIR Binding Affinity with Synthetic Data"
tags: [binding-affinity, drug-discovery, machine-learning, synthetic-data, protein-ligand, quantum-chemistry]
created: 2026-07-10
updated: 2026-07-10
sources: [2026.03.02.708607v1.full.pdf, Ryczko-et-al-2026]
related: [ml-guided-aqfep, nex-binding-free-energy, biology-and-consciousness-substrates, sair-protein-ligand-dataset]
---

# SAIR Binding Affinity with Synthetic Data

Ryczko, Zin, Crivelli-Decker et al. (SandboxAQ, 2026) extend the Structurally Augmented IC50 Repository (SAIR) with ~80K absolute free energy perturbation calculations, demonstrating that simultaneous training on synthetic and experimental data improves binding affinity prediction on public benchmarks.

## Overview

Deep learning binding affinity prediction models are limited by available experimental data. This paper addresses the data gap by augmenting SAIR with physics-based synthetic data and two new dataset splits (SAIR-FEP and SAIR-OOD), showing that combining synthetic and experimental data yields predictable performance gains.

## Key Contributions

### SAIR Dataset Extension

- SAIR extended with ~80K absolute free energy perturbation (AFEP) calculations
- Two splits: **SAIR-FEP** (in-distribution) and **SAIR-OOD** (out-of-distribution) for realistic drug-discovery scenario simulation
- Compares proteochemometric (PCM) sequence-based models vs structure-based deep learning models

### Synthetic Data Effectiveness

- Physics-based descriptors enhance PCM models
- Structure-based deep learning methods capture finer geometric detail but are highly input-structure sensitive
- Co-folded complexes filtered at high confidence improve predictions predictably
- Training blindly on all complexes without structural filtering does not yield reliable gains

### Training Strategy

- Simultaneous training on synthetic + experimental data outperforms experimental-only training
- SAIR-OOD split assesses realistic generalization to unseen chemical space
- Results validate physics-informed synthetic data as a practical strategy for drug discovery

## Wiki Connections

- [[ml-guided-aqfep]] — complementary AQFEP ML approach
- [[nex-binding-free-energy]] — NEX framework for stabilizing FEP calculations
- [[sair-protein-ligand-dataset]] — the underlying SAIR dataset
- [[biology-and-consciousness-substrates]] — molecular-coherence angle

## Source

- bioRxiv preprint 2026.03.02.708607v1; Ryczko et al., SandboxAQ, 2026
