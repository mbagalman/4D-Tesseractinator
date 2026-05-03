"""Shared constants for geometry and rendering."""

EPSILON = 1e-6
TOL = 1e-8

VALID_PLANES = ("xy", "xz", "yz", "xw", "yw", "zw")
PLANE_TO_AXES = {
    "xy": (0, 1),
    "xz": (0, 2),
    "yz": (1, 2),
    "xw": (0, 3),
    "yw": (1, 3),
    "zw": (2, 3),
}

AXES = (
    ("X", "orange"),
    ("Y", "green"),
    ("Z", "blue"),
    ("W", "red"),
)
AXIS_LABELS = tuple(label for label, _ in AXES)
AXIS_COLORS = tuple(color for _, color in AXES)
DEFAULT_VIEWER_DISTANCE = 3.0
DEFAULT_W_SLICE = 0.0
