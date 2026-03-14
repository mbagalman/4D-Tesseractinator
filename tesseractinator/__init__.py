"""Unified tools for exploring a rotating tesseract."""

from .geometry import (
    SliceError,
    compose_rotation_matrix,
    generate_tesseract_edge_indices,
    generate_tesseract_vertices,
    project_4d_to_3d,
    slice_tesseract,
)
from .notebook import create_interactive_dashboard
from .presets import standard_presets
from .rendering import plot_dashboard, plot_projection, plot_slice

__all__ = [
    "SliceError",
    "compose_rotation_matrix",
    "create_interactive_dashboard",
    "generate_tesseract_edge_indices",
    "generate_tesseract_vertices",
    "plot_dashboard",
    "plot_projection",
    "plot_slice",
    "project_4d_to_3d",
    "slice_tesseract",
    "standard_presets",
]

__version__ = "0.1.0"
