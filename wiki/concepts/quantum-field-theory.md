---
created: 2026-06-22
protected: true
related:
- quantum-computation
- field-manipulation
- field-geometry-tensor
- spacetime
- fields-vs-particles
sources:
- Peskin-Schroeder-1995
- Carroll-GR-2004
- Babbush-2023
tags:
- quantum
- physics
- qft
title: Quantum Field Theory
updated: '2026-06-25'
---

# Quantum Field Theory

## What QFT Says

Quantum Field Theory (QFT) is the theoretical framework that unifies quantum mechanics with special relativity. Its core claims:

1. **Fields are fundamental** — Every particle type has a corresponding field that exists at every point in spacetime
2. **Particles are excitations** — What we observe as a "particle" is a localized excitation of its field
3. **Interactions are field couplings** — Forces arise from field couplings in the Lagrangian density
4. **Spacetime is also a field** — The metric tensor g_μν is the gravitational field

This is the mathematical foundation for the [[fields-vs-particles]] argument.

## The Lagrangian

The dynamics of any QFT are encoded in its Lagrangian density ℒ:

```
ℒ = ℒ_kinetic + ℒ_mass + ℒ_interaction
```

For the gravitational field (general relativity as an effective field theory):

```
ℒ_GR = (1/16πG) R √(-g)
```

Where R is the Ricci scalar (curvature) and g is the metric determinant. This is the **Einstein-Hilbert action** — the core equation that the [[field-geometry-tensor]] encodes.

## QFT in This Project

### The Spacetime Metric as a Quantum Field

The [[field-geometry-tensor]] is a classical field (not quantum) — it represents the metric g_μν(x) as a continuous function on a discretized grid. However, the *computation* that produces it uses quantum circuits.

This is the regime of **QFT on curved spacetime**: quantum fields (the Qiskit circuits) evolving on a classical curved background (the metric). This is valid below Planck energy (~10¹⁹ GeV), which is the regime this project operates in.

### The Coupled Oscillator Connection

Babbush et al. (2023) proved exponential quantum speedup for simulating coupled classical oscillators. Spacetime itself is a coupled oscillator system — each grid point in the [[field-geometry-tensor]] is coupled to its neighbors via the metric. This is why Hamiltonian simulation on quantum computers can solve the Einstein equations faster than classical methods.

### Key QFT Concepts Used

| Concept | Role in Project |
|---------|----------------|
| **Lagrangian density** | Encodes the dynamics the Spacetime Engine simulates |
| **Effective field theory** | Justifies using QFT on curved spacetime below Planck scale |
| **Field operators** | Quantum gates that act on the metric encoded as qubit registers |
| **Vacuum fluctuations** | Source of "quantum foam" — noise the Field Manipulator must account for |
| **Causality** | Commutators vanish outside light cones — the Navigator must respect this |

## The Gap Between QFT and GR

Quantum gravity (a full theory of quantum fields on a quantum spacetime) does not yet exist. This project does not require it:

- **Scope boundary:** Below Planck energy, QFT on curved classical spacetime is well-understood physics
- **Effective theory:** The Einstein-Hilbert action plus quantum matter fields is an effective field theory — valid in the regime we operate in
- **No quantum gravity needed:** The [[field-geometry-tensor]] is classical; its *computation* is quantum

## Feynman Diagrams

While Feynman diagrams are the standard QFT visualization (particles as lines, interactions as vertices), this project uses **field-based computation** — evolving the field on a grid, not perturbative scattering calculations. The QFT is used as the *justification* for field-based computation, not the *method*.

## See Also

- [[quantum-computation]] — How quantum circuits implement QFT computations
- [[fields-vs-particles]] — Why fields are the chosen paradigm
- [[field-geometry-tensor]] — The classical output of quantum field computations
- [[spacetime]] — The 4D fabric
- [[field-manipulation]] — The mechanism that perturbs the field

