import numpy as np
import pytest

from tesseractinator.geometry import (
    SliceError,
    compose_rotation_matrix,
    generate_tesseract_edge_indices,
    generate_tesseract_vertices,
    project_4d_to_3d,
    rotation_matrix_4d,
    slice_tesseract,
)
from tesseractinator.presets import standard_presets


def _canonical_vertices(vertices, decimals=8):
    rounded = [tuple(np.round(vertex, decimals)) for vertex in vertices]
    return tuple(sorted(rounded))


def test_generate_tesseract_vertices_shape_and_values():
    vertices = generate_tesseract_vertices()
    assert vertices.shape == (16, 4)
    assert set(np.unique(vertices)) == {-0.5, 0.5}


def test_generate_tesseract_edges_count():
    edges = generate_tesseract_edge_indices()
    assert edges.shape == (32, 2)
    assert len({tuple(edge) for edge in edges}) == 32


def test_rotation_matrix_is_orthonormal():
    matrix = rotation_matrix_4d(0, 3, np.pi / 4)
    assert np.allclose(matrix.T @ matrix, np.eye(4), atol=1e-10)


def test_compose_rotation_matrix_is_orthonormal():
    matrix = compose_rotation_matrix({"xy": np.pi / 4, "xw": np.pi / 6})
    assert np.allclose(matrix.T @ matrix, np.eye(4), atol=1e-10)


@pytest.mark.parametrize(
    "axis1, axis2",
    [
        (-1, 2),
        (0, 4),
        (1, 1),
        ("0", 2),
    ],
)
def test_rotation_matrix_rejects_invalid_axes(axis1, axis2):
    with pytest.raises(ValueError):
        rotation_matrix_4d(axis1, axis2, 0.2)


def test_project_4d_to_3d_preserves_sign_near_projection_plane():
    viewer_distance = 3.0
    epsilon = 5e-7
    points = np.array(
        [
            [1.0, 0.0, 0.0, viewer_distance - epsilon],
            [1.0, 0.0, 0.0, viewer_distance + epsilon],
        ]
    )
    projected = project_4d_to_3d(points, viewer_distance=viewer_distance)
    assert projected[0, 0] > 0
    assert projected[1, 0] < 0


@pytest.mark.parametrize(
    "points4d, viewer_distance",
    [
        (np.array([1.0, 2.0, 3.0, 4.0]), 3.0),
        (np.array([[1.0, 2.0, 3.0]]), 3.0),
        (np.array([[1.0, 2.0, 3.0, 4.0]]), 0.0),
        (np.array([[1.0, 2.0, 3.0, 4.0]]), np.inf),
    ],
)
def test_project_4d_to_3d_rejects_invalid_inputs(points4d, viewer_distance):
    with pytest.raises(ValueError):
        project_4d_to_3d(points4d, viewer_distance=viewer_distance)


def test_slice_tesseract_raises_for_missing_slice():
    with pytest.raises(SliceError):
        slice_tesseract({}, w_fixed=2.0)


def test_slice_tesseract_preserves_known_vertex_counts():
    presets = standard_presets()
    expected_counts = {
        "identity": 8,
        "4d_symmetric": 12,
        "octahedron": 12,
    }
    for name, expected in expected_counts.items():
        vertices, _ = slice_tesseract(presets[name])
        assert len(vertices) == expected


def test_rotation_order_is_respected():
    angles_a = {"xy": 0.6, "xw": 0.9}
    angles_b = {"xw": 0.9, "xy": 0.6}
    vertices_a, _ = slice_tesseract(angles_a)
    vertices_b, _ = slice_tesseract(angles_b)
    assert _canonical_vertices(vertices_a) != _canonical_vertices(vertices_b)
