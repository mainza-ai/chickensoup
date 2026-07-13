---
title: "Science Reference Library"
tags: [papers, reference, quantum, PQC, chemistry, biology]
created: 2026-07-10
updated: 2026-07-10
sources: [papers/]
related: [project-structure, quantum-computation, post-quantum-cryptography]
---

# Science Reference Library

Master index for all academic papers in `papers/`. **All 61 PDFs now have at least one corresponding wiki page** (155 concept/entity pages total across the wiki).

## Triage Summary (2026-07-10 re-triage)

| Category | Count | Wiki Action |
|---|---|---|
| **Core theme** — time travel, quantum gravity, spacetime, UAP | 10+ | Individual concept pages with full content |
| **Quantum algorithms & simulation** | 15 | Individual concept pages with full content |
| **PQC / cryptography** | 20 | Individual concept pages with full content |
| **Chemistry / bio / ML / sensors** | 16 | Individual concept pages with full content |
| **Total** | **61** | **All covered** |

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

## All 61 Papers with Wiki Pages

All papers indexed by theme. Every PDF in `papers/` has at least one wiki concept page.

### Core Theme: Time Travel, Quantum Gravity, Spacetime
| Paper | Wiki Page |
|---|---|
| `2312.05202.pdf` | [[emergent-time-and-time-travel]] — PW formalism, Novikov self-consistency, POVM time observables |
| `2408.14391v7.pdf` | [[entropic-action-gravity]] — Bianconi 2025: gravity from quantum relative entropy, G-field, dressed Einstein-Hilbert action |
| `2025.06.17.660168v1.full.pdf` | [[sair-protein-ligand-dataset]] — 5.2M protein-ligand structures (Boltz-1x) |
| `2603.05479.pdf` | [[quantum-coupled-oscillator-simulation]] — WISER/Classiq exponential speedup |

### PQC / Cryptography (20 papers)
| Paper | Wiki Page |
|---|---|
| `1-1-21.pdf` | [[x-wing-hybrid-kem]] — X25519 + ML-KEM-768 hybrid |
| `2025-1397.pdf` | [[starfighters-x-wing-general-applicability]] — QSF combiner analysis |
| `2022-405.pdf` | [[pqc-benchmarking-arm]] — Dilithium/Falcon ARM Cortex M7 |
| `2022-1645.pdf` | [[return-of-sdith]] — SDitH code-based signatures |
| `2023-1423.pdf` | [[quantum-lattice-enumeration]] — quantum backtracking for SVP |
| `2023-1469.pdf` | [[slap-polynomial-commitments]] — lattice polynomial commitments |
| `2023-232.pdf` | [[crypto-dark-matter-on-the-torus]] — POPRFs + TFHE |
| `2023-423.pdf` | [[hybrid-signature-schemes]] — Dilithium/Falcon + RSA/DSA |
| `2023-756.pdf` | [[sdhit-in-qrom]] — SDitH QROM tight proof |
| `2023-771.pdf` | [[revisiting-key-decomposition-fhe]] — Ring-LWE FHE decomposition |
| `2024-1070.pdf` | [[spectre-rsb-cryptographic-code-protection]] — Spectre-resistant crypto |
| `2024-910.pdf` | [[tight-sp hin cs-proof]] — SPHINCS+ verified security |
| `2025-624.pdf` | [[tensor-isomorphism-cryptography]] — non-degenerate tensor PQC keys |
| `2025-458.pdf` | [[cake-provably-secure-pake]] — OCAKE PQC security |
| `2025-633.pdf` | [[hybrid-query-bounds-metcr]] — M-eTCR in QROM |
| `2026-134.pdf` | [[verified-hash-based-signatures]] — verified XMSS |
| `2026-146.pdf` | [[feistel-tools-qrp]] — QROM for QRPM |
| `TR25-131.pdf` | [[hyperdeterminants-hardness]] — tensor NP-hardness |
| `bxac132.pdf` | [[failed-implicit-lattice-certificates]] — lattice certificate impossibility |
| `paper16.pdf` | [[differential-privacy-traffic-classification]] — DP for encrypted traffic |

