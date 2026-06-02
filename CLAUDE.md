# CLAUDE.md

Guidance for working in this repository.

## What this is

`pyo_oracle` is the Python client for the **Bio-ORACLE** ERDDAP server
(<https://erddap.bio-oracle.org/erddap/>). It is the Python counterpart of the R
package [`biooracler`](https://github.com/bio-oracle/biooracler) and is built on
top of [`erddapy`](https://github.com/ioos/erddapy).

## Layout

- `pyo_oracle/__init__.py` — public namespace; re-exports the API.
- `pyo_oracle/main.py` — public functions: `list_layers`, `info_layer`,
  `load_layer`, `download_layers`, `list_local_data`.
- `pyo_oracle/utils.py` — internals: `_build_griddap_server` (the single shared
  griddap setup path), `_layer_info`, `_layer_dataframe`, `build_constraints`,
  `_as_bool`, download helpers.
- `pyo_oracle/_config.py` — configparser-based config (data dir, server URL,
  `skip_confirmation`). `config.ini` is generated and git-ignored.
- `tests/` — `test_utils.py` (offline), `test_main.py` (mostly live), `test_config.py`.
- `docs/` + `mkdocs.yml` — MkDocs Material site (mkdocstrings API ref).

## Public API parity with `biooracler`

`list_layers`, `info_layer`, `download_layers` mirror the R package. Python adds
`load_layer` (in-memory pandas/xarray) and `build_constraints` (friendly
subsetting helper).

## Dev environment

All development happens in the conda env named **`pyo_oracle`**:

```bash
conda env create -n pyo_oracle -f environment-dev.yaml   # or `mamba`
conda activate pyo_oracle
pip install -e ".[dev,xarray,docs]"
```

## Tests

Two kinds, separated by the `integration` marker:

```bash
pytest -m "not integration"   # offline unit tests (fast, used in CI by default)
pytest                        # full suite incl. tests that hit the live server
pytest -m integration         # only the live-server tests
```

The exit goal for changes is a **fully green `pytest`** in the `pyo_oracle` env.

## Lint & docs

```bash
ruff check pyo_oracle tests
mkdocs serve          # live preview
mkdocs build --strict # must pass (CI deploys to GitHub Pages)
```

## Release flow

1. Bump `version` in `pyproject.toml` and update `CHANGELOG.md`.
2. Ensure `pytest`, `ruff`, and `mkdocs build --strict` pass.
3. `python -m build` and inspect the artifacts.
4. Push a tag — `.github/workflows/pypi-publish.yml` builds and publishes to PyPI
   (package name `pyo-oracle`).

## Gotchas

- **erddapy private API**: `_build_griddap_server` relies on
  `ERDDAP._constraints_original`. It is guarded with `getattr`/`hasattr` but
  watch this if bumping erddapy (verified against erddapy 3.2.x).
- Requires `erddapy>=2.2`, `pandas>=2.0`, Python `>=3.9`. xarray loading needs
  the optional `xarray` extra (`xarray` + `netCDF4`).
- `download_layers` with no constraints downloads the entire global layer and
  prompts for confirmation unless `skip_confirmation=True`.
