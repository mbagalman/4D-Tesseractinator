"""Matplotlib rendering helpers for projection, slicing, and the unified dashboard."""

from __future__ import annotations

from itertools import combinations
from typing import Mapping

import numpy as np
from scipy.spatial import ConvexHull, QhullError

from ._constants import AXIS_COLORS, AXIS_LABELS, DEFAULT_VIEWER_DISTANCE, DEFAULT_W_SLICE, TOL
from .geometry import (
    generate_tesseract_edge_indices,
    generate_tesseract_vertices,
    normalize_angles,
    project_4d_to_3d,
    rotate_points,
    slice_tesseract,
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


def _edge_axis_index(edge) -> int:
    vertices = generate_tesseract_vertices()
    diff = vertices[edge[0]] - vertices[edge[1]]
    return int(np.flatnonzero(diff)[0])


def _set_equal_aspect(ax, vertices: np.ndarray) -> None:
    max_range = (vertices.max(axis=0) - vertices.min(axis=0)).max() / 2.0
    center = vertices.mean(axis=0)
    max_range = max(max_range, 0.5)
    for setter, coord in zip((ax.set_xlim, ax.set_ylim, ax.set_zlim), center):
        setter(coord - max_range, coord + max_range)
    ax.set_box_aspect((1, 1, 1))


def _rotation_text(angles: Mapping[str, float]) -> str:
    if not angles:
        return "(none)"
    return ", ".join(f"{plane}={value:+.2f}" for plane, value in angles.items())


def _draw_projection(ax, angles: Mapping[str, float], viewer_distance: float, *, add_legend: bool, add_colorbar: bool):
    plt, Line2D, Line3DCollection, _ = _require_matplotlib()
    vertices4d = generate_tesseract_vertices()
    edges = generate_tesseract_edge_indices()
    rotated_vertices = rotate_points(vertices4d, angles)
    projected = project_4d_to_3d(rotated_vertices, viewer_distance=viewer_distance)

    edge_colors = [AXIS_COLORS[_edge_axis_index(edge)] for edge in edges]
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
            for color, label in zip(AXIS_COLORS, AXIS_LABELS)
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


def _render_dashboard_to_figure(figure, angles: Mapping[str, float], view_mode: str, viewer_distance: float, w_fixed: float):
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


def _build_slice_surface(vertices: np.ndarray, ax):
    plt, _, _, Poly3DCollection = _require_matplotlib()
    try:
        hull = ConvexHull(vertices, qhull_options="QJ")
    except QhullError:
        return None, [], np.array([], dtype=int)

    centroid = vertices.mean(axis=0)
    view_dir = _camera_direction(ax)
    face_normals = {}
    face_vertices = {}
    front_face_indices = set()
    edge_to_faces = {}

    for face_index, simplex in enumerate(hull.simplices):
        triangle = vertices[simplex]
        normal = np.cross(triangle[1] - triangle[0], triangle[2] - triangle[0])
        norm = np.linalg.norm(normal)
        if np.isclose(norm, 0.0):
            continue
        normal = normal / norm
        face_center = triangle.mean(axis=0)
        if np.dot(normal, face_center - centroid) < 0:
            normal = -normal

        face_normals[face_index] = normal
        face_vertices[face_index] = triangle
        if np.dot(normal, view_dir) > 1e-9:
            front_face_indices.add(face_index)

        for edge in combinations(simplex, 2):
            edge_to_faces.setdefault(tuple(sorted(edge)), []).append(face_index)

    front_faces = [face_vertices[index] for index in front_face_indices if index in face_vertices]
    if not front_faces:
        return None, [], np.array([], dtype=int)

    face_strength = np.array([max(0.0, np.dot(face_normals[index], view_dir)) for index in front_face_indices], dtype=float)
    if np.isclose(face_strength.max(), face_strength.min()):
        color_values = np.full(len(front_faces), 0.5)
    else:
        color_values = (face_strength - face_strength.min()) / (face_strength.max() - face_strength.min())

    face_colors = plt.get_cmap("plasma")(0.2 + 0.55 * color_values)
    face_colors[:, 3] = 0.7
    face_collection = Poly3DCollection(
        front_faces,
        facecolors=face_colors,
        edgecolors="none",
        linewidths=0.0,
        zsort="average",
    )

    visible_edges = []
    visible_vertex_indices = set()
    for edge_indices, adjacent_faces in edge_to_faces.items():
        front_adjacent = [face_index for face_index in adjacent_faces if face_index in front_face_indices]
        if not front_adjacent:
            continue
        if len(front_adjacent) == len(adjacent_faces) and len(front_adjacent) >= 2:
            normals = [face_normals[face_index] for face_index in front_adjacent]
            first = normals[0]
            if all(np.linalg.norm(np.cross(first, normal)) < 1e-6 for normal in normals[1:]):
                continue
        visible_edges.append(vertices[list(edge_indices)])
        visible_vertex_indices.update(edge_indices)

    if not visible_vertex_indices:
        for face_index in front_face_indices:
            visible_vertex_indices.update(hull.simplices[face_index])

    return face_collection, visible_edges, np.array(sorted(visible_vertex_indices), dtype=int)


def _draw_slice(ax, angles: Mapping[str, float], w_fixed: float, *, tol: float, show_info: bool) -> bool:
    _, _, Line3DCollection, _ = _require_matplotlib()
    try:
        vertices, edges = slice_tesseract(angles, w_fixed=w_fixed, tol=tol)
    except Exception as exc:
        from .geometry import SliceError

        if isinstance(exc, SliceError):
            _draw_empty_slice(ax, w_fixed)
            return False
        raise

    distances = np.linalg.norm(vertices, axis=1)
    denominator = float(np.max(distances))
    normalized = np.zeros_like(distances) if np.isclose(denominator, 0.0) else distances / denominator
    colors = np.linspace(0.15, 0.95, len(vertices))
    if len(vertices):
        colors = normalized

    face_collection, visible_edges, visible_vertex_indices = _build_slice_surface(vertices, ax)
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
