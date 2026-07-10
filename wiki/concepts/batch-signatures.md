---
title: "Batch Signatures, Revisited"
tags: [post-quantum-cryptography, digital-signatures, batch-verification, research-paper, papers]
created: 2026-07-10
updated: 2026-07-10
sources: [2023-492.pdf, Aguilar-Melchor-2023]
related: [post-quantum-cryptography, quantum-computation]
---

# Batch Signatures, Revisited

## Overview

"Batch Signatures, Revisited" (Aguilar-Melchor et al., SandboxAQ, IACR Communications in Cryptology, 2023) formally defines and analyzes **batch signatures** — a construction where a single expensive inner signature authenticates a Merkle tree of many messages.

## Key Contributions

- Formal unforgeability and privacy proofs for batch signature construction
- Demonstrates **3.2× throughput increase** for Falcon-512 in TLS at the cost of ~14% signature size increase and ~25% median latency
- Only 82 bytes additional bandwidth per extra message after the first batch signature
- Enables slow signing algorithms (including NIST PQC lattice schemes) to scale to high-throughput applications

## Connection to Project Chicken Soup

- [[post-quantum-cryptography]] — batch signatures as a deployment strategy for NIST-standardized PQC in high-throughput systems
- [[quantum-computation]] — efficient PQC deployment is part of the near-term quantum transition
- [[api-design]] — the Chicken Soup API's authenticated endpoints (`X-API-Key` middleware) could adopt batch verification under heavy multi-agent load

## Authors

Carlos Aguilar-Melchor, Martin R. Albrecht, Thomas Bailleux, Nina Bindel, James Howe, Andreas Hülsing, David Joseph, Marc Manzano — SandboxAQ + Eindhoven University of Technology.

## Source

- IACR Communications in Cryptology, 2023 — [ePrint: 2023/492](https://eprint.iacr.org/2023/492)