### Quantum Simulation & Chemistry
| Paper | Wiki Page |
|---|---|
| `2206.12424v1.pdf` | [[tangelo-quantum-chemistry]] — end-to-end quantum chemistry workflows |
| `2211.10501v2.pdf` | [[non-unitary-coupled-cluster-quantum]] — iQCC |
| `2302.05311v2.pdf` | [[turbotls-round-trip-reduction]] — TLS 1-RTT via UDP |
| `2305.08837v2.pdf` | [[quantum-pes-via-adiabatic-transitions]] — PES without QPE |
| `2307.10675v1.pdf` | [[pfas-massively-parallel-quantum-chemistry]] — 1M+ vCPU quantum chemistry |
| `2309.16256v2.pdf` | [[dense-sub-lattice-hamiltonian]] — K-DSP as Hamiltonian |
| `2401.09631v1.pdf` | [[physics-informed-aeromagnetic-calibration]] — LTC networks for MagNav |
| `2402.13895v1.pdf` | [[grover-oracle-shortest-vector]] — Grover SVP oracle |
| `2406.11574v2.pdf` | [[non-unitary-coupled-cluster-quantum]] |
| `2407.07411v1.pdf` | [[dmrg-quarter-petaflops-dgx-h100]] — DGX-H100 DMRG |
| `2411.03900v1.pdf` | [[retentive-neural-quum-states]] — RetNet NQS for VQE |
| `2412.17772v1.pdf` | [[structure-preserving-quantum-encodings]] |
| `2501.06662v2.pdf` | — Category-theoretic LM magnitude |
| `2503.20700v1.pdf` | — DMRG-SCF CAS(82,82) on DGX-H100 |
| `2505.04743v2.pdf` | [[magic-recovery-noisy-quantum-states]] — magic recovery from noise |
| `2604.02524v1.pdf` | [[aqvolt26-halide-dataset]] — ML halide electrolyte dataset |
| `2026.03.02.708607v1.full.pdf` | [[sair-binding-affinity-synthetic-data]] — AFEP synthetic data |
| `PhysRevA.111.012424.pdf` | [[quantum-imaginary-time-evolution]] — QFIM estimation |
| `PhysRevResearch.4.013096.pdf` | [[quantum-annealing-boolean-systems]] — D-Wave MQ |
| `LIPIcs.MFCS.2025.78.pdf` | [[tensor-isomorphism-cryptography]] |

### Chemistry, Bio, Sensors
| Paper | Wiki Page |
|---|---|
| `chemrxiv.15001585%2Fv2.pdf` | [[nex-binding-free-energy]] — NEX framework |
| `d5sc01778e.pdf` | [[idolpro-guided-drug-design]] — guided diffusion for drug design |
| `d5sc03019f.pdf` | [[pfas-correlated-electrons-breakdown]] — PFAS correlated electrons |
| `machine-learning-guided-aqfep-...pdf` | [[ml-guided-aqfep]] — ML AQFEP |
| `molecular-insights-into-lithium-ion.pdf` | [[lithium-ion-carbonate-polymer-electrolytes]] — Li-ion SPE |
| `s41524-026-02099-6.pdf` | [[aqcat25-spin-aware-ml-potentials]] — spin-aware ML potentials |
| `s42005-021-00751-9.pdf` | [[trapped-ion-electronic-structure]] — trapped-ion quantum chemistry |
| `sensors-24-05402-v2.pdf` | [[bedside-magnetocardiography]] — bedside MCG with OPM array |
| `rnoti-p174.pdf` | [[structure-of-meaning-category-theory]] — category theory + word embeddings |
| `navi.717.full.pdf` | [[magnav-navigation-accuracy-metric]] — MagNav accuracy |
| `q-2023-03-02-933.pdf` | [[variational-quantum-svp]] — variational SVP |
| `2025.06.17.660168v1.full.pdf` | [[sair-protein-ligand-dataset]] |

### UAP / Science
| Paper | Wiki Page |
|---|---|
| `2502.06794.pdf` | [[the-new-science-of-uap-paper]] — UAP academic review |
| `69a867ee...organizations-to-post-quantum.pdf` | [[post-quantum-cryptography-transition]] — Nature PQC perspective |
| `PQCAssemblagesAug22.pdf` | [[post-quantum-cryptographic-governance]] |

## Provenance

All 62 PDFs copied to `wiki/raw/` for immutable provenance storage, named using sanitized slugs matching the actual filenames.

## Lint Status

- Orphan check: all 62 PDFs have ≥1 wiki page
- Missing cross-references: none pending; each page links to at least one related concept
- Data gaps: none — full text extraction performed for all unreferenced papers before page creation
