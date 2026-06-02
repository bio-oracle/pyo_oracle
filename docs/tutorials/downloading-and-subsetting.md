# Downloading and subsetting

Bio-ORACLE layers are global and can be several gigabytes. Subsetting before
downloading keeps requests fast and small.

## Inspect first

Always check a layer's real ranges before subsetting:

```python
import pyo_oracle as pyo

info = pyo.info_layer("thetao_baseline_2000_2019_depthsurf")
info["dimensions"]   # {'time': (...), 'latitude': (...), 'longitude': (...)}
info["variables"]    # {'thetao_mean': {'units': 'degree_C', 'long_name': ...}, ...}
```

## Build constraints

[`build_constraints`][pyo_oracle.build_constraints] turns friendly `(min, max)`
bounds and strides into the griddap dictionary ERDDAP expects:

```python
constraints = pyo.build_constraints(
    "thetao_baseline_2000_2019_depthsurf",
    time=("2000-01-01T00:00:00Z", "2010-01-01T00:00:00Z"),
    latitude=(-40, -10),
    longitude=(110, 155),
    latitude_step=1,
    longitude_step=1,
)
```

The equivalent hand-written dictionary (still accepted) looks like:

```python
constraints = {
    "time>=": "2000-01-01T00:00:00Z",
    "time<=": "2010-01-01T00:00:00Z",
    "time_step": 1,
    "latitude>=": -40,
    "latitude<=": -10,
    "latitude_step": 1,
    "longitude>=": 110,
    "longitude<=": 155,
    "longitude_step": 1,
}
```

### Strides

`*_step` arguments take every *n*-th grid cell along a dimension — a quick way
to downsample a large region.

For the full anatomy of this dictionary — every key, value types, partial
constraints, and how to edit it by hand — see
[The constraints dictionary](../constraints.md).

## Restrict variables

Most layers ship several statistics (`_mean`, `_min`, `_max`, `_range`, ...).
Download only what you need:

```python
pyo.download_layers(
    "thetao_baseline_2000_2019_depthsurf",
    constraints=constraints,
    variables=["thetao_mean"],
    response="nc",          # or "csv"
)
```

## Where files go

Downloads land in the configured data directory (see
[`print_config_values`][pyo_oracle.print_config_values]) unless you pass
`output_directory=`. A `.log` file recording the constraints is written next to
each download.

```python
pyo.list_local_data()
```

!!! warning
    Calling `download_layers` without constraints downloads the **entire global
    layer**. `pyo_oracle` will ask for confirmation first; pass
    `skip_confirmation=True` to bypass the prompt in scripts. See
    [What happens if you don't specify constraints](../constraints.md#what-happens-if-you-dont-specify-constraints).
