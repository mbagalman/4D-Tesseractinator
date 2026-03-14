import os

import matplotlib
import numpy as np
import pytest

os.environ.setdefault("MPLBACKEND", "Agg")
matplotlib.use("Agg")

from matplotlib.figure import Figure
from mpl_toolkits.mplot3d.art3d import Line3DCollection, Poly3DCollection

from tesseractinator.geometry import slice_tesseract
from tesseractinator import plot_dashboard, plot_projection, plot_slice


def test_plot_projection_returns_figure():
    figure = plot_projection({"xy": 0.3, "xw": 0.8})
    assert isinstance(figure, Figure)
    assert any(axis.name == "3d" for axis in figure.axes)


def test_plot_slice_returns_figure_for_real_slice():
    figure = plot_slice({"xy": 0.3, "xw": 0.8}, w_fixed=0.0)
    assert isinstance(figure, Figure)
    assert any(axis.name == "3d" for axis in figure.axes)
    assert any(isinstance(collection, Poly3DCollection) for collection in figure.axes[0].collections)


def test_plot_slice_hides_occluded_edges_for_default_view():
    figure = plot_slice({}, w_fixed=0.0)
    line_collection = next(
        collection for collection in figure.axes[0].collections if isinstance(collection, Line3DCollection)
    )
    _, all_edges = slice_tesseract({}, w_fixed=0.0)
    assert 0 < len(line_collection._segments3d) < len(all_edges)


def test_plot_slice_hides_back_side_vertices_for_default_view():
    figure = plot_slice({}, w_fixed=0.0)
    scatter = next(collection for collection in figure.axes[0].collections if hasattr(collection, "_offsets3d"))
    visible_vertex_count = len(np.asarray(scatter._offsets3d[0]))
    all_vertices, _ = slice_tesseract({}, w_fixed=0.0)
    assert 0 < visible_vertex_count < len(all_vertices)


def test_plot_slice_renders_empty_state_for_missing_slice():
    figure = plot_slice({}, w_fixed=2.0)
    assert figure.axes[0].get_title() == "No Slice Intersection"


@pytest.mark.parametrize("view_mode, expected_axes", [("projection", 1), ("slice", 1), ("both", 2)])
def test_plot_dashboard_supports_all_view_modes(view_mode, expected_axes):
    figure = plot_dashboard(
        angles={"xy": 0.6, "xw": 0.9},
        view_mode=view_mode,
        viewer_distance=3.5,
        w_fixed=0.0,
    )
    three_d_axes = [axis for axis in figure.axes if axis.name == "3d"]
    assert len(three_d_axes) == expected_axes


def test_plot_dashboard_rejects_invalid_mode():
    with pytest.raises(ValueError):
        plot_dashboard({}, view_mode="invalid")
