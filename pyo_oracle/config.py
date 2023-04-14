"""
Module to handle configuration, such as data directory, etc.
"""
import configparser
from pathlib import Path
from erddapy import ERDDAP


_default_config = {
    "data_directory": str(Path(__file__).parent.joinpath("data/").absolute()),
    "erddap_server": "http://erddap.bio-oracle.org:8080/erddap/",
}

config_file = Path(__file__).absolute().parent.joinpath(("config.ini"))


def create_config(default_config: dict = _default_config, path: str = None) -> None:
    """
    Creates the configuration file.
    """
    config = configparser.ConfigParser()
    config["DEFAULT"] = default_config
    if config_file.exists():
        response = input(
            f"Config file '{config_file}' already exists, overwrite it? y/N \n"
        )
        if (response.lower() not in "y yes") or (not response):
            print("Operation cancelled.\n")
            return
    with open(config_file, "w") as f:
        config.write(f)
        print(f"Created configuration at '{config_file}'.")


def _get_default_config() -> configparser.ConfigParser:
    if config_file.exists():
        current_config = configparser.ConfigParser()
        _ = current_config.read(config_file)
        return current_config
    else:
        try:
            print("Config file doesn't exist, creating it.")
            create_config()
            return _get_default_config()
        except Exception as e:
            print(
                f"Error: could not load or create configuration file. Loading default values."
            )
            config = configparser.ConfigParser()
            config["DEFAULT"] = _default_config
            return config


def get_config_path() -> Path:
    """
    Returns the path to the config file.
    """
    if config_file.exists():
        return config_file
    else:
        print("Config file doesn't exist, creating it.")
        create_config()
        get_config_path()


def print_config_values() -> None:
    """
    Prints configuration values.
    """
    if not config_file.exists():
        print("Config file doesn't exist, creating it.")
        create_config()
    print(f"Configuration values in '{config_file}' are as following:\n")
    for key, value in _get_default_config()["DEFAULT"].items():
        print(key, "\t", value)
    print()
    print(
        f"Edit the configuration file '{config_file}' or use the 'update_setting' function in this module to edit them."
    )


def update_setting(key, value) -> None:
    """
    Modifies a setting in the configuration file.
    """
    config = _get_default_config()
    config["DEFAULT"][key] = value
    with open(config_file, "w") as f:
        config.write(f)
    print(f"Successfully updated config file at '{config_file}'.")


config = dict(_get_default_config()["DEFAULT"])
default_server = ERDDAP(
    server=config["erddap_server"],
)
