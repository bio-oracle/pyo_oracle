"""Offline unit tests for helpers that do not require network access.

Functions that normally reach the Bio-ORACLE server are exercised here by
mocking the network boundary (``_build_griddap_server``, ``_get_griddap_dataset_url``,
``_download_file_from_url``, ``_layer_info``) so the suite stays fast and
deterministic.
"""

from pathlib import Path

import httpx
import pytest

from pyo_oracle import utils
from pyo_oracle.utils import (
    _as_bool,
    _download_file_from_url,
    _download_layer,
    _ensure_hashable,
    _layer_info,
    _validate_argument,
    build_constraints,
    confirm,
    convert_bytes,
)


# --------------------------------------------------------------------------- #
# Pure helpers
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize(
    "value, expected",
    [
        (True, True),
        (False, False),
        ("True", True),
        ("true", True),
        ("False", False),
        ("false", False),
        ("1", True),
        ("0", False),
        ("yes", True),
        ("no", False),
        (1, True),
        (0, False),
        (1.0, True),
        (None, False),
    ],
)
def test_as_bool(value, expected):
    assert _as_bool(value) is expected


def test_convert_bytes():
    assert convert_bytes(0) == "0.0 bytes"
    assert convert_bytes(1024) == "1.0 KB"
    assert convert_bytes(1024 * 1024) == "1.0 MB"
    assert convert_bytes(1024 ** 4) == "1.0 TB"


def test_ensure_hashable():
    assert _ensure_hashable(None) is None
    assert _ensure_hashable("a") == ("a",)
    assert _ensure_hashable(["b", "a"]) == ("a", "b")
    assert _ensure_hashable({"b", "a"}) == ("a", "b")


def test_ensure_hashable_rejects_unhashable_input():
    with pytest.raises(ValueError):
        _ensure_hashable(123)


# --------------------------------------------------------------------------- #
# _validate_argument
# --------------------------------------------------------------------------- #
class TestValidateArgument:
    def test_none_is_ok(self, capsys):
        _validate_argument("variables", None, {"thetao"})
        assert capsys.readouterr().out == ""

    def test_valid_str(self, capsys):
        _validate_argument("variables", "thetao", {"thetao"})
        assert capsys.readouterr().out == ""

    def test_invalid_str_prints(self, capsys):
        _validate_argument("variables", "bogus", {"thetao"})
        assert "not a valid variables" in capsys.readouterr().out

    def test_invalid_in_iterable_prints(self, capsys):
        _validate_argument("variables", ["thetao", "bogus"], {"thetao"})
        assert "bogus" in capsys.readouterr().out


# --------------------------------------------------------------------------- #
# confirm
# --------------------------------------------------------------------------- #
class TestConfirm:
    def test_yes(self, monkeypatch):
        monkeypatch.setattr("builtins.input", lambda *_: "y")
        assert confirm("proceed?") is True

    def test_no(self, monkeypatch, capsys):
        monkeypatch.setattr("builtins.input", lambda *_: "n")
        assert confirm("proceed?") is False
        assert "cancelled" in capsys.readouterr().out.lower()


# --------------------------------------------------------------------------- #
# build_constraints
# --------------------------------------------------------------------------- #
class TestBuildConstraints:
    def test_full_constraints(self):
        c = build_constraints(
            time=("2000-01-01T00:00:00Z", "2010-01-01T00:00:00Z"),
            latitude=(0, 10),
            longitude=(0, 10),
            latitude_step=2,
            validate=False,
        )
        assert c == {
            "time>=": "2000-01-01T00:00:00Z",
            "time<=": "2010-01-01T00:00:00Z",
            "time_step": 1,
            "latitude>=": 0,
            "latitude<=": 10,
            "latitude_step": 2,
            "longitude>=": 0,
            "longitude<=": 10,
            "longitude_step": 1,
        }

    def test_partial_constraints(self):
        c = build_constraints(latitude=(0, 5), validate=False)
        assert set(c) == {"latitude>=", "latitude<=", "latitude_step"}

    def test_empty_constraints(self):
        assert build_constraints(validate=False) == {}

    def test_depth_included(self):
        c = build_constraints(depth=(0, 100), depth_step=5, validate=False)
        assert c["depth>="] == 0
        assert c["depth<="] == 100
        assert c["depth_step"] == 5

    def test_validate_within_range_no_warning(self, monkeypatch, recwarn):
        monkeypatch.setattr(
            utils,
            "_layer_info",
            lambda _id: {"dimensions": {"latitude": (-90, 90)}},
        )
        build_constraints("fake", latitude=(0, 10))
        assert len(recwarn) == 0

    def test_validate_out_of_range_warns(self, monkeypatch):
        monkeypatch.setattr(
            utils,
            "_layer_info",
            lambda _id: {"dimensions": {"latitude": (-90, 90)}},
        )
        with pytest.warns(UserWarning, match="outside the dataset range"):
            build_constraints("fake", latitude=(-200, 10))

    def test_validate_lookup_failure_warns(self, monkeypatch):
        def boom(_id):
            raise RuntimeError("offline")

        monkeypatch.setattr(utils, "_layer_info", boom)
        with pytest.warns(UserWarning, match="Could not fetch ranges"):
            build_constraints("fake", latitude=(0, 10))

    def test_validate_incomparable_bounds_ignored(self, monkeypatch):
        # Non-numeric bounds against a numeric range hit the TypeError guard
        # and are silently skipped (no warning, constraint still emitted).
        monkeypatch.setattr(
            utils,
            "_layer_info",
            lambda _id: {"dimensions": {"latitude": (-90, 90)}},
        )
        c = build_constraints("fake", latitude=("a", "b"))
        assert c["latitude>="] == "a"


