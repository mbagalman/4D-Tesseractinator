import os

import matplotlib
import pytest

os.environ.setdefault("MPLBACKEND", "Agg")
matplotlib.use("Agg")

pytest.importorskip("ipywidgets")
pytest.importorskip("IPython")

import ipywidgets as widgets

from tesseractinator.notebook import create_interactive_dashboard


def test_create_interactive_dashboard_smoke():
    container = create_interactive_dashboard(display_ui=False)
    assert isinstance(container, widgets.VBox)
