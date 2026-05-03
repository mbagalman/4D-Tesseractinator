"""Matplotlib rendering helpers for projection, slicing, and the unified dashboard."""

from __future__ import annotations

from collections.abc import Mapping
from itertools import combinations

import numpy as np
from scipy.spatial import ConvexHull

from ._constants import AXIS_COLORS, AXIS_LABELS, DEFAULT_VIEWER_DISTANCE, DEFAULT_W_SLICE, TOL
from .geometry import (
    SliceError,
    _slice_tesseract_with_hull,
    generate_tesseract_edge_indices,
    generate_tesseract_vertices,
    normalize_angles,
    project_4d_to_3d,
    rotate_points,
)

__all__ = ["plot_dashboard", "plot_projection", "plot_slice"]


def _require_matplotlib():
    try:
        import matplotlib.pyplot as plt
        from matplotlib.lines import Line2D
        from mpl_toolkits.mplot3d.art3d import Line3DCollection, Poly3DCollection
    except ImportError as exc:
        raise ImportError("matplotlib is required for rendering. Install with `pip install -e .`.") from exc
    return plt, Line2D, Line3DCollection, Poly3DCollection


def _compute_edge_axis_indices() -> np.ndarray:
    vertices = generate_tesseract_vertices()
    return np.array(
        [int(np.flatnonzero(vertices[i] - vertices[j])[0]) for i, j in generate_tesseract_edge_indices()],
        dtype=int,
    )


_EDGE_AXIS_INDICES = _compute_edge_axis_indices()


def _set_equal_aspect(ax, vertices: np.ndarray) -> None:
    max_range = (vertices.max(axis=0) - vertices.min(axis=0)).max() / 2.0
    center = vertices.mean(axis=0)
    max_range = max(max_range, 0.5)
    for setter, coord in zip((ax.set_xlim, ax.set_ylim, ax.set_zlim), center, strict=True):
        setter(coord - max_range, coord + max_range)
    ax.set_box_aspect((1, 1, 1))


def _rotation_text(angles: Mapping[str, float]) -> str:
    if not angles:
        return "(none)"
    return ", ".join(f"{plane}={value:+.2f}" for plane, value in angles.items())


def _draw_projection(
    ax, angles: Mapping[str, float], viewer_distance: float, *, add_legend: bool, add_colorbar: bool
):
    plt, Line2D, Line3DCollection, _ = _require_matplotlib()
    vertices4d = generate_tesseract_vertices()
    edges = generate_tesseract_edge_indices()
    rotated_vertices = rotate_points(vertices4d, angles)
    projected = project_4d_to_3d(rotated_vertices, viewer_distance=viewer_distance)

    edge_colors = [AXIS_COLORS[axis] for axis in _EDGE_AXIS_INDICES]
    line_segments = [projected[list(edge)] for edge in edges]
    w_values = rotated_vertices[:, 3]

    w_min = float(w_values.min())
    w_max = float(w_values.max())
    if np.isclose(w_min, w_max):
        weights = np.full_like(w_values, 0.5)
    else:
        weights = (w_values - w_min) / (w_max - w_min)
    sizes = 30 + 50 * weights

    ax.add_collection3d(Line3DCollection(line_segments, colors=edge_colors, linewidths=1.5, alpha=0.9))
    scatter = ax.scatter(
        projected[:, 0],
        projected[:, 1],
        projected[:, 2],
        c=w_values,
        s=sizes,
        cmap="viridis",
        depthshade=True,
        edgecolors="black",
        linewidths=0.5,
    )
    _set_equal_aspect(ax, projected)
    ax.set_xlabel("X")
    ax.set_ylabel("Y")
    ax.set_zlabel("Z")
    ax.set_title("4D Projection")
    ax.text2D(
        0.02,
        0.98,
        f"Viewer distance: {viewer_distance:.2f}\nRot: {_rotation_text(angles)}",
        transform=ax.transAxes,
        va="top",
        bbox=dict(boxstyle="round,pad=0.4", facecolor="white", alpha=0.75),
        fontsize=9,
    )

    if add_legend:
        legend_elements = [
            Line2D([0], [0], color=color, lw=3, label=f"{label}-aligned")
            for color, label in zip(AXIS_COLORS, AXIS_LABELS, strict=True)
        ]
        ax.legend(handles=legend_elements, loc="upper right")
    if add_colorbar:
        plt.colorbar(scatter, ax=ax, shrink=0.7, pad=0.1, label="Rotated W")


def _draw_empty_slice(ax, w_fixed: float) -> None:
    ax.set_title("No Slice Intersection")
    ax.text2D(
        0.5,
        0.55,
        f"No intersection at W = {w_fixed:+.2f}",
        transform=ax.transAxes,
        ha="center",
        va="center",
        bbox=dict(boxstyle="round,pad=0.5", facecolor="#f6ead8", alpha=0.9),
    )
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_zticks([])
    ax.set_xlabel("X")
    ax.set_ylabel("Y")
    ax.set_zlabel("Z")
    ax.set_box_aspect((1, 1, 1))


