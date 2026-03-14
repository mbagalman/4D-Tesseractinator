"""Notebook helpers for the unified interactive dashboard."""

from __future__ import annotations

import numpy as np

from ._constants import DEFAULT_VIEWER_DISTANCE, DEFAULT_W_SLICE, VALID_PLANES
from .presets import standard_presets
from .rendering import plot_dashboard

__all__ = ["create_interactive_dashboard"]


def create_interactive_dashboard(display_ui: bool = True):
    try:
        import ipywidgets as widgets
        import matplotlib.pyplot as plt
        from IPython.display import display
    except ImportError as exc:
        raise ImportError(
            "Interactive notebooks require ipywidgets and IPython. Install with `pip install -e \".[notebook]\"`."
        ) from exc

    presets = standard_presets()
    custom_value = "__custom__"
    state = {"applying_preset": False}

    sliders = {
        plane: widgets.FloatSlider(
            value=0.0,
            min=-float(np.pi),
            max=float(np.pi),
            step=0.05,
            description=plane.upper(),
            continuous_update=True,
            readout_format=".2f",
            layout=widgets.Layout(width="320px"),
        )
        for plane in VALID_PLANES
    }

    viewer_distance = widgets.FloatSlider(
        value=DEFAULT_VIEWER_DISTANCE,
        min=2.0,
        max=10.0,
        step=0.1,
        description="View",
        continuous_update=True,
        readout_format=".1f",
        layout=widgets.Layout(width="320px"),
    )
    w_fixed = widgets.FloatSlider(
        value=DEFAULT_W_SLICE,
        min=-1.2,
        max=1.2,
        step=0.05,
        description="W slice",
        continuous_update=True,
        readout_format=".2f",
        layout=widgets.Layout(width="320px"),
    )
    view_mode = widgets.ToggleButtons(
        options=[
            ("Projection", "projection"),
            ("Slice", "slice"),
            ("Both", "both"),
        ],
        value="both",
        description="Mode",
    )
    preset_dropdown = widgets.Dropdown(
        options=[("Custom", custom_value)] + [(name, name) for name in presets],
        value="identity",
        description="Preset",
        layout=widgets.Layout(width="320px"),
    )
    output = widgets.Output()

    def current_angles():
        return {
            plane: slider.value
            for plane, slider in sliders.items()
            if not np.isclose(slider.value, 0.0)
        }

    def render(*_):
        figure = plot_dashboard(
            angles=current_angles(),
            view_mode=view_mode.value,
            viewer_distance=viewer_distance.value,
            w_fixed=w_fixed.value,
            show_plot=False,
        )
        with output:
            output.clear_output(wait=True)
            display(figure)
        plt.close(figure)

    def apply_preset(change):
        if change["name"] != "value":
            return
        preset_name = change["new"]
        if preset_name == custom_value:
            return
        state["applying_preset"] = True
        preset_angles = presets[preset_name]
        for plane, slider in sliders.items():
            slider.value = float(preset_angles.get(plane, 0.0))
        state["applying_preset"] = False
        render()

    def mark_custom(change):
        if change["name"] != "value" or state["applying_preset"]:
            return
        if preset_dropdown.value != custom_value:
            state["applying_preset"] = True
            preset_dropdown.value = custom_value
            state["applying_preset"] = False

    for slider in sliders.values():
        slider.observe(mark_custom, names="value")
        slider.observe(render, names="value")

    preset_dropdown.observe(apply_preset, names="value")
    viewer_distance.observe(render, names="value")
    w_fixed.observe(render, names="value")
    view_mode.observe(render, names="value")

    controls_left = widgets.VBox([preset_dropdown, view_mode, viewer_distance, w_fixed])
    controls_right = widgets.VBox(list(sliders.values()))
    container = widgets.VBox(
        [
            widgets.HTML("<h2>4D-Tesseractinator</h2><p>Rotate a 4D tesseract and inspect the projection, slice, or both.</p>"),
            widgets.HBox([controls_left, controls_right]),
            output,
        ]
    )

    apply_preset({"name": "value", "new": "identity"})
    if display_ui:
        display(container)
    return container
