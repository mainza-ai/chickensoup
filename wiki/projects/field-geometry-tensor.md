---
created: 2026-06-22
protected: true
related:
- time-travel-machinery-architecture
- quantum-systems-comparison
- spacetime
- field-manipulation
sources:
- Einstein-1915
- ADM-1959
- Alcubierre-1994
tags:
- project
- quantum
- tensor
- integration
title: Field Geometry Tensor Specification
updated: '2026-06-25'
---

# Field Geometry Tensor Specification

## Overview

The field geometry tensor is the **intermediate data structure** that flows between the three quantum layers of the time travel machinery. It encodes the complete geometric state of spacetime at each point in the simulation domain and serves as the API contract between:

1. **Spacetime Engine (Qiskit)** — produces the base metric
2. **Field Manipulator (CUDA-Q)** — applies perturbations to the metric
3. **AI Navigator (PennyLane)** — finds optimal paths through the perturbed metric

## Coordinate System

The tensor uses the **3+1 ADM (Arnowitt-Deser-Misner) decomposition** of general relativity, which splits 4D spacetime into:

- **3 spatial dimensions** (x, y, z)
- **1 time slice** (t)

This decomposition is chosen because:
- It maps naturally to quantum circuit encoding (each component is a register)
- The evolution of spatial geometry over time is explicit
- Field manipulations (perturbations) are expressed as modifications to spatial slices

### Grid Structure

```
Spatial grid:  N_x × N_y × N_z
Time slices:   N_t (default: 1 for static, N_t for evolution)

Total grid points: N_x × N_y × N_z × N_t
```

Grid dimensions are configured at runtime by the Spacetime Engine and passed downstream.

## Tensor Shape

### Primary Representation (4×4 metric tensor)

For each grid point, the full 4D metric tensor `g_μν`:

```
Shape: (N_x, N_y, N_z, N_t, 4, 4)
Components: 16 (10 independent, symmetric)
```

### ADM Decomposition

The metric is stored and manipulated in its ADM components for efficiency:

| Component | Symbol | Shape | Count | Physical Meaning |
|-----------|--------|-------|-------|------------------|
| Lapse | `α` | (N_x, N_y, N_z, N_t) | 1 | Rate of proper time per coordinate time |
| Shift | `β_i` | (N_x, N_y, N_z, N_t, 3) | 3 | How spatial coordinates shift between slices |
| 3-Metric | `γ_ij` | (N_x, N_y, N_z, N_t, 3, 3) | 6 | Spatial geometry (symmetric) |

**Total independent components per grid point: 10**

### Reconstruction

The ADM components reconstruct the full 4D metric:

```
g_00 = -α² + β_i β^i
g_0i = β_i
g_ij = γ_ij
```

## Data Structure

```python
@dataclass
class FieldGeometryTensor:
    # Grid dimensions
    shape: tuple[int, ...]  # (N_x, N_y, N_z) or (N_x, N_y, N_z, N_t)

    # Coordinate arrays
    x: np.ndarray  # shape (N_x,)
    y: np.ndarray  # shape (N_y,)
    z: np.ndarray  # shape (N_z,)
    t: np.ndarray  # shape (N_t,) — optional, single slice if omitted

    # ADM components (canonical storage)
    lapse: np.ndarray          # shape (N_x, N_y, N_z, N_t) — scalar α
    shift: np.ndarray           # shape (N_x, N_y, N_z, N_t, 3) — vector β_i
    metric_3d: np.ndarray       # shape (N_x, N_y, N_z, N_t, 3, 3) — symmetric γ_ij

    # Full 4D metric (derived from ADM, or directly populated)
    metric_4d: np.ndarray | None = None  # shape (N_x, N_y, N_z, N_t, 4, 4) — g_μν

    # Extrinsic curvature (derived, optional)
    extrinsic_curvature: np.ndarray | None = None  # shape (N_x, N_y, N_z, N_t, 3, 3) — K_ij

    # Field perturbation (the "manipulation")
    # Applied by CUDA-Q: g'_μν = g_μν + δg_μν
    perturbation: np.ndarray | None = None  # shape same as metric_4d

    # Energy-momentum tensor (source of curvature)
    stress_energy: np.ndarray | None = None  # shape (N_x, N_y, N_z, N_t, 4, 4) — T_μν

    # Curvature invariants (derived, optional)
    ricci_scalar: np.ndarray | None = None       # shape (N_x, N_y, N_z, N_t) — R
    ricci_contracted: np.ndarray | None = None    # shape (N_x, N_y, N_z, N_t) — R_μν R^μν
    riemann_contracted: np.ndarray | None = None  # shape (N_x, N_y, N_z, N_t) — R_μνρσ R^μνρσ

    # Metadata
    coordinate_system: str = "cartesian"
    gauge: str = "harmonic"
    created_by: str = ""  # Which layer created this instance
    parameters: dict = field(default_factory=dict)  # Layer-specific params
```

