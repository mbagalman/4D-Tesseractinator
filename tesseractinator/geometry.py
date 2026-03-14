"""Core 4D math shared by all Tesseractinator views."""

from __future__ import annotations

from functools import lru_cache
from numbers import Integral
from typing import Dict, List, Mapping, Tuple

import numpy as np
from scipy.spatial import ConvexHull, QhullError

from ._constants import DEFAULT_VIEWER_DISTANCE, EPSILON, PLANE_TO_AXES, TOL, VALID_PLANES

AngleDict = Dict[str, float]
Edge = Tuple[np.ndarray, np.ndarray]

__all__ = [
    "AngleDict",
    "Edge",
    "SliceError",
    "compose_rotation_matrix",
    "generate_tesseract_edge_indices",
    "generate_tesseract_vertices",
    "project_4d_to_3d",
    "slice_tesseract",
]


class SliceError(Exception):
    """Raised when the requested 3D slice does not produce a valid polyhedron."""


def _validate_axis_index(axis: int, name: str) -> int:
    if not isinstance(axis, Integral):
        raise ValueError(f"{name} must be an integer in [0, 3], got {axis!r}.")
    axis_int = int(axis)
    if axis_int < 0 or axis_int > 3:
        raise ValueError(f"{name} must be in [0, 3], got {axis_int}.")
    return axis_int


def _validate_finite_number(value: float, name: str, *, positive: bool = False) -> float:
    try:
        value_float = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name} must be a finite number, got {value!r}.") from exc
    if not np.isfinite(value_float):
        raise ValueError(f"{name} must be finite, got {value!r}.")
    if positive and value_float <= 0:
        raise ValueError(f"{name} must be > 0, got {value_float}.")
    return value_float


def _round_decimals_for_tol(tol: float) -> int:
    safe_tol = max(float(tol), 1e-15)
    return max(0, int(np.ceil(-np.log10(safe_tol))))


def normalize_angles(angles: Mapping[str, float] | None) -> AngleDict:
    normalized: AngleDict = {}
    if not angles:
        return normalized
    for plane, value in angles.items():
        if plane not in VALID_PLANES:
            raise ValueError(f"Invalid rotation plane: {plane!r}")
        normalized[plane] = _validate_finite_number(value, plane)
    return normalized


@lru_cache(maxsize=1)
def generate_tesseract_vertices() -> np.ndarray:
    return np.array(
        [
            [
                0.5 if (i >> 3) & 1 else -0.5,
                0.5 if (i >> 2) & 1 else -0.5,
                0.5 if (i >> 1) & 1 else -0.5,
                0.5 if i & 1 else -0.5,
            ]
            for i in range(16)
        ],
        dtype=float,
    )


@lru_cache(maxsize=1)
def generate_tesseract_edge_indices() -> np.ndarray:
    edges = []
    for i in range(16):
        for dim in range(4):
            j = i ^ (1 << dim)
            if i < j:
                edges.append((i, j))
    return np.array(edges, dtype=int)


def rotation_matrix_4d(axis1: int, axis2: int, angle_rad: float) -> np.ndarray:
    axis1 = _validate_axis_index(axis1, "axis1")
    axis2 = _validate_axis_index(axis2, "axis2")
    if axis1 == axis2:
        raise ValueError("axis1 and axis2 must be different.")
    angle_rad = _validate_finite_number(angle_rad, "angle_rad")

    matrix = np.eye(4)
    c, s = np.cos(angle_rad), np.sin(angle_rad)
    matrix[axis1, axis1] = c
    matrix[axis1, axis2] = -s
    matrix[axis2, axis1] = s
    matrix[axis2, axis2] = c
    return matrix


def compose_rotation_matrix(angles: Mapping[str, float] | None) -> np.ndarray:
    matrix = np.eye(4)
    for plane, angle in normalize_angles(angles).items():
        axis1, axis2 = PLANE_TO_AXES[plane]
        matrix = rotation_matrix_4d(axis1, axis2, angle) @ matrix
    return matrix


def rotate_points(points4d: np.ndarray, angles: Mapping[str, float] | None) -> np.ndarray:
    points4d = np.asarray(points4d, dtype=float)
    if points4d.ndim != 2 or points4d.shape[1] != 4:
        raise ValueError(f"points4d must have shape (n, 4), got {points4d.shape}.")
    return points4d @ compose_rotation_matrix(angles).T


def project_4d_to_3d(points4d: np.ndarray, viewer_distance: float = DEFAULT_VIEWER_DISTANCE) -> np.ndarray:
    points4d = np.asarray(points4d, dtype=float)
    if points4d.ndim != 2 or points4d.shape[1] != 4:
        raise ValueError(f"points4d must have shape (n, 4), got {points4d.shape}.")
    viewer_distance = _validate_finite_number(viewer_distance, "viewer_distance", positive=True)

    w = points4d[:, 3]
    denom = viewer_distance - w
    near_plane = np.abs(denom) < EPSILON
    denom = np.where(near_plane & (denom < 0), -EPSILON, denom)
    denom = np.where(near_plane & (denom >= 0), EPSILON, denom)
    factor = viewer_distance / denom
    return points4d[:, :3] * factor[:, np.newaxis]


def slice_tesseract(
    angles: Mapping[str, float] | None,
    *,
    w_fixed: float = 0.0,
    tol: float = TOL,
) -> Tuple[np.ndarray, List[Edge]]:
    w_fixed = _validate_finite_number(w_fixed, "w_fixed")
    tol = _validate_finite_number(tol, "tol", positive=True)
    rotated_verts = rotate_points(generate_tesseract_vertices(), angles)

    intersection_points = []
    for i, j in generate_tesseract_edge_indices():
        p1 = rotated_verts[i]
        p2 = rotated_verts[j]
        w1, w2 = p1[3], p2[3]

        if (w1 < w_fixed and w2 > w_fixed) or (w2 < w_fixed and w1 > w_fixed):
            if np.isclose(w1, w2, atol=tol):
                continue
            t = (w_fixed - w1) / (w2 - w1)
            intersection = p1 + t * (p2 - p1)
            intersection_points.append(intersection[:3])
        elif np.isclose(w1, w_fixed, atol=tol):
            intersection_points.append(p1[:3])
        elif np.isclose(w2, w_fixed, atol=tol):
            intersection_points.append(p2[:3])

    if not intersection_points:
        raise SliceError("Slice plane does not intersect the tesseract.")

    decimals = _round_decimals_for_tol(tol)
    unique_points = {tuple(np.round(point, decimals)) for point in intersection_points}
    slice_points = np.array([list(point) for point in unique_points], dtype=float)

    if slice_points.shape[0] < 4:
        raise SliceError(
            f"Slice resulted in only {slice_points.shape[0]} unique vertices, not enough for a 3D shape."
        )

    try:
        hull = ConvexHull(slice_points, qhull_options="QJ")
    except QhullError as exc:
        raise SliceError("Convex hull failed because the slice is degenerate.") from exc

    edge_set = set()
    for simplex in hull.simplices:
        for index in range(len(simplex)):
            a, b = sorted((simplex[index], simplex[(index + 1) % len(simplex)]))
            edge_set.add((a, b))

    final_vertices = hull.points
    edges = [(final_vertices[i], final_vertices[j]) for i, j in edge_set]
    return final_vertices, edges
