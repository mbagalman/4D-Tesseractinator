# Contributing to 4D-Tesseractinator

Thanks for your interest. This is a small notebook-first project, so the
workflow is intentionally lightweight.

## Development setup

Create a virtual environment, activate it (see the [README](README.md#install)
for OS-specific activation), and install the package with the dev extras:

```bash
python -m pip install -e ".[notebook,dev]"
```

The `dev` extra brings in `pytest`, `pytest-cov`, and `ruff`.

## Running checks locally

Before pushing, run the same checks CI runs:

```bash
ruff check .
ruff format --check .
python -m pytest -q
```

To autofix lint and reformat:

```bash
ruff check . --fix
ruff format .
```

## Pull requests

- Branch off `main`, push your branch, and open a PR.
- One logical change per PR. Keep diffs small and focused.
- Make sure CI is green before requesting review (or merging if you're the
  maintainer).
- If your change is user-visible, add a bullet under `## [Unreleased]` in
  [CHANGELOG.md](CHANGELOG.md).

## Reporting bugs and proposing features

Use the issue templates under
[.github/ISSUE_TEMPLATE/](.github/ISSUE_TEMPLATE/). For bugs, include the
Python version, OS, and a minimal reproduction.
