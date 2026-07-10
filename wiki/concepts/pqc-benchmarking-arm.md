---
title: "PQC Benchmarking on ARM Cortex M7"
tags: [post-quantum-cryptography, embedded-systems, benchmarking, lattice-cryptography, research-paper, papers]
created: 2026-07-10
updated: 2026-07-10
sources: [2022-405.pdf, Howe-2022]
related: [post-quantum-cryptography, quantum-computation]
---

# PQC Benchmarking on ARM Cortex M7

## Overview

"Benchmarking and Analysing the NIST PQC Lattice-Based Signature Schemes Standards on the ARM Cortex M7" (Howe & Westerbaan, 2022) evaluates **Dilithium** and **Falcon** — the two NIST-standardized lattice-based digital signature schemes — on the ARM Cortex M7 processor.

## Key Contributions

- ARM Cortex M7 is the only Cortex-M processor with native double-precision (64-bit) FPU — critical for Falcon, which requires 53-bit precision
- **Falcon speedups**: 6.2–8.3× clock cycles, 6.2–11.8× runtime on native FPU vs. software emulation
- Profiling of both schemes on Cortex-M7 to identify remaining bottlenecks
- **Critical security finding**: constant-time irregularities detected on all tested STM32 boards and Raspberry Pi 3 — Falcon is **insecure** on these devices for applications where signature generation can be timed by an attacker

## Connection to Project Chicken Soup

- [[post-quantum-cryptography]] — practical embedded deployment considerations; protocol selection for the Chicken Soup backend's API key authentication under PQC migration
- [[quantum-computation]] — NIST PQC standardization is the near-term response to quantum threat; understanding scheme trade-offs is prerequisite to quantum-safe architecture
- [[backdoor-science]] — timing side-channel discovery suggests Falcon deployment requires careful hardware selection; parallels to how implementation details reveal security properties not visible in the algorithm specification

## Authors

James Howe (SandboxAQ), Bas Westerbaan (Cloudflare).

## Source

- [arXiv:2022-405](https://eprint.iacr.org/2022/405) — 2022
