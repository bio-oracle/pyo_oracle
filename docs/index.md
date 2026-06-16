# pyo_oracle

**Python client for the [Bio-ORACLE](https://bio-oracle.org/) ERDDAP server.**

`pyo_oracle` lets you discover, inspect, subset, download, and load Bio-ORACLE
marine environmental layers (temperature, salinity, nutrients, sea ice, and
more) straight from Python. It is the Python counterpart of the R package
[`biooracler`](https://github.com/bio-oracle/biooracler) and is built on top of
[`erddapy`](https://github.com/ioos/erddapy).

## Features

- **List & filter** layers by free-text search, variable, SSP scenario, time period, and depth.
- **Inspect** a layer's dimension ranges and variables with [`info_layer`][pyo_oracle.info_layer].
- **Subset** easily with [`build_constraints`][pyo_oracle.build_constraints] — no hand-written constraint dicts.
- **Download** to NetCDF/CSV files, optionally restricting to a subset of variables.
- **Load into memory** as a `pandas.DataFrame` or `xarray.Dataset` with [`load_layer`][pyo_oracle.load_layer].

## Installation

```bash
# With pip
pip install pyo-oracle

# Load layers as xarray (optional extra)
pip install "pyo-oracle[xarray]"

# With conda
conda create -n pyo_oracle conda-forge::pyo-oracle
```

## Quick example

```python
import pyo_oracle as pyo

# Discover layers
pyo.list_layers(search="Temperature")

# Inspect one
pyo.info_layer("thetao_baseline_2000_2019_depthsurf")

# Build constraints and load into memory
constraints = pyo.build_constraints(
    "thetao_baseline_2000_2019_depthsurf",
    latitude=(0, 10),
    longitude=(0, 10),
)
df = pyo.load_layer(
    "thetao_baseline_2000_2019_depthsurf",
    constraints=constraints,
    variables=["thetao_mean"],
)
```

See the [Quickstart](quickstart.md) and [Tutorials](tutorials/listing-and-filtering.md)
to go further, or browse the [Gallery](gallery/index.md) for visualisation recipes.