## Data Flow

### Sequential Pipeline Architecture

The layers compose as pure functions — each takes a `FieldGeometryTensor`, transforms it, passes it to the next:

```
┌────────────────────────────────────────────────────────────────────┐
│                         Qiskit (Spacetime Engine)                   │
│                                                                     │
│  Input: initial conditions (mass distribution, initial metric)      │
│  Output: FieldGeometryTensor(lapse, shift, metric_3d, stress_energy)│
│  Computation:                                                       │
│    1. Solve Einstein field equations: G_μν = 8πG T_μν              │
│    2. Encode metric components as quantum circuits (amplitude       │
│       encoding)                                                     │
│    3. Simulate via Qiskit Aer (GPU-accelerated)                     │
│    4. Extract classical tensor from measurement outcomes             │
└──────────────────────────────────┬─────────────────────────────────┘
                                   │
                                   ▼
┌────────────────────────────────────────────────────────────────────┐
│                      CUDA-Q (Field Manipulator)                    │
│                                                                     │
│  Input: FieldGeometryTensor from Spacetime Engine                   │
│  Output: FieldGeometryTensor(lapse, shift, metric_3d, perturbation)│
│  Computation:                                                       │
│    1. Apply field manipulation to the base metric                   │
│    2. perturbation = encode_manipulation(parameters)                │
│    3. metric'_4d = metric_4d + perturbation (g' = g + δg)          │
│    4. Optionally compute extrinsic curvature K_ij from new metric   │
│    5. GPU-accelerated via CUDA-Q hybrid quantum-classical kernels   │
└──────────────────────────────────┬─────────────────────────────────┘
                                   │
                                   ▼
┌────────────────────────────────────────────────────────────────────┐
│                     PennyLane (AI Navigator)                        │
│                                                                     │
│  Input: FieldGeometryTensor (perturbed metric from CUDA-Q)          │
│  Output: Path[] (optimal trajectories through spacetime)            │
│  Computation:                                                       │
│    1. Compute geodesics from perturbed metric                       │
│    2. Evaluate path cost functional (proper time, energy, risk)     │
│    3. Optimize paths via quantum ML (PennyLane)                     │
│    4. Hardware backends: D-Wave (optimization), IonQ (precision)    │
└────────────────────────────────────────────────────────────────────┘
```

### Pure Functional Interfaces

Each layer implements the same interface:

```python
FieldGeometryTensor → Layer(FieldGeometryTensor, **params) → FieldGeometryTensor
```

This design means:
- **Layers are independently testable** — each can be tested with synthetic inputs
- **The tensor is the contract** — any layer can be replaced as long as it respects the shape and semantics
- **Parallel execution is additive** — once sequential correctness is verified, a service-bus adapter can dispatch to multiple instances of a layer
- **Classical baselines exist** — each quantum layer has a classical CPU/GPU fallback (NumPy/SciPy for Spacetime Engine, array math for Field Manipulator, scipy.optimize for Navigator)

## Serialization

### In-Memory

NumPy arrays with a Pydantic dataclass wrapper. This is the default runtime representation.

### On-Disk (HDF5)

For large grids and persistent storage:

```python
# Write
with h5py.File("field_tensor.h5", "w") as f:
    f.create_dataset("lapse", data=tensor.lapse, compression="gzip")
    f.create_dataset("shift", data=tensor.shift, compression="gzip")
    f.create_dataset("metric_3d", data=tensor.metric_3d, compression="gzip")
    f.attrs["coordinate_system"] = tensor.coordinate_system
    f.attrs["gauge"] = tensor.gauge

# Read
with h5py.File("field_tensor.h5", "r") as f:
    lapse = f["lapse"][:]
    ...
```

