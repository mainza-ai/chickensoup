import logging
import math
from typing import Dict, Any
from src.spacetime_engine.tensor import FieldGeometryTensor

logger = logging.getLogger("chickensoup.spacetime_engine.qiskit")

# Gracefully attempt to import Qiskit
HAS_QISKIT = False
try:
    import qiskit
    from qiskit import QuantumCircuit
    from qiskit.quantum_info import Statevector
    try:
        from qiskit_aer import Aer, AerSimulator
        HAS_AER = True
    except ImportError:
        HAS_AER = False
    HAS_QISKIT = True
except ImportError:
    logger.warning("Qiskit not installed. Spacetime engine will run in classical NumPy fallback mode.")

import time
from src.observability import quantum_simulation_duration

def simulate_spacetime_metrics(target_year: int, energy_level: float) -> FieldGeometryTensor:
    """
    Simulates spacetime warping and Closed Timelike Curves using a Qiskit circuit
    if available, otherwise falls back to classical NumPy.
    """
    start_time = time.perf_counter()
    try:
        return _simulate_spacetime_metrics_impl(target_year, energy_level)
    finally:
        duration = time.perf_counter() - start_time
        quantum_simulation_duration.record(duration)

def _simulate_spacetime_metrics_impl(target_year: int, energy_level: float) -> FieldGeometryTensor:
    logger.info(f"Simulating spacetime for target year {target_year} at energy level {energy_level}...")
    
    # Calculate target parameter based on year difference (anchored at 2026)
    year_diff = abs(target_year - 2026)
    theta = min(math.pi, (year_diff / 100.0) * energy_level)

    if HAS_QISKIT:
        try:
            logger.info("Executing Qiskit spacetime circuit simulation...")
            # 2-qubit circuit: Qubit 0 represents lapse field, Qubit 1 represents spatial warp
            qc = QuantumCircuit(2)
            qc.ry(theta, 0)
            qc.cx(0, 1)
            qc.rz(theta / 2.0, 1)
            
            # Extract statevector
            if HAS_AER:
                # Aer statevector simulator
                backend = AerSimulator(method='statevector')
                job = backend.run(qc)
                state = job.result().get_statevector()
            else:
                # Fallback to local Statevector class
                state = Statevector.from_instruction(qc)
            
            probabilities = state.probabilities()
            
            # Map quantum probabilities to ADM metric parameters
            # p00: flat state, p11: maximally warped state
            p00, p01, p10, p11 = probabilities
            
            lapse = float(1.0 - 0.5 * (p10 + p11))  # Lapse decreases with mass/energy
            warp = float(1.0 + 3.0 * p11)
            entropy = float(-sum(p * math.log(p + 1e-9) for p in probabilities))
            
            spatial_metric = [
                [warp, 0.0, 0.0],
                [0.0, 1.0, 0.0],
                [0.0, 0.0, 1.0]
            ]
            
            extrinsic_curvature = [
                [0.0, 0.0, float(p01)],
                [0.0, 0.0, 0.0],
                [float(p01), 0.0, 0.0]
            ]
            
            shift = [float(p10 * 0.5), 0.0, 0.0]
            
            return FieldGeometryTensor(
                lapse=max(0.1, lapse),
                shift=shift,
                spatial_metric=spatial_metric,
                extrinsic_curvature=extrinsic_curvature,
                entropy_density=entropy,
                warp_factor=warp
            )
        except Exception as e:
            logger.warning(f"Error during Qiskit circuit execution: {e}. Falling back to NumPy.")
            
    # NumPy Classical Fallback
    logger.info("Using NumPy spacetime geometry fallback calculation.")
    import numpy as np
    
    # Simulate a similar state using classical matrices
    # State: cos(theta/2)|00> + sin(theta/2)|11>
    c = np.cos(theta / 2.0)
    s = np.sin(theta / 2.0)
    probs = np.array([c**2, 0.0, 0.0, s**2])
    
    p00, p01, p10, p11 = probs
    
    lapse = float(1.0 - 0.5 * (p10 + p11))
    warp = float(1.0 + 3.0 * p11)
    entropy = float(-sum(p * math.log(p + 1e-9) for p in probs))
    
    spatial_metric = [
        [warp, 0.0, 0.0],
        [0.0, 1.0, 0.0],
        [0.0, 0.0, 1.0]
    ]
    
    extrinsic_curvature = [
        [0.0, 0.0, 0.0],
        [0.0, 0.0, 0.0],
        [0.0, 0.0, 0.0]
    ]
    
    shift = [0.0, 0.0, 0.0]
    
    return FieldGeometryTensor(
        lapse=max(0.1, lapse),
        shift=shift,
        spatial_metric=spatial_metric,
        extrinsic_curvature=extrinsic_curvature,
        entropy_density=entropy,
        warp_factor=warp
    )