def test_get_griddap_dataset_url(monkeypatch):
    class _UrlServer:
        def get_download_url(self, response="nc"):
            return f"https://x/griddap/ds.{response}"

    monkeypatch.setattr(utils, "_build_griddap_server", lambda *a, **k: _UrlServer())
    url = utils._get_griddap_dataset_url("ds", response="csv")
    assert url == "https://x/griddap/ds.csv"


# --------------------------------------------------------------------------- #
# _layer_info (network boundary mocked)
# --------------------------------------------------------------------------- #
class _FakeServer:
    def __init__(self, info_csv=None, raise_info=False):
        self.constraints = {
            "latitude>=": -90,
            "latitude<=": 90,
            "longitude>=": -180,
            "longitude<=": 180,
        }
        self.variables = ["thetao_mean"]
        self._info_csv = info_csv
        self._raise_info = raise_info

    def get_info_url(self, response="csv"):
        if self._raise_info:
            raise RuntimeError("no network")
        return str(self._info_csv)


def _write_info_csv(path: Path) -> Path:
    path.write_text(
        "Row Type,Variable Name,Attribute Name,Data Type,Value\n"
        "attribute,thetao_mean,units,String,degree_C\n"
        "attribute,thetao_mean,long_name,String,Average OceanTemperature\n"
    )
    return path


class TestLayerInfo:
    def test_success(self, monkeypatch, tmp_path):
        _layer_info.cache_clear()
        csv = _write_info_csv(tmp_path / "info.csv")
        monkeypatch.setattr(
            utils, "_build_griddap_server", lambda _id: _FakeServer(info_csv=csv)
        )
        info = _layer_info("ds-success")
        assert info["dataset_id"] == "ds-success"
        assert info["dimensions"]["latitude"] == (-90, 90)
        assert info["variables"]["thetao_mean"]["units"] == "degree_C"
        assert info["variables"]["thetao_mean"]["long_name"] == "Average OceanTemperature"

    def test_metadata_fallback(self, monkeypatch):
        _layer_info.cache_clear()
        monkeypatch.setattr(
            utils, "_build_griddap_server", lambda _id: _FakeServer(raise_info=True)
        )
        info = _layer_info("ds-fallback")
        # Falls back to bare variable names when metadata can't be read.
        assert info["variables"]["thetao_mean"] == {"units": None, "long_name": None}


# --------------------------------------------------------------------------- #
# _download_file_from_url (httpx mocked with respx)
# --------------------------------------------------------------------------- #
import respx  # noqa: E402


@respx.mock
def test_download_file_from_url(tmp_path):
    url = "https://example.org/data.nc"
    respx.get(url).mock(return_value=httpx.Response(200, content=b"hello-bytes"))
    dest = tmp_path / "out.nc"
    result = _download_file_from_url(url, dest)
    assert result == dest
    assert dest.read_bytes() == b"hello-bytes"


# --------------------------------------------------------------------------- #
# _download_layer (network + url building mocked)
# --------------------------------------------------------------------------- #
class TestDownloadLayer:
    def test_writes_file_when_skipping_confirmation(self, monkeypatch, tmp_path):
        monkeypatch.setattr(
            utils, "_get_griddap_dataset_url", lambda *a, **k: "https://x/y.nc"
        )

        def fake_dl(url, local_path, **kwargs):
            Path(local_path).write_text("data")
            return local_path

        monkeypatch.setattr(utils, "_download_file_from_url", fake_dl)

        _download_layer(
            "thetao_test",
            output_directory=tmp_path,
            response="nc",
            skip_confirmation=True,
            timestamp=False,
        )
        assert (tmp_path / "thetao_test.nc").exists()

    def test_cancel_when_existing_layer_and_user_declines(self, monkeypatch, tmp_path):
        # Pre-existing layer with the same prefix triggers the confirmation block.
        (tmp_path / "thetao_test.nc").write_text("old")

        called = {"dl": False}

        def fake_dl(url, local_path, **kwargs):
            called["dl"] = True
            return local_path

        monkeypatch.setattr(utils, "_download_file_from_url", fake_dl)
        monkeypatch.setattr(
            utils, "_get_griddap_dataset_url", lambda *a, **k: "https://x/y.nc"
        )
        monkeypatch.setattr(utils, "confirm", lambda *a, **k: False)

        _download_layer(
            "thetao_test",
            output_directory=tmp_path,
            skip_confirmation=False,
            timestamp=False,
        )
        assert called["dl"] is False

    def test_skip_confirmation_none_reads_config(self, monkeypatch, tmp_path):
        # skip_confirmation=None -> resolved from config via _as_bool.
        monkeypatch.setitem(utils.config, "skip_confirmation", "True")
        monkeypatch.setattr(
            utils, "_get_griddap_dataset_url", lambda *a, **k: "https://x/y.nc"
        )

        def fake_dl(url, local_path, **kwargs):
            Path(local_path).write_text("data")
            return local_path

        monkeypatch.setattr(utils, "_download_file_from_url", fake_dl)

        _download_layer(
            "thetao_test",
            output_directory=tmp_path,
            skip_confirmation=None,
            timestamp=False,
        )
        assert (tmp_path / "thetao_test.nc").exists()
