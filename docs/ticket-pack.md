# 4D-Tesseractinator Ticket Pack

## Status Summary

| Ticket | Title | Status |
| --- | --- | --- |
| TKT-001 | Bootstrap unified repo | Done |
| TKT-002 | Extract shared 4D math core | Done |
| TKT-003 | Port projection renderer | Done |
| TKT-004 | Port slice renderer | Done |
| TKT-005 | Build synced notebook dashboard | Done |
| TKT-006 | Add regression and integration tests | Done |
| TKT-007 | Polish docs and backlog | Done |

## Ticket Details

### TKT-001 Bootstrap unified repo
- Created a fresh git repo in this workspace.
- Added `pyproject.toml`, package skeleton, tests, notebook entrypoint, docs, and CI.
- Acceptance: the repo now has install, run, and test instructions in `README.md`.

### TKT-002 Extract shared 4D math core
- Added `tesseractinator.geometry` for tesseract generation, ordered 4D rotation, projection, and slicing.
- Preserved insertion-order rotation composition so non-commutative rotations stay correct.
- Acceptance: both render paths use the same geometry functions.

### TKT-003 Port projection renderer
- Added `plot_projection` with perspective projection, axis-colored edges, and W-based point coloring.
- Acceptance: the projection view reuses the legacy `Tesseract` projection behavior.

### TKT-004 Port slice renderer
- Added `plot_slice` with hull-based slice edges and friendly empty-state handling.
- Acceptance: preset vertex counts remain covered in tests.

### TKT-005 Build synced notebook dashboard
- Added `create_interactive_dashboard` with shared controls, presets, and mode switching.
- Acceptance: one control surface drives projection, slice, or both.

### TKT-006 Add regression and integration tests
- Added geometry and rendering tests covering edge counts, rotation order, projection edge cases, slice miss behavior, and dashboard modes.
- Acceptance: local `pytest` and CI workflow execute the suite.

### TKT-007 Polish docs and backlog
- Documented the new unified workflow in `README.md`.
- Deferred export and analysis follow-up work into the backlog.
- Acceptance: shipped and deferred work are clearly separated.

## Backlog

- Add export helpers after the visualization workflows stabilize.
- Revisit analysis metrics as a second-phase feature.
- Consider a browser-friendly front end if the notebook UX proves out.
