"""Offline unit tests for the public functions in ``pyo_oracle.main``.

Network-touching helpers are mocked so these run without hitting the server.
"""

import pandas as pd
import pytest

import pyo_oracle as pyo
from pyo_oracle import main


# --------------------------------------------------------------------------- #
# download_layers (delegates to _download_layer, mocked)
# --------------------------------------------------------------------------- #
class TestDownloadLayers:
    def test_skip_confirmation_passes_through(self, monkeypatch):
        calls = []
        monkeypatch.setattr(
            main, "_download_layer", lambda dataset_id, *a, **k: calls.append(dataset_id)
        )
        pyo.download_layers("thetao_test", skip_confirmation=True)
        assert calls == ["thetao_test"]

    def test_no_constraints_declined_aborts(self, monkeypatch):
        calls = []
        monkeypatch.setattr(main, "_download_layer", lambda *a, **k: calls.append(1))
        # Force the "no constraints" confirmation and decline it.
        monkeypatch.setattr(main, "confirm", lambda *a, **k: False)
        pyo.download_layers("thetao_test", skip_confirmation=False, constraints=None)
        assert calls == []

    def test_no_constraints_accepted_proceeds(self, monkeypatch):
        calls = []
        monkeypatch.setattr(main, "_download_layer", lambda *a, **k: calls.append(1))
        monkeypatch.setattr(main, "confirm", lambda *a, **k: True)
        pyo.download_layers("thetao_test", skip_confirmation=False, constraints=None)
        assert calls == [1]

    def test_uppercase_id_is_lowercased(self, monkeypatch, capsys):
        seen = []
        monkeypatch.setattr(
            main, "_download_layer", lambda dataset_id, *a, **k: seen.append(dataset_id)
        )
        pyo.download_layers("Thetao_TEST", skip_confirmation=True)
        assert seen == ["thetao_test"]
        assert "lowercase" in capsys.readouterr().out

    def test_skip_confirmation_none_reads_config(self, monkeypatch):
        calls = []
        monkeypatch.setattr(main, "_download_layer", lambda *a, **k: calls.append(1))
        monkeypatch.setitem(main.config, "skip_confirmation", "True")
        pyo.download_layers("thetao_test", skip_confirmation=None, constraints=None)
        assert calls == [1]


# --------------------------------------------------------------------------- #
# info_layer (uses _layer_info, mocked)
# --------------------------------------------------------------------------- #
_FAKE_INFO = {
    "dataset_id": "thetao_test",
    "dimensions": {"latitude": (-90, 90), "longitude": (-180, 180)},
    "variables": {
        "thetao_mean": {"units": "degree_C", "long_name": "Average OceanTemperature"},
        "thetao_no_meta": {"units": None, "long_name": None},
    },
    "griddap_constraints": {},
}


class TestInfoLayer:
    def test_returns_info(self, monkeypatch):
        monkeypatch.setattr(main, "_layer_info", lambda _id: _FAKE_INFO)
        info = pyo.info_layer("thetao_test", verbose=False)
        assert info is _FAKE_INFO

    def test_verbose_prints(self, monkeypatch, capsys):
        monkeypatch.setattr(main, "_layer_info", lambda _id: _FAKE_INFO)
        pyo.info_layer("thetao_test", verbose=True)
        out = capsys.readouterr().out
        assert "Dimensions:" in out
        assert "latitude: -90 to 90" in out
        assert "Average OceanTemperature [degree_C]" in out
        # Variable without metadata falls back to its name and no units.
        assert "thetao_no_meta" in out


# --------------------------------------------------------------------------- #
# load_layer (uses _build_griddap_server, mocked)
# --------------------------------------------------------------------------- #
class _FakeServer:
    def to_pandas(self):
        return pd.DataFrame({"thetao_mean": [1.0, 2.0]})

    def to_xarray(self):
        return {"sentinel": "xarray-dataset"}


