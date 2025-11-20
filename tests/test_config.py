import configparser

import pytest

import pyo_oracle._config as config_module


@pytest.fixture
def temp_config_path(tmp_path, monkeypatch):
    """Use a temporary config file to avoid mutating the real one."""
    path = tmp_path / "config.ini"
    monkeypatch.setattr(config_module, "config_file", path)
    return path


def _read_config(path):
    parser = configparser.ConfigParser()
    parser.read(path)
    return parser


def test_create_config_creates_file_with_defaults(temp_config_path):
    config_module.create_config()

    parser = _read_config(temp_config_path)
    assert temp_config_path.exists()
    assert parser["DEFAULT"]["data_directory"] == config_module._default_config["data_directory"]
    assert parser["DEFAULT"]["erddap_server"] == config_module._default_config["erddap_server"]
    assert parser["DEFAULT"]["skip_confirmation"] == str(
        config_module._default_config["skip_confirmation"]
    )


def test_create_config_does_not_overwrite_without_confirmation(
    temp_config_path, monkeypatch
):
    temp_config_path.write_text("[DEFAULT]\nkey=original\n")
    monkeypatch.setattr("builtins.input", lambda *_: "n")

    config_module.create_config(default_config={"key": "new-value"})

    parser = _read_config(temp_config_path)
    assert parser["DEFAULT"]["key"] == "original"


def test_get_config_path_creates_missing_file(temp_config_path):
    created_path = config_module.get_config_path()

    assert created_path == temp_config_path
    assert temp_config_path.exists()


def test_update_setting_writes_changes(temp_config_path):
    config_module.create_config()

    config_module.update_setting("custom_key", "custom_value")
    parser = _read_config(temp_config_path)
    assert parser["DEFAULT"]["custom_key"] == "custom_value"


def test_print_config_values_outputs_defaults(temp_config_path, capsys):
    config_module.create_config()

    config_module.print_config_values()
    output = capsys.readouterr().out
    assert str(temp_config_path) in output
    for key in ("data_directory", "erddap_server", "skip_confirmation"):
        assert key in output
