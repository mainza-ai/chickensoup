---
title: "Strong Keys for Tensor Isomorphism Cryptography"
tags: [post-quantum-cryptography, tensor-cryptography, hyperdeterminants, research-paper, papers]
created: 2026-07-10
updated: 2026-07-10
sources: [LIPIcs.MFCS.2025.78.pdf, Narayanan-2025]
related: [quantum-computation, post-quantum-cryptography]
---

# Strong Keys for Tensor Isomorphism Cryptography

## Overview

"Strong Keys for Tensor Isomorphism Cryptography" (Narayanan, LIPIcs MFCS 2025) addresses the problem of sampling **non-degenerate boundary format tensors** for use as public keys in tensor isomorphism-based cryptography.

## Key Contributions

- Sampling invertible tensors in >2 dimensions is hard because testing degeneracy requires computing **hyperdeterminants**
- Proposes two scrambling strategies:
  1. **Per-dimension random invertible matrix multiplication** — preserves dimension and format; samples computationally indistinguishable from uniform
  2. **Tensor convolution** — can increase dimension; recursive sampler reduces arbitrary dimensions to 3D via hyperdeterminant multiplicativity
- Provides candidate key generation algorithm protected against recent **weak key attacks** (geometric-structure attacks, rank-deficient attacks)
- Establishes boundary formats (2k+1)×(k+1)×(k+1) as preferred instantiations

## Connection to Project Chicken Soup

- [[post-quantum-cryptography]] — tensor isomorphism is an alternative PQC construction beyond lattice/code-based; 
- [[quantum-computation]] — higher-dimensional tensor structures have connections to quantum state encoding
- [[backdoor-science]] — weak key attacks show that even seemingly random-structured keys can harbor exploitable geometry; relevant to any quantum protocol design

## Author

Anand Kumar Narayanan (SandboxAQ).

## Source

- LIPIcs MFCS 2025, vol. 347, pp. 78:1–78:17 — [DOI: 10.4230/LIPIcs.MFCS.2025.78](https://drops.dagstuhl.de/entities/document/10.4230/LIPIcs.MFCS.2025.78)
