import logging
import math
from typing import Optional

import numpy as np

logger = logging.getLogger("chickensoup.spacetime_engine.entanglement")


def meyer_wallach(statevector: np.ndarray) -> float:
    n = int(math.log2(len(statevector)))
    if n <= 0:
        return 0.0
    if 2 ** n != len(statevector):
        # Pad to next power of two if needed (should not happen for proper statevectors)
        next_pow = 2 ** math.ceil(math.log2(len(statevector)))
        padded = np.zeros(next_pow, dtype=complex)
        padded[:len(statevector)] = statevector
        statevector = padded
        n = int(math.log2(len(statevector)))

    # Normalise
    norm = np.linalg.norm(statevector)
    if norm < 1e-12:
        return 0.0
    psi = statevector / norm

    # Reshape to n-qubit tensor: shape (2,)*n
    psi_tensor = psi.reshape([2] * n)

    # Q = 1 - (1/n) sum_k Tr(rho_k^2)
    # rho_k = reduced density matrix of qubit k (tracing out all others)
    total_purity = 0.0
    for k in range(n):
        # Move k-th axis to front, then reshape to (2, rest)
        perm = [k] + [i for i in range(n) if i != k]
        transposed = np.transpose(psi_tensor, perm)
        mat = transposed.reshape(2, -1)  # (2, 2^{n-1})

        # rho_k = mat @ mat^dagger (2x2)
        rho_k = mat @ mat.conj().T
        purity = float(np.real(np.trace(rho_k @ rho_k)))
        total_purity += purity

    q = 1.0 - (total_purity / n)
    # Clamp to [0,1] — may slightly exceed due to numerical errors
    return float(max(0.0, min(1.0, q)))


def meyer_wallach_from_probs(probs: np.ndarray) -> float:
    # Classical proxy: treat probs as diagonal mixed state's effective entanglement
    # Q ≈ 1 - (1/n) sum purity — for sparse high-diversity distributions, Q is higher
    # We map entropy to approximate Q via normalised entropy
    probs = np.asarray(probs, dtype=float)
    probs = probs[probs > 1e-12]
    if len(probs) == 0:
        return 0.0
    # Normalise
    probs = probs / probs.sum()
    # Normalised Shannon entropy as proxy for entanglement when full statevector unavailable
    # entropy / log(d) in [0,1] — we map to Q-like scale
    try:
        ent = -float(np.sum(probs * np.log(probs)))
        max_ent = math.log(len(probs)) if len(probs) > 1 else 1.0
        q_proxy = ent / max_ent if max_ent > 1e-9 else 0.0
        return float(max(0.0, min(1.0, q_proxy)))
    except Exception as e:
        logger.debug(f"meyer_wallach_from_probs failed: {e}")
        return 0.0


def is_entangled_state(statevector: np.ndarray, threshold: float = 0.3) -> bool:
    return meyer_wallach(statevector) >= threshold
