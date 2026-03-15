# 4D-Tesseractinator

[![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/mbagalman/4D-Tesseractinator/HEAD?urlpath=lab/tree/notebooks/4D_Tesseractinator_Demo.ipynb)

`4D-Tesseractinator` unifies two earlier experiments into one notebook-first codebase:

- a 4D-to-3D projection view derived from `Tesseract`
- a 4D slice/intersection view derived from `Four_D_Rotator`

The shared controls let you rotate the same tesseract and inspect the projection, the slice, or both at once.

For a short explanation of the geometry behind the project, see [How It Works](docs/how-it-works.md).

## What ships in v1

- Shared 4D math core for vertices, edges, rotation composition, projection, and slicing
- `plot_projection`, `plot_slice`, and `plot_dashboard` rendering APIs
- An `ipywidgets` dashboard with:
  - six 4D rotation sliders
  - `viewer_distance`
  - `w_fixed`
  - preset selection
  - `projection`, `slice`, and `both` modes
- Regression tests and GitHub Actions CI

## Install

Recommended local setup:

```bash
python3 -m venv .venv
.venv/bin/pip install ".[notebook,dev]"
```

If you only want the library without notebook tooling:

```bash
.venv/bin/pip install .
```

## Run

Launch in Binder:

- Open the badge above, or use [this Binder link](https://mybinder.org/v2/gh/mbagalman/4D-Tesseractinator/HEAD?urlpath=lab/tree/notebooks/4D_Tesseractinator_Demo.ipynb).
- Binder builds can take a minute on first launch because it needs to install the notebook dependencies and package.

Launch the test suite:

```bash
.venv/bin/python -m pytest -q
```

Launch the notebook demo:

```bash
.venv/bin/jupyter notebook notebooks/4D_Tesseractinator_Demo.ipynb
```

Or use the API directly:

```python
from tesseractinator import plot_dashboard

fig = plot_dashboard(
    angles={"xy": 0.6, "xw": 0.9},
    view_mode="both",
    viewer_distance=3.5,
    w_fixed=0.0,
)
```

For the widget dashboard:

```python
from tesseractinator import create_interactive_dashboard

create_interactive_dashboard()
```

## Tests

```bash
.venv/bin/python -m pytest -q
```

## Deferred for later

- JSON/OBJ export
- analysis/reporting helpers
- browser or desktop packaging

## Legacy baselines

This repo was assembled from the local baselines below, preserving their working math and tests:

- `Tesseract` at `2a6776d`
- `Four_D_Rotator` at `b85a78f`
