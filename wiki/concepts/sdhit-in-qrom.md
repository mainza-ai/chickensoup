---
title: "SDitH in the Quantum Random Oracle Model"
tags: [post-quantum-cryptography, code-based-cryptography, signatures, qrom, research-paper, papers]
created: 2026-07-10
updated: 2026-07-10
sources: [2023-756.pdf, Aguilar-Melchor-2023]
related: [post-quantum-cryptography, quantum-computation]
---

# SDitH in the Quantum Random Oracle Model

## Overview

"SDitH in the QROM" (Aguilar-Melchor et al., 2023) provides the first **tight security proof in the Quantum Random Oracle Model (QROM)** for the Hypercube-MPCitH-based **SDitH** ( Syndrome Decoding in the Head) signature scheme, reducing it from five rounds to three.

## Key Contributions

- Compresses Hypercube-MPCitH from 5-round to **3-round code-based identification scheme**
- Tight security proof in QROM avoiding catastrophic reduction losses from generic QROM-to-classical translations
- Reduces online cost further using proof-of-work techniques
- Generalizes QROM proof techniques and introduces **extractable QROM** variant
- Current state-of-the-art for code-based signature sizes

## Connection to Project Chicken Soup

- [[post-quantum-cryptography]] — SDitH is a leading candidate for code-based PQC signatures
- [[quantum-computation]] — QROM security proofs are essential for analyzing protocols that will run alongside quantum systems
- [[backdoor-science]] — tight QROM proofs reduce the attack surface available to quantum adversaries, analogous to how classified physics reduces uncertainty in the UAP context

## Authors

Carlos Aguilar-Melchor, Andreas Hülsing, David Joseph, Christian Majenz, Eyal Ronen, Dongze Yue — SandboxAQ, TU Denmark, Tel Aviv University.

## Source

- ePrint: 2023/756 — [iacr.org](https://eprint.iacr.org/2023/756)
