import logging
import math
from typing import Dict, Any, List, Optional, Tuple

import numpy as np

from src.spacetime_engine.tensor import FieldGeometryTensor
from src.spacetime_engine.entanglement import meyer_wallach, is_entangled_state

logger = logging.getLogger("chickensoup.spacetime_engine.vqe_runner")

HAS_AER_V2 = False
HAS_AER = False
HAS_QISKIT = False

try:
    import qiskit
    from qiskit import QuantumCircuit
    try:
        from qiskit_aer import Aer
        HAS_AER = True
    except ImportError:
        try:
            from qiskit.quantum_info import Statevector
            HAS_AER = False
        except ImportError:
            pass

    try:
        from qiskit_aer.primitives import EstimatorV2 as AerEstimatorV2
        HAS_AER_V2 = True
    except ImportError:
        try:
            from qiskit.primitives import EstimatorV2 as AerEstimatorV2
            HAS_AER_V2 = True
        except ImportError:
            try:
                from qiskit_aer.primitives import Estimator as AerEstimatorV2
                HAS_AER_V2 = True
            except ImportError:
                HAS_AER_V2 = False

    HAS_QISKIT = True
except ImportError:
    logger.info("Qiskit not available — VQE runner in classical fallback mode")


def build_claim_state_circuit(
    amplitudes: List[float],
    entanglement_penalty: float = 0.0,
) -> Tuple[Any, np.ndarray]:
    n_states = len(amplitudes)
    if n_states == 0:
        return None, np.array([])

    # Normalise amplitudes to probabilities then to statevector
    amps = np.array(amplitudes, dtype=float)
    norm = np.linalg.norm(amps)
    if norm < 1e-12:
        amps = np.ones(n_states) / math.sqrt(n_states)
    else:
        amps = amps / norm

    # Map to qubit register: need ceil(log2(n_states)) qubits
    n_qubits = max(1, math.ceil(math.log2(n_states))) if n_states > 1 else 1

    if not HAS_QISKIT:
        # Return probabilities directly as fallback
        return None, amps

    try:
        qc = QuantumCircuit(n_qubits)

        # Encode amplitudes via RY rotations — simplified amplitude encoding
        # For 2 qubits / 3 basis states we can do explicit state prep
        if n_qubits == 1:
            theta = 2 * math.acos(float(np.clip(amps[0] if len(amps) > 0 else 1.0, -1.0, 1.0)))
            if len(amps) > 1:
                qc.ry(theta, 0)
            # single qubit |0>/|1> mapped to first two basis states
        elif n_qubits == 2:
            # For 3 states we use 2 qubits: |00>, |01>, |10> → map to basis
            # Use RY on qubit 0 to split between ground and superposition
            # This is a simplified state prep for the 3-basis claim system
            p0 = float(amps[0] ** 2) if len(amps) > 0 else 1.0 / 3
            p1 = float(amps[1] ** 2) if len(amps) > 1 else 1.0 / 3
            p2 = float(amps[2] ** 2) if len(amps) > 2 else 1.0 / 3
            total = p0 + p1 + p2
            if total > 1e-12:
                p0 /= total
                p1 /= total
                p2 /= total

            # Use amplitude encoding: RY(theta0) on q0, controlled RY on q1
            # theta0 = 2*arccos(sqrt(p0))
            theta0 = 2 * math.acos(math.sqrt(max(0.0, min(1.0, p0))))
            qc.ry(theta0, 0)

            # For the |1> branch of q0, split between |01> and |10>
            remaining = 1.0 - p0
            if remaining > 1e-12:
                r = p1 / remaining if remaining > 1e-12 else 0.5
                theta1 = 2 * math.acos(math.sqrt(max(0.0, min(1.0, r))))
                # Controlled RY
                qc.x(0)
                qc.ry(theta1, 1)
                qc.x(0)
                # When q0=1, q1=0 → |10> corresponds to p2 branch, |11> is p1 branch after RY on q1 controlled by q0
                # Adjust: we need |01> and |10>/<11> mapping — use CX to entangle appropriately
                qc.cx(0, 1)

        return qc, amps

    except Exception as e:
        logger.debug(f"Failed to build claim circuit: {e}")
        return None, amps


