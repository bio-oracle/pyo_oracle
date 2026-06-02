"""Offline unit tests for helpers that do not require network access."""

import pytest

from pyo_oracle.utils import (
    _as_bool,
    _ensure_hashable,
    build_constraints,
    convert_bytes,
)


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
        (None, False),
    ],
)
def test_as_bool(value, expected):
    assert _as_bool(value) is expected


def test_convert_bytes():
    assert convert_bytes(0) == "0.0 bytes"
    assert convert_bytes(1024) == "1.0 KB"
    assert convert_bytes(1024 * 1024) == "1.0 MB"


def test_ensure_hashable():
    assert _ensure_hashable(None) is None
    assert _ensure_hashable("a") == ("a",)
    # order independence
    assert _ensure_hashable(["b", "a"]) == ("a", "b")
    assert _ensure_hashable({"b", "a"}) == ("a", "b")


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
