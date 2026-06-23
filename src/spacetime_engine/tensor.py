from typing import List, Dict, Any
from pydantic import BaseModel, Field
import numpy as np

class FieldGeometryTensor(BaseModel):
    """
    Represents the ADM 3+1 decomposition of spacetime:
    ds^2 = - (N^2 - N_i N^i) dt^2 + 2 N_i dt dx^i + g_ij dx^i dx^j
    """
    lapse: float = Field(1.0, description="Lapse function N (scalar regulating flow of proper time)")
    shift: List[float] = Field(default_factory=lambda: [0.0, 0.0, 0.0], description="Shift vector N^i (3-vector regulating coordinate movement on spatial slices)")
    spatial_metric: List[List[float]] = Field(
        default_factory=lambda: [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]],
        description="3D spatial metric tensor g_ij (3x3 symmetric matrix)"
    )
    extrinsic_curvature: List[List[float]] = Field(
        default_factory=lambda: [[0.0, 0.0, 0.0], [0.0, 0.0, 0.0], [0.0, 0.0, 0.0]],
        description="Extrinsic curvature tensor K_ij (3x3 symmetric matrix)"
    )
    entropy_density: float = Field(0.0, description="Entropy density of the field slice")
    warp_factor: float = Field(1.0, description="Spacetime distortion warp factor")

    @classmethod
    def create_flat(cls) -> "FieldGeometryTensor":
        """Returns a flat Minkowski spacetime tensor."""
        return cls(
            lapse=1.0,
            shift=[0.0, 0.0, 0.0],
            spatial_metric=[[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]],
            extrinsic_curvature=[[0.0, 0.0, 0.0], [0.0, 0.0, 0.0], [0.0, 0.0, 0.0]],
            entropy_density=0.0,
            warp_factor=1.0
        )

    def to_numpy(self) -> Dict[str, np.ndarray]:
        """Converts components to NumPy arrays."""
        return {
            "lapse": np.array(self.lapse),
            "shift": np.array(self.shift),
            "spatial_metric": np.array(self.spatial_metric),
            "extrinsic_curvature": np.array(self.extrinsic_curvature)
        }
