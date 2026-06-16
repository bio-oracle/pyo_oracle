"""Render every figure used by the documentation Gallery.

This script is the single source of truth for the pictures embedded in
``docs/gallery/*.md``. It hits the live Bio-ORACLE ERDDAP server, so it is *not*
run during the (offline, ``--strict``) docs build — instead run it locally and
commit the resulting PNGs:

    pip install -e ".[viz,docs]"
    python docs/gallery/generate_images.py

All figures share one visual style (see ``setup_style``) so the Gallery looks
cohesive. Grids are deliberately coarse and the DPI modest to keep the committed
PNGs small.
"""

from __future__ import annotations

from pathlib import Path

import cmocean
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
import xarray as xr

import pyo_oracle as pyo

IMAGES = Path(__file__).parent / "images"

# Native Bio-ORACLE grid is 0.05 deg; ``*_step`` values are strides over it.
GLOBAL_STEP = 20  # -> 1 deg, good enough for global maps and fast to fetch.

# Dataset ids (baseline year ranges differ per variable — confirmed live).
THETAO_SURF = "thetao_baseline_2000_2019_depthsurf"
THETAO_SSP585_SURF = "thetao_ssp585_2020_2100_depthsurf"
SCENARIOS = {
    "SSP1-2.6": "thetao_ssp126_2020_2100_depthsurf",
    "SSP2-4.5": "thetao_ssp245_2020_2100_depthsurf",
    "SSP5-8.5": "thetao_ssp585_2020_2100_depthsurf",
}
THETAO_DEPTHS = {
    "Surface": "thetao_baseline_2000_2019_depthsurf",
    "Mean depth": "thetao_baseline_2000_2019_depthmean",
    "Max depth": "thetao_baseline_2000_2019_depthmax",
}
BASELINE_VARS = {  # variable -> (dataset_id, column)
    "thetao": ("thetao_baseline_2000_2019_depthmean", "thetao_mean"),
    "o2": ("o2_baseline_2000_2018_depthmean", "o2_mean"),
    "ph": ("ph_baseline_2000_2018_depthmean", "ph_mean"),
    "so": ("so_baseline_2000_2019_depthmean", "so_mean"),
}


def setup_style() -> None:
    """One cohesive look for every figure."""
    sns.set_theme(style="whitegrid", context="talk")
    plt.rcParams.update(
        {
            "figure.dpi": 120,
            "savefig.dpi": 120,
            "savefig.bbox": "tight",
            "figure.facecolor": "white",
            "axes.titleweight": "bold",
        }
    )


def save(fig: plt.Figure, name: str) -> None:
    out = IMAGES / name
    fig.savefig(out)
    plt.close(fig)
    print(f"  wrote {out.relative_to(Path.cwd())}")


def load_global(dataset_id: str, variables, step: int = GLOBAL_STEP):
    """Load a coarse global subset as an xarray.Dataset."""
    constraints = pyo.build_constraints(
        dataset_id,
        latitude=(-89.975, 89.975),
        longitude=(-179.975, 179.975),
        latitude_step=step,
        longitude_step=step,
    )
    return pyo.load_layer(
        dataset_id, constraints=constraints, variables=variables, fmt="xarray"
    )