### Wire Format (API)

For FastAPI transport between the SwiftUI frontend and the backend:

```json
{
  "shape": [64, 64, 64, 1],
  "coordinate_system": "cartesian",
  "gauge": "harmonic",
  "lapse": "<base64-compressed-numpy>",
  "shift": "<base64-compressed-numpy>",
  "metric_3d": "<base64-compressed-numpy>",
  "created_by": "spacetime_engine",
  "parameters": {
    "resolution": "medium",
    "noise_model": "aer_simulation",
    "shots": 4096
  }
}
```

Base64 encoding uses gzip-compressed, little-endian numpy byte buffers.

### MCP Tool Format

When returned via MCP tools (e.g., `simulate_spacetime`, `analyze_field`):

```json
{
  "tensor": {
    "shape": [64, 64, 64, 1],
    "lapse_shape": [64, 64, 64, 1],
    "shift_shape": [64, 64, 64, 1, 3],
    "metric_3d_shape": [64, 64, 64, 1, 3, 3],
    "size_bytes": 5898240,
    "data": "<base64-compressed-numpy>"
  },
  "summary": {
    "mean_curvature": 0.042,
    "max_perturbation": 0.187,
    "valid_metric": true
  }
}
```

## Validation Rules

Every `FieldGeometryTensor` instance must satisfy these invariants:

### Structural

| Rule | Check | Error |
|------|-------|-------|
| Shape consistency | lapse.shape == shift.shape[:-1] == metric_3d.shape[:-2] | ShapeError |
| Symmetry | metric_3d[..., i, j] == metric_3d[..., j, i] | SymmetryError |
| ADM consistency | g_00 = -α² + β⋅β | ReconstructionError |

### Physical

| Rule | Check | Meaning |
|------|-------|---------|
| Lorentzian signature | g_μν has signature (-, +, +, +) | Time is timelike, space is spacelike |
| Non-degenerate | det(g_μν) < 0 | Metric is invertible |
| Positive lapse | α > 0 everywhere | Time flows forward |
| Physical stress-energy | T_μν satisfies energy conditions | No exotic energy (unless explicitly flagged) |

### Simulation

| Rule | Check | Meaning |
|------|-------|---------|
| Grid bounds | All coordinate values finite | No singularities in domain |
| Reasonable curvature | R_μνρσ R^μνρσ < Planck scale | Classical gravity valid |

## Integration with Each Layer

### Spacetime Engine (Qiskit)

- **Encodes** metric components as quantum registers using amplitude encoding
- **Simulates** the Einstein equations via Hamiltonian simulation (Qiskit Aer)
- **Outputs** the base FieldGeometryTensor with physical metric, stress-energy, and curvature invariants
- **Simulation modes**: `light` (fewer shots, coarser grid for CI), `heavy` (production quality)

### Field Manipulator (CUDA-Q)

- **Reads** the base metric from the Spacetime Engine
- **Computes** the perturbation δg by encoding field manipulation parameters as quantum kernels
- **Outputs** the perturbed metric (base + perturbation) and the perturbation field separately
- **GPU acceleration** via CUDA-Q's hybrid quantum-classical backend

### AI Navigator (PennyLane)

- **Reads** the perturbed metric from the Field Manipulator
- **Computes** geodesic equations: `d²x^μ/dλ² + Γ^μ_ρσ dx^ρ/dλ dx^σ/dλ = 0`
- **Optimizes** path selection via quantum ML (variational circuits)
- **Outputs** one or more candidate paths, each with:
  - Trajectory (sequence of spacetime points)
  - Proper time along path
  - Energy cost
  - Confidence score

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-06-22 | Initial specification |

## See Also

- [[time-travel-machinery-architecture]] — Three-layer architecture
- [[quantum-systems-comparison]] — Platform comparison
- [[integration-architecture]] — Integration decisions
- [[spacetime]] — Spacetime physics
- [[field-manipulation]] — Field manipulation mechanism
- [[closed-timelike-curves]] — CTCs and path geometry

