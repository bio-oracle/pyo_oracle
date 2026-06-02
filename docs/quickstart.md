# Quickstart

This page walks through the full workflow: **list → inspect → subset → load/download → manage local data.**

## 1. List available layers

```python
import pyo_oracle as pyo

# All layers as a DataFrame
layers = pyo.list_layers()

# Free-text search
pyo.list_layers(search="Temperature")

# Filter by variable, scenario, time period, depth
pyo.list_layers(variables=["thetao"], time_period="present", depth="surf")

# Just the dataset IDs
ids = pyo.list_layers(variables="thetao", dataframe=False)
```

## 2. Inspect a layer

```python
pyo.info_layer("thetao_baseline_2000_2019_depthsurf")
```

This prints the dimension ranges (time, latitude, longitude, and depth when
present) and the available variables with their units. It also returns a
dictionary you can use programmatically.

## 3. Build constraints

Instead of hand-writing the griddap constraint dictionary, use
[`build_constraints`][pyo_oracle.build_constraints]:

```python
constraints = pyo.build_constraints(
    "thetao_baseline_2000_2019_depthsurf",
    time=("2000-01-01T00:00:00Z", "2010-01-01T00:00:00Z"),
    latitude=(0, 10),
    longitude=(0, 10),
    latitude_step=2,   # take every 2nd grid cell along latitude
)
```

When the `dataset_id` is supplied, requested bounds are checked against the
dataset's real ranges and a warning is emitted if they fall outside.

`build_constraints` just returns a plain dictionary, which you can also write or
edit by hand. For its full structure — and what happens when you pass no
constraints — see [The constraints dictionary](constraints.md).

## 4. Load into memory or download to disk

```python
# In-memory DataFrame
df = pyo.load_layer(
    "thetao_baseline_2000_2019_depthsurf",
    constraints=constraints,
    variables=["thetao_mean"],
)

# In-memory xarray.Dataset (requires the `xarray` extra)
ds = pyo.load_layer(
    "thetao_baseline_2000_2019_depthsurf",
    constraints=constraints,
    fmt="xarray",
)

# Download to a NetCDF file
pyo.download_layers(
    "thetao_baseline_2000_2019_depthsurf",
    constraints=constraints,
    variables=["thetao_mean"],
)
```

Prefer just the request URL (to share, email, or fetch elsewhere)? Use
[`get_layer_url`][pyo_oracle.get_layer_url]:

```python
url = pyo.get_layer_url(
    "thetao_baseline_2000_2019_depthsurf",
    constraints=constraints,
    variables=["thetao_mean"],
    response="nc",
)
```

## 5. Manage local data

```python
pyo.list_local_data()
```

## Configuration

`pyo_oracle` stores a small config (data directory, ERDDAP server URL,
confirmation prompts):

```python
pyo.print_config_values()
pyo.update_setting("skip_confirmation", "True")
```
