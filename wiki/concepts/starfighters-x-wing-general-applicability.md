---
title: "Starfighters: General Applicability of X-Wing"
tags: [post-quantum-cryptography, hybrid-kem, kem-combiners, security-analysis, qsf-combiner]
created: 2026-07-10
updated: 2026-07-10
sources: [2025-1397.pdf, Connolly-Hövelmanns-Hülsing-Kousidis-Meijers-2025]
related: [post-quantum-cryptography, x-wing-hybrid-kem, feistel-tools-qrp, cake-secure-pake]
---

# Starfighters: On the General Applicability of X-Wing

Connolly, Hövelmanns, Hülsing, Kousidis, and Meijers (2025) analyze the QSF (Quasi-Synchronized Filtering) KEM combiner that underlies X-Wing, extending security guarantees beyond the original ML-KEM-768 + X25519 instantiation to arbitrary KEM pairs.

## Overview

X-Wing's QSF combiner was initially analyzed only for its specific application. This work provides the first comprehensive proof of general applicability across arbitrary KEMs.

## QSF Combiner Mechanics

- Each component KEM produces its own shared secret (or aborts)
- The combiner outputs the XOR of successful shared secrets
- Security: succeeds only if **both** components succeed independently
- Failure of one component does not degrade the other

## Extended Instantiations

- Original X-Wing: X25519 + ML-KEM-768
- Additional classical ECDH-based combinations
- Additional post-quantum combinations analyzed under same framework

## Security Properties

- CCA2 security in the standard model
- Tight security reduction without random oracles
- Handles adaptive corruptions and key confirmation

## Wiki Connections

- [[x-wing-hybrid-kem]] — the primitive this paper generalizes
- [[post-quantum-cryptography]] — broader PQC deployment context
- [[feistel-tools-qrp]] — related QROM proof methodology
- [[post-quantum-cryptographic-governance]] — organizational transition policies

## Source

- `2025-1397.pdf`; Connolly et al., IACR Communications in Cryptology, 2025
