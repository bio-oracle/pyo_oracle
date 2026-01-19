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


class TestListLayers:
    """Tests for the `pyo.list_layers` function with various filters."""

    @pytest.fixture(scope="class")
    def all_layers(self) -> pd.DataFrame:
        """Fixture to fetch all layers once for the class."""
        return pyo.list_layers()

    def test_simple_call(self):
        all_layers = pyo.list_layers()
        assert isinstance(all_layers, pd.DataFrame)
        assert not all_layers.empty

    def test_filter_variables(self, all_layers: pd.DataFrame):
        df = pyo.list_layers(variables=["po4"])
        assert isinstance(df, pd.DataFrame)
        assert not df.empty
        assert len(df) < len(all_layers)

    def test_filter_ssp(self, all_layers: pd.DataFrame):
        df = pyo.list_layers(ssp=["ssp119"])
        assert isinstance(df, pd.DataFrame)
        assert not df.empty
        assert len(df) < len(all_layers)

    def test_filter_time_period(self, all_layers: pd.DataFrame):
        df = pyo.list_layers(time_period="present")
        assert isinstance(df, pd.DataFrame)
        assert not df.empty
        assert len(df) < len(all_layers)

    def test_filter_depth(self, all_layers: pd.DataFrame):
        df = pyo.list_layers(depth=["mean", "surf"], simplify=True)
        assert isinstance(df, pd.DataFrame)
        assert not df.empty
        assert len(df) < len(all_layers)

    def test_return_list(self):
        layers_list = pyo.list_layers(
            variables="po4",
            ssp=["ssp119", "ssp126"],
            time_period="future",
            dataframe=False,
        )
        assert isinstance(layers_list, list)
        assert len(layers_list) > 0
        assert all(isinstance(layer, str) for layer in layers_list)

    def test_search_query(self, all_layers: pd.DataFrame):
        df = pyo.list_layers(search=["temperature"])
        assert isinstance(df, pd.DataFrame)
        assert not df.empty
        assert len(df) < len(all_layers)

    def test_caching_order_independence(self):
        df1 = pyo.list_layers(variables=["po4", "chl"], ssp=["ssp119", "ssp126"])
        df2 = pyo.list_layers(variables=["chl", "po4"], ssp=["ssp126", "ssp119"])
        assert df1 is df2  # Same object for caching

    def test_iterable_type_independence(self):
        df1 = pyo.list_layers(variables=["po4", "chl"], ssp=["ssp119", "ssp126"])
        df2 = pyo.list_layers(variables=("po4", "chl"), ssp=("ssp119", "ssp126"))
        df3 = pyo.list_layers(variables={"po4", "chl"}, ssp={"ssp119", "ssp126"})
        assert df1 is df2
        assert df1 is df3


def test_download_layers(layer, constraints, test_data_dir):
    pyo.download_layers(
        layer,
        output_directory=test_data_dir,
        response="csv",
        constraints=constraints,
        skip_confirmation=True,
    )


def test_list_local_data(test_data_dir):
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
