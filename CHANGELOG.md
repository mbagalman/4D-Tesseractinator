# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Cross-platform CI matrix on Linux, Windows, and macOS, covering Python
  3.10–3.13 (#8).
- `ruff check` and `ruff format --check` gates in CI, with corresponding
  `[tool.ruff]` configuration in `pyproject.toml` (#8).
- Pytest coverage reporting; `coverage.xml` is uploaded as a CI artifact (#8).
- `CONTRIBUTING.md`, issue templates, and a PR template (#4).
- CI status badge in the README (#4).
- Binder `runtime.txt` to pin the notebook's Python version (#4).

### Changed

- Read `__version__` from package metadata via `importlib.metadata.version`
  so `pyproject.toml` is the single source of truth for the version (#10).
- README install and run commands are now cross-platform (`python -m pip`
  / `python -m pytest` instead of POSIX-only `.venv/bin/...`) (#4).
- `slice_tesseract` now exposes its convex hull via an internal helper so
  the renderer reuses it instead of recomputing on already-jittered points,
  eliminating a double `QJ` jitter (#7).
- Type hints standardized on PEP 585 built-ins (`dict`/`list`/`tuple`) and
  `collections.abc.Mapping` (#8).

### Removed

- Vestigial `setup.py` shim. `pyproject.toml` is now the only build
  configuration (#10).
- Internal `docs/ticket-pack.md` planning artifact. Git history is the
  durable record of completed tickets (#4).
- "Legacy baselines" section in the README, which referenced inaccessible
  commit hashes from precursor repos (#4).

### Fixed

- `_draw_slice` now catches only `SliceError` instead of swallowing every
  `Exception`. Unrelated errors are no longer silently rendered as empty
  slices (#7).
- Removed dead `linspace` initializer and unreachable `isclose(w1, w2)`
  guard in the slice path (#7).

## [0.1.0] — Unreleased initial cut

Initial unified codebase combining the `Tesseract` projection view and the
`Four_D_Rotator` slice view into a single notebook-first package.

### Added

- Shared 4D math core: tesseract vertices, edges, rotation composition,
  perspective projection, and hyperplane slicing.
- `plot_projection`, `plot_slice`, and `plot_dashboard` rendering APIs.
- `ipywidgets` dashboard with six rotation sliders, `viewer_distance`,
  `w_fixed`, preset selection, and `projection`/`slice`/`both` modes.
- Regression tests and a GitHub Actions CI workflow.