# --------------------------------------------------------------------------- #
# Page 1 — Global maps & projections
# --------------------------------------------------------------------------- #
def global_maps() -> None:
    print("global maps...")
    ds = load_global(THETAO_SURF, ["thetao_mean"])
    sst = ds["thetao_mean"].isel(time=0)

    # Fig 1 — plain xarray map with an oceanographic colormap.
    fig, ax = plt.subplots(figsize=(11, 5.5))
    sst.plot(
        ax=ax,
        cmap=cmocean.cm.thermal,
        cbar_kwargs={"label": "Sea surface temperature (°C)"},
    )
    ax.set_title("Mean sea surface temperature — baseline (2000–2019)")
    save(fig, "sst_global.png")

    # Fig 2 — cartopy Robinson projection with coastlines.
    import cartopy.crs as ccrs

    fig = plt.figure(figsize=(11, 5.5))
    ax = plt.axes(projection=ccrs.Robinson())
    sst.plot(
        ax=ax,
        transform=ccrs.PlateCarree(),
        cmap=cmocean.cm.thermal,
        cbar_kwargs={"label": "Sea surface temperature (°C)", "shrink": 0.7},
    )
    ax.coastlines(linewidth=0.4)
    ax.set_global()
    ax.set_title("Sea surface temperature on a Robinson projection")
    save(fig, "sst_robinson.png")

    # Fig 3 — regional zoom over the Coral Triangle (finer grid, pcolormesh).
    constraints = pyo.build_constraints(
        THETAO_SURF,
        latitude=(-15, 25),
        longitude=(90, 165),
        latitude_step=4,
        longitude_step=4,
    )
    region = pyo.load_layer(
        THETAO_SURF, constraints=constraints, variables=["thetao_mean"], fmt="xarray"
    )
    fig, ax = plt.subplots(figsize=(9, 6))
    region["thetao_mean"].isel(time=0).plot.pcolormesh(
        ax=ax,
        cmap=cmocean.cm.thermal,
        cbar_kwargs={"label": "Sea surface temperature (°C)"},
    )
    ax.set_title("Coral Triangle — a marine biodiversity hotspot")
    save(fig, "sst_region.png")


# --------------------------------------------------------------------------- #
# Page 2 — Climate change
# --------------------------------------------------------------------------- #
def climate_change() -> None:
    print("climate change...")
    base = load_global(THETAO_SURF, ["thetao_mean"])["thetao_mean"].isel(time=0)
    future = load_global(THETAO_SSP585_SURF, ["thetao_mean"])["thetao_mean"].isel(
        time=-1
    )  # 2090
    delta = future - base

    # Fig 1 — warming delta map (diverging colormap centred on 0).
    fig, ax = plt.subplots(figsize=(11, 5.5))
    limit = float(abs(delta).quantile(0.99))
    delta.plot(
        ax=ax,
        cmap=cmocean.cm.balance,
        vmin=-limit,
        vmax=limit,
        cbar_kwargs={"label": "Temperature change (°C)"},
    )
    ax.set_title("Projected SST change by 2090 — SSP5-8.5 minus baseline")
    save(fig, "warming_delta.png")

    # Fig 2 — faceted scenario maps at 2090.
    layers = []
    for label, dsid in SCENARIOS.items():
        da = load_global(dsid, ["thetao_mean"])["thetao_mean"].isel(time=-1)
        layers.append(da)
    facet = xr.concat(layers, dim=pd.Index(list(SCENARIOS), name="scenario"))
    fg = facet.plot(
        col="scenario",
        col_wrap=3,
        cmap=cmocean.cm.thermal,
        figsize=(15, 4.5),
        cbar_kwargs={"label": "SST (°C)"},
    )
    fg.fig.suptitle("Sea surface temperature in 2090 across SSP scenarios", y=1.03)
    save(fg.fig, "scenario_facets.png")

    # Fig 3 — regional-mean projection trends (North Atlantic).
    fig, ax = plt.subplots(figsize=(10, 6))
    for label, dsid in SCENARIOS.items():
        constraints = pyo.build_constraints(
            dsid,
            time=("2020-01-01T00:00:00Z", "2090-01-01T00:00:00Z"),
            latitude=(30, 60),
            longitude=(-60, 0),
            latitude_step=8,
            longitude_step=8,
        )
        da = pyo.load_layer(
            dsid, constraints=constraints, variables=["thetao_mean"], fmt="xarray"
        )["thetao_mean"]
        series = da.mean(dim=["latitude", "longitude"])
        years = [int(str(t)[:4]) for t in series["time"].values]
        ax.plot(years, series.values, marker="o", label=label)
    ax.set_xlabel("Year")
    ax.set_ylabel("Mean SST (°C)")
    ax.set_title("North Atlantic SST projections (2020–2090)")
    ax.legend(title="Scenario")
    save(fig, "projection_trends.png")


