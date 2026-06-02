# pyo_oracle

**Python client for the [Bio-ORACLE](https://bio-oracle.org/) ERDDAP server.**

Discover, inspect, subset, download, and load Bio-ORACLE marine environmental
layers (temperature, salinity, nutrients, sea ice, and more) from Python.
`pyo_oracle` is the Python counterpart of the R package
[`biooracler`](https://github.com/bio-oracle/biooracler) and is built on
[`erddapy`](https://github.com/ioos/erddapy).

📖 **Documentation:** <https://bio-oracle.github.io/pyo_oracle/>

## Installation

```bash
# With pip
pip install pyo-oracle

# Load layers as xarray (optional extra)
pip install "pyo-oracle[xarray]"

# With conda
conda create -n pyo_oracle conda-forge::pyo-oracle
```

## Quick start

```python
import pyo_oracle as pyo

# 1. List available layers (filter by search term, variable, scenario, depth, ...)
pyo.list_layers(search="Temperature")

# 2. Inspect a layer: dimension ranges + variables and units
pyo.info_layer("thetao_baseline_2000_2019_depthsurf")

# 3. Build constraints from friendly bounds (no hand-written dicts)
constraints = pyo.build_constraints(
    "thetao_baseline_2000_2019_depthsurf",
    time=("2000-01-01T00:00:00Z", "2010-01-01T00:00:00Z"),
    latitude=(0, 10),
    longitude=(0, 10),
)

# 4a. Load directly into memory (pandas or xarray)
df = pyo.load_layer(
    "thetao_baseline_2000_2019_depthsurf",
    constraints=constraints,
    variables=["thetao_mean"],
)
ds = pyo.load_layer(
    "thetao_baseline_2000_2019_depthsurf",
    constraints=constraints,
    fmt="xarray",
)

# 4b. Or download to a file (NetCDF by default)
pyo.download_layers(
    "thetao_baseline_2000_2019_depthsurf",
    constraints=constraints,
    variables=["thetao_mean"],
)

# 5. See local data
pyo.list_local_data()
```

## Key functions

| Function | Purpose |
|----------|---------|
| `list_layers` | List/filter available layers |
| `info_layer` | Inspect a layer's dimensions and variables |
| `build_constraints` | Build griddap constraints from `(min, max)` bounds + strides |
| `load_layer` | Load a layer into memory (`pandas` or `xarray`) |
| `download_layers` | Download a layer (NetCDF/CSV), optionally a variable subset |
| `list_local_data` | List downloaded files |

## Contributing

See [`CLAUDE.md`](CLAUDE.md) for the dev setup, testing, and release flow.
Please open an issue if you experience any problems.
