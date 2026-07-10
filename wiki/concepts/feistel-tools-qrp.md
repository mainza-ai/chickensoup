---
title: "Feistel Tools for Quantum Random Permutation Oracles"
tags: [quantum-computation, cryptography, feistel-construction, qrom, post-quantum-cryptography, research-paper, papers]
created: 2026-07-10
updated: 2026-07-10
sources: [2026-146.pdf, Huang-2026]
related: [quantum-computation, post-quantum-cryptography]
---

# Feistel Tools for Quantum Random Permutation Oracles

## Overview

"Feistel Tools: Query-Recording and Reprogramming for QRPs" (Huang, Hülsing, Maram, Ritsch, Saha, 2026) extends QROM proof techniques (query-recording and reprogramming) to the **Quantum Random Permutation Model (QRPM)** using Feistel constructions.

## Key Contributions

- Framework for simulating bidirectional-query random permutation oracles using **Feistel constructions** — ports QROM features for underlying round functions to the overall Feistel-simulated QRP
- **Tighter lower bound** for the query extrapolation problem in bidirectional QRPM
- Recovers meaningful lower bound for the **double-sided zero search problem**
- Proves **adaptive zero-knowledge** property of NIZKs derived from duplex-sponge Fiat-Shamir in a post-quantum setting
- Demonstrates **non-uniform security** in QRPM — a first for this model

## Connection to Project Chicken Soup

- [[post-quantum-cryptography]] — Feistel-based NIZK security in the quantum setting informs the PQC migration strategy
- [[quantum-computation]] — QRPM is more realistic than QROM for many post-quantum protocols; this paper makes QROM-style proofs applicable to a broader class of schemes
- [[backdoor-science]] — adaptive security against non-uniform adversaries with preprocessing mirrors the UAP disclosure problem: how do you design systems secure against adversaries with entrenched classified knowledge?

## Authors

Yu-Hsuan Huang (Max Planck Institute for Security and Privacy), Andreas Hülsing, Varun Maram (Warwick), Silvia Ritsch, Abishanka Saha — TU/e, SandboxAQ.

## Source

- ePrint: 2026/146 — 2026
