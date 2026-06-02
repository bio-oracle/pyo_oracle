# Changelog

All notable changes to this project are documented here. The format is based on
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and this project adheres
to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.1.0] - Unreleased

### Added

- **`get_layer_url(dataset_id, ...)`** — build the ERDDAP download URL for a
  layer (with constraints, variable subset, and response format) without
  downloading it, for sharing or fetching elsewhere. Resolves #1.
- Greatly expanded the test suite with offline unit tests that mock the network
  boundary (`_build_griddap_server`, `_layer_info`, `_download_file_from_url`,
  `_layer_dataframe`). Total coverage rose from 85% to ~99%, and the
  network-free `list_layers` filtering, config error paths, `build_constraints`
  validation, and download flows are now covered without hitting the server.
- CI enforces a minimum coverage of 90% on the offline test run.

### Documentation

- Added a dedicated "The constraints dictionary" page documenting the dictionary
  structure (keys, value types, strides), how to edit it manually, partial
  constraints, and what happens when no constraints are given.

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
