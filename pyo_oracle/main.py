"""
Main module with library functions.
"""
from copy import deepcopy
from functools import lru_cache
from pathlib import Path

import httpx
import pandas as pd
from erddapy import ERDDAP

from pyo_oracle.config import config


default_server = ERDDAP(
    server=config["erddap_server"],
)


def _format_args(function):
    """
    Converts list/str to tuple.

    Prevent TypeError when passing list to function with lru_cache.

    From: https://stackoverflow.com/questions/49210801/python3-pass-lists-to-function-with-functools-lru-cache
    """
    def wrapper(*args, **kwargs):
        kwargs = {k: tuple(x) if type(x) == list else x for k, x in kwargs.items()}
        kwargs = {k: (x,) if type(x) == str else x for k, x in kwargs.items()}
        args = [tuple(x) if type(x) == list else x for x in args]
        args = [(x,) if type(x) == str else x for x in args]
        result = function(*args, **kwargs)
        return result
    return wrapper


def _validate_argument(name: str, value: str or list or tuple, valid_values: list):
    """Check if argument is in a valid list of values."""
    if value:
        for v in value:
            if v.lower() not in valid_values:
                print(f"Selected {name} '{v}' is not a valid {name}. These are valid values:\n{valid_values}")


def download_layers(dataset_ids: str or list, output_directory: str or Path = None, response: str = "nc", constraints: dict = None, skip_confirmation=False):
    """
    Downloads one or more layers.
    """
    if isinstance(dataset_ids, str):
        dataset_ids = (dataset_ids,)

    if not skip_confirmation:
        response = input("No constraints have been set. This will download the full dataset, which may be a few GBs in size. Would you like to proceed? y/N")
        if response.lower() not in "y yes".split():
            print("Download cancelled.")
            return

    s = deepcopy(default_server)
    for dataset_id in dataset_ids:
        url = _get_griddap_dataset_url(dataset_id, constraints=constraints, response=response)  # Response is converted to 
        filename = f"{dataset_id}.{response}"
        outdir = output_directory if output_directory else config["data_directory"]
        local_path = Path(outdir).joinpath(filename)
        _download_file_from_url(url, local_path)
        


def _download_file_from_url(url: str, local_path: Path):
    """
    Downloads a large file from a URL.
    From: https://stackoverflow.com/questions/16694907/download-large-file-in-python-with-requests
    """
    with open(local_path, "wb") as f:
        with httpx.stream("GET", url) as response:
            for chunk in response.iter_bytes():
                f.write(chunk)
    return local_path




def _get_griddap_dataset_url(
    dataset_id,
    variables=None,
    constraints=None,
    response="nc",
    _print=False,
):
    printer = lambda message: print(message) if _print else None

    server = deepcopy(default_server)
    server.dataset_id = dataset_id
    server.protocol = "griddap"
    server.griddap_initialize()

    printer(f"Selected '{dataset_id}' dataset.")
    printer(f"Dataset info available at: {server.get_info_url()}")

    # Setting constraints that match
    if constraints:
        constraints = {**server._constraints_original, **constraints}
        for k, v in constraints.items():
            if k in server.constraints.keys():
                server.constraints[k] = v
                server._constraints_original[k] = v

    # The same for variables
    if variables:
        server.variables = [v for v in server.variables if v in variables]
    printer(
        f"Selected {len(server.variables)} variables: {server.variables}."
    )
    url = server.get_download_url(response=response)
    return url


@lru_cache(2)
def _layer_dataframe(include_allDatasets=False):
    """
    Requests the list of layers as a pandas DataFrame.
    
        include_allDatasets (bool): whether to include the row with the 'allDatasets' dataset.
    """
    s = deepcopy(default_server)
    s.dataset_id = "allDatasets"
    s.protocol = "tabledap"
    df = s.to_pandas()

    if not include_allDatasets:
        df = df.iloc[1:]
    return df


@_format_args
@lru_cache(8)
def list_layers(variables: str or list = None, ssp: str or list = None, time_period: str = None, dataframe: bool = True, _include_allDatasets: bool = False) -> pd.DataFrame or list:
    """
    Lists available layers in the Bio-ORACLE server.

        variables (str|list): variables to filter from. Valid values are ['po4','o2','si','ph','sws','phyc','so','thetao','dfe','no3','sithick','tas','siconc','chl','mlotst','clt','terrain'].
        ssp (str|list): future scenario to choose from. Valid values are ['ssp119', 'ssp126', 'ssp370', 'ssp585', 'ssp460', 'ssp245', 'baseline'].
        time_period (str): time period to choose from. Valie values are either 'present' or 'future'.
        dataframe (bool): whether to return a Pandas DataFrame. If False, will return a list.
    """
    valid_variables = ['po4','o2','si','ph','sws','phyc','so','thetao','dfe','no3','sithick','tas','siconc','chl','mlotst','clt','terrain']
    valid_ssp = ['ssp119', 'ssp126', 'ssp370', 'ssp585', 'ssp460', 'ssp245', 'baseline']
    valid_time_period = "present future".split()

    for arg in "variables", "ssp", "time_period":
        _validate_argument(arg, eval(arg), eval(f"valid_{arg}"))

    _dataframe = _layer_dataframe(_include_allDatasets)
    # Filter resulting dataframe
    if variables:
        _dataframe = pd.concat([_dataframe[_dataframe["datasetID"].str.startswith(v.lower())] for v in variables])
    if time_period:
        start_decade = _dataframe["datasetID"].str.split("_", expand=True)[2]
        if time_period == ("present",):
            _dataframe = _dataframe[start_decade == "2000"]
        elif time_period == ("future",):
            _dataframe = _dataframe[start_decade == "2020"]
    if ssp:
        _dataframe = pd.concat([_dataframe[(_dataframe["datasetID"].str.contains(v.lower())) | (_dataframe["datasetID"].str.contains(v.capitalize())) | (_dataframe["datasetID"].str.contains(v.upper()))] for v in ssp])

    # Convert to list
    if dataframe:
        return _dataframe.reset_index(drop=True)
    else:
        return _dataframe["datasetID"].to_list()


def list_local_data():
    """
    Lists datasets that are locally downloaded.
    """
    pass
