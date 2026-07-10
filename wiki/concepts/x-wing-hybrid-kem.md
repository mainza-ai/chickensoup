---
title: "X-Wing Hybrid KEM"
tags: [post-quantum-cryptography, hybrid-kem, key-encapsulation, x25519, ml-kem-768, cryptography, implementation]
created: 2026-07-10
updated: 2026-07-10
sources: [1-1-21.pdf, Barbosa-Connolly-Duarte-et-al-2024]
related: [post-quantum-cryptography, batch-signatures, feistel-tools-qrp, post-quantum-cryptographic-governance, starfighters-x-wing]
---

# X-Wing Hybrid KEM

Barbosa, Connolly, Duarte, Kaiser, Schwabe, Varner, Westerbaan (2024) design X-Wing as a hybrid KEM combining X25519 and ML-KEM-768, intended as the sensible default for most transport-layer security deployments.

## Design

- X-Wing performs **both** X25519 and ML-KEM-768 key agreements in a single round trip
- The client sends both its X25519 public key and its ML-KEM-768 ciphertext in one message; server responds with both shared secrets
- Final shared secret is accepted only if **both** algorithms agree on the same key
- Security is preserved even if one component is computationally broken: an attacker must break both simultaneously

## Security Claim

- Classical security: X25519 (~128-bit)
- Post-quantum security: ML-KEM-768 (~128-bit quantum)
- Tight composable security in the standard model
- Resistant to chosen-ciphertext attacks (CCA2)

## Wiki Connections

- [[post-quantum-cryptography]] — deployment-ready hybrid transition primitive
- [[starfighters-x-wing]] — follow-on analysis of X-Wing's general applicability
- [[post-quantum-cryptographic-governance]] — organizational migration via hybrid deployment
- [[feistel-tools-qrp]] — QROM proof techniques used in analysis

## Source

- `1-1-21.pdf`; IACR Communications in Cryptology Vol. 1, No. 1, 2024
