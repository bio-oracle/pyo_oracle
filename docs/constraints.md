# The constraints dictionary

Every request that subsets a layer — [`download_layers`][pyo_oracle.download_layers],
[`load_layer`][pyo_oracle.load_layer], and [`get_layer_url`][pyo_oracle.get_layer_url] —
accepts a `constraints` dictionary. It tells the Bio-ORACLE ERDDAP server **which
slice of a layer to return** along each of its dimensions.

You can build it the easy way with
[`build_constraints`][pyo_oracle.build_constraints], or write/edit it by hand.
This page describes its exact structure so you can do either with confidence.

## Anatomy

A layer is a grid with dimensions — typically `time`, `latitude`, `longitude`,
and sometimes `depth`. For each dimension you want to subset, the dictionary
holds **three keys**:

| Key pattern | Meaning | Example value |
|-------------|---------|---------------|
| `"<dim>>="` | Lower bound (inclusive) | `"latitude>=": -40` |
| `"<dim><="` | Upper bound (inclusive) | `"latitude<=": -10` |
| `"<dim>_step"` | Stride — take every *n*-th grid cell | `"latitude_step": 1` |

So a fully specified request looks like this:

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

This maps directly onto ERDDAP's griddap selection syntax
`[(start):(stride):(stop)]` for each dimension.

### Value types

- **`time`** bounds are **ISO 8601 strings** with a trailing `Z`, e.g.
  `"2010-01-01T00:00:00Z"`. (Some datasets contain a single time step — check
  with [`info_layer`][pyo_oracle.info_layer].)
- **`latitude` / `longitude` / `depth`** bounds are **numbers** in the
  dataset's units (degrees, metres).
- **`<dim>_step`** is a positive **integer** stride. `1` keeps every cell; `10`
  keeps every tenth, downsampling the result.

!!! tip "Find the valid ranges first"
    The bounds must fall inside the layer's actual extent. Inspect it before
    building constraints:

    ```python
    info = pyo.info_layer("thetao_baseline_2000_2019_depthsurf")
    info["dimensions"]   # {'time': (min, max), 'latitude': (min, max), ...}
    ```

## Editing it manually

The dictionary is plain Python, so you can edit it like any `dict`. A few common
operations:

```python
# Start from a helper-built dict (or write one from scratch)
constraints = pyo.build_constraints(
    "thetao_baseline_2000_2019_depthsurf",
    latitude=(-40, -10),
    longitude=(110, 155),
)

# Widen the longitude range
constraints["longitude<="] = 180

# Downsample latitude/longitude to every 5th cell
constraints["latitude_step"] = 5
constraints["longitude_step"] = 5

# Drop a dimension entirely (it then defaults to the full range — see below)
for key in ("longitude>=", "longitude<=", "longitude_step"):
    constraints.pop(key, None)
```

### Partial constraints

You do **not** have to specify every dimension. **Any dimension you omit is
returned in full.** For example, constraining only latitude and longitude
returns *all* time steps within that spatial box:

```python
constraints = {
    "latitude>=": 0,
    "latitude<=": 10,
    "longitude>=": 0,
    "longitude<=": 10,
}
```

Internally, your keys are merged on top of the layer's full-range defaults, so
unspecified bounds and strides fall back to "everything, every cell".

## What happens if you don't specify constraints

Omitting `constraints` (or passing `None`) means **no subsetting** — the request
covers the entire global layer, all dimensions, every cell. These layers can be
**several gigabytes**.

- [`download_layers`][pyo_oracle.download_layers] guards against this: with no
  constraints it prints a warning and asks for confirmation before downloading.
  Pass `skip_confirmation=True` (or set it in the config) to proceed without the
  prompt — useful in scripts, but make sure you really want the whole layer.

  ```python
  # Prompts: "No constraints have been set. This will download the full
  #           dataset, which may be a few GBs in size. ... y/N"
  pyo.download_layers("thetao_baseline_2000_2019_depthsurf")
  ```

- [`load_layer`][pyo_oracle.load_layer] and
  [`get_layer_url`][pyo_oracle.get_layer_url] do **not** prompt. Calling
  `load_layer` with no constraints will attempt to pull the **entire layer into
  memory**, which can exhaust RAM. Always pass constraints when loading into
  memory.

!!! warning
    A request with no constraints is the full global layer. Prefer at least a
    spatial or temporal bound, and use [`info_layer`][pyo_oracle.info_layer] to
    confirm the ranges first.

## See also

- [`build_constraints`][pyo_oracle.build_constraints] — build the dictionary
  from friendly `(min, max)` bounds and strides, with optional validation.
- [Downloading and subsetting](tutorials/downloading-and-subsetting.md) — the
  workflow in context.
