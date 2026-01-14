from pathlib import Path

import pandas as pd
import pytest
from erddapy import ERDDAP

import pyo_oracle as pyo


@pytest.fixture(scope="session")
def test_data_dir(tmp_path_factory):
    test_data_dir = tmp_path_factory.mktemp("test_dir")
    return test_data_dir


@pytest.fixture
def constraints():
    constraints = {
        "time>=": "2000-01-01T00:00:00Z",
        "time<=": "2010-01-01T12:00:00Z",
        "time_step": 100,
        "latitude>=": 0,
        "latitude<=": 10,
        "latitude_step": 100,
        "longitude>=": 0,
        "longitude<=": 10,
        "longitude_step": 1,
    }
    return constraints


@pytest.fixture
def layer():
    layer = "thetao_baseline_2000_2019_depthsurf"
    return layer


def test_list_layers():
    # Simple call
    layers_df_all = pyo.list_layers()
    assert isinstance(layers_df_all, pd.DataFrame)
    assert layers_df_all.empty is False

    # Test variables
    layers_df_filter = pyo.list_layers(
        variables={
            "po4",
        }
    )
    assert isinstance(layers_df_filter, pd.DataFrame)
    assert layers_df_filter.empty is False
    assert len(layers_df_filter) < len(layers_df_all)

    # Test ssp
    layers_df_filter = pyo.list_layers(
        ssp=(
            "ssp119",
        )
    )
    assert isinstance(layers_df_filter, pd.DataFrame)
    assert layers_df_filter.empty is False
    assert len(layers_df_filter) < len(layers_df_all)

    # Test time
    layers_df_filter = pyo.list_layers(time_period="present")
    assert isinstance(layers_df_filter, pd.DataFrame)
    assert layers_df_filter.empty is False
    assert len(layers_df_filter) < len(layers_df_all)

    # Test depth
    layers_df_filter = pyo.list_layers(depth=["mean", "surf"], simplify=True)
    assert isinstance(layers_df_filter, pd.DataFrame)
    assert layers_df_filter.empty is False
    assert len(layers_df_filter) < len(layers_df_all)

    # Test list
    layers_list = pyo.list_layers(
        variables="po4", ssp=["ssp119", "ssp126"], time_period="future", dataframe=False
    )
    assert isinstance(layers_list, list)
    assert len(layers_list) > 0

    # Test search
    layers_search = pyo.list_layers(
        search=["temperature"]
    )
    assert isinstance(layers_search, pd.DataFrame)
    assert layers_search.empty is False
    assert len(layers_search) < len(layers_df_all)


def test_download_layers(layer, constraints, test_data_dir):
    pyo.download_layers(
        layer,
        output_directory=test_data_dir,
        response="csv",
        constraints=constraints,
        skip_confirmation=True,
    )


def test_list_local_data():
    pyo.list_local_data(
        test_data_dir,
    )
    pyo.list_local_data(test_data_dir, verbose=True)


def test_manual_erddapy_requests(layer, constraints, test_data_dir):
    e = ERDDAP(server=pyo.config["erddap_server"], protocol="griddap")
    e.dataset_id = layer
    e.griddap_initialize()
    e.constraints = constraints
    e._constraints_original = constraints
    df = e.to_pandas()
    assert isinstance(df, pd.DataFrame)
    assert df.empty is False
    outfile = test_data_dir.joinpath(f"{layer}.csv")
    df.to_csv(outfile)
    assert Path(outfile).exists()
