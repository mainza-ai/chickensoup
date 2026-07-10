---
title: "Verified Implementations of Hash-Based Signatures"
tags: [post-quantum-cryptography, formal-verification, hash-based-signatures, research-paper, papers]
created: 2026-07-10
updated: 2026-07-10
sources: [2026-134.pdf, Barbosa-2026]
related: [post-quantum-cryptography, quantum-computation]
---

# Verified Implementations of Hash-Based Signatures

## Overview

"Completing the Chain: Verified Implementations of Hash-Based Signatures and Their Security" (Barbosa et al., 2026) presents the **first formally verified implementation** of a hash-based signature scheme linked to a machine-checked proof of security — specifically **XMSS** and **XMSS^MT** in the Jasmin assembly-like language.

## Key Contributions

- **Jasmin implementations** of XMSS and XMSS^MT targeting amd64, verified against RFC 8391 specifications
- **EasyCrypt specifications** formally proven to refine the abstract secure-specification from CRYPTO 2023
- Bridges low-level TreeHash implementations with high-level functional specifications
- Proves that the implementation not only functions correctly, but adheres to a **provably secure specification**

## Connection to Project Chicken Soup

- [[post-quantum-cryptography]] — XMSS is one of the three NIST PQC standards (hash-based); verified implementations set the security baseline
- [[quantum-computation]] — hash-based signatures are the most conservative PQC choice (minimal mathematical assumptions); preferred for long-lived secrets
- [[backdoor-science]] — formal verification methodology provides a template for verifying any quantum-safe protocol implementation against its specification

## Authors

Manuel Barbosa, François Dupressoir, Rui Fernandes, Andreas Hülsing, Matthias Meijers, Pierre-Yves Strub — University of Porto, Bristol, Max Planck, TU/e, SandboxAQ, PQShield.

## Source

- ePrint: 2026/134 — 2026
