"""
Module to handle configuration, such as data dir, etc.
"""
import configparser
from pathlib import Path



default_config = {
    "local_data_directory": Path(__file__).joinpath("local_data"),
    "config_file": Path(__file__).joinpath("local_data/config.ini")
}


def create_config(default_config: dict, path: str = None):
    """
    Creates the configuration file.
    """
    config = configparser.ConfigParser("DEFAULT")
    config["DEFAULT"] = default_config
    config_file = Path(config["DEFAULT"]["config_file"]) if not path else path
    if config_file.exists():
        response = input(f"Config file '{config_file}' already exists, overwrite it? y/N")
        if response.lower() not in "y yes":
            print("Operation cancelled.")
            return
    with open(config_file, "w") as f:
        config.write(f)



def show_config_path():
    """
    Returns the path to the config file.
    """
    


def show_config_values():
    """
    Prints configuration values.
    """
    pass


def update_setting(key, value):
    """
    Modifies a setting in the configuration file.
    """
    pass


