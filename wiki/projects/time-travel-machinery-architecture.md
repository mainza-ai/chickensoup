---
created: 2026-06-22
protected: true
related:
- time-travel-machinery
- quantum-systems
sources:
- Grusch-2023
- Lazar-1989
tags:
- project
- time-travel
- machinery
- architecture
title: Project Chicken Soup — Architecture
updated: '2026-06-25'
---

# Project Chicken Soup — Architecture

Detailed architecture of the time travel machinery we're building.

## Three-Layer Architecture

### 1. Spacetime Engine (Qiskit)
- Simulates the fabric of time
- Calculates time dilation based on velocity and gravity
- Models closed timelike curves (paths that loop back in time)
- Handles the "where" of spacetime
- **Output:** Base [[field-geometry-tensor]] with lapse, shift, 3-metric, and stress-energy

### 2. Field Manipulator (CUDA-Q)
- The UAP mechanism
- Manipulates the field of spacetime itself
- Creates a bubble, shifts the field, lets the traveler ride the wave
- Uses quantum circuits to represent the time travel path
- Handles the "how" of time travel
- **Input/Output:** Takes base tensor, applies perturbation δg, outputs perturbed tensor

### 3. AI Navigator (PennyLane)
- Uses a neural-field model to find optimal paths
- Learns patterns in the field via quantum machine learning
- Recognizes where to go
- Handles the "when" of time travel
- Hardware backends: D-Wave (optimization), IonQ (precision)
- **Input:** Perturbed tensor → **Output:** optimal trajectories

## Data Flow Between Layers

The layers compose as a **sequential pipeline** — each is a pure function that takes a [[field-geometry-tensor]] and returns a transformed one:

```
Qiskit → (metric tensor) → CUDA-Q → (perturbed tensor) → PennyLane → (paths)
```

The field geometry tensor is the **contract** between layers. Its shape, components, and physics semantics are fixed. Any layer can be replaced independently.

## Timeline Model

Many-Worlds. When you travel back in time, you don't change the past — you branch into a new timeline. The original timeline continues unchanged.

## Implementation

- Python with NumPy for math
- [[field-geometry-tensor]] as the intermediate data structure
- Qiskit for quantum simulation (Spacetime Engine)
- CUDA-Q for hybrid quantum-classical computation (Field Manipulator)
- PennyLane for quantum machine learning (AI Navigator)
- D-Wave for optimization
- IonQ for precision
- HDF5 for on-disk tensor storage
- matplotlib for visualization

## Trade-offs

- **Quantum vs. Classical**: Quantum is more powerful but more expensive. Classical is cheaper but slower. All layers have classical fallbacks (see [[quantum-simulation-tier]]).
- **Simulation vs. Hardware**: Simulation is easier to test. Hardware is more realistic. Three-tier simulation (light/medium/heavy) for CI through production.
- **Many-Worlds vs. Fixed Timeline**: Many-worlds is more flexible. Fixed timeline is more realistic.
- **Sequential vs. Service Bus**: Sequential first for correctness. Bus later for parallel exploration of multiple field configurations.

## See Also

- [[time-travel-machinery]]
- [[quantum-systems]]
- [[time-travel]]
- [[field-manipulation]]

