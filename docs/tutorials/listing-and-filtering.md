# Listing and filtering layers

Bio-ORACLE exposes hundreds of layers. [`list_layers`][pyo_oracle.list_layers]
helps you find the ones you need.

## All layers

```python
import pyo_oracle as pyo

df = pyo.list_layers()
df.head()
```

By default a `pandas.DataFrame` is returned. Pass `dataframe=False` to get a
plain list of dataset IDs instead.

## Free-text search

```python
pyo.list_layers(search="Oxygen")
pyo.list_layers(search=["Temperature", "Salinity"])  # OR across terms
```

The search matches against the dataset ID, title, long name and standard name.

## Structured filters

You can combine any of the following filters:

| Argument | Valid values |
|----------|--------------|
| `variables` | `chl, clt, dfe, mlotst, no3, o2, ph, phyc, po4, si, siconc, sithick, so, swd, sws, tas, terrain, thetao` |
| `ssp` | `ssp119, ssp126, ssp245, ssp370, ssp460, ssp585, baseline` |
| `time_period` | `present`, `future` |
| `depth` | `min, mean, max, surf` |

```python
# Future projections of phosphate under two SSP scenarios, as IDs
pyo.list_layers(
    variables="po4",
    ssp=["ssp119", "ssp126"],
    time_period="future",
    dataframe=False,
)
```

## Simplify the output

```python
pyo.list_layers(variables="thetao", simplify=True)  # only datasetID + title
```

!!! tip
    Results are cached, so repeated calls with the same filters (in any order)
    are instant and return the same object.
