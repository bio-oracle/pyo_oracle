# Changelog

All notable changes to this project are documented here. The format is based on
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and this project adheres
to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Documentation **Gallery**: four visualisation tutorials (global maps &
  projections, climate change, distributions & gradients, multi-variable
  relationships) built on the xarray/pandas plotting APIs with cmocean and
  cartopy. Figures are pre-rendered by `docs/gallery/generate_images.py` so the
  docs build stays offline.
- **`viz` optional dependency extra** (`matplotlib`, `cmocean`, `cartopy`,
  `seaborn`) for running the Gallery examples.

## [1.0.0] - 2026-06-02

First stable release. Modernizes dependencies, reaches feature parity with the
R package [`biooracler`](https://github.com/bio-oracle/biooracler), and adds new
functionality.

### Added

- **`info_layer(dataset_id)`** — inspect a layer's dimension ranges (time,
  latitude, longitude, depth) and its variables with units and long names
  (parity with `biooracler::info_layer`).
- **`load_layer(dataset_id, ...)`** — load a layer directly into memory as a
  `pandas.DataFrame` (default) or `xarray.Dataset` (`fmt="xarray"`).
- **`build_constraints(...)`** — build griddap constraints from friendly
  `(min, max)` bounds and strides, with optional validation against the
  dataset's real ranges.
- **`variables=`** argument on `download_layers` to download a subset of
  variables.
- Optional dependency extras: `xarray`, `docs`, `dev`.
- MkDocs Material documentation site (quickstart, tutorials, API reference) with
  a GitHub Pages deploy workflow.
- `respx` and `ruff` to the dev toolchain; `integration` pytest marker to
  separate live-server tests from offline unit tests.
- `CLAUDE.md` contributor guide and this changelog.

### Changed

- Declared explicit dependencies (`erddapy>=2.2`, `pandas>=2.0`, `httpx>=0.27`)
  and raised the Python floor to `>=3.9`.
- Refactored griddap server construction into a single shared
  `_build_griddap_server` helper used by downloads, in-memory loading, and
  metadata lookups.
- CI now tests a Python 3.9–3.13 matrix, lints with ruff, and runs offline unit
  tests by default with a separate (non-blocking) integration job.

### Fixed

- Replaced unsafe `eval()` parsing of the `skip_confirmation` config value with a
  safe boolean coercion (`_as_bool`), which also handles strings like `"false"`.
- Hardened handling of erddapy's private `_constraints_original` attribute.

## [0.2.0]

- Previous release.