def _camera_direction(ax) -> np.ndarray:
    elev = np.deg2rad(ax.elev)
    azim = np.deg2rad(ax.azim)
    return np.array(
        [
            np.cos(elev) * np.cos(azim),
            np.cos(elev) * np.sin(azim),
            np.sin(elev),
        ],
        dtype=float,
    )


def _configure_figure(figure, view_mode: str):
    if view_mode == "both":
        figure.set_size_inches(14, 6, forward=True)
        figure.subplots_adjust(left=0.05, right=0.97, bottom=0.08, top=0.9, wspace=0.18)
        projection_axis = figure.add_subplot(121, projection="3d")
        slice_axis = figure.add_subplot(122, projection="3d")
        return projection_axis, slice_axis

    figure.set_size_inches(8, 7, forward=True)
    figure.subplots_adjust(left=0.08, right=0.95, bottom=0.08, top=0.92)
    return figure.add_subplot(111, projection="3d")


def _render_dashboard_to_figure(
    figure, angles: Mapping[str, float], view_mode: str, viewer_distance: float, w_fixed: float
):
    figure.clear()
    if view_mode == "projection":
        axis = _configure_figure(figure, view_mode)
        _draw_projection(axis, angles, viewer_distance, add_legend=True, add_colorbar=True)
    elif view_mode == "slice":
        axis = _configure_figure(figure, view_mode)
        _draw_slice(axis, angles, w_fixed, tol=TOL, show_info=True)
    else:
        projection_axis, slice_axis = _configure_figure(figure, view_mode)
        _draw_projection(
            projection_axis,
            angles,
            viewer_distance,
            add_legend=False,
            add_colorbar=False,
        )
        _draw_slice(slice_axis, angles, w_fixed, tol=TOL, show_info=True)
        figure.suptitle("4D-Tesseractinator Dashboard")
    return figure


def _compute_face_geometry(vertices: np.ndarray, hull: ConvexHull, centroid: np.ndarray):
    """For each non-degenerate hull face, return its outward normal, its triangle
    of vertices, and the edge -> [face_index, ...] adjacency map."""
    face_normals: dict[int, np.ndarray] = {}
    face_vertices: dict[int, np.ndarray] = {}
    edge_to_faces: dict[tuple[int, int], list[int]] = {}
    for face_index, simplex in enumerate(hull.simplices):
        triangle = vertices[simplex]
        normal = np.cross(triangle[1] - triangle[0], triangle[2] - triangle[0])
        norm = np.linalg.norm(normal)
        if np.isclose(norm, 0.0):
            continue
        normal = normal / norm
        if np.dot(normal, triangle.mean(axis=0) - centroid) < 0:
            normal = -normal
        face_normals[face_index] = normal
        face_vertices[face_index] = triangle
        for edge in combinations(simplex, 2):
            edge_to_faces.setdefault(tuple(sorted(edge)), []).append(face_index)
    return face_normals, face_vertices, edge_to_faces


def _select_front_faces(face_normals: dict[int, np.ndarray], view_dir: np.ndarray) -> set[int]:
    return {idx for idx, normal in face_normals.items() if np.dot(normal, view_dir) > 1e-9}


def _build_face_collection(
    front_face_indices: set[int],
    face_vertices: dict[int, np.ndarray],
    face_normals: dict[int, np.ndarray],
    view_dir: np.ndarray,
):
    plt, _, _, Poly3DCollection = _require_matplotlib()
    indices = list(front_face_indices)
    front_faces = [face_vertices[idx] for idx in indices]
    face_strength = np.array([max(0.0, np.dot(face_normals[idx], view_dir)) for idx in indices], dtype=float)
    if np.isclose(face_strength.max(), face_strength.min()):
        color_values = np.full(len(front_faces), 0.5)
    else:
        color_values = (face_strength - face_strength.min()) / (face_strength.max() - face_strength.min())

    face_colors = plt.get_cmap("plasma")(0.2 + 0.55 * color_values)
    face_colors[:, 3] = 0.7
    return Poly3DCollection(
        front_faces,
        facecolors=face_colors,
        edgecolors="none",
        linewidths=0.0,
        zsort="average",
    )


def _compute_visible_edges(
    edge_to_faces: dict[tuple[int, int], list[int]],
    front_face_indices: set[int],
    face_normals: dict[int, np.ndarray],
    vertices: np.ndarray,
    hull: ConvexHull,
):
    visible_edges = []
    visible_vertex_indices: set[int] = set()
    for edge_indices, adjacent_faces in edge_to_faces.items():
        front_adjacent = [idx for idx in adjacent_faces if idx in front_face_indices]
        if not front_adjacent:
            continue
        # Drop interior edges between coplanar front faces (they'd just clutter a flat region).
        if len(front_adjacent) == len(adjacent_faces) and len(front_adjacent) >= 2:
            normals = [face_normals[idx] for idx in front_adjacent]
            first = normals[0]
            if all(np.linalg.norm(np.cross(first, normal)) < 1e-6 for normal in normals[1:]):
                continue
        visible_edges.append(vertices[list(edge_indices)])
        visible_vertex_indices.update(edge_indices)

    if not visible_vertex_indices:
        # Fallback: front faces exist but every edge was filtered out — show all front-face vertices.
        for face_index in front_face_indices:
            visible_vertex_indices.update(hull.simplices[face_index])
    return visible_edges, np.array(sorted(visible_vertex_indices), dtype=int)