class TestLoadLayer:
    def test_pandas(self, monkeypatch):
        monkeypatch.setattr(main, "_build_griddap_server", lambda *a, **k: _FakeServer())
        df = pyo.load_layer("thetao_test")
        assert isinstance(df, pd.DataFrame)
        assert list(df.columns) == ["thetao_mean"]

    def test_xarray(self, monkeypatch):
        monkeypatch.setattr(main, "_build_griddap_server", lambda *a, **k: _FakeServer())
        ds = pyo.load_layer("thetao_test", fmt="xarray")
        assert ds == {"sentinel": "xarray-dataset"}

    def test_bad_fmt(self):
        with pytest.raises(ValueError, match="Unsupported fmt"):
            pyo.load_layer("thetao_test", fmt="bogus")


# --------------------------------------------------------------------------- #
# list_local_data
# --------------------------------------------------------------------------- #
_FAKE_DATASETS = pd.DataFrame(
    {
        "datasetID": [
            "thetao_baseline_2000_2019_depthsurf",
            "thetao_ssp119_2020_2100_depthmean",
            "po4_baseline_2000_2018_depthsurf",
            "po4_ssp585_2020_2100_depthmax",
        ],
        "title": [
            "Sea water potential temperature baseline",
            "Sea water potential temperature ssp119",
            "Phosphate baseline",
            "Phosphate ssp585",
        ],
        "long_name": ["temperature", "temperature", "phosphate", "phosphate"],
        "standard_name": ["sea_water_temp", "sea_water_temp", "po4", "po4"],
    }
)


class TestListLayersOffline:
    """Exercise the filtering logic of list_layers without the network."""

    @pytest.fixture(autouse=True)
    def _mock_datasets(self, monkeypatch):
        main._list_layers.cache_clear()
        monkeypatch.setattr(main, "_layer_dataframe", lambda *a, **k: _FAKE_DATASETS.copy())
        yield
        main._list_layers.cache_clear()

    def test_all(self):
        df = pyo.list_layers()
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 4

    def test_filter_variables(self):
        df = pyo.list_layers(variables="po4")
        assert set(df["datasetID"].str.split("_").str[0]) == {"po4"}

    def test_filter_ssp(self):
        df = pyo.list_layers(ssp="ssp119")
        assert df["datasetID"].str.contains("ssp119").all()
        assert len(df) == 1

    def test_filter_time_period_present(self):
        df = pyo.list_layers(time_period="present")
        assert (df["datasetID"].str.split("_").str[2] == "2000").all()

    def test_filter_time_period_future(self):
        df = pyo.list_layers(time_period="future")
        assert (df["datasetID"].str.split("_").str[2] == "2020").all()

    def test_filter_depth(self):
        df = pyo.list_layers(depth="surf")
        assert df["datasetID"].str.contains("depthsurf").all()

    def test_search(self):
        df = pyo.list_layers(search="phosphate")
        assert len(df) == 2

    def test_simplify(self):
        df = pyo.list_layers(simplify=True)
        assert list(df.columns) == ["datasetID", "title"]

    def test_return_list(self):
        result = pyo.list_layers(variables="po4", dataframe=False)
        assert isinstance(result, list)
        assert all(isinstance(x, str) for x in result)

    def test_invalid_variable_warns(self, capsys):
        pyo.list_layers(variables="not_a_var")
        assert "not a valid variables" in capsys.readouterr().out


class TestListLocalData:
    def test_empty_directory(self, monkeypatch, tmp_path, capsys):
        monkeypatch.setitem(main.config, "data_directory", str(tmp_path))
        pyo.list_local_data()
        assert "does not contain any data" in capsys.readouterr().out

    def test_with_files_verbose(self, monkeypatch, tmp_path, capsys):
        monkeypatch.setitem(main.config, "data_directory", str(tmp_path))
        (tmp_path / "layer.nc").write_text("data")
        (tmp_path / "layer.log").write_text("log")
        pyo.list_local_data(verbose=True)
        out = capsys.readouterr().out
        assert "layer.nc" in out
        assert "Size of data directory" in out

    def test_with_files_non_verbose_hides_logs(self, monkeypatch, tmp_path, capsys):
        monkeypatch.setitem(main.config, "data_directory", str(tmp_path))
        (tmp_path / "layer.nc").write_text("data")
        (tmp_path / "layer.log").write_text("log")
        pyo.list_local_data(verbose=False)
        out = capsys.readouterr().out
        assert "layer.nc" in out
        assert "layer.log" not in out
