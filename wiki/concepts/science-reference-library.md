---
title: "Science Reference Library"
tags: [papers, reference, quantum, PQC, chemistry, biology]
created: 2026-07-10
updated: 2026-07-10
sources: [papers/]
related: [project-structure, quantum-computation, post-quantum-cryptography]
---

# Science Reference Library

This page is the master index for all academic papers in `papers/`. 61 PDFs + 1 DOCX (already ingested separately as [[kordylewski-clouds]] transcript).

## Triage Summary

| Category | Count | Wiki Action |
|---|---|---|
| **HIGH** — directly relevant to wiki themes | 11 | Individual wiki pages created |
| **MEDIUM** — tangentially relevant | 14 | Indexed here, no individual pages |
| **LOW** — pure chemistry/bio/math, no wiki relevance | 36 | Indexed here only |
| **Scanned/blank** | 0 | None |

## HIGH-Relevance Papers (11) — Individual Pages Created

### Quantum Simulation & Algorithms
- [[quantum-coupled-oscillator-simulation]] — WISER/Classiq 2026: exponential quantum speedup for coupled oscillator simulation (2603.05479)
- [[non-unitary-coupled-cluster-quantum]] — Fleury et al. 2024: mid-circuit measurements for CC ansatz, 28% CNOT reduction (2406.11574)
- [[structure-preserving-quantum-encodings]] — Parzygnat et al. 2024: category-theoretic QML encoding framework (2412.17772)
- [[quantum-imaginary-time-evolution]] — Kolotouros et al. 2025: rapid QFIM estimation via random measurements (PhysRevA.111.012424)
- [[quantum-annealing-boolean-systems]] — Ramos-Calderer et al. 2022: D-Wave MQ problem embedding (PhysRevResearch.4.013096)
- [[grover-oracle-shortest-vector]] — Prokop et al. 2024: Grover oracle construction for SVP (2402.13895)
- [[dense-sub-lattice-hamiltonian]] — Barberá-Rodríguez et al. 2024: K-DSP as Hamiltonian first excited state (2309.16256)
- [[retentive-neural-quantum-states]] — Knitter et al. 2024: RetNet as NQS ansatz for VQE (2411.03900)
- [[magic-recovery-noisy-quantum-states]] — Lloyd et al. 2026: recovering magic/entanglement from noisy states (2505.04743)

### Post-Quantum Cryptography
- [[post-quantum-cryptography-transition]] — Nature 2022 Perspective on organizational PQC migration (69a867ee)
- [[post-quantum-cryptographic-governance]] — Csenkey & Bindel 2022: assemblage theory for quantum threat governance (PQCAssemblagesAug22)
- [[batch-signatures]] — Aguilar-Melchor et al. 2023: 3.2× TLS throughput for Falcon-512 (2023-492)
- [[sdhit-in-qrom]] — Aguilar-Melchor et al. 2023: tight QROM proof for code-based SDitH (2023-756)
- [[tensor-isomorphism-cryptography]] — Narayanan 2025: non-degenerate tensor sampling for PQC keys (LIPIcs.MFCS.2025.78)
- [[verified-hash-based-signatures]] — Barbosa et al. 2026: first verified XMSS implementation (2026-134)
- [[feistel-tools-qrp]] — Huang et al. 2026: QROM techniques extended to QRPM (2026-146)

### UAP / Science
- [[the-new-science-of-uap-paper]] — Knuth et al. 2025: 195-page multi-author UAP academic review (2502.06794)

## MEDIUM-Relevance Papers (14) — Indexed Only

| Paper | Slug | Description |
|---|---|---|
| NIST PQC Benchmarking on ARM Cortex M7 | 2022-405 | Dilithium/Falcon performance on embedded; Falcon timing side-channel |
| Trapdoor one-way functions from tensors | 2025-624 | GPV-style trapdoors via Vandermonde-Weyman-Zelevinsky tensors (SandboxAQ) |
| SAIR synthetic protein-ligand dataset | 2025.06.17 | 5.2M structures, Boltz-1x folding, binding affinity benchmark (SandboxAQ/NVIDIA) |
| Orbital optimization via AI-accelerators | 2503.20700 | DMRG-SCF CAS(82,82) on NVIDIA DGX-H100 (SandboxAQ/Max Planck) |
| Variational quantum SVP | q-2023-03-02-933 | NISQ-era SVP via Hamiltonian ground-state, dimension-28 on emulation |
| Physics-Informed Aeromagnetic Calibration | 2401.09631 | LTC networks for airborne mag-nav (Stanford/SandboxAQ) |
| Iterative Qubit Coupled Cluster | 2211.10501v2 | Clifford-only iQCC variant (SandboxAQ/Dow/qBraid/DLR) |
| Category Magnitude of LM-enriched texts | 2501.06662v2 | Category-theoretic magnitude/Tsallis entropy for LLM corpora |

## LOW-Relevance Papers (36) — Reference Only

Pure chemistry (lithium electrolytes, quantum chemistry packages, DMRG petaflops), pure biology (protein folding, AQFEP), pure CS/math (TLS, hyperdeterminants, category theory, privacy, sensors), and technical IACR/NIST PQC internals.

Full list with filenames: see `papers/triage-report-full.json`.

## Provenance

All PDFs copied to `wiki/raw/` for immutable provenance storage. Raw copies use sanitized slugs derived from original filenames.
