# Working with xarray

For gridded analysis and plotting, load layers directly into an
`xarray.Dataset` with [`load_layer`][pyo_oracle.load_layer]. This requires the
optional `xarray` extra:

```bash
pip install "pyo-oracle[xarray]"
```

## Load a subset as xarray

```python
import pyo_oracle as pyo

ds_id = "thetao_baseline_2000_2019_depthsurf"
constraints = pyo.build_constraints(
    ds_id,
    latitude=(-60, 60),
    longitude=(-180, 180),
    latitude_step=4,
    longitude_step=4,
)

ds = pyo.load_layer(ds_id, constraints=constraints, variables=["thetao_mean"], fmt="xarray")
ds
```

`ds` is a standard `xarray.Dataset` with `time`, `latitude` and `longitude`
coordinates, so the whole xarray ecosystem is available.

## Quick map

```python
import matplotlib.pyplot as plt

ds["thetao_mean"].isel(time=0).plot(figsize=(10, 5), cmap="thermal")
plt.title("Mean sea surface temperature (baseline)")
plt.show()
```

For publication-quality maps with coastlines and projections, combine with
[`cartopy`](https://scitools.org.uk/cartopy/):

```python
import cartopy.crs as ccrs

ax = plt.axes(projection=ccrs.Robinson())
ds["thetao_mean"].isel(time=0).plot(
    ax=ax, transform=ccrs.PlateCarree(), cmap="thermal"
)
ax.coastlines()
plt.show()
```

## pandas instead

If you prefer tabular data (e.g. to join with occurrence records for species
distribution modelling), use the default `fmt="pandas"`:

```python
df = pyo.load_layer(ds_id, constraints=constraints, variables=["thetao_mean"])
df.head()
```
