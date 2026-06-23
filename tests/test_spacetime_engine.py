import numpy as np
from unittest.mock import patch, MagicMock
from src.spacetime_engine.tensor import FieldGeometryTensor
from src.spacetime_engine.qiskit_simulation import simulate_spacetime_metrics

def test_field_geometry_tensor_flat():
    tensor = FieldGeometryTensor.create_flat()
    assert tensor.lapse == 1.0
    assert tensor.shift == [0.0, 0.0, 0.0]
    assert tensor.warp_factor == 1.0
    
    np_dict = tensor.to_numpy()
    assert isinstance(np_dict["lapse"], np.ndarray)
    assert np_dict["lapse"] == 1.0
    assert np_dict["shift"].tolist() == [0.0, 0.0, 0.0]

def test_simulate_spacetime_metrics_classical_fallback():
    # Force HAS_QISKIT to False to test classical NumPy fallback
    with patch("src.spacetime_engine.qiskit_simulation.HAS_QISKIT", False):
        tensor = simulate_spacetime_metrics(target_year=1947, energy_level=2.0)
        assert isinstance(tensor, FieldGeometryTensor)
        assert tensor.warp_factor > 1.0
        assert tensor.lapse <= 1.0

def test_simulate_spacetime_metrics_qiskit_execution():
    # Force HAS_QISKIT to True and mock Aer and Statevector response
    mock_state = MagicMock()
    mock_state.probabilities.return_value = [0.1, 0.2, 0.3, 0.4]  # p00, p01, p10, p11
    
    with patch("src.spacetime_engine.qiskit_simulation.HAS_QISKIT", True), \
         patch("src.spacetime_engine.qiskit_simulation.QuantumCircuit") as mock_qc_cls, \
         patch("src.spacetime_engine.qiskit_simulation.Statevector.from_instruction", return_value=mock_state), \
         patch("src.spacetime_engine.qiskit_simulation.HAS_AER", False):
         
        tensor = simulate_spacetime_metrics(target_year=1937, energy_level=1.5)
        
        # Verify metric calculation derived from mocked probabilities
        # p00, p01, p10, p11 = 0.1, 0.2, 0.3, 0.4
        # lapse = 1.0 - 0.5 * (0.3 + 0.4) = 0.65
        # warp = 1.0 + 3.0 * 0.4 = 2.2
        assert tensor.lapse == 0.65
        assert tensor.warp_factor == 2.2