def run_vqe_estimation(
    circuit: Any,
    hamiltonian_label: str = "claim_confidence",
) -> Dict[str, Any]:
    if circuit is None or not HAS_QISKIT:
        return {
            "backend": "numpy-fallback",
            "entanglement_score": 0.0,
            "expectation": 0.0,
            "collapsed": False,
        }

    try:
        # Try AerEstimatorV2 path first
        if HAS_AER_V2:
            try:
                from qiskit.quantum_info import SparsePauliOp
                # Simple Z-measurement Hamiltonian — <Z> encodes bias toward corroborated basis
                # For 2 qubits, weight Z0 higher (first basis = corroborated)
                if circuit.num_qubits == 1:
                    hamiltonian = SparsePauliOp.from_list([("Z", 1.0)])
                else:
                    # Weight: +1.0 on Z0 (distinguishes |0> vs |1> on first qubit), +0.5 on Z1
                    hamiltonian = SparsePauliOp.from_list(
                        [("Z" + "I" * (circuit.num_qubits - 1), 1.0),
                         ("I" + "Z" + "I" * (circuit.num_qubits - 2), 0.5)] if circuit.num_qubits >= 2
                        else [("Z", 1.0)]
                    )

                # Statevector simulation to extract entanglement
                try:
                    from qiskit.quantum_info import Statevector
                    sv = Statevector.from_instruction(circuit)
                    sv_data = sv.data
                    ent_score = meyer_wallach(np.array(sv_data))
                except Exception:
                    ent_score = 0.0

                # Expectation estimation
                try:
                    estimator = AerEstimatorV2()
                    # AerEstimatorV2 API: estimator.run([(circuit, hamiltonian)]])
                    pub = (circuit, hamiltonian)
                    job = estimator.run([pub])
                    result = job.result()
                    exp_val = float(result[0].data.evs) if hasattr(result[0].data, 'evs') else 0.0
                except Exception as est_err:
                    logger.debug(f"AerEstimatorV2 estimation failed: {est_err}, using classical fallback")
                    exp_val = 0.0
                    ent_score = ent_score if 'ent_score' in locals() else 0.0

                return {
                    "backend": "AerEstimatorV2" if HAS_AER_V2 else "Statevector",
                    "entanglement_score": ent_score,
                    "expectation": exp_val,
                    "collapsed": abs(exp_val) > 0.7,
                }

            except Exception as v2_err:
                logger.debug(f"VQE V2 path failed: {v2_err}")

        # Fallback: Aer statevector simulator (legacy path, kept for compatibility)
        if HAS_AER:
            try:
                backend = Aer.get_backend("statevector_simulator")
                job = backend.run(circuit)
                state = job.result().get_statevector()
                probs = state.probabilities() if hasattr(state, 'probabilities') else np.abs(state.data) ** 2
                probs = np.array(probs)

                try:
                    sv_data = state.data if hasattr(state, 'data') else np.array(probs)
                    ent_score = meyer_wallach(np.array(sv_data))
                except Exception:
                    ent_score = 0.0

                return {
                    "backend": "Aer-statevector",
                    "entanglement_score": ent_score,
                    "expectation": float(probs[0] - probs[-1]) if len(probs) > 1 else 0.0,
                    "probabilities": probs.tolist(),
                    "collapsed": float(np.max(probs)) > 0.7 if len(probs) > 0 else False,
                }
            except Exception as aer_err:
                logger.debug(f"Aer fallback failed: {aer_err}")

        return {
            "backend": "numpy-fallback",
            "entanglement_score": 0.0,
            "expectation": 0.0,
            "collapsed": False,
        }

    except Exception as e:
        logger.warning(f"VQE estimation error: {e}")
        return {
            "backend": "numpy-fallback-error",
            "entanglement_score": 0.0,
            "expectation": 0.0,
            "collapsed": False,
            "error": str(e),
        }


def score_claim_state(
    amplitudes: List[float],
) -> Dict[str, Any]:
    circuit, norm_amps = build_claim_state_circuit(amplitudes)
    vqe_result = run_vqe_estimation(circuit)

    probs = norm_amps ** 2 if len(norm_amps) > 0 else np.array([1.0 / 3, 1.0 / 3, 1.0 / 3])
    # Renormalise probs
    if probs.sum() > 1e-12:
        probs = probs / probs.sum()

    collapsed = bool(probs.max() > 0.75) if len(probs) > 0 else False
    # Also consider VQE collapsed signal
    if vqe_result.get("collapsed"):
        collapsed = True

    return {
        "amplitudes": norm_amps.tolist() if hasattr(norm_amps, 'tolist') else list(norm_amps),
        "probabilities": probs.tolist() if hasattr(probs, 'tolist') else list(probs),
        "collapsed": collapsed,
        "vqe": vqe_result,
    }
