---
title: "Entropic Action Gravity"
tags: [physics, gravity, entropy, quantum-field-theory, cosmology]
created: 2026-07-13
updated: 2026-07-13
sources: [Bianconi-2025]
related: [entropic-gravity, entropy, quantum-gravity, field-manipulation, dark-matter, holographic-principle, black-hole-entropy]
---

# Entropic Action Gravity

Ginestra Bianconi's framework deriving gravity from a quantum relative entropy (entropic action) between the spacetime metric and the metric induced by matter fields.

## Core Idea

Gravity is not fundamental but emerges from an entropic action. The metric of Lorentzian spacetime is treated as a **renormalizable effective density matrix** (a quantum operator). Matter fields are described topologically via a Dirac-Kähler formalism as the direct sum of a 0-form, 1-form, and 2-form. The matter fields induce an alternative metric **G** that captures how matter curves spacetime.

The action is the **quantum relative entropy** between the spacetime metric **g** and the matter-induced metric **G**:

```
S = (1/ℓ_P) ∫ √|−g| Tr_F ln( G̃ g̃⁻¹ ) d^d x
```

## Key Components

### 1. Topological Matter Fields

Bosonic matter fields are described as:
```
Φ = ϕ ⊕ ω_μ dx^μ ⊕ ζ_μν dx^μ ∧ dx^ν
```
- 0-form ϕ (scalar field)
- 1-form ω_μ (vector field)
- 2-form ζ_μν (tensor field)

The metric induced by these matter fields is expressed via the Hodge-Dirac operator.

### 2. G-Field (Auxiliary Field)

The G-field **G̃** acts as a set of Lagrangian multipliers enforcing linear constraints on the metric induced by matter fields. This transforms the theory into a dressed Einstein-Hilbert action with an emergent positive cosmological constant that depends exclusively on the G-field.

### 3. Modified Einstein Equations

In the linearized limit (α′, β′ ≪ 1), the action reduces to the Einstein-Hilbert action with zero cosmological constant coupled with topological scalar fields:

```
L = 3βR − α|∇ϕ|² − α(m² + ξR)|ϕ|²
```

For non-zero coupling, the equations yield:
- Second-order derivatives only (no Ostrogradsky instability)
- Emergent cosmological constant from G-field
- dressed metric **g̃_G = G̃⁻¹ g** affecting matter propagation

## Relationship to Existing Entropic Gravity

| Aspect | Verlinde/Jacobson | Bianconi (2025) |
|--------|-------------------|-----------------|
| Foundation | Statistical mechanics of spacetime microstates | Quantum relative entropy between metrics |
| Matter coupling | Not primary | Central — matter fields induce metric G |
| Mathematical framework | Thermodynamics + holography | Von Neumann algebras, Araki quantum relative entropy |
| Key novel field | — | G-field (Lagrangian multipliers) |
| Cosmological constant | Not derived | Emergent from G-field |

## Implications

- **Quantum gravity**: Canonical quantization of the G-field coupled to gravity could yield new insights
- **Dark matter**: The G-field may play a role in dark matter dynamics
- **UAP/field manipulation**: If gravity is entropic, manipulating spacetime curvature may involve reconfiguring the metric operator — aligning with [[field-manipulation]] thesis
- **Black hole entropy**: Directly builds on Bekenstein-Hawking entropy; connects to [[holographic-principle]]

## See Also

- [[entropic-gravity]]
- [[entropy]]
- [[quantum-gravity]]
- [[field-manipulation]]
- [[dark-matter]]
- [[holographic-principle]]
- [[black-hole-entropy]]
