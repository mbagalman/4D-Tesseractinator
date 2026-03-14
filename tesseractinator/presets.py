"""Preset rotations used by the notebook dashboard and regression tests."""

from __future__ import annotations

from typing import Dict

import numpy as np

AngleDict = Dict[str, float]

__all__ = ["standard_presets"]


def standard_presets() -> Dict[str, AngleDict]:
    return {
        "identity": {},
        "xy_45": {"xy": np.pi / 4},
        "xy_90": {"xy": np.pi / 2},
        "xyz_equal": {"xy": np.pi / 6, "xz": np.pi / 6, "yz": np.pi / 6},
        "4d_symmetric": {"xy": np.pi / 4, "xz": np.pi / 4, "xw": np.pi / 4},
        "complex": {
            "xy": 0.6,
            "xz": 0.7,
            "yz": 0.4,
            "xw": 0.9,
            "yw": 1.2,
            "zw": 0.3,
        },
        "rhombic_dodeca": {"xy": 0.5, "xw": 0.5, "yz": 0.3},
        "octahedron": {"xy": np.pi / 3, "xw": np.pi / 4},
        "tetrahedron": {"xy": 0.2, "xz": 0.2, "xw": 1.2, "yw": 0.8},
    }
