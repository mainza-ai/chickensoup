---
title: "Weak Measurement"
tags: [quantum, measurement, retrocausality, time]
created: 2026-06-23
updated: 2026-06-23
sources: [Aharonov-Albert-Vaidman-1988]
related: [arrow-of-time, temporal-quantum-tomography, closed-timelike-curves, time-travel, quantum-computation]
---

# Weak Measurement

## The Core Idea

Weak measurement (Aharonov, Albert, Vaidman, 1988) is a technique for measuring a quantum system without significantly disturbing it. By coupling the measurement apparatus very weakly, the system's state is not collapsed, but the information obtained per trial is also very small. By averaging over many trials, statistically significant information emerges.

## Conditional Measurements

The critical innovation is that weak measurements are **conditional measurements**: they allow asking "what was the average momentum of the particles that later reached a specific detector?" This makes it possible to talk about the history of a system between preparation and detection — something textbook quantum mechanics traditionally denied.

$$
\langle p \rangle_{\text{conditional}} = \frac{\langle \psi_f | p | \psi_i \rangle}{\langle \psi_f | \psi_i \rangle}
$$

This is the **weak value** — the conditioned expectation of an observable between pre-selected and post-selected states.

## Time Symmetry

Weak measurement reveals the time symmetry of quantum mechanics:
- The same mathematical formalism works for predicting the future (from initial state) and retrodicting the past (from final state)
- Both initial and final boundary conditions are equally useful for determining what happened in between
- This challenges the standard view that measurement breaks time symmetry by collapsing the state

## Retrocausality

Yakir Aharonov interprets weak measurements as evidence that **the future informs the past** — ontologically, not just epistemically. The conditional nature of weak values means the future boundary condition constrains the past. This is controversial: many physicists accept the mathematics but dispute the metaphysical interpretation.

## Arrow of Time Implications

If both past and future boundary conditions constrain the present, the arrow of time may not be fundamental. The standard thermodynamic arrow (entropy increases from the Big Bang) may coexist with future boundary conditions we don't yet understand. Some researchers speculate the universe is conditioned both by how it starts and how it ends.

## Connection to Temporal Reasoning

Weak measurement provides a mathematical framework for:
- [[temporal-quantum-tomography]]: reconstructing the quantum state of spacetime between events
- [[time-travel]]: if future boundary conditions affect the present, time travel is information flow from future to past
- [[temporal-information-fusion]]: combining pre-selected and post-selected information

## See Also

- [[arrow-of-time]]
- [[temporal-quantum-tomography]]
- [[quantum-computation]]
- [[time-travel]]
- [[closed-timelike-curves]]
