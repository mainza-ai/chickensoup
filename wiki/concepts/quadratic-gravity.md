---
title: "Quadratic Gravity"
tags: [physics, quantum-gravity, cosmology]
created: 2026-06-23
updated: 2026-06-23
sources: [Stelle-1977, Turok-Bateman-2026]
related: [neil-turok, quantum-gravity, spacetime, cpt-symmetric-universe]
---

# Quadratic Gravity

## The Theory

Quadratic gravity generalizes the Einstein-Hilbert action by adding terms quadratic in the curvature (Ricci scalar squared + Weyl curvature squared). This makes gravity renormalizable — infinities can be absorbed into coupling constants — and asymptotically free (coupling goes to zero at short distances, like QCD).

$$
S = \int d^4x \sqrt{-g} \left[ \Lambda + \frac{1}{16\pi G} R + \alpha R^2 + \beta C_{\mu\nu\rho\sigma} C^{\mu\nu\rho\sigma} \right]
$$

## The Two Problems

### 1. Ostrogradsky Instability (Classical)

Ostrogradsky's theorem (1850) states that systems with more than two derivatives have unbounded energy — you can have arbitrarily negative energy configurations. Turok argues that in gravity, this instability is actually normal gravitational expansion: the expanding universe is the Ostrogradsky instability, and it is stable when analyzed correctly.

### 2. Negative Norm States (Quantum) 

Higher-derivative theories produce states with negative norm (called "ghosts"). Turok and Bateman resolve this by:

- Working in a **Krein space** (a generalization of Hilbert space allowing positive, negative, and null norm states)
- Requiring **ghost parity symmetry** (operator that gives +1 on positive norm, -1 on negative norm)
- Replacing the Born rule with a **projection operator formulation** that yields positive probabilities despite negative norm states

The modified Born rule: instead of $P = |\langle f|S|i\rangle|^2$, use $P = \text{Tr}(A^\dagger A)$ where $A = P_f S P_i$ (project onto initial state → evolve → project onto final state → trace over all states including ghosts).

## The Scalar Sector

The simplest working limit studies only the scalar mode (Ricci scalar squared), which decouples the spin-2 graviton, vector mode, and spin-2 ghost. This scalar theory is UV complete and describes the local scale of the metric — sufficient for cosmology.

## Connection to CMB

The CMB fluctuations follow the spectrum of a four-derivative field — exactly what quadratic gravity predicts. Turok argues this is direct observational evidence of quantum gravity. The 36 scalar fields needed to cancel standard model divergences match the 36 components of BF theory in loop quantum gravity.

## Implications

If correct, quadratic gravity eliminates the need for:
- String theory and extra dimensions (the assumption of Hilbert space was the key constraint)
- Inflation (CPT-symmetric universe replaces it)
- Fine-tuning (hierarchy problem solved naturally)

## See Also

- [[neil-turok]]
- [[holographic-principle]]
- [[quantum-gravity]]
- [[spacetime]]