# --------------------------------------------------------------------------- #
# Page 3 — Distributions & latitudinal gradients
# --------------------------------------------------------------------------- #
def distributions() -> None:
    print("distributions...")
    ds = load_global(THETAO_SURF, ["thetao_min", "thetao_mean", "thetao_max"])

    # Fig 1 — zonal mean with a min–max band.
    zonal = ds.mean(dim="longitude").isel(time=0)
    lat = zonal["latitude"].values
    fig, ax = plt.subplots(figsize=(8, 7))
    ax.fill_betweenx(
        lat,
        zonal["thetao_min"].values,
        zonal["thetao_max"].values,
        color="tab:blue",
        alpha=0.2,
        label="min–max range",
    )
    ax.plot(zonal["thetao_mean"].values, lat, color="tab:red", lw=2.5, label="mean")
    ax.set_xlabel("Sea surface temperature (°C)")
    ax.set_ylabel("Latitude (°)")
    ax.set_title("Latitudinal temperature gradient")
    ax.legend()
    save(fig, "zonal_mean.png")

    # Fig 2 — distribution of SST (pandas/seaborn, KDE overlaid).
    df = ds["thetao_mean"].isel(time=0).to_dataframe().dropna()
    fig, ax = plt.subplots(figsize=(9, 5.5))
    sns.histplot(df["thetao_mean"], bins=50, kde=True, color="teal", ax=ax)
    ax.set_xlabel("Sea surface temperature (°C)")
    ax.set_title("Global distribution of sea surface temperature")
    save(fig, "sst_distribution.png")

    # Fig 3 — temperature by depth layer (violin).
    frames = []
    for label, dsid in THETAO_DEPTHS.items():
        d = load_global(dsid, ["thetao_mean"])["thetao_mean"].isel(time=0)
        sub = d.to_dataframe().dropna()[["thetao_mean"]]
        sub["Depth layer"] = label
        frames.append(sub)
    long = pd.concat(frames, ignore_index=True)
    fig, ax = plt.subplots(figsize=(9, 6))
    sns.violinplot(
        data=long,
        x="Depth layer",
        y="thetao_mean",
        hue="Depth layer",
        palette="crest",
        legend=False,
        ax=ax,
    )
    ax.set_ylabel("Temperature (°C)")
    ax.set_title("Temperature distribution by depth layer (baseline)")
    save(fig, "violin_depths.png")


# --------------------------------------------------------------------------- #
# Page 4 — Multi-variable relationships
# --------------------------------------------------------------------------- #
def multivariable() -> None:
    print("multivariable...")
    merged = None
    for var, (dsid, col) in BASELINE_VARS.items():
        da = load_global(dsid, [col])[col].isel(time=0, drop=True)
        da = da.rename(var)
        merged = da if merged is None else xr.merge([merged, da])
    df = merged.to_dataframe().dropna().reset_index()

    # Fig 1 — temperature vs dissolved oxygen (hexbin density).
    fig, ax = plt.subplots(figsize=(8.5, 6.5))
    hb = ax.hexbin(df["thetao"], df["o2"], gridsize=45, cmap=cmocean.cm.dense, mincnt=1)
    fig.colorbar(hb, ax=ax, label="number of grid cells")
    ax.set_xlabel("Temperature (°C)")
    ax.set_ylabel("Dissolved oxygen (mmol/m³)")
    ax.set_title("Surface temperature vs. dissolved oxygen")
    save(fig, "temp_oxygen_hexbin.png")

    # Fig 2 — correlation heatmap across variables.
    corr = df[["thetao", "o2", "ph", "so"]].rename(
        columns={
            "thetao": "Temperature",
            "o2": "Oxygen",
            "ph": "pH",
            "so": "Salinity",
        }
    ).corr()
    fig, ax = plt.subplots(figsize=(7, 6))
    sns.heatmap(
        corr,
        annot=True,
        fmt=".2f",
        cmap=cmocean.cm.balance,
        vmin=-1,
        vmax=1,
        square=True,
        linewidths=0.5,
        ax=ax,
    )
    ax.set_title("Correlations among surface ocean variables")
    save(fig, "corr_heatmap.png")


def main() -> None:
    IMAGES.mkdir(parents=True, exist_ok=True)
    setup_style()
    global_maps()
    climate_change()
    distributions()
    multivariable()
    print("done.")


if __name__ == "__main__":
    main()