def _build_slice_surface(vertices: np.ndarray, hull: ConvexHull, ax):
    centroid = vertices.mean(axis=0)
    view_dir = _camera_direction(ax)
    face_normals, face_vertices, edge_to_faces = _compute_face_geometry(vertices, hull, centroid)
    front_face_indices = _select_front_faces(face_normals, view_dir)
    if not front_face_indices:
        return None, [], np.array([], dtype=int)
    face_collection = _build_face_collection(front_face_indices, face_vertices, face_normals, view_dir)
    visible_edges, visible_vertex_indices = _compute_visible_edges(
        edge_to_faces, front_face_indices, face_normals, vertices, hull
    )
    return face_collection, visible_edges, visible_vertex_indices


def _draw_slice(ax, angles: Mapping[str, float], w_fixed: float, *, tol: float, show_info: bool) -> bool:
    _, _, Line3DCollection, _ = _require_matplotlib()
    try:
        vertices, edges, hull = _slice_tesseract_with_hull(angles, w_fixed=w_fixed, tol=tol)
    except SliceError:
        _draw_empty_slice(ax, w_fixed)
        return False

    distances = np.linalg.norm(vertices, axis=1)
    denominator = float(np.max(distances))
    colors = np.zeros_like(distances) if np.isclose(denominator, 0.0) else distances / denominator

    face_collection, visible_edges, visible_vertex_indices = _build_slice_surface(vertices, hull, ax)
    if face_collection is not None:
        ax.add_collection3d(face_collection)
    edge_segments = visible_edges or edges
    ax.add_collection3d(Line3DCollection(edge_segments, colors="black", linewidths=1.4, alpha=0.8))
    visible_vertices = vertices[visible_vertex_indices] if len(visible_vertex_indices) else vertices
    visible_colors = colors[visible_vertex_indices] if len(visible_vertex_indices) else colors
    ax.scatter(
        visible_vertices[:, 0],
        visible_vertices[:, 1],
        visible_vertices[:, 2],
        s=60,
        c=visible_colors,
        cmap="plasma",
        edgecolors="black",
        linewidths=0.5,
        alpha=0.9,
    )
    _set_equal_aspect(ax, vertices)
    ax.set_xlabel("X")
    ax.set_ylabel("Y")
    ax.set_zlabel("Z")
    ax.set_title(f"3D Slice at W = {w_fixed:+.2f}")

    if show_info:
        ax.text2D(
            0.02,
            0.98,
            f"Vertices: {len(vertices)}\nRot: {_rotation_text(angles)}",
            transform=ax.transAxes,
            va="top",
            bbox=dict(boxstyle="round,pad=0.4", facecolor="white", alpha=0.75),
            fontsize=9,
        )
    return True


def plot_projection(
    angles: Mapping[str, float] | None,
    viewer_distance: float = DEFAULT_VIEWER_DISTANCE,
    *,
    figure=None,
    show_plot: bool = False,
):
    plt, _, _, _ = _require_matplotlib()
    if figure is None:
        figure = plt.figure(figsize=(8, 7))
    _render_dashboard_to_figure(
        figure,
        normalize_angles(angles),
        "projection",
        viewer_distance,
        DEFAULT_W_SLICE,
    )
    if show_plot:
        plt.show()
    return figure


def plot_slice(
    angles: Mapping[str, float] | None,
    w_fixed: float = DEFAULT_W_SLICE,
    *,
    figure=None,
    show_plot: bool = False,
):
    plt, _, _, _ = _require_matplotlib()
    if figure is None:
        figure = plt.figure(figsize=(8, 7))
    _render_dashboard_to_figure(
        figure,
        normalize_angles(angles),
        "slice",
        DEFAULT_VIEWER_DISTANCE,
        w_fixed,
    )
    if show_plot:
        plt.show()
    return figure


def plot_dashboard(
    angles: Mapping[str, float] | None,
    view_mode: str,
    viewer_distance: float = DEFAULT_VIEWER_DISTANCE,
    w_fixed: float = DEFAULT_W_SLICE,
    *,
    figure=None,
    show_plot: bool = False,
):
    plt, _, _, _ = _require_matplotlib()
    normalized_angles = normalize_angles(angles)
    if view_mode not in {"projection", "slice", "both"}:
        raise ValueError(f"Invalid view_mode: {view_mode!r}")

    if figure is None:
        figure = plt.figure(figsize=(14, 6) if view_mode == "both" else (8, 7))
    _render_dashboard_to_figure(
        figure,
        normalized_angles,
        view_mode,
        viewer_distance,
        w_fixed,
    )

    if show_plot:
        plt.show()
    return figure
